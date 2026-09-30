"""
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
from app.models.adapters import (
    PydanticPosition as Position, 
    PydanticMultiple as Multiple, 
    PydanticVelocity as Velocity,
)
from app.models.state.core import (
    AnimationState,
    AssetState
)

# Cython Libraries
from libs.core.models import (
    Velocity as CoreVelocity
)

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------------- OBJECT STATES
# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class PositionalState(AssetState):
    position: Optional[Position] = None # type: ignore
    velocity: Optional[Velocity] = field(default_factory=lambda: CoreVelocity(0.0, 0.0)) # type: ignore

@dataclass(slots=True)
class ContainerState(AssetState):
    content: Optional[List[str]] = field(default_factory=list)
    position: Optional[Position] = None # type: ignore
    switch: Optional[bool] = False
    animation: AnimationState = field(default_factory=AnimationState)

@dataclass(slots=True)
class DoorState(AssetState):
    position: Optional[Position] = None # type: ignore
    out: Optional[Position] = None # type: ignore
    outlayer: Optional[str] = None

@dataclass(slots=True)
class SwitchState(AssetState):
    link: Optional[str] = None
    position: Optional[Position] = None # type: ignore
    switch: Optional[bool] = False
    animation: AnimationState = field(default_factory=AnimationState)

@dataclass(slots=True)
class DialogueState(AssetState):
    position: Optional[Position] = None # type: ignore
    persona: Optional[str] = None
    lexicon: Optional[str] = None