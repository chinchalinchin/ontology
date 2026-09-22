"""
# Ontology: app.models.state.geography

Python data models for typing Geography state attributes.
"""
# Standard Libraries
from typing import ( 
    List,
    Optional
)
from dataclasses import dataclass, field

# Application Libraries
from app.config.enums import (
    Directions,
)
from app.models.adapters import (
    PydanticPosition as Position, 
    PydanticHitbox as Hitbox
)
from app.models.state.core import (
    AssetState
)


# --------------------------------------------------------------------- GEOGRAPHY STATES

@dataclass(slots=True)
class ShorelineState(AssetState):
    position: Optional[Position] = None # type: ignore
    orientation: str = Directions.DOWN.value
    length: int = 0
    thickness: int = 8
    bidirectional: bool = True
    parent_fluid: Optional[str] = None
    hitboxes: List[Hitbox] = field(default_factory=list) # type: ignore