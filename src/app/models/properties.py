"""
# Ontology: app.models.properties
"""
from typing import Dict, List, Union, Optional
from dataclasses import dataclass, field

from app.config.enums import (
    Actions,
    Directions,
    Alignments,
    Lifecycles
)
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
    directions: Dict[Directions, Direction]
    delay: int = 1

@dataclass(slots=True)
class Cost:
    item: str
    quantity: int

@dataclass(slots=True)
class Lifecycle:
    type: Lifecycles = Lifecycles.CONTINUOUS.value
    delay: int = 1
    frequency: int = 0
    cooldown: int = 60
    persist: bool = False

# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class AssetProperties:
    pass 

# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class RGBA:
    r: int = 255
    g: int = 255
    b: int = 255
    a: int = 255

@dataclass(slots=True)
class Outline:
    color: RGBA = field(default_factory=lambda: RGBA(r=255, g=255, b=255, a=255))    
    width: int = 0

@dataclass(slots=True)
class FontProperties:
    alignment: Alignments = Alignments.START.value
    color: RGBA = field(default_factory=lambda: RGBA(r=255, g=255, b=255, a=255))    
    outline: Optional[Outline] = None
    bold: bool = False
    italics: bool = False
    strikethrough: bool = False
    underline: bool = False
    margins: float = 0
    size: int = 24

# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class CursorProperties(AssetProperties):
    dimensions: Dimensions # type: ignore
    frames: List[str] = field(default_factory=list)

@dataclass(slots=True)
class EffectProperties(AssetProperties):
    dimensions: Dimensions # type: ignore
    count: int
    lifecycle: Lifecycle = field(default_factory=Lifecycle)
    mass: int = -1
    hitboxes: Optional[List[Hitbox]] = field(default_factory=list) # type: ignore

@dataclass(slots=True)
class ObjectProperties(AssetProperties):
    dimensions: Dimensions # type: ignore
    mass: int = 0
    count: int = 1
    hitboxes: Optional[List[Hitbox]] = field(default_factory=list) # type: ignore

@dataclass(slots=True)
class TileProperties(AssetProperties):
    dimensions: Dimensions # type: ignore
    friction: float = 0.0

@dataclass(slots=True)
class CraftProperties(AssetProperties):
    dimensions: Dimensions # type: ignore
    cost: List[Cost]
    mass: int = 0
    hitboxes: Optional[List[Hitbox]] = field(default_factory=list) # type: ignore

@dataclass(slots=True)
class SheetProperties(AssetProperties):
    dimensions: Dimensions # type: ignore
    stack: List[str] = field(default_factory=list)
    mass: int = 0
    hitboxes: Optional[List[Hitbox]] = field(default_factory=list) # type: ignore
    actions: Union[str, Dict[Actions, Action]] = field(default_factory=dict)
    attackboxes: Optional[Dict[str, List[Hitbox]]] = field(default_factory=dict) # type: ignore
    
@dataclass(slots=True)
class WidgetProperties(AssetProperties):
    dimensions: Dimensions # type: ignore
    frames: Optional[List[str]] = field(default_factory=list)

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------------- ROOT SCHEMAS

@dataclass(slots=True)
class TilePropertyInstances:
    back: Dict[str, TileProperties] = field(default_factory=dict)
    fore: Dict[str, TileProperties] = field(default_factory=dict)

@dataclass(slots=True)
class EffectPropertyInstances:
    collectables: Dict[str, EffectProperties] = field(default_factory=dict)
    reactables: Dict[str, EffectProperties] = field(default_factory=dict)
    hazards: Dict[str, EffectProperties] = field(default_factory=dict)
    passive: Dict[str, EffectProperties] = field(default_factory=dict)
    fluids: Dict[str, EffectProperties] = field(default_factory=dict)
    
@dataclass(slots=True)
class ObjectPropertyInstances:
    obstacles: Dict[str, ObjectProperties] = field(default_factory=dict)
    chests: Dict[str, ObjectProperties] = field(default_factory=dict)
    crates: Dict[str, ObjectProperties] = field(default_factory=dict)
    doors: Dict[str, ObjectProperties] = field(default_factory=dict)
    gates: Dict[str, ObjectProperties] = field(default_factory=dict)
    plates: Dict[str, ObjectProperties] = field(default_factory=dict)
    signs: Dict[str, ObjectProperties] = field(default_factory=dict)
    rafts: Dict[str, ObjectProperties] = field(default_factory=dict)
    
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
    widgets: WidgetPropertyInstances = field(default_factory=WidgetPropertyInstances)