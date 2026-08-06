"""
# Ontology: Asset Base

Package for foundational Asset classes and interfaces.
"""
# Standard Libraries
from abc import ABC, abstractmethod
from typing import Union

# Application Libraries
from app.models.properties import AssetProperties
from app.models.state import AssetState, AnimationState
from app.player import Player

# Cython Libraries
from libs.math import Geometry
from libs.core import Dimensions, Shape

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

class Asset:
    """
    Foundational class for all game Assets.
    """
    properties: AssetProperties
    state: AssetState
    frame: int
    animation: Animation

    def __init__(self, properties, state, frame=None, animation=None):
        self.properties = properties
        self.state = state
        self.frame = frame
        self.animation = animation

    def onscreen(self, player: Player, screensize: Dimensions) -> bool: 
        return Geometry.onscreen(
            self.state.position, self.properties.dimensions,
            player.state.position, player.properties.dimensions, 
            screensize
        )