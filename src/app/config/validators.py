"""
# Ontology: app.config.validators

Package for Pydantic models used for loading and validating YAML. These models are data-transfer-objects and are not used ingame to manage properties or state, due 
to the overhead with Pydantic models. They are used purely for easy-loading the YAML configuration files and ensuring they match schemas.
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
    PlayerGoals,
    Mechanics,
    AssetCategories,
    Configurations,
    Relationships
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
#       whereas no prefix indicates game object class.

# ---------------------------------------------------------------------------------------
# ----------------------------------------------------------- PRIMITIVE MODELS VALIDATION
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

class PyDirection(BaseModel):
    row: int

class PyAction(BaseModel):
    count: int
    directions: Dict[str, PyDirection]

class PyCost(BaseModel):
    item: str
    quantity: int

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------- PROPERTY VALIDATION
# ---------------------------------------------------------------------------------------

class PyCursorProperties(BaseModel):
    dimensions: PyDimensions

class PyEffectProperties(BaseModel):
    dimensions: PyDimensions
    count: int

class PyObjectProperties(BaseModel):
    dimensions: PyDimensions
    hitboxes: Optional[List[PyHitbox]] = []
    mass: int

class PyTileProperties(BaseModel):
    dimensions: PyDimensions
    ids: List[str]

class PyCraftProperties(BaseModel):
    dimensions: PyDimensions
    hitboxes: Optional[List[PyHitbox]] = []
    cost: List[PyCost]
    mass: int

class PySheetProperties(BaseModel):
    dimensions: PyDimensions
    hitboxes: Optional[List[PyHitbox]] = None
    stack: Optional[List[str]] = None
    actions: str
    mass: Optional[int] = -1

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------- PROPERTY DATA STRUCTURES

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
    pixies: Optional[Dict[str, PySheetProperties]] = {}
    sprites: Optional[Dict[str, PySheetProperties]] = {}
    weapons: Optional[Dict[str, PySheetProperties]] = {}
    utilities: Optional[Dict[str, PySheetProperties]] = {}
    armor: Optional[Dict[str, PySheetProperties]] = {}
    tools: Optional[Dict[str, PySheetProperties]] = {}
    shields: Optional[Dict[str, PySheetProperties]] = {}

# ---------------------------------------------------------------------------------------
# ---------------------------------------------------------------------- STATE VALIDATION
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

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------- SPRITE STATE FIELDS

class PyCharacterState(BaseModel):
    strength: int = 10
    defense: int = 10
    speed: int = 10

class PyEquipmentState(BaseModel):
    armor: Optional[str] = None
    weapon: Optional[str] = None
    tool: Optional[str] = None
    utility: Optional[str] = None
    shield: Optional[str] = None

class PyMeterState(BaseModel):
    current: int = 100
    maximum: int = 100

class PyPsycheState(BaseModel):
    motivation: str
    expression: str
    communication: str

class PyGoalState(BaseModel):
    name: str
    category: str
    position: PyPosition

class PyInventoryState(BaseModel):
    loot: Optional[Dict[str, int]] = None
    equipment: PyEquipmentState
    wallet: int

class PyMetersState(BaseModel):
    health: PyMeterState
    magic: PyMeterState

class PyVisionMutatorParameters(BaseModel):
    radius: int

class PyFearMutatorParameters(BaseModel):
    radius: int
    limit: float
    enemy: int

class PyMutatorTriggers(BaseModel):
    fear: bool = False
    vision: bool = False

class PyMutatorParameters(BaseModel):
    fear: PyFearMutatorParameters
    vision: PyVisionMutatorParameters

class PyMutatorState(BaseModel):
    parameters: Optional[PyMutatorParameters] = None
    triggers: Optional[PyMutatorTriggers] = None
    
class PyMemoryState(BaseModel):
    goal: Optional[PyGoalState] = None
    communications: Optional[List[str]] = []
    prices: Optional[Dict[str, float]] = {}
    relationships: Optional[Dict[str, Relationships]] = {}
    property: List[str]

# -----------------------------------------------------------------------------------
# ------------------------------------------------------------------ STATE CONTAINERS

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
    animation: Optional[PyAnimationState] = None

class PyContainerState(PyAssetState):
    content: List[str]
    position: PyPosition
    switch: bool
    animation: Optional[PyAnimationState] = None

class PyDoorState(PyAssetState):
    position: PyPosition
    out: PyPosition
    outlayer: str

class PySwitchState(PyAssetState):
    link: str
    position: PyPosition
    switch: bool
    animation: Optional[PyAnimationState] = None

class PySpriteState(PyAssetState):
    intention: str
    position: PyPosition
    character: PyCharacterState
    inventory: PyInventoryState
    meters: PyMetersState
    mutators: PyMutatorState
    memory: PyMemoryState
    goal: Optional[PyGoalState] = None
    animation: Optional[PyAnimationState] = None

class PyPlayerState(PyAssetState):
    position: PyPosition
    character: PyCharacterState
    inventory: PyInventoryState
    meters: PyMetersState
    mutators: Optional[PyMutatorState] = None
    goal: Optional[PyGoalState] = None
    animation: Optional[PyAnimationState] = None
    intention: Optional[str] = None

# ---------------------------------------------------------------------------------------
# ----------------------------------------------------------------- STATE DATA STRUCTURES

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
    players: Optional[List[PyPlayerState]] = []

# --------------------------------------------------------------------------------------
# ------------------------------------------------------------- CONFIGURATION VALIDATION
# --------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------ RECIPES

class PyRecipe(BaseModel):
    frame: Optional[FrameRecipe] = None
    animation: Optional[AnimationRecipe] = None
    state: Optional[StateRecipe] = None

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
    players: PyRecipe
    armor: PyRecipe
    tools: PyRecipe
    shields: PyRecipe
    utilities: PyRecipe
    weapons: PyRecipe

class PyRecipes(BaseModel):
    tiles: Optional[PyTileRecipe] = None
    crafts: Optional[PyCraftRecipe] = None
    cursors: Optional[PyCursorRecipe] = None
    effects: Optional[PyEffectRecipe] = None
    objects: Optional[PyObjectRecipe] = None
    sheets: Optional[PySheetRecipe] = None

# --------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------ DEVICES

class PyDeviceMapping(BaseModel):
    intentions: Dict[Intentions, Optional[int]]
    goals: Dict[PlayerGoals, Optional[int]]

class PyDeviceMappings(BaseModel):
    keyboard: PyDeviceMapping
    controller: Optional[PyDeviceMapping] = None

# --------------------------------------------------------------------------------------
# --------------------------------------------------------------------------- INTENTIONS

class PyIntentionTransition(BaseModel):
    next: str
    conditions: List[str]

# --------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------ ACTIONS

class PyActionData(BaseModel):
    id: str 
    data: Dict[str, PyAction]

# -------------------------------------------------------------------------------------
# ------------------------------------------------------------------------ YAML SCHEMAS
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# ----------------------------------------------------------------- ACTIONS YAML SCHEMA


class PyActionsConfiguration(YamlBaseSettings):
    actions: List[PyActionData]

    model_config = SettingsConfigDict(
        yaml_file = settings.CONFIG_DIR / Configurations.ACTIONS / settings.APP_EXT
    )


# -------------------------------------------------------------------------------------
# --------------------------------------------------------------- MECHANICS YAML SCHEMA

class PyMechanicsConfiguration(YamlBaseSettings):
    order: List[Mechanics]

    model_config = SettingsConfigDict(
        yaml_file = settings.CONFIG_DIR / Configurations.MECHANICS / settings.APP_EXT
    )

# -------------------------------------------------------------------------------------
# ------------------------------------------------------------------ DEVICE YAML SCHEMA

class PyMappingConfiguration(YamlBaseSettings):
    mappings: PyDeviceMappings

    model_config = SettingsConfigDict(
        yaml_file = settings.CONFIG_DIR / Configurations.MAPPINGS / settings.APP_EXT
    )

# -------------------------------------------------------------------------------------
# --------------------------------------------------------------- INTENTION YAML SCHEMA

class PyIntentionConfiguration(YamlBaseSettings):
    intentions: Dict[Intentions, List[PyIntentionTransition]]

    model_config = SettingsConfigDict(
        yaml_file = settings.CONFIG_DIR / Configurations.INTENTIONS / settings.APP_EXT
    )
# -------------------------------------------------------------------------------------
# ------------------------------------------------------------------ RECIPE YAML SCHEMA

class PyRecipeConfiguration(YamlBaseSettings):
    recipes: PyRecipes

    model_config = SettingsConfigDict(
        yaml_file = settings.CONFIG_DIR / Configurations.RECIPES / settings.APP_EXT
    )

# -------------------------------------------------------------------------------------
# ------------------------------------------------------------------- STATE YAML SCHEMA

class PyStateSchema(BaseModel):
    tiles: Optional[PyTileStateInstances] = None
    objects: Optional[PyObjectStateInstances] = None
    crafts: Optional[PyCraftStateInstances] = None
    cursors: Optional[PyCursorStateInstances] = None
    effects: Optional[PyEffectStateInstances] = None
    sheets: Optional[PySheetStateInstances] = None

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------ PROPERTY YAML SCHEMA

# ---------------------------------------------------------------------------------------

class PyTilePropertySchema(YamlBaseSettings):
    tiles: PyTilePropertyInstances

    model_config = SettingsConfigDict(
        yaml_file = settings.ASSET_DIR / AssetCategories.TILES / settings.APP_EXT
    )


class PyEffectPropertySchema(YamlBaseSettings):
    effects: PyEffectPropertyInstances

    model_config = SettingsConfigDict(
        yaml_file = settings.ASSET_DIR / AssetCategories.EFFECTS / settings.APP_EXT
    )
    
class PyObjectPropertySchema(YamlBaseSettings):
    objects: PyObjectPropertyInstances

    model_config = SettingsConfigDict(
        yaml_file = settings.ASSET_DIR / AssetCategories.OBJECTS / settings.APP_EXT
    )

class PyCraftPropertySchema(YamlBaseSettings):
    crafts: PyCraftPropertyInstances

    model_config = SettingsConfigDict(
        yaml_file = settings.ASSET_DIR / AssetCategories.CRAFTS / settings.APP_EXT
    )

class PyCursorPropertySchema(YamlBaseSettings):
    cursors: PyCursorPropertyInstances

    model_config = SettingsConfigDict(
        yaml_file = settings.ASSET_DIR / AssetCategories.CURSORS / settings.APP_EXT
    )

class PySheetPropertySchema(YamlBaseSettings):
    sheets: PySheetPropertyInstances

    model_config = SettingsConfigDict(
        yaml_file = settings.ASSET_DIR / AssetCategories.SHEETS / settings.APP_EXT
    )