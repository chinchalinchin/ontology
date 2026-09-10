"""
# Ontology: libs.core.math.geometry
"""
# cython: language_level=3
# C Libraries
from libc.math cimport sqrt

# Cython Libraries
from libs.core.models cimport (
    Position, 
    Dimensions, 
    Hitbox, 
    Boundary
)

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
    cdef int cam_x = p_pos.x + (p_dim.w // 2) - (screen.w // 2)
    cdef int cam_y = p_pos.y + (p_dim.l // 2) - (screen.l // 2)
    
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


# -----------------------------------------------------------------------------
# SWEEP-LINE CONTOUR ALGORITHM
# -----------------------------------------------------------------------------


cdef list merge(list intervals):
    """
    Sorts and merges overlapping active 1D intervals.
    """
    if not intervals:
        return []
    intervals.sort()
    cdef list merged = []
    cdef int current_start = intervals[0][0]
    cdef int current_end = intervals[0][1]
    cdef int start, end
    cdef tuple iv
    
    for iv in intervals[1:]:
        start, end = iv
        if start <= current_end:
            if end > current_end:
                current_end = end
        else:
            merged.append((current_start, current_end))
            current_start = start
            current_end = end
            
    merged.append((current_start, current_end))
    return merged

cdef list xor(list A, list B):
    """
    Evaluates the symmetric difference between two sets of merged intervals.
    Any interval present in (A XOR B) exactly represents an exposed contour edge.
    """
    cdef list events = []
    for start, end in A:
        events.append((start, 1))
        events.append((end, -1))
    for start, end in B:
        events.append((start, 1))
        events.append((end, -1))
        
    events.sort()
    
    cdef list xor_intervals = []
    cdef int count = 0
    cdef int last_y = -1
    cdef int i = 0
    cdef int n = len(events)
    cdef int y
    
    while i < n:
        y = events[i][0]
        if count == 1 and y > last_y:
            xor_intervals.append((last_y, y))
            
        # Process all coincident coordinates to avoid false fragmentation
        while i < n and events[i][0] == y:
            count += events[i][1]
            i += 1
        last_y = y
        
    return merge(xor_intervals)


cpdef list contours(list rects):
    """
    Executes a 2-pass Sweep-Line algorithm over primitive AABBs.
    Returns the exact mathematical segments of the outer hull as Boundaries.
    Input: list of (min_x, min_y, max_x, max_y)
    Output: list of Boundary
    """
    cdef list boundaries = []
    
    # ---------------------------------------------------------
    # PASS 1: VERTICAL SWEEP
    # ---------------------------------------------------------
    cdef list v_events = []
    cdef tuple r
    cdef int i = 0
    for r in rects:
        v_events.append((r[0], 1, r[1], r[3], i))  # Left edge
        v_events.append((r[2], -1, r[1], r[3], i)) # Right edge
        i += 1
        
    v_events.sort()
    
    cdef dict active_v = {}
    cdef list prev_merged_v = []
    cdef list curr_merged_v = []
    cdef int x
    cdef int n_v = len(v_events)
    i = 0
    
    while i < n_v:
        x = v_events[i][0]
        
        while i < n_v and v_events[i][0] == x:
            if v_events[i][1] == 1:
                active_v[v_events[i][4]] = (v_events[i][2], v_events[i][3])
            else:
                if v_events[i][4] in active_v:
                    del active_v[v_events[i][4]]
            i += 1
            
        curr_merged_v = merge(list(active_v.values()))
        
        for y1, y2 in xor(prev_merged_v, curr_merged_v):
            # A vertical segment has width 1 and length y2 - y1
            boundaries.append(Boundary(Position(x, y1), Dimensions(1, y2 - y1)))
            
        prev_merged_v = curr_merged_v
        
    # ---------------------------------------------------------
    # PASS 2: HORIZONTAL SWEEP
    # ---------------------------------------------------------
    cdef list h_events = []
    i = 0
    for r in rects:
        h_events.append((r[1], 1, r[0], r[2], i))  # Bottom edge
        h_events.append((r[3], -1, r[0], r[2], i)) # Top edge
        i += 1
        
    h_events.sort()
    
    cdef dict active_h = {}
    cdef list prev_merged_h = []
    cdef list curr_merged_h = []
    cdef int y
    cdef int n_h = len(h_events)
    i = 0
    
    while i < n_h:
        y = h_events[i][0]
        
        while i < n_h and h_events[i][0] == y:
            if h_events[i][1] == 1:
                active_h[h_events[i][4]] = (h_events[i][2], h_events[i][3])
            else:
                if h_events[i][4] in active_h:
                    del active_h[h_events[i][4]]
            i += 1
            
        curr_merged_h = merge(list(active_h.values()))
        
        for x1, x2 in xor(prev_merged_h, curr_merged_h):
            # A horizontal segment has width x2 - x1 and length 1
            boundaries.append(Boundary(Position(x1, y), Dimensions(x2 - x1, 1)))
            
        prev_merged_h = curr_merged_h

    return boundaries

cpdef tuple bounded(
    int a_x, int a_y, list hitboxes,
    int b_x, int b_y, int b_w, int b_l
):
    """
    Evaluates Asset hitboxes against a raw mathematical Boundary constraint.
    """
    cdef int x1, y1, w1, h1
    cdef Hitbox hb
    
    for item in hitboxes:
        hb = <Hitbox>item
        x1 = a_x + hb.position.x
        y1 = a_y + hb.position.y
        w1 = hb.dimensions.w
        h1 = hb.dimensions.l
        
        if (x1 < b_x + b_w and x1 + w1 > b_x and
            y1 < b_y + b_l and y1 + h1 > b_y):
            return (hb,)
            
    return None