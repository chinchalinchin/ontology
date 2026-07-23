from pydantic import BaseModel
from typing import Dict, List, Tuple

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
    # Properties
    rel: RelativeDimensions
    # State
    pos: Position

# ---------------------------------------------------------------------------------------
# ----------------------------------------------------------------- ASSET PROPERTY MODELS
# ---------------------------------------------------------------------------------------

class AssetProperties(BaseModel):
    asset: str
    dimensions: Dimensions
    hitboxes: List[Hitbox]

class SpriteProperties(BaseModel):
    asset: str
    dimensions: Dimensions
    hitboxes: List[Hitbox]
    count: Dict[str, int]
