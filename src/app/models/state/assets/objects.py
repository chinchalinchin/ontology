"""
@workflow.compositions

# Ontology: app.models.state.objects

Python data models for typing Object state attributes.
"""
# Standard Libraries
from typing import ( 
    List,
    Optional
)
from dataclasses import (
    dataclass, 
    field
)

# Application Libraries
from app.config.enums import (
    LayerProjections
)
from app.models.adapters import (
    PydanticPosition as Position, 
    PydanticVelocity as Velocity,
)
from app.models.state.core import (
    AssetState
)

# Cython Libraries
from libs.core.models import (
    Velocity as CoreVelocity
)

# -----------------------------------------------------

@dataclass(slots=True)
class ObjectState(AssetState):
    position: Optional[Position] = None # type: ignore
    material: Optional[str] = None

@dataclass(slots=True)
class MotiveState(AssetState):
    velocity: Optional[Velocity] = field(default_factory=lambda: CoreVelocity(0.0, 0.0)) # type: ignore

@dataclass(slots=True)
class ContainerState(AssetState):
    content: Optional[List[str]] = field(default_factory=list)
    switch: Optional[bool] = False

@dataclass(slots=True)
class DoorState(AssetState):
    out: Optional[Position] = None # type: ignore
    outlayer: Optional[str] = None
    projection: str = LayerProjections.IN.value

@dataclass(slots=True)
class SwitchState(AssetState):
    link: Optional[str] = None
    switch: Optional[bool] = False

@dataclass(slots=True)
class DialogueState(AssetState):
    persona: Optional[str] = None
    lexicon: Optional[str] = None