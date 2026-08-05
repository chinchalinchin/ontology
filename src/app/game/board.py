"""
# Ontology: Board

Package for game Board. The Board holds and mutates the state of the game for the engine loop.
"""

# Standard Libraries 
from typing import List, Dict

# Application Libraries
from app.assets.base import Asset
from app.game.mechanics import Mechanic, \
                                    AnimationMechanics, \
                                    CollisionMechanics, \
                                    ProjectileMechanics, \
                                    SwitchMechanics
from app.player import Player

class Board:
    """
    """
    layers: int
    player: Player
    mechanics: List[Mechanic]
    assets: List[Asset]

    def __init__(self, 
        assets: List[Asset]
    ):
        self.assets = assets
        self.mechanics = [ 
            AnimationMechanics(),
            CollisionMechanics(),
            ProjectileMechanics(),
            SwitchMechanics()
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
