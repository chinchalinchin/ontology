"""
# Ontology: Asset Base

Package for foundational Asset classes and interfaces.
"""
# Standard Libraries
from abc import ABC, abstractmethod
from itertools import chain
from typing import Union

# Application Libraries
from app.assets.base import Frame, Shape, Animation
from app.game.board import Board
from app.models.properties import AssetProperties
from app.models.state import AssetState, AnimationState

# Cython Libraries
from libs.math import Geometry
from libs.core import Dimensions, Shape

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

    def onscreen(self, player: Player, screensize: Dimensions) -> str: 
        """
        """
        return Geometry.onscreen(self.shape, player.shape, screensize)


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
    def update(self, board: Board, delta: float) -> None:
        pass

class AnimationMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta: float) -> None:
        for asset in chain(
            board.permanent, 
            board.temporary,
            board.chests, 
            board.gates, 
            board.plates,
            board.pixies, 
            board.sprites
        ):
            asset.animate(asset.state, asset.properties)
        pass 