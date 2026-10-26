"""
@domain.logic
@app.services
@modality.material
@workflow.compositions

# Ontology: Source - app.services.generators.game.decomposer

Package for decomposing Compositions into their constituent Assets.

## TODOs

1. Induct the terminology into app.static.semantics once it is clear what the terminology is.
    * Composition Context:
        - parent
        - root
    * Composition Macros:
        - bind
        - anchor
"""
# Standard Libraries
import re
import dataclasses
import logging
from typing import (
    Dict,
    List,
    Any,
    Optional,
    Tuple,
    Callable
)

# Application Libraries
import app.static.settings as settings
from app.assets.base import Asset
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    LayerProjections,
    Orientations,
    MultipliedAssets,
    MultiplicationStrategies,
    Shortcuts,
    Substrates
)
from app.services.factories.assets import AssetFactory
from app.game.logic.relations import MaterialIndex
from app.game.logic.modules.multipliers import (
    SimpleMultiplier,
    OrientedMultiplier,
    ExpansionMultiplier,
    PerimeterMultiplier,
)
from app.models.config import (
    CompositionConfiguration,
    RecipeConfiguration
)
from app.models.properties import (
    PropertiesSchema,
)
from app.models.state import (
    PropertyState,
    CraftState,
    DoorState,
    AssetState
)

# Cython Libraries
from libs.core.models import Position

# --------------------------------------------------------------

logger = logging.getLogger(__name__)

# --------------------------------------------------------------

class Decomposer:
    """
    Service for unpacking Composition configurations, hydrating PseudoStates,
    projecting Door footprints, and dispatching Craft multiplication strategies.
    """
    
    compositions: Dict[str, CompositionConfiguration]
    properties: PropertiesSchema
    materials: MaterialIndex
    recipes: RecipeConfiguration
    _increment: int
    _strategies: Dict[str, Callable]

    def __init__(
        self,
        compositions: Dict[str, CompositionConfiguration],
        properties: PropertiesSchema,
        recipes: RecipeConfiguration,
        materials: MaterialIndex
    ):
        self.compositions = compositions
        self.properties = properties
        self.recipes = recipes
        self.materials = materials
        self._increment = 0
        self._strategies = {
            MultiplicationStrategies.SIMPLE.value: SimpleMultiplier(self.materials).multiply,
            MultiplicationStrategies.ORIENTED.value: OrientedMultiplier(self.materials).multiply,
            MultiplicationStrategies.EXPANSION.value: ExpansionMultiplier(self.materials).multiply,
            MultiplicationStrategies.PERIMETER.value: PerimeterMultiplier(self.materials).multiply,
        }

    # ---------------------------------------------------------
    # ---------------------------------------- HELPER UTILITIES
    # ---------------------------------------------------------

    def _get_length(self, cat_key: str, inst_key: str, asset_id: str) -> int:
        """
        Retrieves static length (l) property for an asset ID.
        """
        cat_props = getattr(self.properties, cat_key)
        inst_props = getattr(cat_props, inst_key)
        props = inst_props.get(asset_id)
        if not props or not props.dimensions:
            return 0
        return props.dimensions.l


    def _get_span_length(
        self,
        cat_key: str,
        inst_key: str,
        state_obj: AssetState
    ) -> int:
        """
        Computes total vertical footprint length (l) for an AssetState,
        accounting for Craft multiplication strategies when resolving anchors.
        """
        unit_l = self._get_length(cat_key, inst_key, state_obj.id)
        if (
            inst_key not in MultipliedAssets 
            or not isinstance(state_obj, CraftState)
        ): return unit_l

        cat_props = getattr(self.properties, cat_key)
        inst_props = getattr(cat_props, inst_key)
        props = inst_props.get(state_obj.id)

        if not props: return unit_l

        ny = state_obj.multiple.ny if state_obj.multiple and state_obj.multiple.ny else 1
        strategy = self.materials.strategy(props.blueprints)

        if strategy in (
            MultiplicationStrategies.EXPANSION.value,
            MultiplicationStrategies.PERIMETER.value
        ):
            if state_obj.multiple is None and state_obj.blueprint in self.materials.blueprints(props.blueprints):
                return unit_l
            return unit_l * (ny + 2)

        if strategy == MultiplicationStrategies.ORIENTED.value:
            if state_obj.blueprint == Orientations.HORIZONTAL.value:
                return unit_l
            return unit_l * ny

        return unit_l * ny
    
    # ---------------------------------------------------------
    # ------------------------------------- HYDRATION UTILITIES
    # ---------------------------------------------------------

    def _layer(
        self,
        layer: Optional[str],
        root_layer: Optional[str],
        inc: int,
        layer_map: Dict[str, str]
    ) -> Optional[str]:
        """
        Namespaces internal composition layers per deployment increment while
        preserving references to the root board layer.
        """
        if layer is None or str(layer) == str(root_layer):
            return layer

        layer_str = str(layer)
        if layer_str in layer_map.values():
            return layer_str

        if layer_str not in layer_map:
            layer_map[layer_str] = settings.SEPARATOR.join([layer_str, str(inc)])

        return layer_map[layer_str]


    def _bind(
        self,
        val: Any,
        root_context: Dict[str, Any],
        parent_context: Dict[str, Any]
    ) -> Any:
        """
        Resolves bind(parent.*) and bind(root.*) macros against active contexts.
        """
        if not isinstance(val, str):
            return val

        match_parent = re.match(r"^bind\(parent\.(.*?)\)$", val)
        if match_parent:
            key = match_parent.group(1)
            return parent_context.get(key, val)

        match_root = re.match(r"^bind\((?:root\.)?(.*?)\)$", val)
        if match_root:
            key = match_root.group(1)
            return root_context.get(key, val)

        return val


    def _anchor(
        self,
        anchor_val: Any,
        self_state: AssetState,
        self_cat: str,
        self_inst: str,
        scope_lookup: Dict[str, Tuple[AssetState, str, str]],
        parent_context: Dict[str, Any],
        root_context: Dict[str, Any]
    ) -> int:
        """
        Evaluates anchor(target) macros:
            anchor = (target.y + target.l) - (self.y + self.l)
        Guarantees return value is always a concrete int.
        """
        if not isinstance(anchor_val, str):
            return int(anchor_val) if anchor_val is not None else 0

        match = re.match(r"^anchor\((.*?)\)$", anchor_val.strip())
        if not match:
            try:
                return int(anchor_val)
            except ValueError:
                return 0

        target_ref = match.group(1).strip()
        self_y = self_state.position.y if self_state.position else 0
        self_l = self._get_span_length(self_cat, self_inst, self_state)

        target_y = 0
        target_l = 0

        if target_ref in ("parent", parent_context.get("pseudo_name")):
            target_y = 0
            target_l = parent_context.get("length", 0)
        elif target_ref in ("root", root_context.get("pseudo_name")):
            target_y = 0
            target_l = root_context.get("length", 0)
        elif target_ref in scope_lookup:
            target_state, target_cat, target_inst = scope_lookup[target_ref]
            target_y = target_state.position.y if target_state.position else 0
            target_l = self._get_span_length(target_cat, target_inst, target_state)
        else:
            logger.warning(
                f"Decomposer: Unable to resolve anchor target '{target_ref}' "
                f"on component '{self_state.name}'. Defaulting to anchor=0."
            )
            return 0

        return int((target_y + target_l) - (self_y + self_l))


    def _state(
        self,
        state_obj: AssetState,
        root_context: Dict[str, Any],
        parent_context: Dict[str, Any],
        inc: int,
        cat_key: str,
        inst_key: str,
        is_strut: bool = False,
        layer_map: Optional[Dict[str, str]] = None,
        scope_lookup: Optional[Dict[str, Tuple[AssetState, str, str]]] = None
    ) -> AssetState:
        """
        Hydrates a component or strut PseudoState into a concrete AssetState.
        """
        if layer_map is None:
            layer_map = root_context.setdefault("_layer_map", {})

        kwargs = {}
        for f in dataclasses.fields(state_obj):
            val = getattr(state_obj, f.name)
            kwargs[f.name] = self._bind(val, root_context, parent_context)

        root_layer = root_context.get("layer")

        # 1. Resolve Layer Namespacing
        if "layer" in kwargs:
            if kwargs["layer"]:
                kwargs["layer"] = self._layer(kwargs["layer"], root_layer, inc, layer_map)
            else:
                kwargs["layer"] = parent_context["layer"]

        if "owner" in kwargs and not kwargs["owner"]:
            kwargs["owner"] = parent_context["owner"]

        if kwargs.get("elevation") is None:
            kwargs["elevation"] = parent_context.get("elevation", 0)

        # 2. Resolve Outlayer for Doors/Portals
        if "outlayer" in kwargs and kwargs["outlayer"]:
            kwargs["outlayer"] = self._layer(kwargs["outlayer"], root_layer, inc, layer_map)

        # 3. Layer Transition Boundary: If moving to an independent layer, reset local origin
        is_cross_layer = str(kwargs.get("layer")) != str(parent_context.get("layer"))
        base_pos = Position(0, 0) if is_cross_layer else parent_context["position"]

        pseudo_pos = kwargs.get("position")
        if pseudo_pos:
            kwargs["position"] = Position(
                x=base_pos.x + pseudo_pos.x,
                y=base_pos.y + pseudo_pos.y
            )
        else:
            kwargs["position"] = Position(base_pos.x, base_pos.y)

        # 4. Teleport destination coordinate mapping
        pseudo_out = kwargs.get("out")
        if pseudo_out:
            outlayer = kwargs.get("outlayer")
            if str(outlayer) == str(root_layer):
                kwargs["out"] = Position(
                    x=root_context["position"].x + pseudo_out.x,
                    y=root_context["position"].y + pseudo_out.y
                )
            else:
                kwargs["out"] = Position(pseudo_out.x, pseudo_out.y)

        # 5. Resolve Anchor Macro (guarantees integer downcast)
        raw_anchor = kwargs.get("anchor", 0)
        kwargs["anchor"] = self._anchor(
            raw_anchor,
            state_obj,
            cat_key,
            inst_key,
            scope_lookup or {},
            parent_context,
            root_context
        )

        # 6. Resolve SwitchState link namespacing
        if "link" in kwargs and kwargs["link"]:
            link_target = str(kwargs["link"])
            link_map = root_context.get("_link_map", {})
            if scope_lookup and link_target in scope_lookup:
                _, _, target_inst = scope_lookup[link_target]
                target_base = target_inst[:-1] if target_inst.endswith("s") else target_inst
                kwargs["link"] = settings.SEPARATOR.join([
                    target_base,
                    parent_context["name"],
                    link_target,
                    str(inc)
                ])
            elif link_target in link_map:
                kwargs["link"] = link_map[link_target]

        base_inst = inst_key[:-1] if inst_key.endswith("s") else inst_key

        if is_strut:
            b_name = kwargs.get("name") or root_context["name"]
            kwargs["name"] = settings.SEPARATOR.join([base_inst, b_name, str(inc)])
        else:
            comp_name = kwargs.get("name") or "comp"
            kwargs["name"] = settings.SEPARATOR.join([base_inst, parent_context["name"], comp_name, str(inc)])

        return type(state_obj)(**kwargs)


    def _asset(
        self,
        cat_key: str,
        instance: str,
        state: AssetState,
        substrate: Optional[int] = None
    ) -> Asset:
        if substrate is None:
            substrate = self.materials.substrate(instance)

        cat_recipes = getattr(self.recipes, cat_key)
        recipe = getattr(cat_recipes, instance)

        prop_instance_key = (
            AssetInstances.SPRITES.value
            if cat_key == AssetCategories.SHEETS.value \
                and instance == AssetInstances.PLAYERS.value
            else instance
        )

        cat_props = getattr(self.properties, cat_key)
        inst_props = getattr(cat_props, prop_instance_key)
        props = inst_props.get(state.id)

        return AssetFactory.asset(
            category=cat_key,
            instance=instance,
            properties=props,
            state=state,
            recipe=recipe,
            substrate=substrate
        )


    # ---------------------------------------------------------
    # ------------------------------------- EXPANSION UTILITIES
    # ---------------------------------------------------------

    def _links(
        self,
        comp_config: CompositionConfiguration,
        root_context: Dict[str, Any],
        inc: int
    ) -> None:
        """
        Pre-indexes hydrated component names across root and branch nodes into
        root_context['_link_map'] so cross-node SwitchState.link references resolve.
        """
        link_map = root_context.setdefault("_link_map", {})
        nodes = [comp_config.root]
        if comp_config.branches:
            nodes.extend(comp_config.branches)

        for node in nodes:
            if not node or not node.components:
                continue
            b_name = node.strut.name or root_context["name"]
            parent_name = settings.SEPARATOR.join(["strut", b_name, str(inc)])

            for cat_field in dataclasses.fields(node.components):
                cat_key = cat_field.name
                if cat_key in Shortcuts:
                    continue
                cat_data = getattr(node.components, cat_key)
                if not cat_data:
                    continue
                for inst_field in dataclasses.fields(cat_data):
                    inst_key = inst_field.name
                    inst_list = getattr(cat_data, inst_key)
                    if not inst_list:
                        continue
                    base_inst = inst_key[:-1] if inst_key.endswith("s") else inst_key
                    for pseudo_state in inst_list:
                        if pseudo_state.name:
                            link_map[pseudo_state.name] = settings.SEPARATOR.join([
                                base_inst,
                                parent_name,
                                pseudo_state.name,
                                str(inc)
                            ])


    def _node(
        self,
        node: Any,
        root_context: Dict[str, Any],
        parent_context: Dict[str, Any],
        inc: int,
        is_root: bool = False
    ) -> List[Asset]:
        assets: List[Asset] = []
        layer_map = root_context.setdefault("_layer_map", {})

        strut_state = self._state(
            node.strut,
            root_context,
            parent_context,
            inc,
            AssetCategories.CRAFTS.value,
            AssetInstances.STRUTS.value,
            is_strut=True,
            layer_map=layer_map,
            scope_lookup={}
        )
        assets.extend(
            self.multiply(
                strut_state,
                AssetCategories.CRAFTS.value,
                AssetInstances.STRUTS.value
            )
        )

        strut_len = self._get_span_length(
            AssetCategories.CRAFTS.value,
            AssetInstances.STRUTS.value,
            strut_state
        )

        node_context = {
            "position": strut_state.position,
            "pseudo_y": node.strut.position.y if node.strut.position else 0,
            "length": strut_len,
            "layer": strut_state.layer,
            "owner": strut_state.owner,
            "name": strut_state.name,
            "pseudo_name": node.strut.name,
            "elevation": strut_state.elevation
        }

        if is_root:
            root_context["elevation"] = strut_state.elevation
            root_context["length"] = strut_len
            root_context["pseudo_name"] = node.strut.name

        initial_scope: Dict[str, Tuple[AssetState, str, str]] = {}
        if node.strut.name:
            initial_scope[node.strut.name] = (
                dataclasses.replace(strut_state, position=Position(0, 0)),
                AssetCategories.CRAFTS.value,
                AssetInstances.STRUTS.value
            )

        self._components(
            node.components, 
            root_context, 
            node_context, 
            inc, 
            assets,
            initial_scope
        )
        return assets


    def _components(
        self,
        components: Any,
        root_context: Dict[str, Any],
        parent_context: Dict[str, Any],
        inc: int,
        assets: List[Asset],
        initial_scope: Optional[Dict[str, Tuple[AssetState, str, str]]] = None
    ) -> None:
        if not components:
            return

        layer_map = root_context.setdefault("_layer_map", {})
        link_map = root_context.setdefault("_link_map", {})

        # PASS 1: Scope Indexing (collect all named siblings)
        scope_lookup: Dict[str, Tuple[AssetState, str, str]] = dict(initial_scope or {})

        for cat_field in dataclasses.fields(components):
            cat_key = cat_field.name
            if cat_key in Shortcuts:
                continue

            cat_data = getattr(components, cat_key)
            if not cat_data:
                continue

            for inst_field in dataclasses.fields(cat_data):
                inst_key = inst_field.name
                inst_list = getattr(cat_data, inst_key)
                if not inst_list:
                    continue

                base_inst = inst_key[:-1] if inst_key.endswith("s") else inst_key
                for pseudo_state in inst_list:
                    if pseudo_state.name:
                        scope_lookup[pseudo_state.name] = (pseudo_state, cat_key, inst_key)
                        link_map[pseudo_state.name] = settings.SEPARATOR.join([
                            base_inst,
                            parent_context["name"],
                            pseudo_state.name,
                            str(inc)
                        ])

        # PASS 2: Hydration with Anchor & Link Resolution
        for cat_field in dataclasses.fields(components):
            cat_key = cat_field.name
            if cat_key in Shortcuts:
                continue

            cat_data = getattr(components, cat_key)
            if not cat_data:
                continue

            for inst_field in dataclasses.fields(cat_data):
                inst_key = inst_field.name
                inst_list = getattr(cat_data, inst_key)
                if not inst_list:
                    continue

                for pseudo_state in inst_list:
                    new_state = self._state(
                        pseudo_state,
                        root_context,
                        parent_context,
                        inc,
                        cat_key,
                        inst_key,
                        is_strut=False,
                        layer_map=layer_map,
                        scope_lookup=scope_lookup
                    )

                    if inst_key in MultipliedAssets:
                        assets.extend(self.multiply(new_state, cat_key, inst_key))
                    elif inst_key == AssetInstances.DOORS.value:
                        assets.extend(self.project(new_state))
                    else:
                        assets.append(self._asset(cat_key, inst_key, new_state))

    # ---------------------------------------------------------
    # ------------------------------------------ PUBLIC METHODS
    # ---------------------------------------------------------

    def project(self, state: DoorState) -> List[Asset]:
        """
        Instantiates a primary Door on state.layer (Substrates.STANDARD) and its
        reciprocal shadow footprint on state.outlayer (Substrates.OVERLAYS).
        If state is already an OUT projection, instantiates it directly without duplicating.
        """
        if state.projection == LayerProjections.OUT.value:
            return [
                self._asset(
                    AssetCategories.OBJECTS.value,
                    AssetInstances.DOORS.value,
                    state,
                    substrate=Substrates.OVERLAYS.value
                )
            ]

        primary_state = dataclasses.replace(
            state,
            projection=LayerProjections.IN.value
        )
        doors = [
            self._asset(
                AssetCategories.OBJECTS.value,
                AssetInstances.DOORS.value,
                primary_state,
                substrate=Substrates.STANDARD.value
            )
        ]

        if not state.outlayer or not state.out:
            return doors

        door_l = self._get_length(
            AssetCategories.OBJECTS.value,
            AssetInstances.DOORS.value,
            state.id
        )
        shadow_name = settings.SEPARATOR.join([
            state.name or state.id,
            LayerProjections.OUT.value
        ])
        shadow_state = dataclasses.replace(
            state,
            name=shadow_name,
            layer=state.outlayer,
            position=Position(state.out.x, state.out.y),
            outlayer=state.layer,
            out=Position(state.position.x, state.position.y + door_l),
            anchor=0,
            projection=LayerProjections.OUT.value
        )
        doors.append(
            self._asset(
                AssetCategories.OBJECTS.value,
                AssetInstances.DOORS.value,
                shadow_state,
                substrate=Substrates.OVERLAYS.value
            )
        )
        return doors


    def unpack(self, deployed_state: PropertyState) -> List[Asset]:
        assets: List[Asset] = []
        comp_config = self.compositions.get(deployed_state.id)
        if not comp_config:
            return assets

        self._increment += 1
        inc = self._increment

        root_context = {
            "id": deployed_state.id,
            "name": deployed_state.name or "",
            "layer": deployed_state.layer or "",
            "owner": deployed_state.owner,
            "position": deployed_state.position or Position(0, 0),
            "elevation": deployed_state.elevation if deployed_state.elevation is not None else 0,
            "_layer_map": {},
            "_link_map": {}
        }

        self._links(comp_config, root_context, inc)

        assets.extend(self._node(comp_config.root, root_context, root_context, inc, is_root=True))

        if comp_config.branches:
            for branch in comp_config.branches:
                assets.extend(self._node(branch, root_context, root_context, inc, is_root=False))

        return assets


    def multiply(
        self,
        state: CraftState,
        category: str,
        instance: str
    ) -> List[Asset]:
        cat_props = getattr(self.properties, category)
        instance_props = getattr(cat_props, instance)
        props = instance_props.get(state.id)

        if props is None:
            logger.error(
                settings.SEPARATOR.join([
                    "Decomposer",
                    "MultiplyMissingProperties",
                    state.id
                ])
            )
            return []

        base_pos = state.position or Position(0, 0)
        layer = state.layer or "0"
        nx = state.multiple.nx if state.multiple and state.multiple.nx is not None else 1
        ny = state.multiple.ny if state.multiple and state.multiple.ny is not None else 1
        base_name = state.name or state.id

        strategy_key = self.materials.strategy(props.blueprints)
        handler = self._strategies.get(strategy_key, self._strategies[MultiplicationStrategies.SIMPLE.value])
        
        cat_recipes = getattr(self.recipes, category)
        recipe = getattr(cat_recipes, instance)

        return handler(
            state,
            props,
            recipe,
            category,
            instance,
            base_pos,
            layer,
            base_name,
            nx,
            ny
        )