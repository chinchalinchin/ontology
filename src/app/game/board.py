"""
# Ontology: Board

Package for game Board. The Board holds and mutates the state of the game for the engine loop.
"""

# Standard Libraries 
from typing import List

# Application Libraries
from app.assets.base import Asset
from app.game.mechanics import (
    Mechanic, AnimationMechanics, CollisionMechanics, 
    ProjectileMechanics, SwitchMechanics, IntentionMechanics
)
from app.player import Player

class Board:
    """
    """
    numlayers: int
    player: Player
    mechanics: List[Mechanic]
    assets: List[Asset]

    def __init__(self, 
        assets: List[Asset]
    ):
        self.assets = assets
        self.mechanics = [ 
            AnimationMechanics(),
            IntentionMechanics(),
            CollisionMechanics(),
            ProjectileMechanics(),
            SwitchMechanics(),
        ]

    def layers(self) -> int:
        if not self.numlayers:
            pass
            # dynamically calculate layers based on loaded Assets dictionary keys
        return self.numlayers

    def categories(self, category, layer = None) -> List[Asset]:
        """
        Returns a list of all categorized Assets on the given layer of the game Board. If no layer is specified, all layers are returned.
        """
        if layer is not None:
            return [ 
                asset for asset in self.assets
                if (asset.state.layer == layer
                  and asset.state.category == category)
            ]
        return [ 
            asset for asset in self.assets
            if asset.state.category == category
        ]

    def instances(self, instance, layer = None) -> List[Asset]:
        """
        Returns a list of all instanced Assets on the given layer of the game Board. If no layer is specified, all layers are returned.
        """
        if layer is not None:
            return [ 
                asset for asset in self.assets 
                if (asset.state.layer == layer 
                    and asset.state.instance == instance)
            ]
        return [ 
            asset for asset in self.assets 
            if asset.state.instance == instance
        ]
    
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
