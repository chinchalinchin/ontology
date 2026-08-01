"""
# Ontology: Board

"""

# Standard Libraries 
from typing import List, Dict

# Application Libraries
from app.assets.base import Asset, Mechanic
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
    tiles: Dict[str, List[Asset]]
    # --------- Effects
    permanent: Dict[str, List[Asset]]
    temporary: Dict[str, List[Asset]]
    # --------- Cursors
    expressions: Dict[str, List[Asset]]
    projectiles: Dict[str, List[Asset]]
    # --------- Objects
    chests: Dict[str, List[Asset]]
    crates: Dict[str, List[Asset]]
    doors: Dict[str, List[Asset]]
    gates: Dict[str, List[Asset]]
    plates: Dict[str, List[Asset]]
    # --------- Sheets
    pixies: Dict[str, List[Asset]]
    sprites: Dict[str, List[Asset]]

    # ------------------------- Mechanics

    def __init__(self, root: Path):
        self._assets()
        self._mechanics(root)

    def _mechanics(self):
        """
        """
        self.mechanics = [ 
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
                properties                  = EffectProperties(),
                state                       = PersistentEffectState(),
                frame                       = EffectFrame(),
                animation                   = PersistentAnimation()
            )
          ]
        
        for snapshot in mutable_animate.sprites:
          sprites                           += [
              Asset(
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
        return self.tiles[layer] 

    def assets(self) -> List[Asset]:
        """
        Returns a list of all Assets on the current layer of the game Board.
        """
        layer = self.player.layer
        return self.expressions[layer] + self.projectiles[layer]  + \
                self.permanent[layer] + self.temporary[layer]  + \
                self.chests[layer] + self.crates[layer] + \
                self.doors[layer] + self.gates[layer] + \
                self.plates[layer] + self.pixies[layer] + \
                self.sprites[layer]

    def animations(self):
        """
        Returns a list of animate Assets()
        """
        return  self.plates + self.gates + \
                self.chests + self.player + \
                self.permanent + self.temporary + \
                self.pixies + self.sprites 

    def menu(self) -> None:
        """
        """
        pass 

    def play(self, delta_time: float) -> None:
        """
        """
        # ------------------------- ANIMATION HANDLING
        for this in self.animations():
            this.animation.animate()
        # -------------------------

        # ------------------------- MECHANIC HANDLING
        for this in self.mechanics:
            this.update(self, delta_time)

        # ------------------------- PLAYER HANDLING
        self.player
        # TODO: player logic
        # -------------------------
