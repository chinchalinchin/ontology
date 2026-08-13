"""
# Ontology: app.models.properties

Models for typing the property attributes of Assets. See documentation for a more in-depth explanation of each field and its purpose. 
"""
# Standard Libraries
from typing import Dict, List, Callable
from dataclasses import dataclass, field

# Application Libraries
from app.config.enums import Directions, Actions

# Cython Libraries
from libs.core.models import Dimensions, Hitbox, Attackbox

# ---------------------------------------------------------------------------------------
# ----------------------------------------------------------------------- PROPERTY MODELS
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# --------------------------------------------------------------------- NESTED PROPERTIES

@dataclass(slots=True)
class Direction:
    row: int
    attackboxes: List[Attackbox] = field(default_factory=list)

@dataclass(slots=True)
class Action:
    count: int
    directions: Dict[str, Direction]

@dataclass(slots=True)
class Cost:
    item: str
    quantity: int

# ---------------------------------------------------------------------------------------
# ---------------------------------------------------------------------- ASSET PROPERTIES

@dataclass(slots=True)
class AssetProperties:
    pass 

@dataclass(slots=True)
class CursorProperties(AssetProperties):
    dimensions: Dimensions

@dataclass(slots=True)
class EffectProperties(AssetProperties):
    dimensions: Dimensions
    count: int 
    hitboxes: List[Hitbox] = field(default_factory=list)

@dataclass(slots=True)
class ObjectProperties(AssetProperties):
    dimensions: Dimensions
    hitboxes: List[Hitbox] = field(default_factory=list)

@dataclass(slots=True)
class TileProperties(AssetProperties):
    dimensions: Dimensions
    ids: List[str]

@dataclass(slots=True)
class CraftProperties(AssetProperties):
    dimensions: Dimensions
    cost: List[Cost]
    hitboxes: List[Hitbox] = field(default_factory=list)

@dataclass(slots=True)
class SheetProperties(AssetProperties):
    dimensions: Dimensions
    stack: List[str]
    hitboxes: List[Hitbox] = field(default_factory=list)
    actions: Dict[str, Action] = field(default_factory=dict)

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------ EQUIPMENT PROPERTIES

@dataclass(slots=True)
class EquipmentAnimationProperty:
    action: Actions
    direction: Directions

@dataclass(slots=True)
class EquipmentProperty:
    animation: EquipmentAnimationProperty
    sheets: List[str]

@dataclass(slots=True)
class EquipmentProperties:
    armor: Dict[str, EquipmentProperty]
    tools: Dict[str, EquipmentProperty]
    utilities: Dict[str, EquipmentProperty]
    weapons: Dict[str, EquipmentProperty]

# ---------------------------------------------------------------------------------------
# ---------------------------------------------------------------- DISPOSITION PROPERTIES

@dataclass(slots=True)
class Transition:
    """
    """
    next: str
    conditions: List[Callable] = field(default_factory=list)

@dataclass(slots=True)
class IntentionProperties:
    """
    """
    intentions: Dict[str, List[Transition]] = field(default_factory=dict)