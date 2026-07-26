"""
Pydantic models for typing the property attributes of Assets. See documentation for a more in-depth explanation of each field and its purpose. 
"""
# Standard Libraries
from typing import Dict, List, Tuple, Union
# External Libraries
from pydantic import BaseModel
# Application Libraries
from app.models import Position, Dimenions, Hitbox

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------------ PROPERTY MODEL
# ---------------------------------------------------------------------------------------

class ShapeProperties(BaseModel):
    dimensions: Dimensions
    hitboxes: List[Hitbox]

class TileProperties(BaseModel):
    # -------------------------- Keys
    asset: str                  # Unique Asset Identifier
    # -------------------------- Properties
    dimensions: Dimensions

class AssetProperties(BaseModel):
    # -------------------------- Keys
    asset: str                  # Unique Asset Identifier 
    # -------------------------- Animation Properties
    #   count: None             => inanimate Assets
    #   count: str              => animate Assets
    #   count: Dict[str, int]   => Sprite Assets
    count: Union[None, str, Dict[str, int]]
