"""
Package for Cursor Assets.
"""
# Application Libraries
import app.assets as assets
import app.models.properties as properties
import app.models.state as state
import app.physics.collisions as collisions

class ExpressionCursor(assets.Asset, collisions.Shape):
    """
    """
    state: State.ExpressionCursorState

    def __init__(self, 
        properties: properties.AssetProperties,
        state: state.ExpressionCursorState
    ):
        super().__init__(properties)
        self.state = state
    
    def frame(self) -> str:
        return self.properties.asset

    def update(self, intent: State.Intention) -> None:
        # TODO: implement
        return

class Projectile(assets.Asset):
    """
    """
    state: State.ProjectileState

    def __init__(self, 
        properties: properties.AssetProperties,
        state: state.ProjectileState
    ):
        super().__init__(properties)
        self.state = state
    
    def frame(self) -> str:
        return self.properties.asset

    def update(self, intent: State.Intention) -> None:
        # TODO: implement
        return
