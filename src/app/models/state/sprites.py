"""
# Ontology: app.models.state.sprites

Python data models for typing Sprite state attributes.
"""
# Standard Libraries
from typing import (
    Dict, 
    List,
    Optional
)
from dataclasses import dataclass, field

# Application Libraries
from app.config.enums import (
    Intentions, 
    Relationships,
)
from app.models.adapters import (
    PydanticPosition as Position, 
    PydanticVelocity as Velocity,
)
from app.models.state.core import (
    AnimationState,
    AssetState
)

# Cython Libraries
from libs.core.models import Velocity as CoreVelocity

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------- SPRITE STATE FIELDS

@dataclass(slots=True)
class Character:
    strength: int = 10
    defense: int = 10
    speed: int = 10
    impulse: int = 10

@dataclass(slots=True)
class Equipment:
    armor: Optional[str] = None
    weapon: Optional[str] = None
    tool: Optional[str] = None
    utility: Optional[str] = None
    shield: Optional[str] = None

@dataclass(slots=True)
class Meter:
    current: int = 100
    maximum: int = 100

@dataclass(slots=True)
class Meters:
    health: Meter
    magic: Meter

@dataclass(slots=True)
class Psyche:
    persona: str
    motivation: Optional[str] = None
    expression: Optional[str] = None
    dialogue: Optional[str] = None

@dataclass(slots=True)
class Goal:
    name: str
    category: str
    position: Position # type: ignore

@dataclass(slots=True)
class Inventory:
    loot: Optional[Dict[str, int]] = field(default_factory=dict)
    equipment: Optional[Equipment] = None
    wallet: int = 0

@dataclass(slots=True)
class Memory:
    goals: Optional[Goal] = None
    rumors: Optional[List[str]] = None
    prices: Optional[Dict[str, float]] = None
    relationships: Optional[Dict[str, Relationships]] = None
    property: Optional[List[str]] = None

@dataclass(slots=True)
class VisionMutatorParameters:
    radius: int

@dataclass(slots=True)
class FearMutatorParameters:
    radius: int
    limit: float
    enemy: int

@dataclass(slots=True)
class MutatorTriggers:
    animated: bool = False
    struck: bool = False
    frightened: bool = False
    dead: bool = False
    vision: bool = False
    executed: bool = False

@dataclass(slots=True)
class MutatorParameters:
    fear: FearMutatorParameters
    vision: VisionMutatorParameters

@dataclass(slots=True)
class Mutators:
    triggers: MutatorTriggers = field(default_factory=MutatorTriggers)
    parameters: Optional[MutatorParameters] = None

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------------- SPRITE STATES

@dataclass(slots=True)
class SpriteState(AssetState):
    intention: Optional[Intentions] = None
    goal: Optional[Goal] = None
    position: Optional[Position] = None # type: ignore
    character: Optional[Character] = None
    inventory: Optional[Inventory] = None
    meters: Optional[Meters] = None
    mutators: Optional[Mutators] = None
    memory: Optional[Memory] = None
    psyche: Optional[Psyche] = None
    velocity: Optional[Velocity] = field(default_factory=lambda: CoreVelocity(0.0, 0.0)) # type: ignore
    animation: AnimationState = field(default_factory=AnimationState)

@dataclass(slots=True)
class PlayerState(AssetState):
    position: Optional[Position] = None # type: ignore
    character: Optional[Character] = None
    inventory: Optional[Inventory] = None
    meters: Optional[Meters] = None
    mutators: Mutators = field(default_factory=Mutators)   
    goal: Optional[Goal] = None
    intention: Optional[Intentions] = None
    velocity: Optional[Velocity] = field(default_factory=lambda: CoreVelocity(0.0, 0.0)) # type: ignore
    animation: AnimationState = field(default_factory=AnimationState)
