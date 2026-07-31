
"""
Package for Tile Assets.
"""
# Application Libraries
from app.assets.base import Frame
from app.models.state import AssetState

class TileFrame(Frame):
    """
    """

    def key(self, asset: str, state: AssetState) -> str:
        """
        """
        return asset