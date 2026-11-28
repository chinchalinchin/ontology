# cython: language_level=3
"""
@domain.system
@domain.logic
@app.library
@workflow.combat
@workflow.collisions
@workflow.navigation
@workflow.rendering

# Ontology: Libraries - libs.core.math.geometry

Cython header for geometrical calculations and inline narrow-phase predicates.
"""
from libs.core.models cimport (
    Position,
    Dimensions,
    Hitbox,
    Boundary
)


cdef inline bint c_intersects(
    int x1,
    int y1,
    list hbs1,
    int x2,
    int y2,
    list hbs2
):
    """
    Zero-allocation narrow-phase AABB overlap predicate across two hitbox lists.
    """
    cdef int ax1, ay1, w1, h1
    cdef int ax2, ay2, w2, h2
    cdef Hitbox hb1, hb2
    cdef object item1, item2

    if not hbs1 or not hbs2:
        return False

    for item1 in hbs1:
        hb1 = item1
        ax1 = x1 + hb1.position.x
        ay1 = y1 + hb1.position.y
        w1 = hb1.dimensions.w
        h1 = hb1.dimensions.l

        for item2 in hbs2:
            hb2 = item2
            ax2 = x2 + hb2.position.x
            ay2 = y2 + hb2.position.y
            w2 = hb2.dimensions.w
            h2 = hb2.dimensions.l

            if (
                ax1 < ax2 + w2 and ax1 + w1 > ax2
                and ay1 < ay2 + h2 and ay1 + h1 > ay2
            ):
                return True

    return False


cdef inline bint c_bounded(
    int a_x,
    int a_y,
    list hitboxes,
    int b_x,
    int b_y,
    int b_w,
    int b_l
):
    """
    Zero-allocation narrow-phase predicate evaluating Asset hitboxes against a raw AABB.
    """
    cdef int x1, y1, w1, h1
    cdef Hitbox hb
    cdef object item

    if not hitboxes:
        return False

    for item in hitboxes:
        hb = item
        x1 = a_x + hb.position.x
        y1 = a_y + hb.position.y
        w1 = hb.dimensions.w
        h1 = hb.dimensions.l

        if (
            x1 < b_x + b_w and x1 + w1 > b_x
            and y1 < b_y + b_l and y1 + h1 > b_y
        ):
            return True

    return False


cpdef Position camera(Position focus, Dimensions dim, Dimensions screen, Dimensions board)
cpdef bint onscreen(Position pos, Dimensions dim, Position p_pos, Dimensions p_dim, Dimensions screen, Dimensions board)
cpdef tuple intersects(Position pos1, list hitboxes1, Position pos2, list hitboxes2)
cpdef list intersections(Position pos1, list hitboxes1, Position pos2, list hitboxes2)
cpdef bint cone(int sx, int sy, int tx, int ty, int radius, double cos_threshold, str direction)
cpdef bint nearby(int sx, int sy, int tx, int ty, int radius)
cpdef tuple bounded(int a_x, int a_y, list hitboxes, int b_x, int b_y, int b_w, int b_l)
cpdef bint inside(int px, int py, list aabbs)
cpdef bint occluded(int qx, int qy, int qw, int ql, list obstacles)
cdef bint c_punctures(float x1, float y1, float x2, float y2, float rx, float ry, float rw, float rl) noexcept nogil
cpdef bint punctures(float x1, float y1, float x2, float y2, float rx, float ry, float rw, float rl)
cpdef bint los(float x1, float y1, float x2, float y2, list rects)
cpdef list contours(list rects)
cpdef tuple raycast(int sx, int sy, int sw, int sl, str direction, list obstacles, int max_dist)