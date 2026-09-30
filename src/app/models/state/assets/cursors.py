"""
# Ontology: app.models.state.cursors

Python data models for typing Cursors state attributes.
"""
# Standard Libraries
from typing import ( 
    Optional
)
from dataclasses import dataclass, field

# Application Libraries
from app.config.enums import (
    Directions,
)
from app.models.adapters import (
    PydanticPosition as Position, 
    PydanticVelocity as Velocity,
)
from app.models.state.core import (
    AssetState
)

# Cython Libraries
from libs.core.models import Velocity as CoreVelocity


@dataclass(slots=True)
class MotorState(AssetState):
    position: Optional[Position] = None # type: ignore
    initial: Optional[Position] = None # type: ignore
    direction: Directions = Directions.DOWN.value
    speed: int = 10
    velocity: Optional[Velocity] = field(default_factory=lambda: CoreVelocity(0.0, 0.0)) # type: ignore

@dataclass(slots=True)
class AttachmentState(AssetState):
    icon: Optional[str] = None
    ttl: Optional[int] = 120
    offset: Optional[Position] = None # type: ignore