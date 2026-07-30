class Position(BaseModel):
    """
    Representation of Cartesian coordinates. Following convention, (0,0) is the upper-left corner and down is the positive-y direction.
    """
    x: int
    y: int


class Dimensions(BaseModel):
    """
    """
    l: int
    w: int

class Multliple(BaseModel):
    """
    """
    nx: int
    ny: int
    
class Velocity(BaseModel):
    """
    Representation of Velocity vector. Down is the positive y-direction.
    """
    vx: int
    vy: int

class Hitbox(BaseModel):
    """
    """
    pos: Position
    dim: Dimenions

class AttackBox(BaseModel):
    """
    """
    pos: Position
    dim: Dimenions
    hitframe: int

class Shape(BaseModel):
    """
    """
    dim: Dimensions
    hitboxes: List[Hitbox]