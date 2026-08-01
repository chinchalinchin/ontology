# NOTE: PSEUDCODE
#       Should be implemented in Cython, I think.
"""
# Ontology: Screen

"""

# Standard Libraries
from typing import List

# Application Libraries
from app.assets.base import Asset
from app.models import Dimensions, Position
from app.player import Player

# Cython Libraries
from libs.math import Geometry

class Screen:
    """
    """

    # Static image assembled from immutable assets
    canvas: Image
    # Buffer to hold copy of canvas for rendering
    buffer: Image
    # Screen size
    screensize: Dimensions


    def __init__(self, 
        screen: Dimensions, 
        immutable: List[Asset]
    ):
        self.screen = screen
        self.canvas(immutable)
        return
    
    def canvas(self, 
        assets: List[Asset]
    ) -> Image:
        """
        Render and stack immutable assets onto static canvas.
        """
        for asset in assets:
            self.canvas.render(
                asset.state.position, 
                asset.properties.dimensions, 
                asset.key(asset.properties.key, asset.state)
            )

        return self.canvas

    def draw(self, 
        assets : List[Asset], 
        player: Player
    ) -> Image:
        """
        Render mutable assets onto the immutable canvas.
        """
        # 1. Copy static canvas into new buffer
        self.buffer = self.canvas.copy()

        # 2. Render all onscreen assets
        for asset in assets:
            if asset.onscreen(player, self.screensize):
                self.buffer.render(
                    asset.state.position,
                    asset.properties.dimensions,
                    asset.key(asset.properties.key, asset.state)
                )
        
        # 3. Clip bufer to the player's POV
        center = Position(*Geometry.center(player))
        clip = Position(*Geometry.offset(center, self.screensize))
        self.buffer.clip(clip, self.screensize)
        return self.buffer