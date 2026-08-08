"""
# Ontology: Frames

Package for Asset Frame implementations.
"""
# Application Libraries
import app.config.constants as constants
from app.assets.base import Frame
from app.models.state import AssetState

class SingleFrame(Frame):
    """
    """

    def key(self, id: str, state: AssetState) -> str:
        """
        """
        return id
    
class IterableFrame(Frame):

    def key(self, id: str, state: AssetState) -> str:
        """
        """
        return constants.SEPARATOR.join(
            id, 
            state.animation.frame
        )
    
class StateFrame(Frame):
    """
    """

    def key(self, id: str, state: AssetState) -> str:
        """
        """
        return constants.SEPARATOR.join([
            id, 
            state.animation.action, 
            state.animation.direction,
            state.animation.frame
        ])
