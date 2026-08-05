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