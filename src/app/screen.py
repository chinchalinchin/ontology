# NOTE: PSEUDCODE
#       Should be implemented in Cython, I think.
"""
# Ontology: Screen

"""

# Standard Libraries
from typing import List

# Application Libraries
from app.assets.base import Asset
from app.player import Player

# Cython Libraries
from libs.core import Position, Dimensions
from libs.math import Geometry
from libs.render import canvas, construct, render

class Screen:
    """
    """

    screensize: Dimensions
    canvas: TexturePtr # ?

    def __init__(self, 
        screensize: Dimensions,
        tiles: List[Asset]   
    ):
        self.screensize = screensize
        self.canvas = canvas(self.screensize)
        cython_tiles = [( 
            # TODO: TexturePtr?
            Position(x=0, y=0),
            tile.properties.dimensions,
            tiles.state.position,
            tiles.state.multiple
        ) for tile in tiles]
        construct(self.canvas, cython_tiles)

    def render(self, 
        assets : List[Asset], 
        player: Player
    ) -> None:
        """
        Render stateful Assets onto the screen.
        """
