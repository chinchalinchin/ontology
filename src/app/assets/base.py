"""
Package for foundational Asset class.
"""
# Standard Libraries
from abc import ABC, abstractmethod
from typing import Union
# Application Libraries
from app.models import Velocity, Dimensions
from app.math import Geometry
import app.models.state as state
import app.models.properties as properties


class Asset:
    """
    Foundational class for all game Assets.
    """
    properties: Union[
        properties.CursorProperties,
        properties.EffectProperties,
        properties.ObjectProperties,
        properties.SheetProperties,
        properties.TileProperties
    ]

    state: Union[
        state.ExpressionCursorState,
        state.ProjectileState,
        state.PersistentEffectState,
        state.TemporaryEffectState,
        state.ChestState,
        state.CrateState,
        state.DoorState,
        state.GateState,
        state.PlateState,
        state.PixieState,
        state.SpriteState,
        state.TileState
    ]

    shape: Shape

    animation: Animation

    def __init__(self, 
        properties, 
        state,
        animation
    ):
        self.properties = properties
        self.state = state
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
    position: Position
    dimensions: Dimensions
    hitboxes: List[Hitbox]

    def __init__(self, 
        position: Position
        dimensions: Dimension
        hitboxes: List[Hitbox]
    ):
        self.position = position
        self.hitboxes = hitboxes
        self.dimensions = dimensions

    def intersects(self, other: Shape):
        """
        """
        for hb in self.hitboxes:
            for ohb in other.hitboxes:
                if Geometry.intersect(hb, ohb):
                    return True 
        return False

    def move(self, velocity: Velocity) -> None:
        """
        Method for moving the Asset position state.
        """
        self.position.x = self.position.x + velocity.vx
        self.position.y = self.position.y + velocity.vy


class Frame(ABC):
    """
    Foundational class for Assets.
    """

    def key(self, animation: properties.Animation) -> str:
        """
        Abstract method for Asset's frame key schema. 
        """
        pass


class Animation(ABC):
    """
    Foundational class for Assets with animate states.
    """

    @abstractmethod
    def animate(self) -> None:
        """
        Abstract method for incrementing Asset's frame key. 
        """
        pass