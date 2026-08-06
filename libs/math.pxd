# cython: language_level=3
"""
# libs/math.pxd
Header file for Cythonized mathematical and geometric operations.
"""

from libs.core cimport Position, Dimensions, Hitbox, Shape, Velocity

cdef class Geometry:
    
    @staticmethod
    cdef bint intersects(Position pos, Shape shape, Position other_pos, Shape other_shape)


cdef class Physics:

    @staticmethod
    cdef void collisions(list assets)