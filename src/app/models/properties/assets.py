"""
@domain.model
@category.crafts
@category.cursors
@category.effects
@category.geography
@category.objects
@category.resources
@category.sheets
@category.tiles
@category.widgets
@app.asset
@asset.property

# Ontology: Source - app.models.properties.assets

Asset Property Models.
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
from app.static.semantics import (
    Actions,
    Lifespans,
    Blueprints
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
    blueprints: Optional[Blueprints] = None
    hitboxes: Optional[Union[
        Dict[int, List[Hitbox]],                                    # type: ignore
        Dict[str, Optional[List[Hitbox]]],                          # type: ignore
        List[Hitbox]]                                               # type: ignore
    ] = None 

# --------------------------------------------------------------

@dataclass(slots=True)
class CursorProperties(AssetProperties):
    frames: List[str] = field(default_factory=list)

# --------------------------------------------------------------

@dataclass(slots=True)
class EffectProperties(AssetProperties):
    count: int = 1
    frequency: Frequency = field(default_factory=Frequency)
    mass: int = -1
    hitboxes: Optional[List[Hitbox]] = None                         # type: ignore

# --------------------------------------------------------------

@dataclass(slots=True)
class GeographyProperties(AssetProperties):
    tile: str = None
    fluid: Optional[str] = None
    thickness: int = 8
    mass: int = -1
    hitboxes: Optional[List[Hitbox]] = field(default_factory=list)  # type: ignore

# --------------------------------------------------------------

@dataclass(slots=True)
class ObjectProperties(AssetProperties):
    mass: int = 0
    count: int = 1
    material: Optional[Material] = None
    hitboxes: Optional[Union[
        Dict[str, List[Hitbox]],                                    # type: ignore
        List[Hitbox]]                                               # type: ignore
    ] = None 

# --------------------------------------------------------------

@dataclass(slots=True)
class ResourceProperties(AssetProperties):
    loot: str = None
    lifespan: Lifespans = Lifespans.ANNUAL.value
    mass: int = 0
    hitboxes: Dict[str, Optional[List[Hitbox]]] = None              # type: ignore

# --------------------------------------------------------------

# TODO: attackboxes need inducted into the new HitboxSchema ECS Architecture.

@dataclass(slots=True)
class SheetProperties(AssetProperties):
    stack: List[str] = field(default_factory=list)
    mass: int = 1
    actions: Union[str, Dict[Actions, Action]] = field(default_factory=dict)
    attackboxes: Optional[
        Dict[str, List[Hitbox]]                                     # type: ignore
    ] = field(default_factory=dict)
    hitboxes: Optional[List[Hitbox]] = field(default_factory=list)  # type: ignore

    
# --------------------------------------------------------------

@dataclass(slots=True)
class TileProperties(AssetProperties):
    friction: float = 0.0

# --------------------------------------------------------------

@dataclass(slots=True)
class WidgetProperties(AssetProperties):
    frames: Optional[List[str]] = field(default_factory=list)
