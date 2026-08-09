"""
# Ontology: Properties

Models for typing the property attributes of Assets. See documentation for a more in-depth explanation of each field and its purpose. 
"""
# Standard Libraries
from typing import Dict, List, Callable

# Cython Libraries
from libs.core import Dimensions, Hitbox, AttackBox

# ---------------------------------------------------------------------------------------
# ----------------------------------------------------------------------- PROPERTY MODELS
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# --------------------------------------------------------------------- NESTED PROPERTIES

class Direction:
    row: int
    attackboxes: List[AttackBox]

class Action:
    count: int
    directions: Dict[str, Direction]

class Persona:
    dim: Dimensions
    hitboxes: List[Hitbox]
    stack: List[str]

class Cost:
    item: str
    quantity: int

# ---------------------------------------------------------------------------------------
# ---------------------------------------------------------------------- ASSET PROPERTIES

class AssetProperties:
    pass 

class CursorProperties(AssetProperties):
    # -------------------------- Properties
    dimensions: Dimensions

class EffectProperties(AssetProperties):
    dimensions: Dimensions
    hitboxes: List[Hitbox]
    count: int 

class ObjectProperties(AssetProperties):
    dimensions: Dimensions
    hitboxes: List[Hitbox]

class TileProperties(AssetProperties):
    dimensions: Dimensions
    ids: List[str]

class CraftProperties(AssetProperties):
    dimensions: Dimensions
    hitboxes: List[Hitbox]
    cost: List[Cost]

class SheetProperties(AssetProperties):
    # NOTE: key, dimension and hitboxes are embedded in the persona!
    # -------------------------- Properties
    personas: Dict[str, Persona]
    actions: Dict[str, Action]

# ---------------------------------------------------------------------------------------
# ---------------------------------------------------------------- DISPOSITION PROPERTIES

class Transition:
    """
    """
    conditions: List[Callable]
    next: str

class Disposition:
    """
    """
    # 
    extensions: List[str]
    actions: List[str]
    # Disposition Scripting Language conditions
    transitions: List[Transition]