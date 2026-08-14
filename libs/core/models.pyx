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

cdef class Dimensions:
    """
    """

    def __init__(self, int w, int l):
        self.w = w
        self.l = l

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

cdef class Hitbox:
    """
    """

    def __init__(self, Position position, Dimensions dimensions):
        self.position = position
        self.dimensions = dimensions

cdef class ScreenPosition:
    """
    Screen position represented as percentages.
    """
    cdef public double px
    cdef public double py

    def __init__(self, double px, double py):
        self.px = px
        self.py = py