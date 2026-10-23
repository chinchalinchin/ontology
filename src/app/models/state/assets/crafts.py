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
class CraftState(AssetState):
    position: Optional[Position] = None # type: ignore
    material: Optional[str] = None
    blueprint: Optional[str] = None
    multiple: Optional[Multiple] = None # type: ignore


@dataclass(slots=True)
class PropertyState(CraftState):
    owner: Optional[str] = None


@dataclass(slots=True)
class StairState(CraftState):
    """
    State representation for walkable incline transitions.
    """
    delta: int = 1

    @property
    def direction(self) -> Optional[str]:
        return self.blueprint                      


@dataclass(slots=True)
class PlatformState(PropertyState):
    elevation: int = 0
