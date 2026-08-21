"""
# Ontology: app.models.state
"""
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field

from app.config.enums import (
    Actions, 
    Directions, 
    Intentions, 
    Relationships
)
from app.models.adapters import (
    PydanticPosition as Position, 
    PydanticMultiple as Multiple, 
    PydanticVelocity as Velocity
)
from libs.core.models import Velocity as CoreVelocity

class NoState:
    pass

@dataclass(slots=True)
class AssetState:
    id: str
    name: Optional[str] = None
    layer: Optional[str] = None
    depth: int = 0
    height: Optional[Union[int, str]] = None

@dataclass(slots=True)
class AnimationState:
    action: str = Actions.WALK
    direction: str = Directions.DOWN
    frame: int = 0

# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class MultiplierState(AssetState):
    position: Optional[Position] = None
    multiple: Optional[Multiple] = None 

@dataclass(slots=True)
class PositionalState(AssetState):
    position: Optional[Position] = None
    velocity: Optional[Velocity] = field(default_factory=lambda: CoreVelocity(0.0, 0.0))

@dataclass(slots=True)
class PropertyState(AssetState):
    owner: Optional[str] = None
    position: Optional[Position] = None

@dataclass(slots=True)
class MotorState(AssetState):
    position: Optional[Position] = None
    initial: Optional[Position] = None
    direction: str = "down"
    speed: int = 10
    velocity: Optional[Velocity] = field(default_factory=lambda: CoreVelocity(0.0, 0.0))

@dataclass(slots=True)
class AnimatorState(AssetState):
    position: Optional[Position] = None
    animation: AnimationState = field(default_factory=AnimationState)

@dataclass(slots=True)
class ContainerState(AssetState):
    content: Optional[List[str]] = field(default_factory=list)
    position: Optional[Position] = None
    switch: Optional[bool] = False
    animation: AnimationState = field(default_factory=AnimationState)

@dataclass(slots=True)
class DoorState(AssetState):
    position: Optional[Position] = None
    out: Optional[Position] = None
    outlayer: Optional[str] = None

@dataclass(slots=True)
class SwitchState(AssetState):
    link: Optional[str] = None
    position: Optional[Position] = None
    switch: Optional[bool] = False
    animation: AnimationState = field(default_factory=AnimationState)

# ---------------------------------------------------------------------------------------

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
    motivation: str
    expression: str
    communication: str

@dataclass(slots=True)
class Goal:
    name: str
    category: str
    position: Position

@dataclass(slots=True)
class Inventory:
    loot: Optional[Dict[str, int]] = field(default_factory=dict)
    equipment: Optional[Equipment] = None
    wallet: int = 0

@dataclass(slots=True)
class Memory:
    goal: Optional[Goal] = None
    communications: List[str] = field(default_factory=list)
    prices: Dict[str, float] = field(default_factory=dict)
    relationships: Dict[str, Relationships] = field(default_factory=dict)
    property: List[str] = field(default_factory=list)

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

@dataclass(slots=True)
class SpriteState(AssetState):
    intention: Optional[Intentions] = None
    goal: Optional[Goal] = None
    position: Optional[Position] = None
    character: Optional[Character] = None
    inventory: Optional[Inventory] = None
    meters: Optional[Meters] = None
    mutators: Optional[Mutators] = None
    memory: Optional[Memory] = None
    velocity: Optional[Velocity] = field(default_factory=lambda: CoreVelocity(0.0, 0.0))
    animation: AnimationState = field(default_factory=AnimationState)

@dataclass(slots=True)
class PlayerState(AssetState):
    position: Optional[Position] = None
    character: Optional[Character] = None
    inventory: Optional[Inventory] = None
    meters: Optional[Meters] = None
    mutators: Mutators = field(default_factory=Mutators)   
    goal: Optional[Goal] = None
    intention: Optional[Intentions] = None
    velocity: Optional[Velocity] = field(default_factory=lambda: CoreVelocity(0.0, 0.0))
    animation: AnimationState = field(default_factory=AnimationState)

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------------- ROOT SCHEMAS

@dataclass(slots=True)
class TileStateInstances:
    back: List[MultiplierState] = field(default_factory=list)
    fore: List[MultiplierState] = field(default_factory=list)

@dataclass(slots=True)
class ObjectStateInstances:
    chests: List[ContainerState] = field(default_factory=list)
    crates: List[PositionalState] = field(default_factory=list)
    doors: List[DoorState] = field(default_factory=list)
    gates: List[SwitchState] = field(default_factory=list)
    plates: List[SwitchState] = field(default_factory=list)

@dataclass(slots=True)
class CraftStateInstances:
    struts: List[PropertyState] = field(default_factory=list)

@dataclass(slots=True)
class CursorStateInstances:
    expressions: List[PositionalState] = field(default_factory=list)
    projectiles: List[MotorState] = field(default_factory=list)

@dataclass(slots=True)
class EffectStateInstances:
    temporary: List[PositionalState] = field(default_factory=list)
    persistent: List[AnimatorState] = field(default_factory=list)

@dataclass(slots=True)
class SheetStateInstances:
    pixies: List[AnimatorState] = field(default_factory=list)
    sprites: List[SpriteState] = field(default_factory=list)
    players: List[PlayerState] = field(default_factory=list)

@dataclass(slots=True)
class StateSchema:
    tiles: TileStateInstances = field(default_factory=TileStateInstances)
    objects: ObjectStateInstances = field(default_factory=ObjectStateInstances)
    crafts: CraftStateInstances = field(default_factory=CraftStateInstances)
    cursors: CursorStateInstances = field(default_factory=CursorStateInstances)
    effects: EffectStateInstances = field(default_factory=EffectStateInstances)
    sheets: SheetStateInstances = field(default_factory=SheetStateInstances)
    compositions: List[PropertyState] = field(default_factory=list)