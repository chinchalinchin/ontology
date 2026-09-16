"""
# Ontology: app.models.state.object

Python data models for typing Object state attributes.
"""
# Standard Libraries
from typing import ( 
    List,
    Optional
)
from dataclasses import dataclass, field

# Application Libraries
from app.config.enums import (
    Reactions,
    Directions,
    Intentions,
    Inventories
)
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
from libs.core.models import Velocity as CoreVelocity

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------------- ASSET STATES

@dataclass(slots=True)
class Damage:
    amount: int = 0
    duration: int = 0
    reaction: Reactions = Reactions.BOUNCE.value

@dataclass(slots=True)
class Lot:
    inventory: Inventories = Inventories.EQUIPMENT.value
    item: Optional[str] = None 
    quantity: int = 0

# ------------------------------------------------------------------------ OBJECTS STATES

@dataclass(slots=True)
class MultiplierState(AssetState):
    position: Optional[Position] = None # type: ignore
    multiple: Optional[Multiple] = None # type: ignore

@dataclass(slots=True)
class PositionalState(AssetState):
    position: Optional[Position] = None # type: ignore
    velocity: Optional[Velocity] = field(default_factory=lambda: CoreVelocity(0.0, 0.0)) # type: ignore

@dataclass(slots=True)
class PropertyState(AssetState):
    owner: Optional[str] = None
    position: Optional[Position] = None # type: ignore

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

# ------------------------------------------------------------------------- CURSOR STATES

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

# ------------------------------------------------------------------------ EFFECT STATES

@dataclass(slots=True)
class EffectState(AssetState):
    position: Optional[Position] = None # type: ignore
    animation: AnimationState = field(default_factory=AnimationState)
    active: bool = True

@dataclass(slots=True)
class HazardState(EffectState):
    damage: Damage = field(default_factory=Damage)

@dataclass(slots=True)
class InteractableState(EffectState):
    intention: str = Intentions.INTERACT.value
    cooldown: int = 60
    active: bool = False

@dataclass(slots=True)
class CollectableState(EffectState):
    lot: Lot = field(default_factory=Lot)