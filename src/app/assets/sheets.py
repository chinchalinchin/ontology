"""
Package for Sheet Assets.
"""
# Application Libraries
from app.assets.base import Asset
from app.models.properties import SpriteProperties
from app.models.state import SpriteState, Animation


# -------------------------------------- SHEET ANIMATION IMPLEMENTATIONS

class SpriteAnimation(Animation):
    """
    """

    def animate(self, animation: Animation, properties: SpriteProperties) -> Aniatmion:
        """
        """
        animation.frame += 1

        if animation.frame > properties[animations.action].count:
            animation.frame = 0

        return animation
    
# -------------------------------------- SHEET FRAME IMPLEMENTATIONS

class SpriteFrame(Frame):
    """
    """

    def key(self, animation: Animation) -> str:
        """
        """
        return animation.action + animation.direction + animation.frame
 