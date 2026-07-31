"""
Package for Effect Assets.
"""
# Application Libraries
import app.constants as constants
from app.assets.base import Frame, Animation
from app.models.state import AssetState
from app.models.properties import AssetProperties

# -------------------------------------- EFFECT ANIMATION IMPLEMENTATIONS

class PersistentAnimation(Animation):

    def animate(self, state: AssetState, properties: AssetProperties) -> AssetState:
        """
        """
        state.animation.frame += 1

        if state.animation.frame > properties.count:
            state.animation.frame = 0

        return state
    
class TemporaryAnimation(Animation):
    pass

    def animate(self, state: AssetState, properties: AssetProperties) -> AssetState:
        """
        """
        if state.animation.frame <= properties.count:
            state.animation.frame += 1

        return state
    
# -------------------------------------- EFFECT FRAME IMPLEMENTATIONS

class EffectFrame(Frame):
    """
    """

    def key(self, asset: str, state: AssetState) -> str:
        """
        """
        return constants.SEPARATOR.join(
            asset, 
            state.animation.frame
        )
