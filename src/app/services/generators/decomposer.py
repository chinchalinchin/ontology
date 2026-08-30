"""
# Ontology: app.services.generators.decomposer

Package for decomposing Compositions into their constituent Assets. 
"""
# Standard Libraries
import re
import dataclasses
import logging
from typing import (
    Dict, 
    List, 
    Any
)

# Application Libraries
from app.assets.base import Asset
from app.config.enums import (
    AssetCategories, 
    AssetInstances
)
from app.services.factory import Factory
from app.models.config import (
    CompositionConfiguration, 
    RecipeConfiguration
)
from app.models.properties import (
    PropertiesSchema, 
    Cost
)
from app.models.state import (
    PropertyState, 
    AssetState
)

# Cython Libraries
from libs.core.models import Position

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
    # ------------------------------------------ COST UTILITIES

    def _accumulate_cost(self, 
        cat: str, 
        inst: str, 
        asset_id: str, 
        cost_map: Dict[str, int]
    ) -> None:
        if cat == AssetCategories.CRAFTS:
            cat_props = getattr(self.properties.crafts, inst, {})
            props = cat_props.get(asset_id)
            if props and hasattr(props, 'cost') and props.cost:
                for c in props.cost:
                    cost_map[c.item] = cost_map.get(c.item, 0) + c.quantity

    def _aggregate_components_cost(self, 
        components: Any, 
        cost_map: Dict[str, int]
    ) -> None:
        if not components: 
            return
        
        for cat_field in dataclasses.fields(components):
            cat_key = cat_field.name
            cat_data = getattr(components, cat_key)
            if not cat_data: continue
            
            for inst_field in dataclasses.fields(cat_data):
                inst_key = inst_field.name
                inst_list = getattr(cat_data, inst_key)
                if not inst_list: continue
                
                for state_obj in inst_list:
                    self._accumulate_cost(cat_key, inst_key, state_obj.id, cost_map)

    # ---------------------------------------------------------
    # ------------------------------------- HYDRATION UTILITIES

    def _resolve_bind(self, 
        val: Any, 
        root_context: Dict[str, Any], 
        parent_context: Dict[str, Any]
    ) -> Any:
        """
        Map Composition `bind(root|parent.(.*))` binding to context.
        """
        if not isinstance(val, str):
            return val
            
        # Prioritize explicit parent bindings
        match_parent = re.match(r"^bind\(parent\.(.*?)\)$", val)
        if match_parent:
            key = match_parent.group(1)
            return parent_context.get(key, val)
            
        # Support root bindings (and legacy bindings without a prefix)
        match_root = re.match(r"^bind\((?:root\.)?(.*?)\)$", val)
        if match_root:
            key = match_root.group(1)
            return root_context.get(key, val)
            
        return val

    def _hydrate_state(self, 
        state_obj: AssetState, 
        root_context: Dict[str, Any], 
        parent_context: Dict[str, Any], 
        inc: int, 
        inst_key: str, 
        is_strut: bool = False
    ) -> AssetState:
        """
        """
        kwargs = {}
        for f in dataclasses.fields(state_obj):
            val = getattr(state_obj, f.name, None)
            kwargs[f.name] = self._resolve_bind(val, root_context, parent_context)
        
        if 'layer' in kwargs and not kwargs['layer']:
            kwargs['layer'] = parent_context['layer']
        if 'owner' in kwargs and not kwargs['owner']:
            kwargs['owner'] = parent_context['owner']
            
        pseudo_pos = kwargs.get('position')
        if pseudo_pos:
            kwargs['position'] = Position(
                x=parent_context['position'].x + pseudo_pos.x,
                y=parent_context['position'].y + pseudo_pos.y
            )
        else:
            kwargs['position'] = Position(parent_context['position'].x, parent_context['position'].y)

        # Apply spatial superposition to the teleport out coordinate
        pseudo_out = kwargs.get('out')
        if pseudo_out:
            kwargs['out'] = Position(
                x=root_context['position'].x + pseudo_out.x,
                y=root_context['position'].y + pseudo_out.y
            )

        base_inst = inst_key[:-1] if inst_key.endswith('s') else inst_key
        
        if is_strut:
            b_name = kwargs.get('name') or root_context['name']
            kwargs['name'] = f"{base_inst}-{b_name}-{inc}"
        else:
            kwargs['name'] = f"{base_inst}-{parent_context['name']}-{inc}"
        
        return type(state_obj)(**kwargs)

    def _create_asset(self, 
        cat_key: str, 
        inst_key: str, 
        state_obj: AssetState
    ) -> Asset:
        cat_recipes = getattr(self.recipes, cat_key, None)
        recipe = getattr(cat_recipes, inst_key, None) if cat_recipes else None
        
        prop_instance_key = inst_key
        if cat_key == AssetCategories.SHEETS and inst_key == AssetInstances.PLAYERS:
            prop_instance_key = AssetInstances.SPRITES
            
        cat_props = getattr(self.properties, cat_key, None)
        inst_props = getattr(cat_props, prop_instance_key, {}) \
                        if cat_props else {}
        props = inst_props.get(state_obj.id)
        
        taxonomy = Factory.taxonomy(state_obj.id, state_obj.name, cat_key, inst_key)
        frame = Factory.frame(recipe.frame) \
                        if recipe and recipe.frame else Factory.frame(None)
        animation = Factory.animation(recipe.animation) \
                        if recipe and recipe.animation else Factory.animation(None)
        
        return Asset(taxonomy, props, state_obj, frame, animation)

    # ---------------------------------------------------------
    # ------------------------------------- EXPANSION UTILITIES

    def _unpack_node(self, 
        node: Any, 
        root_context: Dict[str, Any], 
        parent_context: Dict[str, Any], 
        inc: int, 
        is_root: bool = False
    ) -> List[Asset]:
        assets = []
        
        strut_state = self._hydrate_state(
            node.strut,
            root_context,
            parent_context,
            inc,
            AssetInstances.STRUTS,
            is_strut=True
        )
        strut_asset = self._create_asset(AssetCategories.CRAFTS, AssetInstances.STRUTS, strut_state)
        assets.append(strut_asset)

        # 1. Calculate the physical bottom edge (height) of the instantiated Strut
        node_height = strut_state.position.y + (strut_asset.dimensions.l if strut_asset.dimensions else 0)

        # 2. Inject it into the context dictionary for child components to reference
        node_context = {
            "position": strut_state.position,
            "layer": strut_state.layer,
            "owner": getattr(strut_state, 'owner', None),
            "name": strut_state.name,
            "height": node_height
        }
        
        # 3. If this is the root strut, its height becomes the root height
        if is_root:
            root_context["height"] = node_height

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
            
        for cat_field in dataclasses.fields(components):
            cat_key = cat_field.name
            cat_data = getattr(components, cat_key)
            if not cat_data: continue
            
            for inst_field in dataclasses.fields(cat_data):
                inst_key = inst_field.name
                inst_list = getattr(cat_data, inst_key)
                if not inst_list: continue
                
                for pseudo_state in inst_list:
                    new_state = self._hydrate_state(
                        pseudo_state,
                        root_context,
                        parent_context,
                        inc,
                        inst_key,
                        is_strut=False
                    )
                    assets.append(self._create_asset(cat_key, inst_key, new_state))

    # ---------------------------------------------------------
    # ------------------------------------------ PUBLIC METHODS

    def unpack(self, deployed_state: PropertyState) -> List[Asset]:
        """Flattens a Composition configuration into a native 1D list of fully hydrated Assets."""
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
            "position": getattr(deployed_state, 'position', Position(0,0))
        }

        # Unpack Root node first, explicitly flagging it as the root
        assets.extend(self._unpack_node(comp_config.root, root_context, root_context, inc, is_root=True))

        if comp_config.branches:
            for branch in comp_config.branches:
                assets.extend(self._unpack_node(branch, root_context, root_context, inc, is_root=False))

        return assets

    def cost(self, comp_id: str) -> List[Cost]:
        """Calculates the aggregate cost of an entire Composition tree."""
        config = self.compositions.get(comp_id)
        if not config: 
            return []
        
        cost_map = {}
        
        # Traverse Root
        self._accumulate_cost(AssetCategories.CRAFTS, AssetInstances.STRUTS, config.root.strut.id, cost_map)
        self._aggregate_components_cost(config.root.components, cost_map)
        
        # Traverse Branches
        if config.branches:
            for branch in config.branches:
                self._accumulate_cost(AssetCategories.CRAFTS, AssetInstances.STRUTS, branch.strut.id, cost_map)
                self._aggregate_components_cost(branch.components, cost_map)
                
        return [Cost(item=k, quantity=v) for k, v in cost_map.items()]
