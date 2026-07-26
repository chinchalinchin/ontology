"""
Package for Sheet Assets.
"""
# Application Libraries
from app.models import Velocity
import app.assets as assets
import app.models.properties as properties
import app.models.state as state

class Sprite(assets.Asset):
    """
    """
    state: State.SpriteState

    def __init__(self, 
        properties: properties.AssetProperties,
        state: state.SpriteState
    ):
        super().__init__(properties)
        self.state = state
    
    def onscreen(self) -> str: 
        player.state.position.x, player.state.position.y
        player.properties.dimensions.w, player.properties.dimensions.h
        screen.x, screen.y
        self.state.position.x + self.properties.dimensions.w * self.state.mutliple.nx 
        self.state.position.y + self.properties.dimension.h * self.state.multiple.ny
        
    def frame(self) -> str:
        """
        """
        return self.state.action + self.state.direction + self.state.frame

    def animate(self) -> None:
        """
        """
        self.state.frame = self.state.frame + 1

        if self.state.frame > self.properties.count[self.state.action]:
            self.state.frame = 0
    
    def move(self, velocity: Velocity) -> None:
        """
        """
        self.state.position.x = self.state.position.x + velocity.vx
        self.state.position.y = self.state.position.y + velocity.vy

    def intend(self, intent: State.Intention) -> None:
        """
        """
        # TODO: implement
        return