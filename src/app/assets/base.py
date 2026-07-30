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

UNIFIED_PROPS = Union[
    properties.CursorProperties,
    properties.EffectProperties,
    properties.ObjectProperties,
    properties.SheetProperties,
    properties.TileProperties
]

UNIFIED_STATE = Union[
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

class Asset:
    """
    Foundational class for all game Assets.
    """
    properties: UNIFIED_PROPS
    state: UNIFIED_STATE
    shape: Shape
    animation: Animation
    frame: int

    def __init__(self, 
        properties: UNIFIED_PROPS, 
        state: UNIFIED_STATE,
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

    def _relative(self, position: Position):
        return [
            Hitbox(
                position.x + hb.position.x, 
                position.y + hb.position.y,
                hb.dimensions.w,
                hb.dimensions.l
            ) for hb in self.hitboxes
        ]

    def intersects(self, position: Position, other: Shape):
        """
        """
        for hb in self._relative(position):
            for ohb in other.hitboxes:
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
    def key(self, animation: state.Animation) -> str:
        """
        Abstract method for Asset's frame key schema. 
        """
        pass


class Animation(ABC):
    """
    Foundational interface for Assets with animate states.
    """

    @abstractmethod
    def animate(self, animation: state.Animation, properties: UNIFIED_PROPS) -> None:
        """
        Abstract method for incrementing Asset's frame key. 
        """
        pass