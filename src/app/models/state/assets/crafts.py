"""
# Ontology: app.models.state.crafts

Python data models for typing Craft state attributes.
"""
# Standard Libraries
from typing import ( 
    Optional,
)
from dataclasses import (
    dataclass,
)

# Application Libraries
from app.config.enums import (
    Orientations,
    Directions
)
from app.models.adapters import (
    PydanticPosition as Position, 
    PydanticMultiple as Multiple
)
from app.models.state.core import (
    AssetState,
)

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------------- CRAFT STATES
# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class PropertyState(AssetState):
    owner: Optional[str] = None
    position: Optional[Position] = None # type: ignore

@dataclass(slots=True)
class OrientedState(AssetState):
    position: Optional[Position] = None # type: ignore
    orientation: str = Orientations.HORIZONTAL.value
    multiple: Optional[Multiple] = None # type: ignore
    owner: Optional[str] = None

@dataclass(slots=True)
class StairState(AssetState):
    """
    State representation for walkable incline transitions.
    """
    position: Optional[Position] = None # type: ignore
    direction: str = Directions.UP.value
    delta: int = 1                         
    owner: Optional[str] = None

@dataclass(slots=True)
class PlatformState(AssetState):
    position: Optional[Position] = None # type: ignore
    elevation: int = 0
    owner: Optional[str] = None