# cython: language_level=3

cdef struct RRTNode:
    float x
    float y
    int parent_idx

cdef struct RRTObstacle:
    float x
    float y
    float w
    float l

cpdef list rrt(
    float sx, 
    float sy, 
    float tx, 
    float ty, 
    list obstacles, 
    float step_size=*, 
    int max_iter=*
)