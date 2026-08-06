# cython: language_level=3
"""
# libs/math.pxd
Header file for Cythonized mathematical and geometric operations.
"""

from libs.core cimport Position, Dimensions, Hitbox, Shape, Velocity

cdef class Geometry:
    
    @staticmethod
    cdef bint intersects(Position pos, Shape shape, Position other_pos, Shape other_shape)

    @staticmethod
    cdef bint onscreen(object asset, object player, object screen)

    @staticmethod
    cdef tuple center(object asset)

    @staticmethod
    cdef tuple offset(Position center, Dimensions dim)

cdef class Physics:

    @staticmethod
    cdef void collisions(list assets)