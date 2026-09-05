"""
# Ontology: app.assets.base

Package for foundational Asset classes and interfaces.
"""
# Standard Libraries
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    List, 
    Tuple
)

# Application Libraries
from app.models.properties import AssetProperties
from app.models.state import AssetState

# Cython Libraries
from libs.core.models import (
    Dimensions, 
    Hitbox, 
    Position
)

@dataclass(slots=True)
class Taxonomy:
    id: str
    name: str
    category: str
    instance: str

class Frame(ABC):
    """
    Foundational interface for Assets.
    """
    @abstractmethod
    def keys(self, 
        id: str, 
        state: AssetState
    ) -> List[Tuple[str, int, int]]:
        """
        Abstract method for Asset's frame key schema. 
        Returns a list of tuples: (frame_key, offset_x, offset_y)
        """
        pass

    @abstractmethod
    def index(self, id: str, properties: dict) -> dict[str, tuple[int, int, int, int]]:
        """
        Generates a mapping of all possible frame keys to their crop coordinates (sx, sy, w, l).
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
    taxonomy: Taxonomy
    properties: AssetProperties
    state: AssetState
    frame:  Frame
    animation: Animation

    def __init__(self,
        taxonomy: Taxonomy,
        properties: AssetProperties, 
        state: AssetState, 
        frame: Frame=None, 
        animation: Animation=None
    ):
        self.taxonomy = taxonomy
        self.properties = properties
        self.state = state
        self.frame = frame
        self.animation = animation

    @property
    def id(self) -> str: 
        return self.taxonomy.id

    @property
    def name(self) -> str:
        return self.taxonomy.name

    @property
    def category(self) -> str:
        return self.taxonomy.category

    @property
    def instance(self) -> str:
        return self.taxonomy.instance
    
    @property
    def dimensions(self) -> Dimensions:
        """Unified spatial retrieval for rendering and camera culling."""
        if hasattr(self.properties, 'dimensions'):
            return self.properties.dimensions
        return None

    @property
    def hitboxes(self) -> list:
        """Unified hitbox retrieval. Defaults to sprite bounding box if none explicitly defined."""
        hbs = []
        if hasattr(self.properties, 'hitboxes') and self.properties.hitboxes:
            hbs = self.properties.hitboxes
        elif hasattr(self.properties, 'personas') and self.properties.personas.get(self.taxonomy.id) and self.properties.personas[self.taxonomy.id].hitboxes:
            hbs = self.properties.personas[self.taxonomy.id].hitboxes
            
        # Automatically generate a default physics body matching the visual dimensions
        if not hbs and self.dimensions:
            hbs = [Hitbox(Position(0, 0), self.dimensions)]
            
        return hbs

    def primitive(self, index: int = 0, hitboxes: list = None) -> tuple:
        """
        Extracts spatial attributes into primitive integers for Cython math operations.
        Returns: (index, x, y, w, l, hitboxes)
        """
        pos = getattr(self.state, 'position', None)
        x = pos.x if pos else 0
        y = pos.y if pos else 0
        w = self.dimensions.w if self.dimensions else 0
        l = self.dimensions.l if self.dimensions else 0
        return (index, x, y, w, l, hitboxes if hitboxes is not None else self.hitboxes)