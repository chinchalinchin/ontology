"""
Package for Pydantic models used for loading and validating YAML. These models are data-transfer-objects and are not used ingame to manage properties or state, due to the overhead with Pydantic models. They are used purely for easy-loading the YAML configuration files and ensuring they match schemas.
"""
# Standard Libraries
from typing import List, Union, Dict
# External Libraries
from pydantic import BaseModel

# NOTE: *Py-* prefix denotes Pydantic model that inherits from Pydantic's BaseModel, whereas no prefix indicates game object class.

# ---------------------------------------------------------------------------------------
# --------------------------------------------------- PROPERTY CONFIGURATION & VALIDATION
# ---------------------------------------------------------------------------------------

class PyPosition(BaseModel):
    x: int
    y: int


class PyDimensions(BaseModel):
    l: int
    w: int

class PyMultiple(BaseModel):
    nx: int
    ny: int

class PyHitbox(BaseModel):
    pos: PyPosition
    dim: PyDimensions

class PyAttackBox(BaseModel):
    pos: PyPosition
    dim: PyDimensions
    hitframe: int

class PyShapeProperties(BaseModel):
    dim: PyDimensions
    hitboxes: List[PyHitbox]

# ---------------------------------------------------------------------------------------

class PyCursorProperties(BaseModel):
    key: str
    dim: PyDimensions

class PyEffectProperties(BaseModel):
    key: str
    shape: PyShapeProperties
    count: int 

class PyObjectProperties(BaseModel):
    key: str
    shape: PyShapeProperties

class PyTileProperties(BaseModel):
    key: str
    dim: PyDimensions

class PyPixieActionsProperty(BaseModel):
    count: int
    directions: List[str]

class PyPixieProperties(BaseModel):
    key: str                  
    shape: PyShapeProperties

class PySpriteComposition(BaseModel):
    key: str 
    base: str
    apparel: List[str]
    features: List[str]

class PySpriteDirectionProperty(BaseModel):
    row: int
    attackboxes: List[PyAttackBox]

class PySpriteActionProperty(BaseModel):
    count: int
    directions: Dict[str, PySpriteDirectionProperty]

class PySpriteProperties(BaseModel):
    key: str
    shape: PyShapeProperties
    actions: Dict[str, PySpriteActionProperty]

# ---------------------------------------------------------------------------------------

class PixieConfiguration(BaseModel):
    shapes: Dict[str, PyShapeProperties]
    action: Dict[str, PyPixieActionsProperty]

class SpriteConfiguration(BaseModel):
    shape: PyShapeProperties
    actions: Dict[str, PySpriteActionProperty]
    compostions: List[PySpriteComposition]

class CursorConfiguration(BaseModel):
    expressions: Dict[str, PyCursorProperties]
    projectiles: Dict[str, PyCursorProperties]

class SheetConfiguration(BaseModel):
    pixies: PixieConfiguration
    sprites: SpriteConfiguration

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------ STATE CONFIGURATION & VALIDATION
# ---------------------------------------------------------------------------------------

class PyCharacter(BaseModel):
    strength: int
    defense: int
    speed: int

class PyEquipment(BaseModel):
    armor: str
    weapon: str
    tool: str
    utility: str

class PyHealth(BaseModel):
    current: int 
    maximum: int
    
class PyIntention(BaseModel):
    extension: str
    disposition: str
    motivation: str
    expression: str

class PyGoal(BaseModel):
    name: str
    intention: PyIntention

class PyInventory(BaseModel):
    loot: Dict[str, int]
    equipment: PyEquipment
    wallet: int

class PyMagic(BaseModel):
    current: int
    maximum: int

class PyMeters(BaseModel):
    health: PyHealth
    magic: PyMagic

class PyMutator(BaseModel):
    triggers: Dict[str, bool]
    parameters: Dict[str, Dict[str, Union[int, float]]]

class PyMemory(BaseModel):
    goal: PyGoal
    communications: List[str]

# ---------------------------------------------------------------------------------------

class PyTileState(BaseModel):
    layer: str
    position: PyPosition
    multiple: PyMultiple 

class PyExpressionCursorState(BaseModel):
    pass

class PyProjectileState(BaseModel):
    name: str
    layer: str
    position: PyPosition
    initial: PyPosition

class PyPersistentEffectState(BaseModel):
    pass 

class PyIconState(BaseModel):
    pass

class PySymbolState(BaseModel):
    pass

class PyWindowState(BaseModel):
    pass 

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------- OBJECT STATE MODELS

class PyChestState(BaseModel):
    name: str
    layer: str
    content: List[str]
    position: PyPosition
    switch: bool
    
class PyCrateState(BaseModel):
    name: str
    layer: str
    position: PyPosition

class PyDoorState(BaseModel):
    name: str
    layer: str
    outlayer: str
    position: PyPosition
    out: PyPosition

class GateState(BaseModel):
    name: str
    layer: str
    link: str
    position: PyPosition
    switch: bool

class PlateState(BaseModel):
    name: str
    layer: str
    link: str
    position: PyPosition
    switch: bool

class PixieState(BaseModel):
    pass 

class PySpriteState(BaseModel):
    name: str
    layer: str
    frame: int
    position: PyPosition
    character: PyCharacter
    intention: PyIntention
    inventory: PyInventory
    mutators: PyMutator
    memory: PyMemory
    goal: PyGoal