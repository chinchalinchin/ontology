"""
Package for foundational Asset class.
"""
# Standard Libraries
from abc import ABC, abstractmethod
# Application Libraries
from app.models import Velocity, Dimensions
import app.models.state as state
import app.models.properties as properties

class Asset(ABC):
    """
    Foundational class for all game Assets.
    """
    properties: properties.AssetProperties

    def __init__(self, properties.AssetProperties, **kwargs):
        super().__init__(**kwargs)
        self.properties = properties

    @abstractmethod
    def frame(self) -> str:
        """
        Abstract method for returning Asset's frame key.
        """
        pass 

    @abstractmethod
    def onscreen(self, screen: Dimensions, player: Player) -> bool:
        """
        Abstract method for determining if Asset is onscreen.
        """
        pass

    @abstractmethod
    def animate(self) -> None:
        """
        Abstract method for incrementing Asset's frame key. 
        """
        pass

    @abstractmethod 
    def move(self, velocity: Velocity) -> None:
        """
        Abstract method for moving the Asset Position state.
        """
        pass