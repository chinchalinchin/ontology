# src/app/models/core.pxd

cdef class Position:
    cdef public int x
    cdef public int y

cdef class Dimensions:
    cdef public int w
    cdef public int l

cdef class Multiple:
    cdef public int nx
    cdef public int ny
    
cdef class Velocity:
    cdef public int vx
    cdef public int vy

cdef class Hitbox:
    cdef public Position position
    cdef public Dimensions dimensions