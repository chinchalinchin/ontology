"""
# Ontology: app.models.state

Models for typing the state attributes of Assets. See documentation for a more in-depth explanation of each field and its purpose. 
"""
# Standard Libraries
from typing import Dict, List, Union
from dataclasses import dataclass, field

# Application Libraries
from app.config.enums import (
    Actions, 
    Directions,
    Intentions,
    Relationships
)

# Cython Libraries
from app.models.adapters import PydanticPosition as Position, PydanticMultiple as Multiple, PydanticVelocity as Velocity

class NoState:
    pass

@dataclass(slots=True)
class AssetState:
    """
    ## AssetState

    Foundational class for Asset states. 
    
    ### Fields

    - layer: Asset Layer Key
    """
    id: str
    name: str
    layer: str

# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class AnimationState:
    """
    ## AnimationState

    Foundational class for animate Asset states.
    
    ### Fields

    - action: Stringified Action Enum
    - direction: Stringified Direction Enum
    - frame: Integer Frame Count
    """
    action: str = Actions.WALK
    direction: str = Directions.DOWN
    frame: int = 0

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------- ASSET STATE MODELS
# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class MultiplierState(AssetState):
    """
    ## MultiplierState

    Asset state for multiplying Assets across the screen.

    ### Fields

    - position: Coordinates (horizontal, vertical) of Asset's upper-left corner.
    - multiple: Vector (horizontal, vertical) of Asset's multiples.
    """
    position: Position
    multiple: Multiple 

@dataclass(slots=True)
class PositionalState(AssetState):
    """
    ## PositionalState

    Asset state for Assets that only track position.

    ### Fields

    - position: Coordinates (horizontal, vertical) of Asset's upper-left corner.
    """
    position: Position

@dataclass(slots=True)
class PropertyState(AssetState):
    """
    ## PropertyState

    Asset state for Assets that have "owners".

    ### Fields

    - owner: Asset name of owner.
    - position: Coordinates (horizontal, vertical) of Asset's upper-left corner.
    """
    owner: str
    position: Position

@dataclass(slots=True)
class MotorState(AssetState):
    """
    ## MotorState

    Asset state for measuring distance from spawn point.

    ### Fields

    - position: Coordinates (horizontal, vertical) of Asset's upper-left corner.
    - initial: Coordinates (horizontal, vertical) of Asset's initial position, relative to it's upper-left corner.
    - direction: Direction of motion.
    - speed: Speed of motion.
    """
    position: Position
    initial: Position
    direction: Directions
    speed: int

@dataclass(slots=True)
class AnimatorState(AssetState):
    """
    ## AnimatorState

    Asset state for Assets that possess both position and animation.

    ### Fields

    - position: Coordinates (horizontal, vertical) of Asset's upper-left corner.
    - animation: Nested AnimationState.
    """
    position: Position
    animation: AnimationState = field(default_factory=AnimationState)

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------- OBJECT STATE MODELS

@dataclass(slots=True)
class ContainerState(AssetState):
    """
    """
    content: List[str]
    position: Position
    switch: bool
    animation: AnimationState = field(default_factory=AnimationState)


@dataclass(slots=True)
class DoorState(AssetState):
    """
    """
    position: Position
    out: Position
    outlayer: str

@dataclass(slots=True)
class SwitchState(AssetState):
    """
    """
    link: str
    position: Position
    switch: bool
    animation: AnimationState = field(default_factory=AnimationState)


# ---------------------------------------------------------------------------------------
# --------------------------------------------------------------------------- SHEET STATE
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------- SHEET STATE FIELDS
    
@dataclass(slots=True)
class Character:
    """
    ## Character
    
    Representation of a Sprite's game characteristics.
    
    ### Fields
    
    - strength:
    - defense:
    - speed:
    """
    strength: int = 10
    defense: int = 10
    speed: int = 10

@dataclass(slots=True)
class Equipment:
    """
    ## Equipment

    Representation of the Sprite's equipment set.
    
    ### Fields

    - armor:
    - weapon:
    - tool:
    - utility:
    - shield:
    """
    armor: str = None
    weapon: str = None
    tool: str = None
    utility: str = None
    shield: str = None

@dataclass(slots=True)
class Meter:
    """
    ## Meter

    Representation of a Sprite meter.
    
    ### Fields

    - current:
    - maximum:
    """
    current: int = 100
    maximum: int = 100

@dataclass(slots=True)
class Meters:
    """
    ## Meters

    Representation of a Sprite's Meter fields. Meters track values that change in response to Sprite Actions.
    
    ### Fields

    - health:
    - magic:
    """
    health: Meter
    magic: Meter

# --------------------------------------------------------------------------------------

@dataclass(slots=True)
class Psyche:
    """
    ## Psyche

    Representation of the internal, hidden state of a Sprite. 
    
    ### Fields

    - motivation:
    - expression:
    - communication:
    """
    motivation: str
    expression: str
    communication: str

@dataclass(slots=True)
class Goal:
    """
    ## Goal

    Representation of a Sprite's overarching Goal.
    
    ### Fields

    - name:
    - category:
    - position:
    """
    name: str
    category: str
    position: Position

@dataclass(slots=True)
class Inventory:
    """
    ## Inventory

    Representation of a Sprite's Inventory.
    
    ### Fields

    - loot:
    - equipment:
    - wallet:
    """
    loot: Dict[str, int] = field(default_factory=dict)
    equipment: Equipment = None
    wallet: int = 0

@dataclass(slots=True)
class Memory:
    """
    ## Memory

    Representation of a Sprite's memory. 
    
    ### Fields

    - goal:
    - communications:
    - prices:
    - relationships:
    """
    goal: Goal
    communications: List[str]
    prices: Dict[str, float]
    relationships: Dict[str, Relationships]
    property: List[str]

# --------------------------------------------------------------------------------------

@dataclass(slots=True)
class VisionMutatorParameters:
    """
    """
    radius: int

@dataclass(slots=True)
class FearMutatorParameters:
    """
    """
    radius: int
    limit: float
    enemy: int

@dataclass(slots=True)
class MutatorTriggers:
    """
    """
    animated: bool = False
    struck: bool = False
    frightened: bool = False
    dead: bool = False
    vision: bool = False

@dataclass(slots=True)
class MutatorParameters:
    fear: FearMutatorParameters
    vision: VisionMutatorParameters

@dataclass(slots=True)
class Mutators:
    """
    Representation of a Sprite's mutators. Mutators alter the Sprite's behavior during the gameplay loop.
    """
    triggers: MutatorTriggers = field(default_factory=MutatorTriggers)
    parameters: MutatorParameters = None

# --------------------------------------------------------------------------------------
# ------------------------------------------------------------------- SHEET STATE MODELS

@dataclass(slots=True)
class SpriteState(AssetState):
    """
    Central model for typing Sprite's state.
    """
    intention: Intentions
    goal: Goal
    position: Position
    character: Character
    inventory: Inventory
    meters: Meters
    mutators: Mutators
    memory: Memory
    animation: AnimationState = field(default_factory=AnimationState)

@dataclass(slots=True)
class PlayerState(AssetState):
    """
    Central model for typing Sprite's state.
    """
    position: Position
    character: Character
    inventory: Inventory
    meters: Meters
    mutators: Mutators = field(default_factory=Mutators)    
    goal: Union[Goal, None] = None
    intention: Union[Intentions, None] = None
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
    
# ---------------------------------------------------------------------------------------
# --------------------------------------------------------------------- MENU STATE MODELS

# TODO