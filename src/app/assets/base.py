"""
# Ontology: app.assets.base

Package for foundational Asset classes and interfaces.
"""
# Standard Libraries
from abc import (
    ABC, 
    abstractmethod
)
from dataclasses import dataclass
from typing import (
    Dict,
    List, 
    Tuple,
    Optional,
    Type,
    Any,
)

# Application Libraries
import app.config.settings as settings
from app.config.enums import (
    AssetInstances,
    ChannelTypes,
    Substrates,
    LayerProjections,
)
from app.models.properties import AssetProperties
from app.models.state import (
    AssetState,
    CalendarState
)

# Cython Libraries
from libs.core.models import (
    Dimensions, 
    Hitbox, 
    Position
)

class Singleton(ABC):
    _instances: Dict[Type[Any], Any] = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]

    
@dataclass(slots=True)
class Taxonomy:
    id: str
    name: str
    category: str
    instance: str


class Frame(Singleton):
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

    def channels(self, 
        id: str, 
        state: AssetState, 
        properties: AssetProperties
    ) -> List[Tuple]:
        directives = []
        if state.mutators.triggers.submerged:
            if properties.dimensions:
                half_l = properties.dimensions.l // 2
                # (CHANNEL_SUBMERGE, split_y, r, g, b, a)
                # e.g., deep aquatic modulation: RGBA(40, 110, 180, 170)
                # TODO: this should be codified in a ChannelPayload data structure 
                #       to pass to the screen. Screen should unpack channel payload 
                #       into Cython primitives.  
                directives.append((
                    ChannelTypes.SUBMERGE.value,
                    (half_l, 40, 110, 180, 170)
                ))
        return directives

    def eras(self, 
        id: str, 
        calendar: CalendarState
    ) -> List[Tuple[str, int, int]]:
        """
        Macro-temporal epochal projection for static pre-rendered canvas baking.
        Default implementation falls back to static frame resolution.
        """
        return self.keys(id, None)

    
class Animation(Singleton):
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


class HitboxSchema(Singleton):
    """
    Foundational interface for Assets that participate in collisions and interactions.
    """
    @abstractmethod
    def elevations(
        self,
        properties: AssetProperties,
        state: AssetState
    ) -> List[int]:
        """Returns all discrete elevation tiers this asset participates in."""
        pass

    @abstractmethod
    def get(
        self,
        properties: AssetProperties,
        state: AssetState,
        elevation: int,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        """Resolves active physical hitboxes at the specified elevation plane."""
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
        animation: Animation=None,
        hitbox: HitboxSchema=None,
    ):
        self.taxonomy = taxonomy
        self.properties = properties
        self.state = state
        self.frame = frame
        self.animation = animation
        self.hitbox = hitbox

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
    def elevation(self) -> int:
        return self.state.elevation if self.state.elevation is not None else 0

    
    @elevation.setter
    def elevation(self, value: Optional[int]) -> None:
        self.state.elevation = value

    @property
    def substrate(self) -> int:
        return self.state.substrate

    @substrate.setter
    def substrate(self, value: int) -> None:
        self.state.substrate = value

    @property
    def hitboxes(self) -> List[Hitbox]:
        """Default physical footprint resolved at the asset's deployed elevation."""
        return self.hitbox.get(self.properties, self.state, self.elevation, self.frame)

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