"""
# Ontology: Properties

Models for typing the property attributes of Assets. See documentation for a more in-depth explanation of each field and its purpose. 
"""
# Standard Libraries
from typing import Dict, List

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
    # -------------------------- Keys
    key: str                    # Unique Asset Identifier
    # -------------------------- Properties
    dimensions: Dimensions

class EffectProperties(AssetProperties):
    # -------------------------- Keys
    key: str                    # Unique Asset Identifier
    # -------------------------- Properties
    dimensions: Dimensions
    hitboxes: List[Hitbox]
    count: int 

class ObjectProperties(AssetProperties):
    # -------------------------- Keys
    key: str                    # Unique Asset Identifier
    # -------------------------- Properties
    dimensions: Dimensions
    hitboxes: List[Hitbox]

class TileProperties(AssetProperties):
    # -------------------------- Keys
    key: str                    # Unique Asset Identifier
    # -------------------------- Properties
    dimensions: Dimensions

class CraftProperties(AssetProperties):
    # -------------------------- Keys
    key: str                    # Unique Asset Identifier
    # -------------------------- Properties
    dimensions: Dimensions
    hitboxes: List[Hitbox]
    cost: List[Cost]

class SheetProperties(AssetProperties):
    # NOTE: key, dimension and hitboxes are embedded in the persona!
    # -------------------------- Properties
    personas: Dict[str, Persona]
    actions: Dict[str, Action]