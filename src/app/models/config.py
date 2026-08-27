"""
# Ontology: app.models.config

Models for typing the configuration attributes of Mechanics and other game components. See documentation for a more in-depth explanation of each field and its purpose. 
"""
# Standard Libraries
from typing import Dict, List, Optional
from dataclasses import dataclass, field

# Application Libraries
from app.config.enums import (
    FrameRecipe, 
    AnimationRecipe,
    StateRecipe,
    Intentions,
    PlayerGoals,
    Statuses,
    Layouts,
    Alignments,
    Menus,
    Interactions,
    Traversal
)
from app.game.menus.core import Binding
from app.models.state import (
    PropertyState, 
    StateSchema
)
from app.models.properties import Action
from app.models.adapters import PydanticScreenPosition as ScreenPosition


class Configuration:
    pass

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------ CONFIGURATION MODELS
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------ RECIPE CONFIGURATION

@dataclass(slots=True)
class Recipe:
    frame: FrameRecipe = None
    animation: AnimationRecipe = None
    state: StateRecipe = None

@dataclass(slots=True)
class TileRecipe:
    fore: Recipe = None
    back: Recipe = None

@dataclass(slots=True)
class CraftRecipe:
    struts: Recipe = None

@dataclass(slots=True)
class CursorRecipe:
    expressions: Recipe = None
    projectiles: Recipe = None

@dataclass(slots=True)
class EffectRecipe:
    temporary: Recipe = None
    persistent: Recipe = None

@dataclass(slots=True)
class ObjectRecipe:
    chests: Recipe = None
    crates: Recipe = None
    doors: Recipe = None
    gates: Recipe = None
    plates: Recipe = None

@dataclass(slots=True)
class SheetRecipe:
    pixies: Recipe = None
    sprites: Recipe = None
    players: Recipe = None
    weapons: Recipe = None
    utilities: Recipe = None
    armor: Recipe = None
    tools: Recipe = None
    shields: Recipe = None

@dataclass(slots=True)
class WidgetRecipe:
    buttons: Recipe = None
    icons: Recipe = None
    meters: Recipe = None
    pages: Recipe = None
    panes: Recipe = None
    
@dataclass(slots=True) 
class RecipeConfiguration(Configuration):
    """
    """
    tiles: TileRecipe = None
    crafts: CraftRecipe = None
    cursors: CursorRecipe = None
    effects: EffectRecipe = None
    objects: ObjectRecipe = None
    sheets: SheetRecipe = None
    widgets: WidgetRecipe = None

# ---------------------------------------------------------------------------------------
# ----------------------------------------------------------------- MAPPING CONFIGURATION

@dataclass(slots=True)
class WorldMapping:
    menus: Dict[Menus, int] = field(default_factory=dict)
    intentions: Dict[Intentions, int] = field(default_factory=dict)
    goals: Dict[PlayerGoals, int] = field(default_factory=dict)

@dataclass(slots=True)
class MenuMapping:
    traversal: Dict[Traversal, int] = field(default_factory=dict)
    interactions: Dict[Interactions, int] = field(default_factory=dict)

@dataclass(slots=True)
class DeviceMapping:
    world: WorldMapping
    menu: MenuMapping

@dataclass(slots=True)
class MappingConfiguration(Configuration):
    keyboard: DeviceMapping
    controller: DeviceMapping = None

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------ ACTION CONFIGURATION

@dataclass(slots=True)
class ActionConfiguration(Configuration):
    id: str
    data: Dict[str, Action]
    
# ---------------------------------------------------------------------------------------
# --------------------------------------------------------------- INTENTION CONFIGURATION

@dataclass(slots=True)
class IntentionConfiguration(Configuration):
    """
    """
    next: str
    conditions: List[str] = field(default_factory=list)

# ---------------------------------------------------------------------------------------
# --------------------------------------------------------------- INTENTION CONFIGURATION

@dataclass(slots=True)
class MechanicsConfiguration(Configuration):
    core: List[str] = field(default_factory=list)
    world: List[str] = field(default_factory=list)

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------- COMPOSITION CONFIGURATION

@dataclass(slots=True)
class CompositionPseudoState:
    strut: PropertyState
    components: StateSchema

@dataclass(slots=True)
class CompositionConfiguration(Configuration):
    root: CompositionPseudoState
    branches: Optional[List[CompositionPseudoState]] = field(default_factory=list)

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------- MENU CONFIGURATION

@dataclass(slots=True)
class MenuWidget:
    instance: str
    id: str
    name: str
    bind: Binding
    status: Statuses

@dataclass(slots=True)
class MenuPane:
    id: str 
    name: str
    position: ScreenPosition # type: ignore
    layout: Layouts
    alignment: Alignments
    gap: int
    children: List[MenuWidget]

@dataclass(slots=True)
class MenuConfiguration(Configuration):
    controller: str
    roots: List[MenuPane]

# ---------------------------------------------------------------------------------------
# --------------------------------------------------------------------------- ROOT SCHEMA

@dataclass(slots=True)
class ConfigurationSchema:
    recipes: RecipeConfiguration = field(default_factory=RecipeConfiguration)
    mappings: MappingConfiguration = field(default_factory=MappingConfiguration)
    intentions: Dict[Intentions, List[IntentionConfiguration]] = field(default_factory=dict)
    actions: List[ActionConfiguration] = field(default_factory=list)
    mechanics: MechanicsConfiguration = field(default_factory=MechanicsConfiguration)
    compositions: Dict[str, CompositionConfiguration] = field(default_factory=dict)
    menus: Dict[str, MenuConfiguration] = field(default_factory=dict)