"""
# Ontology: Models

Models for typing the state attributes of Assets. See documentation for a more in-depth explanation of each field and its purpose. 
"""
# Standard Libraries
from typing import Callable, Dict, List, Union
from dataclasses import dataclass

# Cython Libraries
from libs.core import Position, Multiple

# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class AssetState:
    """
    Foundational class for Asset states. 
    """
    name: str
    layer: str
    
# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class AnimationState:
    """
    Foundational class for animate Asset states.

    - action: Action key, possibly null.
    - direction: Direction key, possibly null.
    - frame: Frame index, possible null.
    """
    action: Union[str, None]
    direction: Union[str, None]
    frame: Union[int, None]

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
    owner: str                  # Unique Owner Identifer
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
    animation: AnimationState

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------- OBJECT STATE MODELS

@dataclass(slots=True)
class ContainerState(AssetState):
    """
    """
    content: List[str]      # Content Identifier Keys
    position: Position      # Position of Asset on Board
    animation: AnimationState
    switch: bool            # Binary state flag

@dataclass(slots=True)
class DoorState(AssetState):
    """
    """
    position: Position      # Position of Asset on Board
    out: Position           # Out Position of Asset
    outlayer: str           # Out Layer Identifier Key

@dataclass(slots=True)
class SwitchState(AssetState):
    """
    """
    link: str               # Link Identifier Key
    position: Position      # Position
    animation: AnimationState
    switch: bool            # Binary state flag

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
    strength: int
    defense: int
    speed: int

@dataclass(slots=True)
class Equipment:
    """
    Representation of the Sprite's equipment set.
    """
    armor: str
    weapon: str
    tool: str
    utility: str

@dataclass(slots=True)
class Health:
    """
    Representation of a Sprite's health meter.
    """
    current: int 
    maximum: int

@dataclass(slots=True)
class Magic:
    """
    Representation of a Sprite's magic meter.
    """
    current: int 
    maximum: int

@dataclass(slots=True)
class Meters:
    """
    Representation of a Sprite's Meter fields. Meters track values that change in response to Sprite Actions.
    """
    health: Health
    magic: Magic

# --------------------------------------------------------------------------------------

@dataclass(slots=True)
class Intention:
    """
    Representation of the internal, hidden state of a Sprite. 
    """
    extension: str
    disposition: str
    motivation: str
    expression: str

@dataclass(slots=True)
class Goal:
    """
    Representation of a Sprite's overarching Goal.
    """
    name: str
    category: str
    intention: Intention

@dataclass(slots=True)
class Inventory:
    """
    Representation of a Sprite's Inventory.
    """
    loot: Dict[str, int]
    equipment: Equipment
    wallet: int

# --------------------------------------------------------------------------------------

@dataclass(slots=True)
class VisionMutator:
    """
    """
    radius: int

@dataclass(slots=True)
class FearMutator:
    """
    """
    radius: int
    limit: float
    enemy: int

@dataclass(slots=True)
class Mutators:
    """
    Representation of a Sprite's mutators. Mutators alter the Sprite's behavior during the gameplay loop.
    """
    fear: FearMutator
    vision: VisionMutator

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
    position: Position
    animation: AnimationState
    character: Character
    intention: Intention
    inventory: Inventory
    meters: Meters
    mutators: Mutators
    memory: Memory
    goal: Goal

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------- MENU STATE MODELS

@dataclass(slots=True)
class IconState(AssetState):
    """
    """
    pass

@dataclass(slots=True)
class SymbolState(AssetState):
    """
    """
    pass

@dataclass(slots=True)
class WindowState(AssetState):
    """
    """
    pass