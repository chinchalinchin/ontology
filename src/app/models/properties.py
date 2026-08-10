"""
# Ontology: Properties

Models for typing the property attributes of Assets. See documentation for a more in-depth explanation of each field and its purpose. 
"""
# Standard Libraries
from typing import Dict, List, Callable
from dataclasses import dataclass, field

# Cython Libraries
from libs.core import Dimensions, Hitbox, AttackBox

# ---------------------------------------------------------------------------------------
# ----------------------------------------------------------------------- PROPERTY MODELS
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# --------------------------------------------------------------------- NESTED PROPERTIES

@dataclass(slots=True)
class Direction:
    row: int
    attackboxes: List[AttackBox] = field(default_factory=list)

@dataclass(slots=True)
class Action:
    count: int
    directions: Dict[str, Direction]

@dataclass(slots=True)
class Persona:
    dim: Dimensions
    stack: List[str]
    hitboxes: List[Hitbox] = field(default_factory=list)


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
    # NOTE: key, dimension and hitboxes are embedded in the persona!
    # -------------------------- Properties
    personas: Dict[str, Persona]
    actions: Dict[str, Action]

@dataclass(slots=True)
class PlayerProperties(AssetProperties):
    dimensions: Dimensions
    hitboxes: List[Hitbox] = field(default_factory=list)
# ---------------------------------------------------------------------------------------
# ---------------------------------------------------------------- DISPOSITION PROPERTIES

@dataclass(slots=True)
class Transition:
    """
    """
    next: str
    conditions: List[Callable] = field(default_factory=list)

@dataclass(slots=True)
class Disposition:
    """
    """
    # Reachable nodes
    extensions: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)

    # Disposition Scripting Language conditions
    transitions: List[Transition] = field(default_factory=list)