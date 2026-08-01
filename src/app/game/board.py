"""
# Ontology: Board

Package for game Board. The Board holds and mutates the state of the game for the engine loop.
"""

# Standard Libraries 
from typing import List

# Application Libraries
from app.assets.base import Asset
from app.game.mechanics import Mechanic, \
                                    AnimationMechanics, \
                                    CollisionMechanics, \
                                    ProjectileMechanics, \
                                    SwitchMechanics
from app.game.factory import Factory
from app.player import Player

class Board:
    """
    """
    layers: int
    player: Player
    mechanics: List[Mechanic]
    assets: List[Asset]

    def __init__(self, root: Path):
        self.load()
        self.mechanics = [ 
            AnimationMechanics(),
            CollisionMechanics(),
            ProjectileMechanics(),
            SwitchMechanics()
        ]

    def load(self, root: Path):
        """
        """
        asset_recipes = "TODO: yaml file @ src/assets/main.yaml"
        asset_properties = {}

        for asset_type, type_recipes in asset_recipes.keys():
            for type_key in type_recipes.keys():
                property_path = f"./src/assets/{asset_type}/{type_key}/main.yaml"
                asset_properties[type_key] = "TODO: open(property_path)"

        asset_state = "TODO: concatened yaml files @ src/data/state/{root}/**.yaml"

        for category_key, category in asset_state:
            for instance_key, instances in category:
                for instance_state in instances:
                    instance_recipe             = asset_recipes[category_key][instance_key]
                    instance_properties         = asset_properties[category_key]
                    self.assets                 += [
                        Asset(
                            properties          = Factory.properties(instance_key, instance_properties),
                            state               = Factory.state(instance_key, instance_state),
                            frame               = Factory.frame(instance_recipe.frame),
                            animation           = Factory.animation(instance_recipe.animation)
                        )
                    ]

    def get_layers(self) -> int:
        if not self.layers:
            pass
            # dynamically calculate layers based on loaded Assets dictionary keys
        return self.layers

    def tiles(self, layer) -> List[Asset]:
        """
        Returns a list of all Tile Assets on the given layer of the game Board.
        """
        return [ tile for tile in self.tiles if tile.state.layer == layer ]

    def menu(self) -> None:
        """
        """
        # TODO: implement
        pass 

    def play(self, delta: float) -> None:
        """
        """
        # ------------------------- MECHANIC HANDLING
        for this in self.mechanics:
            this.update(self, delta)

        # ------------------------- PLAYER HANDLING
        self.player
        # TODO: player logic
        # -------------------------
