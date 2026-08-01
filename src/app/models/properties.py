"""
# Ontology: Properties

Models for typing the property attributes of Assets. See documentation for a more in-depth explanation of each field and its purpose. 
"""
# Standard Libraries
from typing import Dict, List

# Application Libraries
from app.models import Dimensions, Hitbox, AttackBox

# ---------------------------------------------------------------------------------------
# ----------------------------------------------------------------------- PROPERTY MODELS
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------ COMPONENT PROPERTIES

class ShapeProperties:
    dimensions: Dimensions
    hitboxes: List[Hitbox]

# ---------------------------------------------------------------------------------------
# --------------------------------------------------------------------- NESTED PROPERTIES

class PixieActionsProperty:
    count: int
    directions: List[str]
    
class SpriteDirectionProperty:
    row: int
    attackboxes: List[AttackBox]

class SpriteActionProperty:
    count: int
    directions: Dict[str, SpriteDirectionProperty]

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
    shape: ShapeProperties
    count: int 

class ObjectProperties(AssetProperties):
    # -------------------------- Keys
    key: str                    # Unique Asset Identifier
    # -------------------------- Properties
    shape: ShapeProperties

class TileProperties(AssetProperties):
    # -------------------------- Keys
    key: str                    # Unique Asset Identifier
    # -------------------------- Properties
    dimensions: Dimensions

class PixieProperties(AssetProperties):
    # -------------------------- Keys
    key: str                    # Unique Asset Identifier
    # -------------------------- Properties
    shape: ShapeProperties

class SpriteProperties(AssetProperties):
    # -------------------------- Keys
    key: str                    # Unique Asset Identifier
    # -------------------------- Properties
    shape: ShapeProperties
    actions: Dict[str, SpriteActionProperty]
