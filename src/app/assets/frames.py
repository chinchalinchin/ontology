"""
# Ontology: Frames

Package for Asset Frame implementations.
"""
# Application Libraries
import app.constants as constants

from app.assets.base import Frame
from app.models.state import AssetState

class SingleFrame(Frame):
    """
    """

    def key(self, asset: str, state: AssetState) -> str:
        """
        """
        return asset
    
class IterableFrame(Frame):

    def key(self, asset: str, state: AssetState) -> str:
        """
        """
        return constants.SEPARATOR.join(
            asset, 
            state.animation.frame
        )
    
class StateFrame(Frame):
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
