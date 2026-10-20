"""
# Ontology: app.services.generators.game.decomposer

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
    Tuple,
    Callable
)

# Application Libraries
import app.config.settings as settings
from app.assets.base import (
    Asset,
    Frame,
    Animation,
    HitboxSchema
)
from app.config.enums import (
    AssetCategories,
    AssetInstances,
    Columns,
    Enclosures,
    LayerProjections,
    Orientations,
    MultipliedAssets,
    MultiplicationStrategies,
    Shortcuts,
    Substrates
)
from app.services.generators.game.factory import Factory
from app.models.config import (
    CompositionConfiguration,
    RecipeConfiguration
)
from app.models.properties import (
    PropertiesSchema,
    CraftProperties,
)
from app.models.state import (
    PropertyState,
    CraftState,
    DoorState,
    AssetState
)

# Cython Libraries
from libs.core.models import (
    Position,
    Multiple
)

logger = logging.getLogger(__name__)


class Decomposer:
    compositions: Dict[str, CompositionConfiguration]
    properties: PropertiesSchema
    recipes: RecipeConfiguration
    _increment: int
    _strategies: Dict[str, Callable]

    def __init__(
        self,
        compositions: Dict[str, CompositionConfiguration],
        properties: PropertiesSchema,
        recipes: RecipeConfiguration
    ):
        self.compositions = compositions
        self.properties = properties
        self.recipes = recipes
        self._increment = 0
        self._strategies = {
            MultiplicationStrategies.SIMPLE.value: self._multiply_simple,
            MultiplicationStrategies.ORIENTED.value: self._multiply_oriented,
            MultiplicationStrategies.EXPANSION.value: self._multiply_expansion,
            MultiplicationStrategies.PERIMETER.value: self._multiply_perimeter,
        }

    # ---------------------------------------------------------
    # ---------------------------------------- HELPER UTILITIES
    # ---------------------------------------------------------

    def _get_length(self, cat_key: str, inst_key: str, asset_id: str) -> int:
        """Retrieves static length (l) property for an asset ID."""
        cat_props = getattr(self.properties, cat_key)
        inst_props = getattr(cat_props, inst_key)
        props = inst_props.get(asset_id)
        if not props or not props.dimensions:
            return 0
        return props.dimensions.l

    # ---------------------------------------------------------
    # ------------------------------------- HYDRATION UTILITIES
    # ---------------------------------------------------------

    def _resolve_layer(
        self,
        layer: Optional[str],
        root_layer: Optional[str],
        inc: int,
        layer_map: Dict[str, str]
    ) -> Optional[str]:
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

    def _resolve_anchor(
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
        self_l = self._get_length(self_cat, self_inst, self_state.id)

        target_y = 0
        target_l = 0

        if target_ref == "parent":
            target_y = parent_context.get("pseudo_y", 0)
            target_l = parent_context.get("length", 0)
        elif target_ref == "root":
            target_y = 0
            target_l = root_context.get("length", 0)
        elif target_ref in scope_lookup:
            target_state, target_cat, target_inst = scope_lookup[target_ref]
            target_y = target_state.position.y if target_state.position else 0
            target_l = self._get_length(target_cat, target_inst, target_state.id)
        else:
            logger.warning(
                f"Decomposer: Unable to resolve anchor target '{target_ref}' "
                f"on component '{self_state.name}'. Defaulting to anchor=0."
            )
            return 0

        return int((target_y + target_l) - (self_y + self_l))

    def _hydrate_state(
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
        if layer_map is None:
            layer_map = root_context.setdefault("_layer_map", {})

        kwargs = {}
        for f in dataclasses.fields(state_obj):
            val = getattr(state_obj, f.name)
            kwargs[f.name] = self._resolve_bind(val, root_context, parent_context)

        root_layer = root_context.get("layer")

        # 1. Resolve Layer Namespacing
        if "layer" in kwargs:
            if kwargs["layer"]:
                kwargs["layer"] = self._resolve_layer(kwargs["layer"], root_layer, inc, layer_map)
            else:
                kwargs["layer"] = parent_context["layer"]

        if "owner" in kwargs and not kwargs["owner"]:
            kwargs["owner"] = parent_context["owner"]

        if kwargs.get("elevation") is None:
            kwargs["elevation"] = parent_context.get("elevation", 0)

        # 2. Resolve Outlayer for Doors/Portals
        if "outlayer" in kwargs and kwargs["outlayer"]:
            kwargs["outlayer"] = self._resolve_layer(kwargs["outlayer"], root_layer, inc, layer_map)

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
        kwargs["anchor"] = self._resolve_anchor(
            raw_anchor,
            state_obj,
            cat_key,
            inst_key,
            scope_lookup or {},
            parent_context,
            root_context
        )

        base_inst = inst_key[:-1] if inst_key.endswith("s") else inst_key

        if is_strut:
            b_name = kwargs.get("name") or root_context["name"]
            kwargs["name"] = settings.SEPARATOR.join([base_inst, b_name, str(inc)])
        else:
            comp_name = kwargs.get("name") or "comp"
            kwargs["name"] = settings.SEPARATOR.join([base_inst, parent_context["name"], comp_name, str(inc)])

        return type(state_obj)(**kwargs)

    def _create_asset(
        self,
        cat_key: str,
        inst_key: str,
        state_obj: AssetState
    ) -> Asset:
        cat_recipes = getattr(self.recipes, cat_key)
        recipe = getattr(cat_recipes, inst_key)

        prop_instance_key = (
            AssetInstances.SPRITES.value
            if cat_key == AssetCategories.SHEETS.value \
                and inst_key == AssetInstances.PLAYERS.value
            else inst_key
        )

        cat_props = getattr(self.properties, cat_key)
        inst_props = getattr(cat_props, prop_instance_key)
        props = inst_props.get(state_obj.id)

        taxonomy = Factory.taxonomy(
            state_obj.id, 
            state_obj.name, 
            cat_key, 
            inst_key
        )
        frame = Factory.frame(recipe.frame)
        animation = Factory.animation(recipe.animation)
        hitbox = Factory.hitbox(recipe.hitbox)

        return Asset(
            taxonomy, 
            props, 
            state_obj, 
            frame, 
            animation, 
            hitbox
        )

    def _spawn_unit(
        self,
        state: CraftState,
        props: CraftProperties,
        frame: Frame,
        animation: Animation,
        hitbox: HitboxSchema,
        category: str,
        instance: str,
        unit_name: str,
        layer: str,
        pos: Position,
        blueprint: Optional[str],
        anchor: int
    ) -> Asset:
        unit_state = dataclasses.replace(
            state,
            name=unit_name,
            layer=layer,
            position=pos,
            blueprint=blueprint,
            multiple=Multiple(1, 1),
            anchor=anchor
        )
        return Asset(
            taxonomy=Factory.taxonomy(state.id, unit_name, category, instance),
            properties=props,
            state=unit_state,
            frame=frame,
            animation=animation,
            hitbox=hitbox
        )

    # ---------------------------------------------------------
    # ------------------------------- MULTIPLICATION STRATEGIES
    # ---------------------------------------------------------

    def _multiply_simple(
        self,
        state: CraftState,
        props: CraftProperties,
        frame: Frame,
        animation: Animation,
        hitbox: HitboxSchema,
        category: str,
        instance: str,
        base_pos: Position,
        layer: str,
        base_name: str,
        nx: int,
        ny: int
    ) -> List[Asset]:
        w = props.dimensions.w
        l = props.dimensions.l
        base_anchor = int(state.anchor or 0)
        units: List[Asset] = []
        idx = 0

        for iy in range(ny):
            for ix in range(nx):
                seg_pos = Position(base_pos.x + ix * w, base_pos.y + iy * l)
                unit_name = settings.SEPARATOR.join([base_name, str(idx)])
                idx += 1
                units.append(
                    self._spawn_unit(
                        state,
                        props,
                        frame,
                        animation,
                        hitbox,
                        category,
                        instance,
                        unit_name,
                        layer,
                        seg_pos,
                        state.blueprint,
                        base_anchor
                    )
                )
        return units

    def _multiply_oriented(
        self,
        state: CraftState,
        props: CraftProperties,
        frame: Frame,
        animation: Animation,
        hitbox: HitboxSchema,
        category: str,
        instance: str,
        base_pos: Position,
        layer: str,
        base_name: str,
        nx: int,
        ny: int
    ) -> List[Asset]:
        if state.blueprint == Orientations.HORIZONTAL.value:
            ny = 1
        else:
            nx = 1
        return self._multiply_simple(
            state,
            props,
            frame,
            animation,
            hitbox,
            category,
            instance,
            base_pos,
            layer,
            base_name,
            nx,
            ny
        )

    def _multiply_expansion(
        self,
        state: CraftState,
        props: CraftProperties,
        frame: Frame,
        animation: Animation,
        hitbox: HitboxSchema,
        category: str,
        instance: str,
        base_pos: Position,
        layer: str,
        base_name: str,
        nx: int,
        ny: int
    ) -> List[Asset]:
        w = props.dimensions.w
        l = props.dimensions.l
        units: List[Asset] = []
        idx = 0

        for ix in range(nx):
            col_x = base_pos.x + ix * w
            base_y = base_pos.y + (ny + 1) * l
            base_ground = base_y + l

            segments: List[Tuple[str, int]] = [
                (Columns.CROWNS.value, base_pos.y)
            ]
            for k in range(ny):
                segments.append(
                    (Columns.SHAFTS.value, base_pos.y + (k + 1) * l)
                )
            segments.append((Columns.BASES.value, base_y))

            for bp_part, seg_y in segments:
                unit_name = settings.SEPARATOR.join([base_name, bp_part, str(idx)])
                idx += 1
                seg_anchor = int(base_ground - (seg_y + l))
                units.append(
                    self._spawn_unit(
                        state,
                        props,
                        frame,
                        animation,
                        hitbox,
                        category,
                        instance,
                        unit_name,
                        layer,
                        Position(col_x, seg_y),
                        bp_part,
                        seg_anchor
                    )
                )
        return units

    def _multiply_perimeter(
        self,
        state: CraftState,
        props: CraftProperties,
        frame: Frame,
        animation: Animation,
        hitbox: HitboxSchema,
        category: str,
        instance: str,
        base_pos: Position,
        layer: str,
        base_name: str,
        nx: int,
        ny: int
    ) -> List[Asset]:
        w = props.dimensions.w
        l = props.dimensions.l
        units: List[Asset] = []
        idx = 0

        north_hbs = props.hitboxes.get(Enclosures.NORTH.value, []) if props.hitboxes else []
        north_bottom = max((hb.position.y + hb.dimensions.l for hb in north_hbs), default=l)
        north_anchor = int(north_bottom - l)

        # Horizontal caps/shafts across [0, nx + 1] (includes corners)
        for ix in range(nx + 2):
            seg_x = base_pos.x + ix * w
            n_name = settings.SEPARATOR.join([base_name, Enclosures.NORTH.value, str(idx)])
            idx += 1
            units.append(
                self._spawn_unit(
                    state,
                    props,
                    frame,
                    animation,
                    hitbox,
                    category,
                    instance,
                    n_name,
                    layer,
                    Position(seg_x, base_pos.y),
                    Enclosures.NORTH.value,
                    north_anchor
                )
            )

            s_name = settings.SEPARATOR.join([base_name, Enclosures.SOUTH.value, str(idx)])
            idx += 1
            units.append(
                self._spawn_unit(
                    state,
                    props,
                    frame,
                    animation,
                    hitbox,
                    category,
                    instance,
                    s_name,
                    layer,
                    Position(seg_x, base_pos.y + (ny + 1) * l),
                    Enclosures.SOUTH.value,
                    0
                )
            )

        # Vertical interior shafts across [1, ny] (2 * (nx + ny + 2) total perimeter units)
        for iy in range(1, ny + 1):
            seg_y = base_pos.y + iy * l
            w_name = settings.SEPARATOR.join([base_name, Enclosures.WEST.value, str(idx)])
            idx += 1
            units.append(
                self._spawn_unit(
                    state,
                    props,
                    frame,
                    animation,
                    hitbox,
                    category,
                    instance,
                    w_name,
                    layer,
                    Position(base_pos.x, seg_y),
                    Enclosures.WEST.value,
                    0
                )
            )

            e_name = settings.SEPARATOR.join([base_name, Enclosures.EAST.value, str(idx)])
            idx += 1
            units.append(
                self._spawn_unit(
                    state,
                    props,
                    frame,
                    animation,
                    hitbox,
                    category,
                    instance,
                    e_name,
                    layer,
                    Position(base_pos.x + (nx + 1) * w, seg_y),
                    Enclosures.EAST.value,
                    0
                )
            )

        return units

    # ---------------------------------------------------------
    # ------------------------------------- EXPANSION UTILITIES
    # ---------------------------------------------------------

    def _unpack_node(
        self,
        node: Any,
        root_context: Dict[str, Any],
        parent_context: Dict[str, Any],
        inc: int,
        is_root: bool = False
    ) -> List[Asset]:
        assets: List[Asset] = []
        layer_map = root_context.setdefault("_layer_map", {})

        strut_state = self._hydrate_state(
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

        unit_len = self._get_length(
            AssetCategories.CRAFTS.value,
            AssetInstances.STRUTS.value,
            node.strut.id
        )
        ny = strut_state.multiple.ny if strut_state.multiple and strut_state.multiple.ny else 1
        strut_len = unit_len * ny

        node_context = {
            "position": strut_state.position,
            "pseudo_y": node.strut.position.y if node.strut.position else 0,
            "length": strut_len,
            "layer": strut_state.layer,
            "owner": strut_state.owner,
            "name": strut_state.name,
            "elevation": strut_state.elevation
        }

        if is_root:
            root_context["elevation"] = strut_state.elevation
            root_context["length"] = strut_len

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

        layer_map = root_context.setdefault("_layer_map", {})

        # PASS 1: Scope Indexing (collect all named siblings)
        scope_lookup: Dict[str, Tuple[AssetState, str, str]] = {}

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
                    if pseudo_state.name:
                        scope_lookup[pseudo_state.name] = (pseudo_state, cat_key, inst_key)

        # PASS 2: Hydration with Anchor Resolution
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
                        cat_key,
                        inst_key,
                        is_strut=False,
                        layer_map=layer_map,
                        scope_lookup=scope_lookup
                    )

                    if inst_key in MultipliedAssets:
                        assets.extend(self.multiply(new_state, cat_key, inst_key))
                    elif inst_key == AssetInstances.DOORS.value:
                        assets.extend(self.project_door(new_state))
                    else:
                        assets.append(self._create_asset(cat_key, inst_key, new_state))

    # ---------------------------------------------------------
    # ------------------------------------------ PUBLIC METHODS
    # ---------------------------------------------------------

    def project_door(self, state: DoorState) -> List[Asset]:
        """
        Instantiates a primary Door on state.layer and its reciprocal shadow footprint
        on state.outlayer if outlayer and out are specified.
        """
        primary_state = dataclasses.replace(
            state,
            projection=LayerProjections.IN.value
        )
        doors = [
            self._create_asset(
                AssetCategories.OBJECTS.value,
                AssetInstances.DOORS.value,
                primary_state
            )
        ]

        if not state.outlayer or not state.out:
            return doors

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
            out=Position(state.position.x, state.position.y),
            anchor=0,
            projection=LayerProjections.OUT.value
        )
        doors.append(
            self._create_asset(
                AssetCategories.OBJECTS.value,
                AssetInstances.DOORS.value,
                shadow_state
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
            "_layer_map": {}
        }

        assets.extend(self._unpack_node(comp_config.root, root_context, root_context, inc, is_root=True))

        if comp_config.branches:
            for branch in comp_config.branches:
                assets.extend(self._unpack_node(branch, root_context, root_context, inc, is_root=False))

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

        strategy_key = settings.BLUEPRINT_STRATEGIES.get(
            props.blueprints,
            MultiplicationStrategies.SIMPLE.value
        )
        handler = self._strategies.get(strategy_key, self._multiply_simple)

        cat_recipes = getattr(self.recipes, category)
        recipe = getattr(cat_recipes, instance)
        frame = Factory.frame(recipe.frame)
        animation = Factory.animation(recipe.animation)
        hitbox = Factory.hitbox(recipe.hitbox)

        return handler(
            state,
            props,
            frame,
            animation,
            hitbox,
            category,
            instance,
            base_pos,
            layer,
            base_name,
            nx,
            ny
        )