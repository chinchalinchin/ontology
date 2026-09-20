# cython: language_level=3
from libs.core.models cimport Position, Dimensions, Hitbox

cpdef tuple intersects(
    Position pos1, 
    Dimensions dim1, 
    list hitboxes1,
    Position pos2, 
    Dimensions dim2, 
    list hitboxes2
)

cpdef bint onscreen(
    Position pos, 
    Dimensions dim, 
    Position p_pos, 
    Dimensions p_dim, 
    Dimensions screen
)

cpdef bint cone(
    int sx, 
    int sy, 
    int tx, 
    int ty, 
    int radius, 
    double cos_threshold, 
    str direction
)

cpdef bint nearby(
    int sx, 
    int sy, 
    int tx, 
    int ty, 
    int radius
)

cdef bint c_punctures(
    float x1, 
    float y1, 
    float x2, 
    float y2, 
    float rx, 
    float ry, 
    float rw, 
    float rl
) noexcept nogil

cpdef bint punctures(
    float x1, 
    float y1, 
    float x2, 
    float y2, 
    float rx, 
    float ry, 
    float rw, 
    float rl
)

cpdef list contours(
    list rects
)

cpdef tuple bounded(
    int a_x,
    int a_y,
    list hitboxes,
    int b_x,
    int b_y, 
    int b_w,
    int b_l
)

cpdef bint los(
    float x1, 
    float y1, 
    float x2, 
    float y2, 
    list rects
)

cpdef tuple raycast(
    int sx, 
    int sy, 
    int sw, 
    int sl, 
    str direction, 
    list obstacles, 
    int max_dist
)