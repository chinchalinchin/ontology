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