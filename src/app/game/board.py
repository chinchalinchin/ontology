"""
# Ontology: Board

Package for game Board. The Board holds and mutates the state of the game for the engine loop.
"""

# Standard Libraries 
from typing import Iterable, List
from itertools import chain

# Application Libraries
from app.assets.base import Asset, Mechanic, AnimationMechanics
from app.assets.cursors import ProjectileMechanics
from app.assets.effects import EffectFrame, \
                                    PersistentAnimation
from app.assets.objects import SwitchMechanics
from app.assets.sheets import CollisionMechanics, \
                                    SpriteAnimation, \
                                    SpriteFrame
from app.models.state import PersistentEffectState, \
                                    TileState,\
                                    SpriteState
from app.models.properties import EffectProperties, \
                                    TileProperties, \
                                    SpriteProperties
from app.player import Player

class Board:
    """
    """
    # ------------------------- PROPERTIES
    layers: int
    mechanics: List[Mechanic]

    # ------------------------- ASSETS
    player: Player
    # --------- Tiles
    tiles: List[Asset]
    # --------- Effects
    permanent: List[Asset]
    temporary: List[Asset]
    # --------- Cursors
    expressions: List[Asset]
    projectiles: List[Asset]
    # --------- Objects
    chests: List[Asset]
    crates: List[Asset]
    doors: List[Asset]
    gates: List[Asset]
    plates: List[Asset]
    # --------- Sheets
    pixies: List[Asset]
    sprites: List[Asset]

    # ------------------------- Mechanics

    def __init__(self, root: Path):
        self._assets()
        self._mechanics(root)

    def _mechanics(self):
        """
        """
        self.mechanics = [ 
            AnimationMechanics(),
            CollisionMechanics(),
            ProjectileMechanics(),
            SwitchMechanics()
        ]

    def _assets(self, root: Path):
        """
        The Asset state information is organized in the /src/data/boards/ directory with the following struture,

        ```tree
            boards
            └── <board-key>
                └── immutable
                    ├── animate.yaml
                    └── inanimate.yaml
                └── mutable
                    ├── animate.yaml
                    └── inanimate.yaml
        ```
        """
        immutable_inanimate = "TODO: yaml file"
        immutable_animate = "TODO: yaml file"
        mutable_animate = "TODO: yaml file "

        for snapshot in immutable_inanimate:
            self.tiles[snapshot.layer]     += [ 
              Asset(
                properties                  = TileProperties(
                    key                     = snapshot.asset, 
                    dimensions              = immutable_inanimate.regular.dimensions
                ),
                state                       = TileState(
                    position                = snapshot.position,
                    multiple                = snapshot.multiple
                )
              )
            ]
        
        for snapshot in immutable_animate.persistent:
          effects                           += [
            Asset(
                # TODO: inits
                properties                  = EffectProperties(),
                state                       = PersistentEffectState(),
                frame                       = EffectFrame(),
                animation                   = PersistentAnimation()
            )
          ]
        
        for snapshot in mutable_animate.sprites:
          sprites                           += [
              Asset(
                # TODO: inits
                properties                  = SpriteProperties(),
                state                       = SpriteState(),
                frame                       = SpriteFrame(),
                animation                   = SpriteAnimation()
              )
          ]

    def get_layers(self) -> int:
        if not self.layers:
            pass
            # dynamically calculate layers based on loaded Assets dictionary keys
        return self.layers

    def tiles_by_layer(self, layer) -> List[Asset]:
        """
        Returns a list of all Tile Assets on the given layer of the game Board.
        """
        return [ tile for tile in self.tiles if tile.state.layer == layer ]

    def assets(self) -> Iterable[Asset]:
        return chain(
            self.permanent, 
            self.temporary, 
            self.expressions, 
            self.projectiles, 
            self.chests, 
            self.crates, 
            self.doors, 
            self.gates, 
            self.plates,
            self.pixies, 
            self.sprites
        )

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
