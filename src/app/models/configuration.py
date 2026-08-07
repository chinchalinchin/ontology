"""
# Ontology: Configuration

Package for Pydantic models used for loading and validating YAML. These models are data-transfer-objects and are not used ingame to manage properties or state, due to the overhead with Pydantic models. They are used purely for easy-loading the YAML configuration files and ensuring they match schemas.
"""
# Standard Libraries
from typing import List, Union, Dict, Optional, Type, Tuple

# Application Libraries
import app.constants as constants

from app.models.recipes import FrameRecipe, AnimationRecipe, \
                                StateRecipe

# External Libraries
from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings, 
    SettingsConfigDict, 
    PydanticBaseSettingsSource, 
    YamlConfigSettingsSource
)

class YamlBaseSettings(BaseSettings):
    """
    Base class that tells Pydantic V2 how to properly parse YAML files.
    """
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (YamlConfigSettingsSource(settings_cls),)
    
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
    hitboxes: Optional[List[PyHitbox]] = None
    count: int 

class PyObjectProperties(BaseModel):
    dim: PyDimensions
    hitboxes: Optional[List[PyHitbox]] = None

class PyTileProperties(BaseModel):
    dim: PyDimensions

class PyStrutProperties(BaseModel):
    dim: PyDimensions
    hitboxes: Optional[List[PyHitbox]] = None
    
# ---------------------------------------------------------------------------------------

class PyPixieEmtityProperty(BaseModel):
    dim: PyDimensions
    hitboxes: Optional[List[PyHitbox]] = None

class PyPixieDirectionProperty(BaseModel):
    row: int

class PyPixieProperties(BaseModel):
    entities: Dict[str, PyPixieEmtityProperty]
    count: int
    directions: Dict[str, PyPixieDirectionProperty]

# ---------------------------------------------------------------------------------------

class PySpritePersonas(BaseModel):
    base: str
    features: List[str]

class PySpriteDirectionProperty(BaseModel):
    row: int
    attackboxes: Optional[List[PyAttackBox]] = None

class PySpriteActionProperty(BaseModel):
    count: int
    directions: Dict[str, PySpriteDirectionProperty]

class PySpriteProperties(BaseModel):
    dim: PyDimensions
    hitboxes: Optional[List[PyHitbox]] = None
    actions: Dict[str, PySpriteActionProperty]
    personas: List[PySpritePersonas]

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------ STATE CONFIGURATION & VALIDATION
# ---------------------------------------------------------------------------------------

class PyAssetState(BaseModel):
    key: str
    name: str
    layer: str
    category: str = ""  # Let Pydantic know to keep this!
    instance: str = ""  # Let Pydantic know to keep this!

class PyAnimationState(BaseModel):
    action: Union[str, None]
    direction: Union[str, None]
    frame: Union[int, None]

class PyPropertyState(BaseModel):
    name: str
    owner: str
    position: PyPosition

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
    animation: Optional[AnimationRecipe] = None
    state: StateRecipe

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

class PyEffectInstances(YamlBaseSettings):
    persistent: Dict[str, PyEffectProperties] = {}
    temporary: Dict[str, PyEffectProperties] = {}

class PyEffectPropertyConfiguration(YamlBaseSettings):
    effects: PyEffectInstances

    model_config = SettingsConfigDict(
        yaml_file = constants.ASSET_DIR / "effects" / constants.APP_EXT
    )

# ---------------------------------------------------------------------------------------

class PyObjectInstances(BaseModel):
    chests: Dict[str, PyObjectProperties] = {}
    crates: Dict[str, PyObjectProperties] = {}
    doors: Dict[str, PyObjectProperties] = {}
    gates: Dict[str, PyObjectProperties] = {}
    plates: Dict[str, PyObjectProperties] = {}

class PyObjectPropertyConfiguration(YamlBaseSettings):
    objects: PyObjectInstances

    model_config = SettingsConfigDict(
        yaml_file = constants.ASSET_DIR / "objects" / constants.APP_EXT
    )

# ---------------------------------------------------------------------------------------

class PyStrutInstances(BaseModel):
    struts: Optional[PyStrutProperties] = None

class PyStrutPropertyConfiguration(YamlBaseSettings):
    objects: PyStrutInstances

    model_config = SettingsConfigDict(
        yaml_file = constants.ASSET_DIR / "objects" / constants.APP_EXT
    )

# ---------------------------------------------------------------------------------------

class PyTileInstances(YamlBaseSettings):
    grids: Optional[PyTileProperties] = None

class PyTilePropertyConfiguration(YamlBaseSettings):
    tiles: PyTileInstances

    model_config = SettingsConfigDict(
        yaml_file = constants.ASSET_DIR / "tiles" / constants.APP_EXT
    )

# ---------------------------------------------------------------------------------------

class PyCursorInstances(BaseModel):
    expressions: Dict[str, PyCursorProperties] = {}
    projectiles: Dict[str, PyCursorProperties] = {}

class PyCursorPropertyConfiguration(YamlBaseSettings):
    cursors: PyCursorInstances

    model_config = SettingsConfigDict(
        yaml_file = constants.ASSET_DIR / "cursors" / constants.APP_EXT
    )

class PySheetInstaces(BaseModel):
    pixies: Optional[PyPixieProperties] = None
    sprites: Optional[PySpriteProperties] = None

class PySheetPropertyConfiguration(YamlBaseSettings):
    sheets: PySheetInstaces

    model_config = SettingsConfigDict(
        yaml_file = constants.ASSET_DIR / "sheets" / constants.APP_EXT
    )

# --------------------------------------------------------------------- RECIPE YAML SCHEMA

class PyRecipeConfiguration(YamlBaseSettings):
    tiles: Optional[PyRecipe] = None
    struts: Optional[PyRecipe] = None
    cursors: Optional[PyCursorRecipe] = None
    effects: Optional[PyEffectRecipe] = None
    objects: Optional[PyObjectRecipe] = None
    sheets: Optional[PySheetRecipe] = None

    model_config = SettingsConfigDict(
        yaml_file = constants.ASSET_DIR / constants.APP_EXT
    )