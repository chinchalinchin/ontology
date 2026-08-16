# /home/grant/Projects/ontology/libs/core/models.pyx
"""
Ontology: libs.core.models
"""

from typing import List

cdef class Position:
    """
    """

    def __init__(self, int x, int y):
        self.x = x
        self.y = y

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y}

cdef class Dimensions:
    """
    """

    def __init__(self, int w, int l):
        self.w = w
        self.l = l

    def to_dict(self) -> dict:
        return {"w": self.w, "l": self.l}

cdef class Multiple:
    """
    """

    def __init__(self, int nx, int ny):
        self.nx = nx
        self.ny = ny
        
    def to_dict(self) -> dict:
        return {"nx": self.nx, "ny": self.ny}
        
cdef class Velocity:
    """
    """
    
    def __init__(self, int vx, int vy):
        self.vx = vx
        self.vy = vy

    def to_dict(self) -> dict:
        return {"vx": self.vx, "vy": self.vy}

cdef class Hitbox:
    """
    """

    def __init__(self, Position position, Dimensions dimensions):
        self.position = position
        self.dimensions = dimensions

    def to_dict(self) -> dict:
        return {
            "position": self.position.to_dict() if self.position is not None else None,
            "dimensions": self.dimensions.to_dict() if self.dimensions is not None else None
        }

cdef class ScreenPosition:
    """
    Screen position represented as percentages.
    """
    cdef public double px
    cdef public double py

    def __init__(self, double px, double py):
        self.px = px
        self.py = py

    def to_dict(self) -> dict:
        return {"px": self.px, "py": self.py}