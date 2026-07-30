"""
Package for geometry calculations.
"""
# Standard Libraries
from typing import List

# Application Libraries
from app.assets.base import Asset
from app.models import Hitbox
from app.screen import Screen

class Geometry:

    @staticmethod
    def intersect(
        a: Hitbox, 
        b: Hitbox
    ) -> bool:
        # implement rectangle intersection

    @staticmethod
    def onscreen( 
        asset: Asset,
        player: Player,
        screen: Screen
    ) ->  bool: 
        # implement onscreen method
        screen.dimensions.w, screen.dimensions.h
        player.shape.position.x, player.shape.position.y
        player.shape.dimensions.w, player.shape.dimensions.h
        asset.shape.position.x, asset.shape.dimensions.w
        asset.shape.position.y, asset.shape.dimension.h
