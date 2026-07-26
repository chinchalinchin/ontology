"""
Pydantic models for typing the property attributes of Assets. See documentation for a more in-depth explanation of each field and its purpose. 
"""
# Standard Libraries
from typing import Dict, List, Tuple, Union
# Externa Libraries
from pydantic import BaseModel

# ---------------------------------------------------------------------------------------
# ----------------------------------------------------------------- ASSET PROPERTY FIELDS
# ---------------------------------------------------------------------------------------

class Dimensions(BaseModel):
    l: int
    w: int

class RelativeDimensions(BaseModel):
    relX: int
    relY: int

class Hitbox(BaseModel):
    rel: RelativeDimensions
    pos: Position

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------- ASSET PROPERTY MODEL
# ---------------------------------------------------------------------------------------

class AssetProperties(BaseModel):
    asset: str
    dimensions: Dimensions
    hitboxes: List[Hitbox]
    # Animate Properties
    #   count: None             => inanimate Assets
    #   count: str              => animate Assets
    #   count: Dict[str, int]   => Sprite Assets
    count: Union[None, str, Dict[str, int]]
