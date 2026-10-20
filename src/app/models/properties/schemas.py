"""
# Ontology: app.models.properties.schemas

Module for typing property schemas.
"""
# Standard Libraries
from typing import Dict
from dataclasses import (
    dataclass, 
    field
)

# Application Libraries
from app.models.properties.assets import (
    CraftProperties,
    CursorProperties,
    EffectProperties,
    GeographyProperties,
    ObjectProperties,
    ResourceProperties,
    SheetProperties,
    TileProperties,
    WidgetProperties,
)
from app.models.properties.fonts import (
    FontProperties
)


@dataclass(slots=True)
class CursorPropertyInstances:
    expressions: Dict[str, CursorProperties] = field(default_factory=dict)
    projectiles: Dict[str, CursorProperties] = field(default_factory=dict)

@dataclass(slots=True)
class CraftPropertyInstances:
    struts: Dict[str, CraftProperties] = field(default_factory=dict)
    bridges: Dict[str, CraftProperties] = field(default_factory=dict)
    platforms: Dict[str, CraftProperties] = field(default_factory=dict)
    stairs: Dict[str, CraftProperties] = field(default_factory=dict)

@dataclass(slots=True)
class EffectPropertyInstances:
    collectables: Dict[str, EffectProperties] = field(default_factory=dict)
    reactables: Dict[str, EffectProperties] = field(default_factory=dict)
    hazards: Dict[str, EffectProperties] = field(default_factory=dict)
    passive: Dict[str, EffectProperties] = field(default_factory=dict)
    fluids: Dict[str, EffectProperties] = field(default_factory=dict)

@dataclass(slots=True)
class GeographyPropertyInstances:
    shorelines: Dict[str, GeographyProperties] = field(default_factory=dict)

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
class ResourcePropertyInstances:
    crops: Dict[str, ResourceProperties] = field(default_factory=dict)
    ore: Dict[str, ResourceProperties] = field(default_factory=dict)
    trees: Dict[str, ResourceProperties] = field(default_factory=dict)

@dataclass(slots=True)
class TilePropertyInstances:
    canopy: Dict[str, TileProperties] = field(default_factory=dict)
    environ: Dict[str, TileProperties] = field(default_factory=dict)
    grid: Dict[str, TileProperties] = field(default_factory=dict)

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


# --------------------------------------------------------------
# -------------------------------------------------- ROOT SCHEMA
# --------------------------------------------------------------

@dataclass(slots=True)
class PropertiesSchema:
    tiles: TilePropertyInstances = field(default_factory=TilePropertyInstances)
    effects: EffectPropertyInstances = field(default_factory=EffectPropertyInstances)
    geography: GeographyPropertyInstances = field(default_factory=GeographyPropertyInstances)
    objects: ObjectPropertyInstances = field(default_factory=ObjectPropertyInstances)
    crafts: CraftPropertyInstances = field(default_factory=CraftPropertyInstances)
    cursors: CursorPropertyInstances = field(default_factory=CursorPropertyInstances)
    resources: ResourcePropertyInstances = field(default_factory=ResourcePropertyInstances)
    sheets: SheetPropertyInstances = field(default_factory=SheetPropertyInstances)
    fonts: Dict[str, FontProperties] = field(default_factory=dict)
    widgets: WidgetPropertyInstances = field(default_factory=WidgetPropertyInstances)