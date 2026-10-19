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
    Tuple
)

# Application Libraries
import app.config.settings as settings
from app.assets.base import Asset
from app.config.enums import (
    AssetCategories, 
    AssetInstances, 
    Columns,
    Orientations, 
    OrientedAssets,
    MultipliedAssets,
    MultiplicationStrategies,
    Shortcuts
)
from app.services.generators.game.factory import Factory
from app.models.config import (
    CompositionConfiguration, 
    RecipeConfiguration
)
from app.models.properties import (
    PropertiesSchema, 
)
from app.models.state import (
    PropertyState, 
    OrientedState, 
    StrutState,
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

    def __init__(self, 
        compositions: Dict[str, CompositionConfiguration], 
        properties: PropertiesSchema, 
        recipes: RecipeConfiguration
    ):
        self.compositions = compositions
        self.properties = properties
        self.recipes = recipes
        self._increment = 0

    # ---------------------------------------------------------
    # ---------------------------------------- HELPER UTILITIES
    # ---------------------------------------------------------

    def _get_length(self, cat_key: str, inst_key: str, asset_id: str) -> int:
        """Retrieves static length (l) property for an asset ID."""
        cat_props = getattr(self.properties, cat_key, None)
        if not cat_props:
            return 0
        inst_props = getattr(cat_props, inst_key, {})
        props = inst_props.get(asset_id)
        return props.dimensions.l if props and props.dimensions else 0


    # ---------------------------------------------------------
    # ------------------------------------- HYDRATION UTILITIES
    # ---------------------------------------------------------

    def _resolve_layer(self, 
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

    
    def _resolve_bind(self, 
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


    def _hydrate_state(self, 
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
            layer_map = root_context.setdefault('_layer_map', {})

        kwargs = {}
        for f in dataclasses.fields(state_obj):
            val = getattr(state_obj, f.name, None)
            kwargs[f.name] = self._resolve_bind(val, root_context, parent_context)
        
        root_layer = root_context.get('layer')

        # 1. Resolve Layer Namespacing
        if 'layer' in kwargs:
            if kwargs['layer']:
                kwargs['layer'] = self._resolve_layer(kwargs['layer'], root_layer, inc, layer_map)
            else:
                kwargs['layer'] = parent_context['layer']

        if 'owner' in kwargs and not kwargs['owner']:
            kwargs['owner'] = parent_context['owner']

        # 2. Resolve Outlayer for Doors/Portals
        if 'outlayer' in kwargs and kwargs['outlayer']:
            kwargs['outlayer'] = self._resolve_layer(kwargs['outlayer'], root_layer, inc, layer_map)

        # 3. Layer Transition Boundary: If moving to an independent layer, reset local origin
        is_cross_layer = str(kwargs.get('layer')) != str(parent_context.get('layer'))
        base_pos = Position(0, 0) if is_cross_layer else parent_context['position']

        pseudo_pos = kwargs.get('position')
        if pseudo_pos:
            kwargs['position'] = Position(
                x=base_pos.x + pseudo_pos.x,
                y=base_pos.y + pseudo_pos.y
            )
        else:
            kwargs['position'] = Position(base_pos.x, base_pos.y)

        # 4. Teleport destination coordinate mapping
        pseudo_out = kwargs.get('out')
        if pseudo_out:
            outlayer = kwargs.get('outlayer')
            if str(outlayer) == str(root_layer):                
                kwargs['out'] = Position(
                    x=root_context['position'].x + pseudo_out.x,
                    y=root_context['position'].y + pseudo_out.y
                )
            else:
                kwargs['out'] = Position(pseudo_out.x, pseudo_out.y)

        # 5. Resolve Anchor Macro (guarantees integer downcast)
        raw_anchor = kwargs.get('anchor', 0)
        kwargs['anchor'] = self._resolve_anchor(
            raw_anchor,
            state_obj,
            cat_key,
            inst_key,
            scope_lookup or {},
            parent_context,
            root_context
        )

        base_inst = inst_key[:-1] if inst_key.endswith('s') else inst_key
        
        if is_strut:
            b_name = kwargs.get('name') or root_context['name']
            kwargs['name'] = settings.SEPARATOR.join([base_inst, b_name, str(inc)])
        else:
            comp_name = kwargs.get('name') or 'comp'
            kwargs['name'] = settings.SEPARATOR.join([base_inst, parent_context['name'], comp_name, str(inc)])
                
        return type(state_obj)(**kwargs)


    def _create_asset(self, 
        cat_key: str, 
        inst_key: str, 
        state_obj: AssetState
    ) -> Asset:
        cat_recipes = getattr(self.recipes, cat_key, None)
        recipe = getattr(cat_recipes, inst_key, None)
        
        prop_instance_key = inst_key

        if cat_key == AssetCategories.SHEETS.value and \
            inst_key == AssetInstances.PLAYERS.value:
            prop_instance_key = AssetInstances.SPRITES.value
            
        cat_props = getattr(self.properties, cat_key, None)
        inst_props = getattr(cat_props, prop_instance_key, {}) 
        props = inst_props.get(state_obj.id)
        
        taxonomy = Factory.taxonomy(state_obj.id, state_obj.name, cat_key, inst_key)
        frame = Factory.frame(recipe.frame)
        animation = Factory.animation(recipe.animation)
        hitbox = Factory.hitbox(recipe.hitbox)
        
        return Asset(taxonomy, props, state_obj, frame, animation, hitbox)

    # ---------------------------------------------------------
    # ------------------------------------- EXPANSION UTILITIES
    # ---------------------------------------------------------

    def _unpack_node(self, 
        node: Any, 
        root_context: Dict[str, Any], 
        parent_context: Dict[str, Any], 
        inc: int, 
        is_root: bool = False
    ) -> List[Asset]:
        assets = []
        layer_map = root_context.setdefault('_layer_map', {})

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
        strut_asset = self._create_asset(
            AssetCategories.CRAFTS.value, 
            AssetInstances.STRUTS.value, 
            strut_state
        )
        assets.append(strut_asset)

        strut_len = self._get_length(
            AssetCategories.CRAFTS.value, 
            AssetInstances.STRUTS.value, 
            node.strut.id
        )

        node_context = {
            "position": strut_state.position,
            "pseudo_y": node.strut.position.y if getattr(node.strut, 'position', None) else 0,
            "length": strut_len,
            "layer": strut_state.layer,
            "owner": getattr(strut_state, 'owner', None),
            "name": strut_state.name,
            "elevation": strut_state.elevation
        }
        
        if is_root:
            root_context["elevation"] = strut_state.elevation
            root_context["length"] = strut_len

        self._unpack_components(node.components, root_context, node_context, inc, assets)
        return assets


    def _unpack_components(self, 
        components: Any, 
        root_context: Dict[str, Any], 
        parent_context: Dict[str, Any], 
        inc: int, 
        assets: List[Asset]
    ) -> None:
        if not components: 
            return

        layer_map = root_context.setdefault('_layer_map', {})

        # ---------------------------------------------------------
        # PASS 1: Scope Indexing (collect all named siblings)
        # ---------------------------------------------------------
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
                    if getattr(pseudo_state, "name", None):
                        scope_lookup[pseudo_state.name] = (pseudo_state, cat_key, inst_key)

        # ---------------------------------------------------------
        # PASS 2: Hydration with Anchor Resolution
        # ---------------------------------------------------------
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
                    
                    if inst_key in OrientedAssets:
                        assets.extend(self.orient(new_state, cat_key, inst_key))

                    elif inst_key in MultipliedAssets:
                        assets.extend(self.multiply(new_state, cat_key, inst_key))

                    else:
                        assets.append(self._create_asset(cat_key, inst_key, new_state))

    # ---------------------------------------------------------
    # ------------------------------------------ PUBLIC METHODS
    # ---------------------------------------------------------

    def unpack(self, deployed_state: PropertyState) -> List[Asset]:
        assets = []
        comp_config = self.compositions.get(deployed_state.id)
        if not comp_config:
            return assets

        self._increment += 1
        inc = self._increment

        root_context = {
            "id": deployed_state.id,
            "name": getattr(deployed_state, 'name', ''),
            "layer": getattr(deployed_state, 'layer', ''),
            "owner": getattr(deployed_state, 'owner', None),
            "position": getattr(deployed_state, 'position', Position(0, 0)),
            "elevation": getattr(deployed_state, 'elevation', 0),
            "_layer_map": {}
        }

        assets.extend(self._unpack_node(comp_config.root, root_context, root_context, inc, is_root=True))

        if comp_config.branches:
            for branch in comp_config.branches:
                assets.extend(self._unpack_node(branch, root_context, root_context, inc, is_root=False))

        return assets


    def orient(self, 
        state: OrientedState, 
        category: str, 
        instance: str
    ) -> List[Asset]:
        cat_props = getattr(self.properties, category, {})
        instance_props = getattr(cat_props, instance, {})
        props = instance_props.get(state.id, None)

        if props is None:
            logger.error(
                settings.SEPARATOR.join([
                    "Decomposer",
                    "OrientationMissingProperties",
                    state.id
                ])
            )
            return []

        w = props.dimensions.w
        l = props.dimensions.l
        orientation = state.orientation
        base_pos = state.position or Position(0, 0)
        layer = state.layer or "0"

        if orientation == Orientations.HORIZONTAL.value:
            count = state.multiple.nx if state.multiple else 1
        else:
            count = state.multiple.ny if state.multiple else 1

        unit_assets: List[Asset] = []
        cat_recipes = getattr(self.recipes, category, None)
        recipe = getattr(cat_recipes, instance, None)

        for i in range(count):
            if orientation == Orientations.HORIZONTAL.value:
                seg_pos = Position(base_pos.x + i * w, base_pos.y)
            else:
                seg_pos = Position(base_pos.x, base_pos.y + i * l)

            unit_name = settings.SEPARATOR.join([
                state.name or state.id,
                str(i)
            ])

            unit_state = OrientedState(
                id=state.id,
                name=unit_name,
                layer=layer,
                position=seg_pos,
                orientation=orientation,
                multiple=Multiple(1, 1),
                owner=state.owner,
                elevation=state.elevation
            )

            unit_asset = Asset(
                taxonomy=Factory.taxonomy(
                    state.id,
                    unit_name,
                    category,
                    instance
                ),
                properties=props,
                state=unit_state,
                frame=Factory.frame(recipe.frame),
                animation=Factory.animation(recipe.animation),
                hitbox=Factory.hitbox(recipe.hitbox)
            )
            unit_assets.append(unit_asset)

        return unit_assets


    def multiply(
        self,
        state: StrutState,
        category: str,
        instance: str
    ) -> List[Asset]:
        cat_props = getattr(self.properties, category, {})
        instance_props = getattr(cat_props, instance, {})
        props = instance_props.get(state.id, None)

        if props is None:
            logger.error(
                settings.SEPARATOR.join([
                    "Decomposer",
                    "MultiplyMissingProperties",
                    state.id
                ])
            )
            return []

        w = props.dimensions.w
        l = props.dimensions.l
        base_pos = state.position
        layer = state.layer
        nx = state.multiple.nx if state.multiple and state.multiple.nx else 1
        ny = state.multiple.ny if state.multiple and state.multiple.ny else 1

        strategy = settings.BLUEPRINT_STRATEGIES.get(
            props.blueprints,
            MultiplicationStrategies.SIMPLE.value
        )

        cat_recipes = getattr(self.recipes, category, None)
        recipe = getattr(cat_recipes, instance, None)
        unit_assets: List[Asset] = []
        idx = 0

        if strategy == MultiplicationStrategies.EXPANSION.value:
            # Column expansion: [crown] + ny * [shaft] + [base] along +y axis
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
                    unit_name = settings.SEPARATOR.join([
                        state.name or state.id,
                        bp_part,
                        str(idx)
                    ])
                    idx += 1
                    seg_anchor = int(base_ground - (seg_y + l))

                    unit_state = dataclasses.replace(
                        state,
                        name=unit_name,
                        layer=layer,
                        position=Position(col_x, seg_y),
                        blueprint=bp_part,
                        multiple=Multiple(1, 1),
                        anchor=seg_anchor
                    )
                    unit_assets.append(
                        Asset(
                            taxonomy=Factory.taxonomy(state.id, unit_name, category, instance),
                            properties=props,
                            state=unit_state,
                            frame=Factory.frame(recipe.frame),
                            animation=Factory.animation(recipe.animation),
                            hitbox=Factory.hitbox(recipe.hitbox)
                        )
                    )
        else:
            # Simple 2D grid multiplication
            for iy in range(ny):
                for ix in range(nx):
                    seg_pos = Position(base_pos.x + ix * w, base_pos.y + iy * l)
                    unit_name = settings.SEPARATOR.join([
                        state.name or state.id,
                        str(idx)
                    ])
                    idx += 1

                    unit_state = dataclasses.replace(
                        state,
                        name=unit_name,
                        layer=layer,
                        position=seg_pos,
                        multiple=Multiple(1, 1)
                    )
                    unit_assets.append(
                        Asset(
                            taxonomy=Factory.taxonomy(state.id, unit_name, category, instance),
                            properties=props,
                            state=unit_state,
                            frame=Factory.frame(recipe.frame),
                            animation=Factory.animation(recipe.animation),
                            hitbox=Factory.hitbox(recipe.hitbox)
                        )
                    )

        return unit_assets