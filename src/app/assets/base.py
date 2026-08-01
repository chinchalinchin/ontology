"""
Package for foundational Asset class.
"""
# Standard Libraries
from abc import ABC, abstractmethod
from typing import Union, List

# Application Libraries
from app.assets.base import Frame, Shape, Animation
from app.models import Position, Velocity,\
                         Dimensions, Hitbox
from app.models.properties import AssetProperties
from app.models.state import AssetState, AnimationState

# Cython Libraries
from libs.math import Geometry

class Asset:
    """
    Foundational class for all game Assets.
    """
    properties: AssetProperties
    state: AssetState
    shape: Shape
    animation: AnimationState
    frame: int

    def __init__(self, 
        properties: AssetProperties, 
        state: AssetState,
        frame: Union[Frame, None] = None,
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
        dimensions: Dimensions,
        hitboxes: List[Hitbox]
    ):
        self.hitboxes = hitboxes
        self.dimensions = dimensions

    def intersects(self, 
        position: Position, 
        shape: Shape,
        other_position: Position, 
        other_shape: Shape
    ):
        """
        """
        return Geometry.intersects(position, shape, other_position, other_shape)

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
    def key(self, 
        asset: str, 
        state: AssetState
    ) -> str:
        """
        Abstract method for Asset's frame key schema. 
        """
        pass


class Animation(ABC):
    """
    Foundational interface for Assets with animate states.
    """

    @abstractmethod
    def animate(self, 
        state: AssetState, 
        properties: AssetProperties
    ) -> AssetState:
        """
        Abstract method for incrementing Asset's frame key. 
        """
        pass

class Mechanic(ABC):
    """
    """

    @abstractmethod 
    def update(self, board: Board, delta_time: float) -> None:
        pass
    