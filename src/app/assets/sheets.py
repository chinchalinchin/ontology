"""
Package for Sheet Assets.
"""
# Application Libraries
from app.models import Velocity
from app.assets.base import Asset
from app.models.properties import SpriteProperties
from app.models.state import SpriteState, Animation
from app.physics.collisions import Shape

class Sprite(Asset):
    """
    """

    def __init__(self, 
        **kwargs
    ):
        super().__init__(**kwargs)
        

    def intend(self, intent: State.Intention) -> None:
        """
        """
        # TODO: implement
        return

class SpriteAnimation(Animation):
    """
    """

    def animate(self, animation: Animation, props: SpriteProperties) -> None:
        """
        """
        animation.frame = animation.frame + 1

        if self.state.frame > self.properties[self.state.action].count:
            self.state.frame = 0
    

class SpriteFrame(Frame):
    """
    """

    def frame(self, animation: Animation) -> str:
        """
        """
        return animation.action + animation.direction + animation.frame
 