"""
# Ontology: app.assets.frames

Package for Asset Frame implementations.
"""
# Application Libraries
import app.config.settings as settings
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
        return settings.SEPARATOR.join([
            id, 
            str(state.animation.frame)
        ])
    
class StateFrame(Frame):
    """
    """

    def key(self, id: str, state: AssetState) -> str:
        """
        """
        return settings.SEPARATOR.join([
            id, 
            state.animation.action, 
            state.animation.direction,
            str(state.animation.frame)
        ])
