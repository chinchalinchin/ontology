
"""
Package for Tile Assets.
"""
# Application Libraries
import app.assets as assets
import app.models.state as state
import app.models.properties as properties

class Tile(assets.Asset):
    """
    Tile Asset class. Tiles are the simplest type of Asset, with property dimensions (asset, dimensions) and state dimensions (layer, position).
    """

    state: State.TileState
    
    def __init__(self, 
        properties: properties.AssetProperties,
        state: state.TileState
    ):
        super().__init__(properties)
        self.state = state

    def frame(self) -> str:
        return self.properties.asset

    def update(self, intent: State.Intention) -> None:
        return