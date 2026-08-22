# /home/grant/Projects/ontology/libs/core/math.pxd
# cython: language_level=3
"""
# libs/math.pxd
Header file for Cythonized mathematical and geometric operations.
"""

from libs.core.models cimport Position, Dimensions, Hitbox, Velocity

cdef class Geometry:
    
    @staticmethod
    cdef tuple _intersects(
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

cdef class Space:
    cdef int cell_size
    cdef int max_entities
    cdef int num_buckets
    cdef int max_per_bucket
    cdef int* bucket_counts
    cdef int* bucket_data

    cpdef void clear(self)
    cdef inline int _hash(self, int cx, int cy)
    cdef void insert(self, int entity_id, int x, int y, int w, int l)
    cdef list query(self)

cdef class Physics:
    pass