"""
Pydantic models for typing the state attributes of Assets. See documentation for a more in-depth explanation of each field and its purpose. 
"""
# Standard Libraries
from typing import Dict, List, Tuple, Union
# External Libraries
from pydantic import BaseModel
# Application Libraries
from app.models import Position

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------- ASSET STATE FIELDS
# ---------------------------------------------------------------------------------------

class Animation(BaseModel):
    """
    Rerpresentation of the animation state of a Sprite.
    """
    action: str
    direction: str
    
class Character(BaseModel):
    """
    Representation of a Sprite's game characteristics.
    """
    strength: int
    defense: int
    speed: int

class Equipment(BaseModel):
    """
    Representation of the Sprite's equipment set.
    """
    armor: str
    weapon: str
    tool: str
    utility: str

class Goal(BaseModel):
    """
    Representation of a Sprite's overarching Goal.
    """
    name: str
    intention: Intention

class Health(BaseModel):
    """
    Representation of a Sprite's health meter.
    """
    current: int 
    maximum: int
    
class Intention(BaseModel):
    """
    Representation of the internal, hidden state of a Sprite. 
    """
    extension: str
    disposition: str
    motivation: str
    expression: str

class Inventory(BaseModel):
    """
    Representation of a Sprite's Inventory.
    """
    loot: Dict[str, int]
    equipment: Equipment
    wallet: int

class Magic(BaseModel):
    """
    Representation of a Sprite's Magic Meter.
    """
    current: int
    maximum: int

class Meters(BaseModel):
    """
    Representation of a Sprite's Meter fields. Meters track values that change in response to Sprite Actions.
    """
    health: Health
    magic: Magic

class Mutator(BaseModel):
    """
    Representation of a Sprite's mutators. Mutators alter the Sprite's behavior during the gameplay loop.
    """
    triggers: Dict[str, bool]
    parameters: Dict[str, Dict[str, Union[int, double]]]

class Memory(BaseModel):
    """
    Representation of a Sprite's memory. 
    """
    goal: Goal
    communications: List[str]

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------- ASSET STATE MODELS
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------- CURSOR STATE MODELS

class ExpressionCursorState(BaseModel):
    pass

class ProjectileState(BaseModel):
    # ---------------------------------------------------- KEYS
    name: str               # Unique Asset Identifier
    layer: str              # Layer Identifier Key
    # ---------------------------------------------------- FIELDS
    position: Position
    initial: Position

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------- EFFECT STATE MODELS

class PersistentEffectState(BaseModel):
    pass 

class TemporaryEffectState(BaseModel):
    pass

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------- ENVIRON STATE MODELS

# TODO: Finish design stage

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------- MENU STATE MODELS

class IconState(BaseModel):
    pass

class SymbolState(BaseModel):
    pass

class WindowState(BaseModel):
    pass 

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------- OBJECT STATE MODELS

class ChestState(BaseModel):
    # ---------------------------------------------------- KEYS
    name: str               # Unique Asset Identifier
    layer: str              # Layer Identifier Key
    content: List[str]      # Content Identifier Keys
    # ---------------------------------------------------- FIELDS
    position: Position      # Position of Asset on Board
    switch: bool            # Binary state flag
    
class CrateState(BaseModel):
    # ---------------------------------------------------- KEYS
    name: str               # Unique Asset Identifier
    layer: str              # Layer Identifier Key
    # ---------------------------------------------------- FIELDS
    position: Position

class DoorState(BaseModel):
    # ---------------------------------------------------- KEYS
    name: str               # Unique Asset Identifier
    layer: str              # Layer Identifier Key
    outlayer: str           # Out Layer Identifier Key
    # ---------------------------------------------------- FIELDS
    position: Position      # Position of Asset on Board
    out: Position           # Out Position of Asset

class GateState(BaseModel):
    # ---------------------------------------------------- KEYS
    name: str               # Unique Asset Identifier
    layer: str              # Layer Identifier Key
    link: str               # Link Identifier Key
    # ---------------------------------------------------- FIELDS
    position: Position      # Position
    switch: bool            # Binary state flag

class PlateState(BaseModel):
    # ---------------------------------------------------- KEYS
    name: str               # Unique Asset Identifier
    layer: str              # Layer Identifier Key
    link: str               # Link Identifier Key
    # ---------------------------------------------------- FIELDS
    position: Position      # Position
    switch: bool            # Binary state flag


# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------- SHEET STATE MODELS

class PixieState(BaseModel):
    pass 

class SpriteState(BaseModel):
    """
    Central model for typing Sprite's state.
    """
    # ---------------------------------------------------- KEYS
    name: str               # Unique Asset Identifier
    layer: str              # Layer Identifier Key
    frame: int              # Current Frame
    # ---------------------------------------------------- FIELDS
    animation: Animation
    position: Position
    character: Character
    intention: Intention
    inventory: Inventory
    mutators: Mutator
    memory: Memory
    goal: Goal

# ------------------------------------------------------------------- TILE STATE MODELS

class TileState(BaseModel):
    # ---------------------------------------------------- KEYS
    layer: str              # Layer Identifier Key
    # ---------------------------------------------------- FIELDS
    position: Position