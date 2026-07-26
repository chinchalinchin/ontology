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
    properties: properties.AssetProperties
    state: state.ExpressionCursorState

    def __init__(self, 
        properties: properties.AssetProperties,
        state: state.ExpressionCursorState,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.state = state
        self.propertis = properties
    
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
        state: state.ProjectileState,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.state = state
    
    def frame(self) -> str:
        return self.properties.asset

    def update(self, intent: State.Intention) -> None:
        # TODO: implement
        return
