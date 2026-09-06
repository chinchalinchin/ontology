# cython: language_level=3
from libs.core.models cimport Position, Dimensions, Hitbox
from libc.math cimport sqrt

cpdef tuple intersects(
    Position pos1, 
    Dimensions dim1, 
    list hitboxes1,
    Position pos2, 
    Dimensions dim2, 
    list hitboxes2
):
    cdef int x1, y1, w1, h1
    cdef int x2, y2, w2, h2
    cdef Hitbox hb1, hb2
    
    if not hitboxes1 or not hitboxes2:
        return None
    
    for item1 in hitboxes1:
        hb1 = <Hitbox>item1
        x1 = pos1.x + hb1.position.x
        y1 = pos1.y + hb1.position.y
        w1 = hb1.dimensions.w
        h1 = hb1.dimensions.l
    
        for item2 in hitboxes2:
            hb2 = <Hitbox>item2
            x2 = pos2.x + hb2.position.x
            y2 = pos2.y + hb2.position.y
            w2 = hb2.dimensions.w
            h2 = hb2.dimensions.l
            
            if (x1 < x2 + w2 and x1 + w1 > x2 and
                y1 < y2 + h2 and y1 + h1 > y2):
                return (hb1, hb2)
                
    return None

cpdef bint onscreen(
    Position pos, 
    Dimensions dim, 
    Position p_pos, 
    Dimensions p_dim, 
    Dimensions screen
):
    cdef int cam_x = p_pos.x + (p_dim.l // 2) - (screen.w // 2)
    cdef int cam_y = p_pos.y + (p_dim.w // 2) - (screen.l // 2)
    
    return (pos.x < cam_x + screen.w and pos.x + dim.w > cam_x and
            pos.y < cam_y + screen.l and pos.y + dim.l > cam_y)

cpdef bint cone(
    int sx, 
    int sy, 
    int tx, 
    int ty, 
    int radius, 
    double cos_threshold, 
    str direction
):
    cdef int dx = tx - sx
    cdef int dy = ty - sy
    cdef int dist_sq = (dx * dx) + (dy * dy)
    
    if dist_sq > (radius * radius):
        return False
        
    if dist_sq == 0:
        return True
        
    cdef double ux = 0.0
    cdef double uy = 0.0
    
    if direction == "up":
        uy = -1.0
    elif direction == "down":
        uy = 1.0
    elif direction == "left":
        ux = -1.0
    elif direction == "right":
        ux = 1.0
        
    cdef double dist = sqrt(<double>dist_sq)
    cdef double dot_product = ((dx / dist) * ux) + ((dy / dist) * uy)
    
    return dot_product >= cos_threshold

cpdef bint nearby(
    int sx, 
    int sy, 
    int tx, 
    int ty, 
    int radius
):
    """
    Zero-allocation squared distance check. Replaces Python-side nearby() calls.
    """
    cdef int dx = tx - sx
    cdef int dy = ty - sy
    return (dx * dx + dy * dy) < (radius * radius)