"""
@domain.logic
@app.services
@modality.material
@workflow.compositions

# Ontology: Source - app.services.generators.game.decomposer

Package for decomposing Compositions into their constituent Assets.
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
    Callable
)

# Application Libraries
import app.static.settings as settings
from app.assets.base import Asset
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    LayerProjections,
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
from app.models.properties import PropertiesSchema
from app.models.state import (
    PropertyState,
    CraftState,
    DoorState,
    AssetState
)

# Cython Libraries
from libs.core.models import Position

logger = logging.getLogger(__name__)


class Decomposer:
    """
    Service for hydrating Composition deployments onto the Board, projecting
    reciprocal Door footprints, and dispatching Craft multiplication strategies.
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
    # ------------------------------------- HYDRATION UTILITIES
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


    def _resolve_layer(
        self,
        layer: Optional[str],
        root_layer: Optional[str],
        inc: int,
        layer_map: Dict[str, str]
    ) -> Optional[str]:
        """
        Namespaces internal composition layers with the deployment increment while
        preserving references to the deployed root layer.
        """
        if layer is None or str(layer) == str(root_layer):
            return layer

        layer_str = str(layer)
        if layer_str in layer_map.values():
            return layer_str

        if layer_str not in layer_map:
            layer_map[layer_str] = settings.SEPARATOR.join([layer_str, str(inc)])

        return layer_map[layer_str]


    def _resolve_bind(
        self,
        val: Any,
        root_context: Dict[str, Any],
        parent_context: Dict[str, Any]
    ) -> Any:
        """
        Resolves deferred deployment-time bind(parent.*) and bind(root.*) strings.
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


    def _index_links(
        self,
        comp_config: CompositionConfiguration,
        root_context: Dict[str, Any],
        inc: int
    ) -> Dict[str, str]:
        """
        Pre-indexes hydrated component names across root and branch nodes so
        SwitchState.link references resolve to their namespaced deployment IDs.
        """
        link_map: Dict[str, str] = {}
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
        return link_map


    def _hydrate_state(
        self,
        state_obj: AssetState,
        root_context: Dict[str, Any],
        parent_context: Dict[str, Any],
        inc: int,
        inst_key: str,
        is_strut: bool = False
    ) -> AssetState:
        """
        Hydrates a validated component or strut PseudoState with deployment-time
        coordinates, layer namespacing, and inherited context attributes.
        """
        layer_map = root_context["_layer_map"]
        link_map = root_context["_link_map"]
        root_layer = root_context["layer"]

        kwargs = {}
        for f in dataclasses.fields(state_obj):
            val = getattr(state_obj, f.name)
            kwargs[f.name] = self._resolve_bind(val, root_context, parent_context)

        # 1. Layer, Owner & Elevation Inheritance
        if "layer" in kwargs:
            if kwargs["layer"]:
                kwargs["layer"] = self._resolve_layer(kwargs["layer"], root_layer, inc, layer_map)
            else:
                kwargs["layer"] = parent_context["layer"]

        if "owner" in kwargs and not kwargs["owner"]:
            kwargs["owner"] = parent_context["owner"]

        if kwargs.get("elevation") is None:
            kwargs["elevation"] = parent_context["elevation"]

        # 2. Door Outlayer Namespacing
        if "outlayer" in kwargs and kwargs["outlayer"]:
            kwargs["outlayer"] = self._resolve_layer(kwargs["outlayer"], root_layer, inc, layer_map)

        # 3. Coordinate Translation (reset origin when crossing into an internal layer)
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

        # 4. Teleport Out Coordinate Translation
        pseudo_out = kwargs.get("out")
        if pseudo_out:
            if str(kwargs.get("outlayer")) == str(root_layer):
                kwargs["out"] = Position(
                    x=root_context["position"].x + pseudo_out.x,
                    y=root_context["position"].y + pseudo_out.y
                )
            else:
                kwargs["out"] = Position(pseudo_out.x, pseudo_out.y)

        # 5. SwitchState Link Namespacing
        if "link" in kwargs and kwargs["link"]:
            link_target = str(kwargs["link"])
            if link_target in link_map:
                kwargs["link"] = link_map[link_target]

        # 6. Unique Entity Nomenclature
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
            if cat_key == AssetCategories.SHEETS.value
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

    def _unpack_node(
        self,
        node: Any,
        root_context: Dict[str, Any],
        parent_context: Dict[str, Any],
        inc: int
    ) -> List[Asset]:
        assets: List[Asset] = []

        strut_state = self._hydrate_state(
            node.strut,
            root_context,
            parent_context,
            inc,
            AssetInstances.STRUTS.value,
            is_strut=True
        )
        assets.extend(
            self.multiply(
                strut_state,
                AssetCategories.CRAFTS.value,
                AssetInstances.STRUTS.value
            )
        )

        node_context = {
            "position": strut_state.position,
            "layer": strut_state.layer,
            "owner": strut_state.owner,
            "name": strut_state.name,
            "elevation": strut_state.elevation
        }

        self._unpack_components(node.components, root_context, node_context, inc, assets)
        return assets


    def _unpack_components(
        self,
        components: Any,
        root_context: Dict[str, Any],
        parent_context: Dict[str, Any],
        inc: int,
        assets: List[Asset]
    ) -> None:
        if not components:
            return

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
                    new_state = self._hydrate_state(
                        pseudo_state,
                        root_context,
                        parent_context,
                        inc,
                        inst_key,
                        is_strut=False
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
        """
        Flattens a Composition configuration into a 1D list of hydrated Assets.
        """
        assets: List[Asset] = []
        comp_config = self.compositions.get(deployed_state.id)
        print(comp_config)
        if not comp_config:
            return assets

        self._increment += 1
        inc = self._increment

        root_context: Dict[str, Any] = {
            "id": deployed_state.id,
            "name": deployed_state.name or "",
            "layer": deployed_state.layer or "",
            "owner": deployed_state.owner,
            "position": deployed_state.position or Position(0, 0),
            "elevation": deployed_state.elevation if deployed_state.elevation is not None else 0,
            "_layer_map": {},
            "_link_map": {}
        }
        root_context["_link_map"] = self._index_links(comp_config, root_context, inc)

        assets.extend(self._unpack_node(comp_config.root, root_context, root_context, inc))

        if comp_config.branches:
            for branch in comp_config.branches:
                assets.extend(self._unpack_node(branch, root_context, root_context, inc))

        return assets


    def multiply(
        self,
        state: CraftState,
        category: str,
        instance: str
    ) -> List[Asset]:
        """
        Expands a CraftState into unit Assets according to its Blueprint schema's
        MultiplicationStrategy.
        """
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
        handler = self._strategies.get(
            strategy_key,
            self._strategies[MultiplicationStrategies.SIMPLE.value]
        )

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