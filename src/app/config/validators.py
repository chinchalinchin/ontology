"""
# Ontology: Validators

Package for Pydantic models used for loading and validating YAML. These models are 
data-transfer-objects and are not used ingame to manage properties or state, due 
to the overhead with Pydantic models. They are used purely for easy-loading the YAML 
configuration files and ensuring they match schemas.
"""
# Standard Libraries
from typing import (
    List, 
    Dict, 
    Optional, 
    Type, 
    Tuple
)

# External Libraries
from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings, 
    SettingsConfigDict, 
    PydanticBaseSettingsSource, 
    YamlConfigSettingsSource
)

# Application Libraries
import app.config.settings as settings
from app.config.enums import (
    FrameRecipe, 
    AnimationRecipe,
    StateRecipe, 
    Actions, 
    Directions,
    Intentions,
    PlayerGoals
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
    
# NOTE: *Py-* prefix denotes Pydantic model that inherits from Pydantic's BaseModel, 
#           whereas no prefix indicates game object class.

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
    position: PyPosition
    dimensions: PyDimensions

class PyAttackBox(BaseModel):
    position: PyPosition
    dimensions: PyDimensions
    hitframe: int

class PyDirection(BaseModel):
    row: int
    attackboxes: Optional[List[PyAttackBox]] = []

class PyAction(BaseModel):
    count: int
    directions: Dict[str, PyDirection]

class PyPersona(BaseModel):
    dimensions: PyDimensions
    hitboxes: Optional[List[PyHitbox]] = []
    stack: List[str]

class PyCost(BaseModel):
    item: str
    quantity: int

# ---------------------------------------------------------------------------------------
# --------------------------------------------------- PROPERTY CONFIGURATION & VALIDATION
# ---------------------------------------------------------------------------------------

class PyCursorProperties(BaseModel):
    dimensions: PyDimensions

class PyEffectProperties(BaseModel):
    dimensions: PyDimensions
    hitboxes: Optional[List[PyHitbox]] = []
    count: int 

class PyObjectProperties(BaseModel):
    dimensions: PyDimensions
    hitboxes: Optional[List[PyHitbox]] = []

class PyTileProperties(BaseModel):
    dimensions: PyDimensions
    ids: List[str]

class PyCraftProperties(BaseModel):
    dimensions: PyDimensions
    hitboxes: Optional[List[PyHitbox]] = []
    cost: List[PyCost]
    
class PySheetProperties(BaseModel):
    personas: Dict[str, PyPersona]
    actions: Dict[str, PyAction]

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------ STATE CONFIGURATION & VALIDATION
# ---------------------------------------------------------------------------------------

class PyAssetState(BaseModel):
    id: str
    layer: str
    name: str

class PyAnimationState(BaseModel):
    action: str = Actions.WALK
    direction: str = Directions.DOWN
    frame: int = 0

class PyPropertyState(BaseModel):
    name: str
    owner: str
    position: PyPosition

# ------------------------------------------------------------- SPRITE STATE FIELDS

class PyCharacterState(BaseModel):
    strength: int
    defense: int
    speed: int

class PyEquipmentState(BaseModel):
    armor: str
    weapon: str
    tool: str
    utility: str

class PyMeterState(BaseModel):
    current: int 
    maximum: int

class PyPsycheState(BaseModel):
    motivation: str
    expression: str
    communication: str

class PyGoalState(BaseModel):
    name: str
    category: str
    position: PyPosition

class PyInventoryState(BaseModel):
    loot: Dict[str, int]
    equipment: PyEquipmentState
    wallet: int

class PyMetersState(BaseModel):
    health: PyMeterState
    magic: PyMeterState

class PyVisionMutator(BaseModel):
    radius: int

class PyFearMutator(BaseModel):
    radius: int
    limit: float
    enemy: int

class PyMutatorState(BaseModel):
    fear: PyFearMutator
    vision: PyVisionMutator

class PyMemoryState(BaseModel):
    goal: Optional[PyGoalState] = None
    communications: Optional[List[str]] = []
    prices: Optional[Dict[str, float]] = {}
    
# --------------------------------------------------------------- STATE CONTAINERS

class PyMultiplierState(PyAssetState):
    position: PyPosition
    multiple: PyMultiple 

class PyPositionalState(PyAssetState):
    position: PyPosition

class PyMetricState(PyAssetState):
    position: PyPosition
    initial: PyPosition

class PyAnimatorState(PyAssetState):
    position: PyPosition
    animation: PyAnimationState

class PyContainerState(PyAssetState):
    content: List[str]
    position: PyPosition
    animation: PyAnimationState
    switch: bool
    
class PyDoorState(PyAssetState):
    position: PyPosition
    out: PyPosition
    outlayer: str

class PySwitchState(PyAssetState):
    link: str
    position: PyPosition
    animation: PyAnimationState
    switch: bool

class PySpriteState(BaseModel):
    intention: str
    animation: PyAnimationState
    position: PyPosition
    character: PyCharacterState
    inventory: PyInventoryState
    meters: PyMetersState
    mutators: PyMutatorState
    memory: PyMemoryState
    goal: Optional[PyGoalState] = None

class PyPlayerState(BaseModel):
    intention: str
    position: PyPosition
    animation: PyAnimationState
    character: PyCharacterState
    inventory: PyInventoryState
    meters: PyMetersState
    goal: Optional[PyGoalState] = None

# --------------------------------------------------------------------------------------
# ---------------------------------------------------- RECIPE CONFIGURATION & VALIDATION
# --------------------------------------------------------------------------------------

class PyRecipe(BaseModel):
    frame: FrameRecipe
    animation: Optional[AnimationRecipe] = None
    state: StateRecipe

class PyTileRecipe(BaseModel):
    fore: PyRecipe
    back: PyRecipe

class PyCraftRecipe(BaseModel):
    struts: PyRecipe

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

class PyRecipes(BaseModel):
    tiles: Optional[PyTileRecipe] = None
    crafts: Optional[PyCraftRecipe] = None
    cursors: Optional[PyCursorRecipe] = None
    effects: Optional[PyEffectRecipe] = None
    objects: Optional[PyObjectRecipe] = None
    sheets: Optional[PySheetRecipe] = None

# --------------------------------------------------------------------------------------
# ---------------------------------------------------- DEVICE CONFIGURATION & VALIDATION
# --------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------ DEVICES

class PyDeviceMapping(BaseModel):
    intentions: Dict[Intentions, Optional[int]]
    goals: Dict[PlayerGoals, Optional[int]]

class PyDeviceMappings(BaseModel):
    keyboard: PyDeviceMapping
    controller: Optional[PyDeviceMapping] = None

# --------------------------------------------------------------------------- INTENTIONS

class PyIntention(BaseModel):
    next: str
    conditions: List[str]

# ---------------------------------------------------------------------------- EQUIPMENT

class PyEquipmentProperties(BaseModel):
    animation: PyAnimationState
    sheets: List[str]

# -------------------------------------------------------------------------------------
# ------------------------------------------------------------------------ YAML SCHEMAS
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# ------------------------------------------------------------------ DEVICE YAML SCHEMA

class PyDeviceMappingConfiguration(YamlBaseSettings):
    mappings: PyDeviceMappings

    model_config = SettingsConfigDict(
        yaml_file = settings.DATA_DIR / "mappings" / settings.APP_EXT
    )

# -------------------------------------------------------------------------------------
# --------------------------------------------------------------- INTENTION YAML SCHEMA

class PyIntentionPropertyConfiguration(YamlBaseSettings):
    intentions: Dict[str, PyIntention]

    model_config = SettingsConfigDict(
        yaml_file = settings.DATA_DIR / "intentions" / settings.APP_EXT
    )

# -------------------------------------------------------------------------------------
# --------------------------------------------------------------- EQUIPMENT YAML SCHEMA

class PyEquipmentPropertyConfiguration(YamlBaseSettings):
    armor: Dict[str, PyEquipmentProperties]
    tools: Dict[str, PyEquipmentProperties]
    utilities: Dict[str, PyEquipmentProperties]
    weapons: Dict[str, PyEquipmentProperties]

    model_config = SettingsConfigDict(
        yaml_file = settings.DATA_DIR / "equipment" / settings.APP_EXT
    )
# -------------------------------------------------------------------------------------
# ------------------------------------------------------------------ RECIPE YAML SCHEMA

class PyRecipeConfiguration(YamlBaseSettings):
    assets: PyRecipes

    model_config = SettingsConfigDict(
        yaml_file = settings.ASSET_DIR / settings.APP_EXT
    )

# -------------------------------------------------------------------------------------
# ------------------------------------------------------------------- STATE YAML SCHEMA

class PyTileStateInstances(BaseModel):
    fore: Optional[List[PyMultiplierState]] = []
    back: List[PyMultiplierState] = []

class PyCraftStateInstances(BaseModel):
    struts: Optional[List[PyPropertyState]] = []

class PyCursorStateInstances(BaseModel):
    expressions: Optional[List[PyPositionalState]] = []
    projectiles: Optional[List[PyMetricState]] = []

class PyEffectStateInstances(BaseModel):
    temporary: Optional[List[PyPositionalState]] = []
    persistent: Optional[List[PyAnimatorState]] = []

class PyObjectStateInstances(BaseModel):
    chests: Optional[List[PyContainerState]] = []
    crates: Optional[List[PyPositionalState]] = []
    doors: Optional[List[PyDoorState]] = []
    gates: Optional[List[PySwitchState]] = []
    plates: Optional[List[PySwitchState]] = []

class PySheetStateInstances(BaseModel):
    pixies: Optional[List[PyAnimatorState]] = []
    sprites: Optional[List[PySpriteState]] = []
    player: Optional[List[PyPlayerState]] = []

# ---------------------------------------------------------------------------------------

class PyStateConfiguration(BaseModel):
    tiles: Optional[PyTileStateInstances] = None
    objects: Optional[PyObjectStateInstances] = None
    crafts: Optional[PyCraftStateInstances] = None
    cursors: Optional[PyCursorStateInstances] = None
    effects: Optional[PyEffectStateInstances] = None
    sheets: Optional[PySheetStateInstances] = None

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------ PROPERTY YAML SCHEMA

class PyTilePropertyInstances(BaseModel):
    fore: PyTileProperties
    back: PyTileProperties

class PyEffectPropertyInstances(BaseModel):
    persistent: Dict[str, PyEffectProperties] = {}
    temporary: Dict[str, PyEffectProperties] = {}

class PyObjectPropertyInstances(BaseModel):
    chests: Dict[str, PyObjectProperties] = {}
    crates: Dict[str, PyObjectProperties] = {}
    doors: Dict[str, PyObjectProperties] = {}
    gates: Dict[str, PyObjectProperties] = {}
    plates: Dict[str, PyObjectProperties] = {}

class PyCraftPropertyInstances(BaseModel):
    struts: Dict[str, PyCraftProperties] = {}

class PyCursorPropertyInstances(BaseModel):
    expressions: Dict[str, PyCursorProperties] = {}
    projectiles: Dict[str, PyCursorProperties] = {}

class PySheetPropertyInstances(BaseModel):
    pixies: Optional[PySheetProperties] = None
    sprites: Optional[PySheetProperties] = None

# ---------------------------------------------------------------------------------------

class PyTilePropertyConfiguration(YamlBaseSettings):
    tiles: PyTilePropertyInstances

    model_config = SettingsConfigDict(
        yaml_file = settings.ASSET_DIR / "tiles" / settings.APP_EXT
    )


class PyEffectPropertyConfiguration(YamlBaseSettings):
    effects: PyEffectPropertyInstances

    model_config = SettingsConfigDict(
        yaml_file = settings.ASSET_DIR / "effects" / settings.APP_EXT
    )
    
class PyObjectPropertyConfiguration(YamlBaseSettings):
    objects: PyObjectPropertyInstances

    model_config = SettingsConfigDict(
        yaml_file = settings.ASSET_DIR / "objects" / settings.APP_EXT
    )

class PyCraftPropertyConfiguration(YamlBaseSettings):
    crafts: PyCraftPropertyInstances

    model_config = SettingsConfigDict(
        yaml_file = settings.ASSET_DIR / "crafts" / settings.APP_EXT
    )

class PyCursorPropertyConfiguration(YamlBaseSettings):
    cursors: PyCursorPropertyInstances

    model_config = SettingsConfigDict(
        yaml_file = settings.ASSET_DIR / "cursors" / settings.APP_EXT
    )

class PySheetPropertyConfiguration(YamlBaseSettings):
    sheets: PySheetPropertyInstances

    model_config = SettingsConfigDict(
        yaml_file = settings.ASSET_DIR / "sheets" / settings.APP_EXT
    )