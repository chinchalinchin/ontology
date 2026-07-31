"""
Package for Object Assets.
"""
# Application Libraries
import ontology.src.app.constants as constants
from app.assets.base import Animation, Frame
from app.models.state import AssetState
from app.models.properties import AssetProperties

# -------------------------------------- OBJECT ANIMATION IMPLEMENTATIONS


class BinaryAnimation(Animation):

    def animate(self, state: AssetState, properties: AssetProperties) -> AssetState:
        """
        """
        state.animation.frame = constants.ON if state.state.switch else constants.OFF
        return state
        
# -------------------------------------- OBJECT FRAME IMPLEMENTATIONS

class ObjectFrame(Frame):
    """
    """

    def key(self, asset: str, state: AssetState) -> str:
        """
        """
        return asset
    
class BinaryFrame(Frame):
    """
    """

    def key(self, asset: str, state: AssetState) -> str:
        """
        """
        return constants.SEPARATOR.join(
            asset, 
            state.animation.frame
        )
