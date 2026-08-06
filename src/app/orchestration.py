"""
# Ontology: Orchestration

Package for orchestrating the application logic.
"""
from typing import List, Any
import yaml
import app.constants as constants
from app.assets.base import Asset
from app.game.board import Board
from app.game.factory import Factory
from app.models.configuration import (
    PyRecipeConfiguration, PyMultiplierState, PyPositionalState, 
    PyMetricState, PyAnimatorState, PyContainerState, PyDoorState, 
    PySwitchState, PyPixieState, PySpriteState, PyPropertyState
)

def migrate(board_key: str = "world-00") -> List[Any]:
    """
    ## state_models
    
    The state directory can contain an arbitrary number of YAML configuration files.
    """
    board_dir = constants.STATE_DIR / board_key
    flat_states = []
    
    if not board_dir.exists():
        return flat_states

    model_map = {
        "tiles": PyMultiplierState,
        "struts": PyPropertyState,
        "cursors": {
            "expressions": PyPositionalState,
            "projectiles": PyMetricState,
        },
        "effects": {
            "persistent": PyAnimatorState,
            "temporary": PyAnimatorState,
        },
        "objects": {
            "chests": PyContainerState,
            "crates": PyPositionalState,
            "doors": PyDoorState,
            "gates": PySwitchState,
            "plates": PySwitchState,
        },
        "sheets": {
            "sprites": PySpriteState,
            "pixies": PyPixieState,
        }
    }

    for yaml_file in board_dir.glob("*.yaml"):
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
            
        if not data:
            continue
            
        for category, content in data.items():
            if category == "tiles":
                for item in content:
                    item["category"] = "tiles"
                    item["instance"] = "regular"
                    if "name" not in item:
                        item["name"] = f"tile_{item.get('key')}"
                    flat_states.append(PyMultiplierState(**item))

            elif category == "struts":
                for item in content:
                    item["category"] = "struts"
                    item["instance"] = "strut"
                    if "name" not in item:
                        item["name"] = f"strut_{item.get('key')}"
                    flat_states.append(PyPropertyState(**item))
                         
            elif category in model_map:
                for instance, items in content.items():
                    model_cls = model_map[category].get(instance)
                    if model_cls and items:
                        for item in items:
                            item["category"] = category
                            item["instance"] = instance
                            if "name" not in item:
                                item["name"] = f"{instance}_{item.get('key')}"
                            flat_states.append(model_cls(**item))
                            
    return flat_states


def orchestrate(board_key: str = "world-00", registry=None):
    """
    ## orchestrate
    """
    import libs.render as render
    from libs.registry import Registry

    # Initialize libs.render if not provided (e.g., from the CLI environment)
    if registry is None:
        render.init()
        # Instantiate Registry to validate /src/assets/** and cache GPU textures.
        registry = Registry()
    
    # 1. Load Pydantic Configurations
    asset_recipes = PyRecipeConfiguration()
    
    # Build property cache from registry
    asset_properties_cache = {
        "tiles": registry.tiles_config.model_dump() if registry.tiles_config else {},
        "cursors": registry.cursors_config.model_dump() if registry.cursors_config else {},
        "effects": registry.effects_config.model_dump() if registry.effects_config else {},
        "objects": registry.objects_config.model_dump() if registry.objects_config else {},
        "sheets": registry.sheets_config.model_dump() if registry.sheets_config else {}
    }
    
    # 2. Flatten and parse PyAssetState models for the current board
    py_states = migrate(board_key) 
    assets = []

    for py_state in py_states:
        # Pydantic's .model_dump() safely converts the validated DTO back to a raw dictionary
        state_dict = py_state.model_dump()
        
        # Extract keys needed for routing
        category = getattr(py_state, 'category', '')
        instance = getattr(py_state, 'instance', '')
        prop_key = py_state.key

        # 3. Lookup Recipes
        category_recipe = getattr(asset_recipes, category, None)
        recipe = getattr(category_recipe, instance, None) if category_recipe else None
        
        if not recipe:
            continue

        # 4. Fetch the specific property dictionary for this asset key
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

        # 5. Build the Unified Asset
        assets.append(
            Asset(
                properties = Factory.properties(category, prop_dict),
                state      = Factory.state(instance, state_dict),
                frame      = Factory.frame(recipe),
                animation  = Factory.animation(recipe)
            )
        )

    # 6. Boot the engine
    board = Board(assets)
    return board, registry