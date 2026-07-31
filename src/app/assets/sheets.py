"""
Package for Sheet Assets.
"""
# Application Libraries
import app.constants as constants
from app.models.properties import AssetProperties
from app.assets.base import Animation, Frame
from app.models.state import AssetState


# -------------------------------------- SHEET ANIMATION IMPLEMENTATIONS

class SpriteAnimation(Animation):
    """
    """

    def animate(self, state: AssetState, properties: AssetProperties) -> AssetState:
        """
        """
        state.animation.frame += 1

        if state.animation.frame > properties.actions[state.animation.action].count:
            state.animation.frame = 0

        return state
    
# -------------------------------------- SHEET FRAME IMPLEMENTATIONS

class SpriteFrame(Frame):
    """
    """

    def key(self, asset: str, state: AssetState) -> str:
        """
        """
        return constants.SEPARATOR.join([
            asset, 
            state.animation.action, 
            state.animation.direction,
            state.animation.frame
        ])
 