cdef class Position:
    """
    """

    def __init__(self, int x, int y):
        self.x = x
        self.y = y

cdef class Dimensions:
    """
    """

    def __init__(self, int l, int w):
        self.l = l
        self.w = w

cdef class Multiple:
    """
    """

    def __init__(self, int nx, int ny):
        self.nx = nx
        self.ny = ny
        
cdef class Velocity:
    """
    """
    
    def __init__(self, int vx, int vy):
        self.vx = vx
        self.vy = vy

cdef class AttackBox:
    """
    """
    def __init__(self, Position position, Dimensions dimensions, int hitframe):
        self.position = position
        self.dimensions = dimensions
        self.hitframe = hitframe

cdef class Hitbox:
    """
    """

    def __init__(self, Position position, Dimensions dimensions):
        self.position = position
        self.dimensions = dimensions