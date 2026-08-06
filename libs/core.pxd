# src/app/models/core.pxd

cdef class Position:
    cdef public int x
    cdef public int y

cdef class Dimensions:
    cdef public int l
    cdef public int w

cdef class Multiple:
    cdef public int nx
    cdef public int ny
    
cdef class Hitbox:
    cdef public Position position
    cdef public Dimensions dimensions

cdef class Attackbox:
    cdef public Position position
    cdef public Dimensions dimensions
    cdef public int hitframe

cdef class Shape:
    cdef public Dimensions dimensions
    cdef public list hitboxes 