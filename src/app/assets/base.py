"""
Package for foundational Asset class.
"""
# Standard Libraries
from abc import ABC, abstractmethod
from typing import Union
# Application Libraries
from app.models import Velocity, Dimensions
from app.models.properties import AssetProperties
from app.models.state import AssetState, Animation
from app.math import Geometry

class Asset:
    """
    Foundational class for all game Assets.
    """
    properties: AssetProperties
    state: AssetState
    shape: Shape
    animation: Animation
    frame: int

    def __init__(self, 
        properties: AssetProperties, 
        state: AssetState,
        frame: Union[Frame, None] = None
        animation: Union[Animation, None] = None
    ):
        self.properties = properties
        self.state = state
        self.frame = frame
        self.animation = animation
        self.shape = Shape(
            state.position, 
            properties.dimensions, 
            properties.hitboxes
        )

    def update(self):
        """
        """
        # TODO: everything else
        self.animation.animate()

    def onscreen(self, player: Player, screen: Screen) -> str: 
        """
        """
        return Geometry.onscreen(self.shape, player.shape, screen.dimensions)


class Shape:
    """
    Foundational class for Assets with mutable states.
    """
    dimensions: Dimensions
    hitboxes: List[Hitbox]

    def __init__(self, 
        dimensions: Dimension
        hitboxes: List[Hitbox]
    ):
        self.hitboxes = hitboxes
        self.dimensions = dimensions

    def intersects(self, 
        position: Position, 
        other_position: Position, 
        other_shape: Shape
    ):
        """
        """
        for hb in self.hitboxes:
            for ohb in other_shape.hitboxes:
                this_x = position.x + hb.position.x, 
                this_y = position.y + hb.position.y,
                this_w = hb.dimensions.w
                this_l = hb.dimensions.l

                that_x = other_position.x + ohb.position.x
                that_y = other_position.y + ohb.position.y
                this_w = ohb.dimensions.w 
                that_l = ohb.dimension.l
                if Geometry.intersect(hb, ohb):
                    return True 
        return False

    def move(self, position: Position, velocity: Velocity) -> None:
        """
        Method for moving the Asset position state.
        """
        position.x = position.x + velocity.vx
        position.y = position.y + velocity.vy


class Frame(ABC):
    """
    Foundational interface for Assets.
    """

    @abstractmethod
    def key(self, animation: Animation) -> str:
        """
        Abstract method for Asset's frame key schema. 
        """
        pass


class Animation(ABC):
    """
    Foundational interface for Assets with animate states.
    """

    @abstractmethod
    def animate(self, animation: Animation, properties: AssetProperties) -> Animation:
        """
        Abstract method for incrementing Asset's frame key. 
        """
        pass