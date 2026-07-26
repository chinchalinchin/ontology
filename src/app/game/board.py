"""

"""
# NOTE: PSEUDCODE

# Standard Libraries 
from typing import List, Dict

# Application Libraries
from app.assets import Asset
from app.player import Player
import app.assets.cursors as cursors
import app.assets.effects as effects 
import app.assets.objects as objects
import app.assets.sheets as sheets 

class Board:
    """
    """
    # ------------------------- PROPERTIES
    layers: int

    # ------------------------- ASSETS
    player: Player
    # --------- Tiles
    tiles: Dict[List[Asset]]
    # --------- Effects
    permanent: Dict[List[Asset]]
    temporary: Dict[List[Asset]]
    # --------- Cursors
    expressions: Dict[List[Asset]]
    projectiles: Dict[List[Asset]]
    # --------- Objects
    chests: Dict[List[Asset]]
    crates: Dict[List[Asset]]
    doors: Dict[List[Asset]]
    gates: Dict[List[Asset]]
    plates: Dict[List[Asset]]
    # --------- Sheets
    pixies: Dict[List[Asset]]
    sprites: Dict[List[Asset]]

    def __init__(self, root: Path):
        # assume the folllowing directory structure for each board
        #
        # ```tree
        #    boards
        #    └── <board-key>
        #        └── immutable
        #            ├── animate.yaml
        #            └── inanimate.yaml
        #        └── mutable
        #            ├── animate.yaml
        #            └── inanimate.yaml
        # ```

    def layers(self) -> int:
        if not self.layers:
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
                self.chests[layer] + self.crates[layer] + 
                self.doors[layer] + self.gates[layer] + \
                self.plates[layer] + self.pixies[layer] + \
                self.sprites[layer]

    def animate(self):
        """
        Returns a list of animate Assets()
        """
        return self.permanent + self.temporary + \
                self.pixies + self.sprites + \
                self.player

    def menu(self) -> None:
        """
        """
        pass 

    def play(self) -> None:
        """
        """
        # ------------------------- ANIMATION HANDLING
        for piece in self.animate()
            piece.animate()
        # -------------------------

        # ------------------------- PROJECTILE HANDLING
        for proj in self.projectiles:
            for target in self.pixes + self.sprites:
                if proj.intersects(target):
                    # TODO: projectile logic
            if not proj.alive(): 
                # TODO: remove projectil
        # -------------------------

        # ------------------------- TEMPORARY EFFECT HANDLING
        for ef in self.temporary:
            if not ef.alive():
                # TODO: remove effect
        # -------------------------

        # ------------------------- PLATE HANDLING
        for plate in self.plates:
            switched = False

            for weight in self.crates + self.sprites + self.pixies:
                if plate.intersects(weight):
                    plate.state.switch = True
                    switched = True
                    break 
            
            if switched:
                for gate in self.gates:
                    if plate.state.link == gate.state.link:
                        gate.state.switch = plate.state.switch
        # -------------------------

        # ------------------------- SHEET-TO-SHEET COLLISION HANDLING
        for this in self.sprites + self.pixies:
            for that in self.sprites + self.pixies:
                if this.name != that.name and this.intersects(that):
                    # collision logic
        # -------------------------

        # ------------------------- PLAYER HANDLING
        self.player
        # player logic
        # -------------------------
