"""
# Ontology: app.models.state.effects

Python data models for typing Effect state attributes.
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
    PydanticHitbox as Hitbox
)
from app.models.state.core import (
    AnimationState,
    AssetState
)

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------------- ASSET STATES

# ------------------------------------------------------------------------ EFFECT FIELDS

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

@dataclass(slots=True)
class Pool:
    x: int
    y: int
    w: int
    l: int

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
class ReactableState(EffectState):
    intention: str = Intentions.INTERACT.value
    cooldown: int = 60
    active: bool = False

@dataclass(slots=True)
class CollectableState(EffectState):
    lot: Lot = field(default_factory=Lot)

@dataclass(slots=True)
class FluidState(EffectState):
    # Overrides
    height: Optional[int] = 0
    depth: int = -1
    # Fluid Fields
    length: int = 0
    pool: Optional[Pool] = None
    hitboxes: List[Hitbox] = field(default_factory=list) # type: ignore
    dirty: bool = True
    flow: int = 1
    source: Directions = Directions.DOWN.value
    shorelines: List[str] = field(default_factory=list)
