"""
# Ontology: app.models.properties

Models for typing the property attributes of Assets. See documentation for a more in-depth explanation of each field and its purpose. 
"""
# Standard Libraries
from typing import Dict, List
from dataclasses import dataclass, field

# Cython Libraries
from libs.core.models import Dimensions, Hitbox

# ---------------------------------------------------------------------------------------
# ----------------------------------------------------------------------- PROPERTY MODELS
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# --------------------------------------------------------------------- NESTED PROPERTIES

@dataclass(slots=True)
class Direction:
    row: int

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

@dataclass(slots=True)
class ObjectProperties(AssetProperties):
    dimensions: Dimensions
    mass: int
    count: int = 1
    hitboxes: List[Hitbox] = field(default_factory=list)

@dataclass(slots=True)
class TileProperties(AssetProperties):
    dimensions: Dimensions
    ids: List[str]

@dataclass(slots=True)
class CraftProperties(AssetProperties):
    dimensions: Dimensions
    mass: int
    cost: List[Cost]
    hitboxes: List[Hitbox] = field(default_factory=list)

@dataclass(slots=True)
class SheetProperties(AssetProperties):
    dimensions: Dimensions
    stack: List[str]
    mass: int
    hitboxes: List[Hitbox] = field(default_factory=list)
    actions: Dict[str, Action] = field(default_factory=dict)