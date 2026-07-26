class Position(BaseModel):
    """
    Representation of Cartesian coordinates. Following convention, (0,0) is the upper-left corner and down is the positive-y direction.
    """
    x: int
    y: int

class Velocity(BaseModel):
    """
    Representation of Velocity vector. Down is the positive y-direction.
    """
    vx: int
    vy: int