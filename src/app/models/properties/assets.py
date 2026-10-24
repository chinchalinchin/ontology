"""
@workflow.asset

# Ontology: app.models.properties.assets

Module for typing Asset property attributes.
"""
# Standard Libraries
from typing import (
    Dict, 
    List, 
    Union, 
    Optional
)
from dataclasses import (
    dataclass, 
    field
)

# Application Libraries
from app.config.enums import (
    Actions,
    Lifespans
)
from app.models.adapters import (
    PydanticHitbox as Hitbox
)
from app.models.properties.core import (
    AssetProperties,
    Action,
    Material,
    Frequency
)

# --------------------------------------------------------------

@dataclass(slots=True)
class CraftProperties(AssetProperties):
    mass: int = 0
    material: Optional[Material] = None
    blueprints: Optional[str] = None
    hitboxes: Optional[Union[Dict[int, List[Hitbox]], Dict[str, Optional[List[Hitbox]]], List[Hitbox]]] = None  # type: ignore

@dataclass(slots=True)
class CursorProperties(AssetProperties):
    frames: List[str] = field(default_factory=list)

@dataclass(slots=True)
class EffectProperties(AssetProperties):
    count: int = 1
    frequency: Frequency = field(default_factory=Frequency)
    mass: int = -1
    hitboxes: Optional[List[Hitbox]] = None # type: ignore

@dataclass(slots=True)
class ObjectProperties(AssetProperties):
    mass: int = 0
    count: int = 1
    material: Optional[Material] = None
    hitboxes: Optional[Union[Dict[str, List[Hitbox]], List[Hitbox]]] = None # type: ignore

@dataclass(slots=True)
class TileProperties(AssetProperties):
    friction: float = 0.0

@dataclass(slots=True)
class ResourceProperties(AssetProperties):
    loot: str = None
    lifespan: Lifespans = Lifespans.ANNUAL.value
    mass: int = 0
    hitboxes: Dict[str, Optional[List[Hitbox]]] = None # type: ignore

@dataclass(slots=True)
class GeographyProperties(AssetProperties):
    hitboxes: Optional[List[Hitbox]] = field(default_factory=list) # type: ignore
    tile: str = None
    fluid: Optional[str] = None
    thickness: int = 8
    mass: int = -1

@dataclass(slots=True)
class SheetProperties(AssetProperties):
    stack: List[str] = field(default_factory=list)
    mass: int = 1
    hitboxes: Optional[List[Hitbox]] = field(default_factory=list) # type: ignore
    actions: Union[str, Dict[Actions, Action]] = field(default_factory=dict)
    attackboxes: Optional[Dict[str, List[Hitbox]]] = field(default_factory=dict) # type: ignore
    
@dataclass(slots=True)
class WidgetProperties(AssetProperties):
    frames: Optional[List[str]] = field(default_factory=list)
