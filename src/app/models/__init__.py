class Position:
    """
    Representation of Cartesian coordinates. Following convention, (0,0) is the upper-left corner and down is the positive-y direction.
    """
    x: int
    y: int


class Dimensions:
    """
    """
    l: int
    w: int

class Multiple:
    """
    """
    nx: int
    ny: int
    
class Velocity:
    """
    Representation of Velocity vector. Down is the positive y-direction.
    """
    vx: int
    vy: int

class Hitbox:
    """
    """
    position: Position
    dimensions: Dimensions

class AttackBox:
    """
    """
    position: Position
    dimensions: Dimensions
    hitframe: int