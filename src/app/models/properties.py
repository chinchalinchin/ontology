"""
Pydantic models for typing the property attributes of Assets. See documentation for a more in-depth explanation of each field and its purpose. 
"""
# Standard Libraries
from typing import Dict, List, Tuple, Union
# External Libraries
from pydantic import BaseModel
# Application Libraries
from app.models import Position, Dimenions, Hitbox, Entity

# ---------------------------------------------------------------------------------------
# ----------------------------------------------------------------------- PROPERTY MODELS
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------ COMPONENT PROPERTIES

class ShapeProperties:
    dimensions: Dimensions
    hitboxes: List[Hitbox]

# ---------------------------------------------------------------------------------------
# ---------------------------------------------------------------------- ASSET PROPERTIES

class CursorProperties:
    # -------------------------- Keys
    key: str                    # Unique Asset Identifier
    # -------------------------- Properties
    dimensions: Dimensions

class EffectProperties(BaseModel):
    # -------------------------- Keys
    key: str                    # Unique Asset Identifier
    # -------------------------- Properties
    shape: ShapeProperties
    count: int 

class ObjectProperties(BaseModel):
    # -------------------------- Keys
    key: str                    # Unique Asset Identifier
    # -------------------------- Properties
    shape: ShapeProperties

class TileProperties(BaseModel):
    # -------------------------- Keys
    key: str                    # Unique Asset Identifier
    # -------------------------- Properties
    dimensions: Dimensions

class PixieProperties(BaseModel):
    # -------------------------- Keys
    key: str                    # Unique Asset Identifier
    # -------------------------- Properties
    shape: ShapeProperties

# ---------------------------------------------------------------------------------------
# ---------------------------------------------------------------------- SPRITE PROPERTIES

class PixieActionsProperty(BaseModel):
    count: int
    directions: List[str]
    
class SpriteDirectionProperty(BaseModel):
    row: int
    attackboxes: List[AttackBox]

class SpriteActionProperty(BaseModel):
    count: int
    directions: Dict[str, SpriteDirection]

class SpriteProperties(BaseModel):
    # -------------------------- Keys
    key: str                    # Unique Asset Identifier
    # -------------------------- Properties
    shape: ShapeProperties
    actions: Dict[str, SpriteActionProperty]
