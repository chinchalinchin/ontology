from pydantic import BaseModel
from typing import Dict, List, Tuple

class Dimensions(BaseModel):
    l: int
    w: int

class Position(BaseModel):
    x: int
    y: int

class Hitbox(BaseModel):
    # Properties
    dim: Dimensions
    # State
    pos: Position
