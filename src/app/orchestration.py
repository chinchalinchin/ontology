"""
# Ontology: Orchestration
"""
# Standard Libraries
from typing import List, Any, Union
import yaml

# Application Libraries
import app.constants as constants
from app.assets.base import Asset
from app.game.board import Board
from app.game.factory import Factory
from app.models.recipes import StateRecipe
from app.models.configuration import (
    PyMultiplierState, PyPositionalState, PyMetricState, PyAnimatorState, 
    PyContainerState, PyDoorState, PySwitchState, PyPixieState, 
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
    StateRecipe.PIXIE: PyPixieState,
    StateRecipe.SPRITE: PySpriteState
}

def migrate(
    board_key: str, 
    asset_recipes: Union[PyRecipeConfiguration, None] = None
) -> List[Any]:
    board_dir = constants.STATE_DIR / board_key
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
        for category, content in data.items():
            
            # Handle flattened lists (e.g., tiles or struts)
            if isinstance(content, list):
                instance = "regular" if category == "tiles" else "strut"
                recipe = getattr(getattr(asset_recipes, category, None), instance, None)
                if not recipe: continue
                
                model_cls = PY_STATE_MAP.get(recipe.state)
                for item in content:
                    item["category"] = category
                    item["instance"] = instance
                    if "layer" in item: item["layer"] = str(item["layer"])
                    if "name" not in item: item["name"] = f"{instance}_{item.get('key')}"
                    flat_states.append(model_cls(**item))

            # Handle nested objects (e.g., objects: chests: [...])
            elif isinstance(content, dict):
                for instance, items in content.items():
                    recipe = getattr(getattr(asset_recipes, category, None), instance, None)
                    if not recipe or not items: continue
                    
                    model_cls = PY_STATE_MAP.get(recipe.state)
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
    
    # 1. Load Pydantic Configurations (RESTORED)
    # The Orchestrator manages how the engine is glued together, so it loads the Recipes.
    if asset_recipes is None:
        asset_recipes = PyRecipeConfiguration()
    
    # 2. Build property cache from registry
    asset_properties_cache = {
        "tiles": registry.tiles_config.model_dump() if registry.tiles_config else {},
        "cursors": registry.cursors_config.model_dump() if registry.cursors_config else {},
        "effects": registry.effects_config.model_dump() if registry.effects_config else {},
        "objects": registry.objects_config.model_dump() if registry.objects_config else {},
        "sheets": registry.sheets_config.model_dump() if registry.sheets_config else {}
    }
    
    # 3. Flatten and parse PyAssetState models for the current board
    py_states = migrate(board_key, asset_recipes) 
    assets = []

    for py_state in py_states:
        state_dict = py_state.model_dump()
        category = py_state.category
        instance = py_state.instance
        prop_key = py_state.key

        # 4. Extract specific recipe dynamically
        category_recipe = getattr(asset_recipes, category, None)
        recipe = getattr(category_recipe, instance, None) if category_recipe else None
        if not recipe:
            continue

        # 5. Extract specific properties dynamically
        prop_dict = {}
        if category in asset_properties_cache:
            cat_props = asset_properties_cache[category]
            if category == "tiles":
                prop_dict = {"dimensions": {"l": 32, "w": 32}}
            else:
                instance_props = cat_props.get(instance, {})
                if category == "sheets" and instance == "sprites":
                    prop_dict = instance_props 
                elif category == "sheets" and instance == "pixies":
                    prop_dict = instance_props.get("entities", {}).get(prop_key, {})
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