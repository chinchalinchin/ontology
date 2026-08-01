# src/app/models/core.pxd

cdef class Position:
    cdef public int x
    cdef public int y

cdef class Dimensions:
    cdef public int l
    cdef public int w

cdef class Hitbox:
    cdef public Position position
    cdef public Dimensions dimensions

cdef class Shape:
    cdef public Position position
    cdef public Dimensions dimensions
    cdef public list hitboxes  # Can remain a Python list, or be typed further