"""
# Ontology: app.assets.base

Package for foundational Asset classes and interfaces.
"""
# Standard Libraries
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    Any,
    Dict,
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
        pass

    @abstractmethod
    def index(self, 
        id: str, 
        properties: AssetProperties
    ) -> Dict[str, Tuple[int, int, int, int]]:
        """
        Generates a mapping of all possible frame keys to their crop coordinates (sx, sy, w, l).
        """
        pass

    @abstractmethod
    def channels(self, 
        id: str, 
        state: AssetState,
        properties: AssetProperties
    ) -> List[Tuple]:
        """
        Emits auxiliary rendering directives (tints, masks, overlays) evaluated against dynamic asset state.
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
        return self.properties.dimensions

    @property
    def hitboxes(self) -> List[Hitbox]:
        """
        Unified hitbox retrieval. Prefers dynamic state hitboxes if present,
        falling back to static property definitions.
        """
        state_hbs = getattr(self.state, "hitboxes", None)
        if state_hbs is not None:
            return state_hbs

        hbs = self.properties.hitboxes
        if not hbs and self.dimensions:
            hbs = [Hitbox(Position(0, 0), self.dimensions)]
            
        return hbs

    def primitive(self, index: int = 0, hitboxes: List[Hitbox] = None) -> Tuple:
        """
        Extracts spatial attributes into primitive integers for Cython math operations.

        - hitboxes: List of Hitbox overrides.

        Returns: (index, x, y, w, l, hitboxes)
        """
        return (
            index, 
            self.state.position.x, 
            self.state.position.y, 
            self.dimensions.w, 
            self.dimensions.l,
            hitboxes if hitboxes is not None else self.hitboxes
        )