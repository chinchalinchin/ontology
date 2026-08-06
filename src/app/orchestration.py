"""
# Ontology: Orchestration

Package for orchestrating the application logic.
"""

# Standard Libraries 
from typing import List, Dict

# Application Libraries
from app.assets.base import Asset
from app.game.board import Board
from app.game.factory import Factory
from app.models.configuration import PyRecipeConfiguration
from app.models.properties import AssetProperties
from app.models.state import AssetState

# Cython Libraries

def orchestrate():
    """
    ## orchestrate
    
    The state directory can contain an arbitrary number of YAML configuration files. Each file must conform to the Asset state schema (`docs/.static/yaml/asset-state.yaml`). Below is an example, followed by the general scheme with <> denoting parameters,

    ```tree
    ontology/src/data/state
    .
    └── world-00
        ├── cursors.yaml
        ├── effects.yaml
        ├── objects.yaml
        ├── sheets.yaml
        └── tiles.yaml
    └── <board-key>
        ├── <state-file>.yaml

    1 directory, 5 files
    ```
    """

    asset_recipes = PyRecipeConfiguration()
    asset_properties = { } # TODO
    asset_states = { } # TODO
    assets = []

    for state in asset_states:
        instance_recipe             = asset_recipes[state.category][state.instance]
        instance_properties         = asset_properties[state.category]
        assets                 += [
            Asset(
                properties          = Factory.properties(state.instance, instance_properties),
                state               = Factory.state(state.instance, state),
                frame               = Factory.frame(instance_recipe.frame),
                animation           = Factory.animation(instance_recipe.animation)
            )
        ]

    board = Board(asset_states)


"""
# Ontology: Orchestration
"""
from typing import List
from app.assets.base import Asset
from app.game.board import Board
from app.game.factory import Factory
from app.models.configuration import PyRecipeConfiguration, PyStateConfiguration

def migrate() -> List[PyStateConfiguration]:
    """
    ## state_models
    
    The state directory can contain an arbitrary number of YAML configuration files. Each file must conform to the Asset state schema (`docs/.static/yaml/asset-state.yaml`). Below is an example, followed by the general scheme with <> denoting parameters,

    ```tree
    ontology/src/data/state
    .
    └── world-00
        ├── cursors.yaml
        ├── effects.yaml
        ├── objects.yaml
        ├── sheets.yaml
        └── tiles.yaml
    └── <board-key>
        ├── <state-file>.yaml

    1 directory, 5 files
        ```
    """
    # TODO: implement

def orchestrate(board_key = "world-00"):
    """
    ## orchestrate
    
    """
    # 1. Load Pydantic Configurations
    asset_recipes = PyRecipeConfiguration()
    # (Assume properties and states are loaded via Py*Configuration here)
    asset_properties_cache = {} 
    
    # 2. Assume we have a flat list of parsed PyAssetState models for the board
    py_states = migrate(board_key) 
    
    assets = []

    for py_state in py_states:
        # Pydantic's .model_dump() safely converts the validated DTO back to a raw dictionary
        state_dict = py_state.model_dump()
        
        # Extract keys needed for routing
        category = py_state.category
        instance = py_state.instance
        prop_key = py_state.key

        # 3. Lookup Recipes and Properties
        # (Assuming your recipe dict is structured to allow fetching by category/instance)
        recipe = getattr(getattr(asset_recipes, category), instance)
        
        # 4. Fetch the specific property dictionary for this asset key
        # (Assuming asset_properties_cache is populated from PyPropertyConfigurations)
        prop_dict = asset_properties_cache[category][prop_key].model_dump()

        # 5. Build the Unified Asset
        assets.append(
            Asset(
                properties = Factory.properties(category, prop_dict),
                state      = Factory.state(instance, state_dict),
                frame      = Factory.frame(recipe.frame),
                animation  = Factory.animation(recipe.animation)
                # Behaviors / Intentions would be compiled and injected here
            )
        )

    # 6. Boot the engine
    board = Board(assets)