"""
Models for typing the state attributes of Assets. See documentation for a more in-depth explanation of each field and its purpose. 
"""
# Standard Libraries
from typing import Dict, List, Union

# Application Libraries
from app.models import Position, Multiple

# ---------------------------------------------------------------------------------------

class AssetState:
    """
    """
    pass 

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------- COMPONENT STATES

class AnimationState:
    """
    """
    action: Union[str, None]
    direction: Union[str, None]
    frame: Union[int, None]
    
# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------- ASSET STATE FIELDS
# ---------------------------------------------------------------------------------------
    
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

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------- ASSET STATE MODELS
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# --------------------------------------------------------------------- TILE STATE MODELS


class TileState(AssetState):
    """
    """
    # ---------------------------------------------------- KEYS
    layer: str              # Layer Identifier Key
    # ---------------------------------------------------- FIELDS
    position: Position
    multiple: Multiple 

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------- CURSOR STATE MODELS

class ExpressionCursorState(AssetState):
    """
    """
    # ---------------------------------------------------- KEYS
    name: str               # Unique Asset Identifier
    layer: str              # Layer Identifier Key
    # ---------------------------------------------------- FIELDS
    position: Position

class ProjectileState(AssetState):
    """
    """
    # ---------------------------------------------------- KEYS
    name: str               # Unique Asset Identifier
    layer: str              # Layer Identifier Key
    # ---------------------------------------------------- FIELDS
    position: Position
    initial: Position

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------- EFFECT STATE MODELS

class PersistentEffectState(AssetState):
    """
    """
    # ---------------------------------------------------- KEYS
    name: str               # Unique Asset Identifier
    layer: str              # Layer Identifier Key
    # ---------------------------------------------------- FIELDS
    position: Position
    animation: AnimationState

class TemporaryEffectState(AssetState):
    """
    """
    # ---------------------------------------------------- KEYS
    name: str               # Unique Asset Identifier
    layer: str              # Layer Identifier Key
    # ---------------------------------------------------- FIELDS
    position: Position
    animation: AnimationState

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------- ENVIRON STATE MODELS

# TODO: Finish design stage

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

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------- OBJECT STATE MODELS

class ChestState(AssetState):
    """
    """
    # ---------------------------------------------------- KEYS
    name: str               # Unique Asset Identifier
    layer: str              # Layer Identifier Key
    content: List[str]      # Content Identifier Keys
    # ---------------------------------------------------- FIELDS
    position: Position      # Position of Asset on Board
    animation: AnimationState
    switch: bool            # Binary state flag
    
class CrateState(AssetState):
    """
    """
    # ---------------------------------------------------- KEYS
    name: str               # Unique Asset Identifier
    layer: str              # Layer Identifier Key
    # ---------------------------------------------------- FIELDS
    position: Position

class DoorState(AssetState):
    """
    """
    # ---------------------------------------------------- KEYS
    name: str               # Unique Asset Identifier
    layer: str              # Layer Identifier Key
    outlayer: str           # Out Layer Identifier Key
    # ---------------------------------------------------- FIELDS
    position: Position      # Position of Asset on Board
    out: Position           # Out Position of Asset

class GateState(AssetState):
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

class PlateState(AssetState):
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
# ------------------------------------------------------------------- SHEET STATE MODELS

class PixieState(AssetState):
    """
    """
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