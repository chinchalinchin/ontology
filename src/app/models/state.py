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
    Intentions
)

# Cython Libraries
from libs.core.models import Position, Multiple

class NoState:
    pass

# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class AssetState:
    """
    Foundational class for Asset states. 
    """
    layer: str
    
# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class AnimationState:
    """
    Foundational class for animate Asset states.
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
    Asset state for multiplying Assets across the screen.

    - position: Coordinates (horizontal, vertical) of Asset's upper-left corner.
    - multiple: Vector (horizontal, vertical) of Asset's multiples.
    """
    position: Position
    multiple: Multiple 

@dataclass(slots=True)
class PositionalState(AssetState):
    """
    Asset state for Assets that only track position.

    - position: Coordinates (horizontal, vertical) of Asset's upper-left corner.
    """
    position: Position

@dataclass(slots=True)
class PropertyState(AssetState):
    """
    """
    owner: str
    position: Position

@dataclass(slots=True)
class MetricState(AssetState):
    """
    Asset state for measuring distance from spawn point.

    - position: Coordinates (horizontal, vertical) of Asset's upper-left corner.
    - initial: Coordinates (horizontal, vertical) of Asset's initial position, relative to it's upper-left corner.
    """
    position: Position
    initial: Position

@dataclass(slots=True)
class AnimatorState(AssetState):
    """
    Asset state for Assets that possess both position and animation.

    - position: Coordinates (horizontal, vertical) of Asset's upper-left corner.
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
    Representation of a Sprite's game characteristics.
    """
    strength: int = 10
    defense: int = 10
    speed: int = 10

@dataclass(slots=True)
class Equipment:
    """
    Representation of the Sprite's equipment set.
    """
    armor: str = None
    weapon: str = None
    tool: str = None
    utility: str = None
    shield: str = None

@dataclass(slots=True)
class Meter:
    """
    Representation of a Sprite meter.
    """
    current: int = 100
    maximum: int = 100

@dataclass(slots=True)
class Meters:
    """
    Representation of a Sprite's Meter fields. Meters track values that change in response to Sprite Actions.
    """
    health: Meter
    magic: Meter

# --------------------------------------------------------------------------------------

@dataclass(slots=True)
class Psyche:
    """
    Representation of the internal, hidden state of a Sprite. 
    """
    motivation: str
    expression: str
    communication: str

@dataclass(slots=True)
class Goal:
    """
    Representation of a Sprite's overarching Goal.
    """
    name: str
    category: str
    position: Position

@dataclass(slots=True)
class Inventory:
    """
    Representation of a Sprite's Inventory.
    """
    loot: Dict[str, int] = field(default_factory=dict)
    equipment: Equipment = None
    wallet: int = 0

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

@dataclass(slots=True)
class Memory:
    """
    Representation of a Sprite's memory. 
    """
    goal: Goal
    communications: List[str]
    prices: Dict[str, float]

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
# --------------------------------------------------------------------- MENU STATE MODELS

# TODO