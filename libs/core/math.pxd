# cython: language_level=3
"""
# libs/math.pxd
Header file for Cythonized mathematical and geometric operations.
"""

from libs.core.models cimport Position, Dimensions, Hitbox, Velocity

cdef class Geometry:
    
    @staticmethod
    cdef bint intersects(
        Position pos1, 
        Dimensions dim1, 
        list hitboxes1,
        Position pos2, 
        Dimensions dim2, 
        list hitboxes2
    )

    @staticmethod
    cdef bint onscreen(
        Position pos, 
        Dimensions dim, 
        Position p_pos, 
        Dimensions p_dim, 
        Dimensions screen
    )


cdef class Physics:

    @staticmethod
    cdef void collisions(list assets)