"""
# Ontology: app.models.properties
"""
from typing import Dict, List, Union, Optional
from dataclasses import dataclass, field

from app.config.enums import Alignments
from app.models.adapters import (
    PydanticDimensions as Dimensions, 
    PydanticHitbox as Hitbox
)

# ---------------------------------------------------------------------------------------

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

@dataclass(slots=True)
class AssetProperties:
    pass 

# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class RGBA:
    r: int
    g: int
    b: int
    a: float

@dataclass(slots=True)
class FontProperties:
    alignment: Alignments
    bold: bool
    italics: bool
    margin: int
    color: RGBA

# ---------------------------------------------------------------------------------------

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
    mass: int = 0
    count: int = 1
    hitboxes: Optional[List[Hitbox]] = field(default_factory=list)

@dataclass(slots=True)
class TileProperties(AssetProperties):
    dimensions: Dimensions
    friction: float = 0.0

@dataclass(slots=True)
class CraftProperties(AssetProperties):
    dimensions: Dimensions
    cost: List[Cost]
    mass: int = 0
    hitboxes: Optional[List[Hitbox]] = field(default_factory=list)

@dataclass(slots=True)
class SheetProperties(AssetProperties):
    dimensions: Dimensions
    stack: List[str] = field(default_factory=list)
    mass: int = 0
    hitboxes: Optional[List[Hitbox]] = field(default_factory=list)
    actions: Union[str, Dict[str, Action]] = field(default_factory=dict)

@dataclass(slots=True)
class WidgetProperties(AssetProperties):
    dimensions: Dimensions
    frames: Optional[List[str]] = field(default_factory=list)

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------------- ROOT SCHEMAS

@dataclass(slots=True)
class TilePropertyInstances:
    back: Dict[str, TileProperties] = field(default_factory=dict)
    fore: Dict[str, TileProperties] = field(default_factory=dict)

@dataclass(slots=True)
class EffectPropertyInstances:
    persistent: Dict[str, EffectProperties] = field(default_factory=dict)
    temporary: Dict[str, EffectProperties] = field(default_factory=dict)

@dataclass(slots=True)
class ObjectPropertyInstances:
    chests: Dict[str, ObjectProperties] = field(default_factory=dict)
    crates: Dict[str, ObjectProperties] = field(default_factory=dict)
    doors: Dict[str, ObjectProperties] = field(default_factory=dict)
    gates: Dict[str, ObjectProperties] = field(default_factory=dict)
    plates: Dict[str, ObjectProperties] = field(default_factory=dict)

@dataclass(slots=True)
class CraftPropertyInstances:
    struts: Dict[str, CraftProperties] = field(default_factory=dict)

@dataclass(slots=True)
class CursorPropertyInstances:
    expressions: Dict[str, CursorProperties] = field(default_factory=dict)
    projectiles: Dict[str, CursorProperties] = field(default_factory=dict)

@dataclass(slots=True)
class SheetPropertyInstances:
    pixies: Dict[str, SheetProperties] = field(default_factory=dict)
    sprites: Dict[str, SheetProperties] = field(default_factory=dict)
    weapons: Dict[str, SheetProperties] = field(default_factory=dict)
    utilities: Dict[str, SheetProperties] = field(default_factory=dict)
    armor: Dict[str, SheetProperties] = field(default_factory=dict)
    tools: Dict[str, SheetProperties] = field(default_factory=dict)
    shields: Dict[str, SheetProperties] = field(default_factory=dict)
    players: Dict[str, SheetProperties] = field(default_factory=dict)

@dataclass(slots=True)
class WidgetPropertyInstances:
    buttons: Dict[str, WidgetProperties] = field(default_factory=dict)
    icons: Dict[str, WidgetProperties] = field(default_factory=dict)
    meters: Dict[str, WidgetProperties] = field(default_factory=dict)
    pages: Dict[str, WidgetProperties] = field(default_factory=dict)
    panes: Dict[str, WidgetProperties] = field(default_factory=dict)

@dataclass(slots=True)
class PropertiesSchema:
    tiles: TilePropertyInstances = field(default_factory=TilePropertyInstances)
    effects: EffectPropertyInstances = field(default_factory=EffectPropertyInstances)
    objects: ObjectPropertyInstances = field(default_factory=ObjectPropertyInstances)
    crafts: CraftPropertyInstances = field(default_factory=CraftPropertyInstances)
    cursors: CursorPropertyInstances = field(default_factory=CursorPropertyInstances)
    sheets: SheetPropertyInstances = field(default_factory=SheetPropertyInstances)
    fonts: Dict[str, FontProperties] = field(default_factory=dict)