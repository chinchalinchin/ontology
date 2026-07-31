"""
Package for Cursor Assets.
"""
# Application Libraries
from app.assets.base import Frame
from app.models.state import AssetState

# -------------------------------------- CURSOR FRAME IMPLEMENTATIONS

class CursorFrame(Frame):
    """
    """

    def key(self, asset: str, state: AssetState) -> str:
        """
        """
        return asset