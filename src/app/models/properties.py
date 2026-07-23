from pydantic import BaseModel
from typing import Dict, List, Tuple

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
