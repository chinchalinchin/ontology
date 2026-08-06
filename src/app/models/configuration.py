"""
# Ontology: Configuration

Package for Pydantic models used for loading and validating YAML. These models are data-transfer-objects and are not used ingame to manage properties or state, due to the overhead with Pydantic models. They are used purely for easy-loading the YAML configuration files and ensuring they match schemas.
"""
# Standard Libraries
from typing import List, Union, Dict

# Application Libraries
import app.constants as constants

from app.models.recipes import FrameRecipe, AnimationRecipe, \
                                StateRecipe, BehaviorRecipe

# External Libraries
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

# NOTE: *Py-* prefix denotes Pydantic model that inherits from Pydantic's BaseModel, whereas no prefix indicates game object class.

# ---------------------------------------------------------------------------------------
# ------------------------------------------- PRIMITIVE MODELS CONFIGURATION & VALIDATION
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

# ---------------------------------------------------------------------------------------

class PyCursorProperties(BaseModel):
    dim: PyDimensions

class PyEffectProperties(BaseModel):
    dim: PyDimensions
    hitboxes: List[PyHitbox]
    count: int 

class PyObjectProperties(BaseModel):
    dim: PyDimensions
    hitboxes: List[PyHitbox]

class PyTileProperties(BaseModel):
    dim: PyDimensions

class PyStrutProperties(BaseModel):
    dim: PyDimensions
    hitboxes: List[PyHitbox]
    
# ---------------------------------------------------------------------------------------

class PyPixieEmtityProperty(BaseModel):
    dim: PyDimensions
    hitboxes: List[PyHitbox]

class PyPixieDirectionProperty(BaseModel):
    row: int

class PyPixieProperties(BaseModel):
    entities: Dict[str, PyPixieEmtityProperty]
    count: int
    directions: Dict[str, PyPixieDirectionProperty]

# ---------------------------------------------------------------------------------------

class PySpriteComposition(BaseModel):
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
    dim: PyDimensions
    hitboxes: List[PyHitbox]
    actions: Dict[str, PySpriteActionProperty]
    compositions: List[PySpriteComposition]

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------ STATE CONFIGURATION & VALIDATION
# ---------------------------------------------------------------------------------------

class PyAssetState(BaseModel):
    key: str
    name: str
    layer: str

class PyAnimationState(BaseModel):
    action: Union[str, None]
    direction: Union[str, None]
    frame: Union[int, None]

# ---------------------------------------------------------------------------------------

class PyCharacterState(BaseModel):
    strength: int
    defense: int
    speed: int

class PyEquipmentState(BaseModel):
    armor: str
    weapon: str
    tool: str
    utility: str

class PyHealthState(BaseModel):
    current: int 
    maximum: int

# ---------------------------------------------------------------------------------------

class PyIntentionState(BaseModel):
    extension: str
    disposition: str
    motivation: str
    expression: str

class PyGoalState(BaseModel):
    name: str
    intention: PyIntentionState

class PyInventoryState(BaseModel):
    loot: Dict[str, int]
    equipment: PyEquipmentState
    wallet: int

# ---------------------------------------------------------------------------------------

class PyMagicState(BaseModel):
    current: int
    maximum: int

class PyMeterState(BaseModel):
    health: PyHealthState
    magic: PyMagicState

# ---------------------------------------------------------------------------------------

class PyVisionMutator(BaseModel):
    radius: int

class PyFearMutator(BaseModel):
    radius: int
    limit: float
    enemy: int

class PyMutatorState(BaseModel):
    fear: PyFearMutator
    vision: PyVisionMutator

# ---------------------------------------------------------------------------------------

class PyMemoryState(BaseModel):
    goal: PyGoalState
    communications: List[str]
    prices: Dict[str, float]
    
# ---------------------------------------------------------------------------------------

class PyMultiplierState(PyAssetState):
    position: PyPosition
    multiple: PyMultiple 

class PyPositionalState(PyAssetState):
    name: str
    position: PyPosition

class PyMetricState(PyAssetState):
    name: str
    position: PyPosition
    initial: PyPosition

class PyAnimatorState(PyAssetState):
    name: str
    position: PyPosition
    animation: PyAnimationState

class PyContainerState(PyAssetState):
    name: str
    content: List[str]
    position: PyPosition
    animation: PyAnimationState
    switch: bool
    
class PyDoorState(PyAssetState):
    name: str
    position: PyPosition
    out: PyPosition
    outlayer: str

class PySwitchState(PyAssetState):
    name: str
    link: str
    position: PyPosition
    animation: PyAnimationState
    switch: bool

class PyPixieState(BaseModel):
    name: str
    position: PyPosition

class PySpriteState(BaseModel):
    name: str
    position: PyPosition
    character: PyCharacterState
    intention: PyIntentionState
    inventory: PyInventoryState
    meters: PyMeterState
    mutators: PyMutatorState
    memory: PyMemoryState
    goal: PyGoalState

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------ RECIPE CONFIGURATION & VALIDATION
# ---------------------------------------------------------------------------------------

class PyRecipe(BaseModel):
    frame: FrameRecipe
    animation: AnimationRecipe
    state: StateRecipe
    behaviors: List[BehaviorRecipe]

class PyCursorRecipe(BaseModel):
    expressions: PyRecipe
    projectiles: PyRecipe

class PyEffectRecipe(BaseModel):
    temporary: PyRecipe
    persistent: PyRecipe

class PyObjectRecipe(BaseModel):
    chests: PyRecipe
    crates: PyRecipe
    doors: PyRecipe
    gates: PyRecipe
    plates: PyRecipe

class PySheetRecipe(BaseModel):
    pixies: PyRecipe
    sprites: PyRecipe

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------------- YAML SCHEMAS
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------

class PyEffectPropertyConfiguration(BaseSettings):
    persistant: Dict[str, PyEffectProperties]
    temporary: Dict[str, PyEffectProperties]

    # Load YAML
    model_config = SettingsConfigDict(
        yaml_file = constants.ASSET_DIR / "effects" / constants.APP_EXT
    )

class PyObjectPropertyConfiguration(BaseSettings):
    chests: Dict[str, PyObjectProperties]
    crates: Dict[str, PyObjectProperties]
    doors: Dict[str, PyObjectProperties]
    gates: Dict[str, PyObjectProperties]
    plates: Dict[str, PyObjectProperties]

    # Load YAML
    model_config = SettingsConfigDict(
        yaml_file = constants.ASSET_DIR / "objects" / constants.APP_EXT
    )

class PyTilePropertyConfiguration(BaseSettings):
    grid: PyTileProperties
    struts: PyStrutProperties

    # Load YAML
    model_config = SettingsConfigDict(
        yaml_file = constants.ASSET_DIR / "tiles" / constants.APP_EXT
    )

class PyCursorPropertyConfiguration(BaseSettings):
    expressions: Dict[str, PyCursorProperties]
    projectiles: Dict[str, PyCursorProperties]

    # Load YAML
    model_config = SettingsConfigDict(
        yaml_file = constants.ASSET_DIR / "cursors" / constants.APP_EXT
    )

class PySheetPropertyConfiguration(BaseSettings):
    pixies: PyPixieProperties
    sprites: PySpriteProperties

    # Load YAML
    model_config = SettingsConfigDict(
        yaml_file = constants.ASSET_DIR / "sheets" / constants.APP_EXT
    )

# --------------------------------------------------------------------- RECIPE YAML SCHEMA

class PyRecipeConfiguration(BaseSettings):
    tiles: PyRecipe
    cursors: PyCursorRecipe
    effects: PyEffectRecipe
    objects: PyObjectRecipe
    sheets: PySheetRecipe

    # Load YAML
    model_config = SettingsConfigDict(
        yaml_file = constants.ASSET_DIR / constants.APP_EXT
    )

# --------------------------------------------------------------------- STATE YAML SCHEMA

class PyCursorStateConfiguration(BaseSettings):
    expressions: List[PyPositionalState]
    projectiles: List[PyMetricState]

class PyEffectStateConfiguration(BaseModel):
    persistent: List[PyAnimatorState]
    temporary: List[PyAnimatorState]

class PyObjectStateConfiguration(BaseModel):
    chests: List[PyContainerState]
    crates: List[PyPositionalState]
    doors: List[PyDoorState]
    gates: List[PySwitchState]
    plates: List[PySwitchState]

class PySheetStateConfiguration(BaseModel):
    sprites: List[PySpriteState]
    pixies: List[PyPixieState]

# ---------------------------------------------------------------------------------------

class PyStateConfiguration(BaseModel):
    tiles: List[PyMultiplierState]
    cursors: PyCursorStateConfiguration
    effects: PyEffectStateConfiguration
    objects: PyObjectStateConfiguration
    sheets: PySheetStateConfiguration

    # Must be loaded at runtime to get board state key!