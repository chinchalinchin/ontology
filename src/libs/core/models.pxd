# src/libs/cores/models.pxd

cdef class Position:
    cdef public int x
    cdef public int y
    cdef public double rx
    cdef public double ry

cdef class Dimensions:
    cdef public int w
    cdef public int l

cdef class Multiple:
    cdef public int nx
    cdef public int ny
    
cdef class Velocity:
    cdef public double vx
    cdef public double vy

cdef class Hitbox:
    cdef public Position position
    cdef public Dimensions dimensions