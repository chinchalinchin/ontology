
"""
Package for Tile Assets.
"""
# Application Libraries
from app.assets import Asset
from app.models import Dimensions
from app.models.state import TileState
from app.models.properties import TileProperties

class Tile(Asset):
    """
    Tile Asset class. Tiles are the simplest type of Asset, with property dimensions (asset, dimensions) and state dimensions (layer, position).
    
    Since Tiles are completely statically, all Tiles are rendered into an in-memory image buffer when the Board is loaded. Animations and other assets are written on top of a copy of this buffer, without ever altering the original buffer image. 
    """
    properties: TilesProperties 
    state: TileState
    
    def __init__(self, 
        properties: TileProperties,
        state: TileState,
        **kwargs
    ):
        self.properties
        self.state = state

    def frame(self) -> str:
        return self.properties.asset

    def onscreen(self, screen: Dimensions, player: Player) -> bool:
        return True
        
    # ----- UNIMPLEMENTED ABSTRACT METHODS 

    def animate(self) -> None:
        return 

    def move(self) -> None:
        return 

    def update(self, intent: State.Intention) -> None:
        return