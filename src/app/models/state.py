"""
# Ontology: Models

Models for typing the state attributes of Assets. See documentation for a more in-depth explanation of each field and its purpose. 
"""
# Standard Libraries
from typing import Dict, List, Union

# Cython Libraries
from libs.models import Position, Multiple

# ---------------------------------------------------------------------------------------

class AssetState:
    """
    Foundational class for Asset states. 

    - key: Asset key
    - layer: Layer key 
    ## Asset Hierarchy Keys
    - category: Category key (e.g. Tile, Object, Cursors, etc.)
    - instance: Instance key (e.g. Expressions, Projectiles, Temporary, etc.)
    """
    # ---------------------------------------------------- KEYS
    key: str
    layer: str
    category: str
    pass 

# ---------------------------------------------------------------------------------------

class AnimationState:
    """
    Foundational class for animate Asset states.

    - action: Action key, possibly null.
    - direction: Direction key, possibly null.
    - frame: Frame index, possible null.
    """
    # ---------------------------------------------------- FIELDS
    action: Union[str, None]
    direction: Union[str, None]
    frame: Union[int, None]

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------- ASSET STATE MODELS
# ---------------------------------------------------------------------------------------

class MultiplierState(AssetState):
    """
    Asset state for multiplying Assets across the screen.

    - position: Coordinates (horizontal, vertical) of Asset's upper-left corner.
    - multiple: Vector (horizontal, vertical) of Asset's multiples.
    """
    # ---------------------------------------------------- FIELDS
    position: Position
    multiple: Multiple 


class PositionalState(AssetState):
    """
    Asset state for Assets that only track position.

    - position: Coordinates (horizontal, vertical) of Asset's upper-left corner.
    """
    # ---------------------------------------------------- KEYS
    name: str               # Deployment Key
    # ---------------------------------------------------- FIELDS
    position: Position

class MetricState(AssetState):
    """
    Asset state for measuring distance from spawn point.

    - position: Coordinates (horizontal, vertical) of Asset's upper-left corner.
    - initial: Coordinates (horizontal, vertical) of Asset's initial position, relative to it's upper-left corner.
    """
    # ---------------------------------------------------- KEYS
    name: str               # Deployment Key
    # ---------------------------------------------------- FIELDS
    position: Position
    initial: Position

class AnimatorState(AssetState):
    """
    Asset state for Assets that possess both position and animation.

    - position: Coordinates (horizontal, vertical) of Asset's upper-left corner.
    """
    # ---------------------------------------------------- KEYS
    name: str               # Deployment Key
    # ---------------------------------------------------- FIELDS
    position: Position
    animation: AnimationState

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------- OBJECT STATE MODELS

class ContainerState(AssetState):
    """
    """
    # ---------------------------------------------------- KEYS
    name: str               # Unique Asset Identifier
    content: List[str]      # Content Identifier Keys
    # ---------------------------------------------------- FIELDS
    position: Position      # Position of Asset on Board
    animation: AnimationState
    switch: bool            # Binary state flag
    
class DoorState(AssetState):
    """
    """
    # ---------------------------------------------------- KEYS
    name: str               # Unique Asset Identifier
    # ---------------------------------------------------- FIELDS
    position: Position      # Position of Asset on Board
    out: Position           # Out Position of Asset
    outlayer: str           # Out Layer Identifier Key

class SwitchState(AssetState):
    """
    """
    # ---------------------------------------------------- KEYS
    name: str               # Unique Asset Identifier
    layer: str              # Layer Identifier Key
    link: str               # Link Identifier Key
    # ---------------------------------------------------- FIELDS
    position: Position      # Position
    animation: AnimationState
    switch: bool            # Binary state flag

# ---------------------------------------------------------------------------------------
# --------------------------------------------------------------------------- SHEET STATE
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------- SHEET  STATE FIELDS
    
class Character:
    """
    Representation of a Sprite's game characteristics.
    """
    strength: int
    defense: int
    speed: int

class Equipment:
    """
    Representation of the Sprite's equipment set.
    """
    armor: str
    weapon: str
    tool: str
    utility: str

class Health:
    """
    Representation of a Sprite's health meter.
    """
    current: int 
    maximum: int
    
class Intention:
    """
    Representation of the internal, hidden state of a Sprite. 
    """
    extension: str
    disposition: str
    motivation: str
    expression: str

class Goal:
    """
    Representation of a Sprite's overarching Goal.
    """
    name: str
    intention: Intention

class Inventory:
    """
    Representation of a Sprite's Inventory.
    """
    loot: Dict[str, int]
    equipment: Equipment
    wallet: int

class Magic:
    """
    Representation of a Sprite's Magic Meter.
    """
    current: int
    maximum: int

class Meters:
    """
    Representation of a Sprite's Meter fields. Meters track values that change in response to Sprite Actions.
    """
    health: Health
    magic: Magic

class Mutator:
    """
    Representation of a Sprite's mutators. Mutators alter the Sprite's behavior during the gameplay loop.
    """
    triggers: Dict[str, bool]
    parameters: Dict[str, Dict[str, Union[int, float]]]

class Memory:
    """
    Representation of a Sprite's memory. 
    """
    goal: Goal
    communications: List[str]

# --------------------------------------------------------------------------------------
# ------------------------------------------------------------------- SHEET STATE MODELS

class PixieState(AssetState):
    """
    """
    # TODO
    pass 

class SpriteState(AssetState):
    """
    Central model for typing Sprite's state.
    """
    # ---------------------------------------------------- KEYS
    name: str               # Unique Asset Identifier
    layer: str              # Layer Identifier Key
    frame: int              # Current Frame
    # ---------------------------------------------------- FIELDS
    position: Position
    animation: AnimationState
    character: Character
    intention: Intention
    inventory: Inventory
    mutators: Mutator
    memory: Memory
    goal: Goal

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------- MENU STATE MODELS

class IconState(AssetState):
    """
    """
    pass

class SymbolState(AssetState):
    """
    """
    pass

class WindowState(AssetState):
    """
    """
    pass 