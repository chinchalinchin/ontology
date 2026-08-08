"""
# Ontology: Orchestration
"""
# Standard Libraries
from typing import List, Any, Union
import yaml

# Application Libraries
import app.config.settings as settings
from app.assets.base import Asset
from app.game.board import Board
from app.hooks.factory import Factory
from app.config.enums import StateRecipe
from app.config.validators import (
    PyMultiplierState, PyPositionalState, PyMetricState, 
    PyAnimatorState, PyContainerState, PyDoorState, PySwitchState,
    PySpriteState, PyPropertyState, PyRecipeConfiguration
)

# Cython Libraries
import libs.render as render
from libs.registry import Registry

# Dynamic mapping of the StateRecipe enum to the Pydantic Validation Models
PY_STATE_MAP = {
    StateRecipe.MULTIPLIER: PyMultiplierState,
    StateRecipe.POSITIONAL: PyPositionalState,
    StateRecipe.METRIC: PyMetricState,
    StateRecipe.ANIMATOR: PyAnimatorState,
    StateRecipe.CONTAINER: PyContainerState,
    StateRecipe.DOOR: PyDoorState,
    StateRecipe.SWITCH: PySwitchState,
    StateRecipe.PROPERTY: PyPropertyState,
    StateRecipe.SPRITE: PySpriteState
}

def migrate(
    board_key: str, 
    asset_recipes: Union[PyRecipeConfiguration, None] = None
) -> List[Any]:
    """
    # migrate

    Transfer the Pydantic DTOs to Python POPOs for the game engine.
    """
    board_dir = settings.STATE_DIR / board_key
    flat_states = []

    if not asset_recipes:
        asset_recipes = PyRecipeConfiguration()

    if not board_dir.exists():
        return flat_states

    for yaml_file in board_dir.glob("*.yaml"):
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
            
        if not data:
            continue

        # Dynamically traverse the parsed dictionary
        for category, instances in data.items():
            if not isinstance(instances, dict):
                continue
                
            for instance, items in instances.items():
                category_recipe = getattr(asset_recipes.assets, category, None)
                recipe = getattr(category_recipe, instance, None) if category_recipe else None
                if not recipe or not items: continue
                
                model_cls = PY_STATE_MAP.get(recipe.state)
                if not model_cls: continue
                
                for item in items:
                    item["category"] = category
                    item["instance"] = instance
                    if "layer" in item: item["layer"] = str(item["layer"])
                    if "name" not in item: item["name"] = f"{instance}_{item.get('key')}"
                    flat_states.append(model_cls(**item))
                        
    return flat_states

def orchestrate(board_key: 
    str = "world-00", 
    registry: Union[Registry, None]=None, 
    asset_recipes: Union[PyRecipeConfiguration, None] = None
):
    """
    # Ontology: Orchestrate
    """

    if registry is None:
        render.init()
        registry = Registry()
    
    # 1. Load Pydantic Configurations
    if asset_recipes is None:
        asset_recipes = PyRecipeConfiguration()
    
    # 2. Build property cache from registry
    asset_properties_cache = {
        "tiles": registry.tiles_config.tiles.model_dump() 
                    if getattr(registry, "tiles_config", None) and registry.tiles_config.tiles else {},
        "cursors": registry.cursors_config.cursors.model_dump() 
                    if getattr(registry, "cursors_config", None) and registry.cursors_config.cursors else {},
        "effects": registry.effects_config.effects.model_dump() 
                    if getattr(registry, "effects_config", None) and registry.effects_config.effects else {},
        "objects": registry.objects_config.objects.model_dump() 
                    if getattr(registry, "objects_config", None) and registry.objects_config.objects else {},
        "sheets": registry.sheets_config.sheets.model_dump() 
                    if getattr(registry, "sheets_config", None) and registry.sheets_config.sheets else {},
        "crafts": registry.crafts_config.objects.model_dump() 
                    if getattr(registry, "crafts_config", None) and registry.crafts_config.objects else {}
    }
    
    # 3. Flatten and parse PyAssetState models for the current board
    py_states = migrate(board_key, asset_recipes) 
    assets = []

    for py_state in py_states:
        state_dict = py_state.model_dump()
        category = py_state.category
        instance = py_state.instance
        # TODO: This is broken. Taxonomy is not part of state.
        prop_key = py_state.key

        # 4. Extract specific recipe dynamically
        category_recipe = getattr(asset_recipes.assets, category, None)
        recipe = getattr(category_recipe, instance, None) if category_recipe else None
        if not recipe:
            continue

        # 5. Extract specific properties dynamically
        prop_dict = {}
        if category in asset_properties_cache:
            cat_props = asset_properties_cache[category]
            instance_props = cat_props.get(instance, {})
            
            # Tiles and Sheets properties apply globally across instances
            if category in ("tiles", "sheets"):
                prop_dict = instance_props 
            else:
                prop_dict = instance_props.get(prop_key, {})

        # 6. Rely on the Factory to translate Enums into live POPOs
        assets.append(
            Asset(
                properties = Factory.properties(category, prop_dict),
                state      = Factory.state(recipe.state, state_dict),
                frame      = Factory.frame(recipe.frame),
                animation  = Factory.animation(recipe.animation)
            )
        )

    return Board(assets), registry