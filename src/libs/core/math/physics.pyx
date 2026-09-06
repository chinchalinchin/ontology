# cython: language_level=3
from libc.math cimport sqrt

from libs.core.models cimport Position, Dimensions, Hitbox, Velocity
from libs.core.math.space cimport Space
from libs.core.math.geometry cimport intersects

cpdef list collisions(list primitive_data, Space grid):
    cdef int i, x, y, w, l
    cdef tuple data
    
    for data in primitive_data:
        i = data[0]
        x = data[1]
        y = data[2]
        w = data[3]
        l = data[4]
        grid.insert(i, x, y, w, l)
        
    cdef list candidate_pairs = grid.query()
    cdef list colliding_pairs = []
    cdef int id_a, id_b
    cdef tuple data_a, data_b
    
    cdef Position pos_a = Position(0, 0)
    cdef Dimensions dim_a = Dimensions(0, 0)
    cdef Position pos_b = Position(0, 0)
    cdef Dimensions dim_b = Dimensions(0, 0)
    cdef tuple pair
    
    for pair in candidate_pairs:
        id_a = pair[0]
        id_b = pair[1]
        data_a = primitive_data[id_a]
        data_b = primitive_data[id_b]
        
        pos_a.x = data_a[1]
        pos_a.y = data_a[2]
        dim_a.w = data_a[3]
        dim_a.l = data_a[4]

        pos_b.x = data_b[1]
        pos_b.y = data_b[2]
        dim_b.w = data_b[3]
        dim_b.l = data_b[4]

        if intersects(pos_a, dim_a, data_a[5], pos_b, dim_b, data_b[5]) is not None:
            colliding_pairs.append(pair)
            
    return colliding_pairs


cpdef void collide(
    Position pos1, Hitbox hb1, Velocity vel1, float m1, bint is_kinematic1,
    Position pos2, Hitbox hb2, Velocity vel2, float m2, bint is_kinematic2
):
    cdef float cx_a = pos1.x + hb1.position.x + hb1.dimensions.w / 2.0
    cdef float cy_a = pos1.y + hb1.position.y + hb1.dimensions.l / 2.0
    cdef float cx_b = pos2.x + hb2.position.x + hb2.dimensions.w / 2.0
    cdef float cy_b = pos2.y + hb2.position.y + hb2.dimensions.l / 2.0

    cdef float dx = cx_b - cx_a
    cdef float dy = cy_b - cy_a

    if dx == 0 and dy == 0:
        dx = 1.0

    cdef float overlap_x = (hb1.dimensions.w / 2.0 + hb2.dimensions.w / 2.0) - abs(dx)
    cdef float overlap_y = (hb1.dimensions.l / 2.0 + hb2.dimensions.l / 2.0) - abs(dy)

    cdef float inv_m1, inv_m2, inv_total, p1, p2
    cdef float shift_x1, shift_x2, shift_y1, shift_y2
    cdef float v1x, v1y, v2x, v2y, v1f_x, v1f_y, v2f_x, v2f_y

    if overlap_x > 0 and overlap_y > 0:
        inv_m1 = 1.0 / m1 if m1 > 0 else 0.0
        inv_m2 = 1.0 / m2 if m2 > 0 else 0.0
        inv_total = inv_m1 + inv_m2

        if inv_total > 0:
            p1 = inv_m1 / inv_total
            p2 = inv_m2 / inv_total

            if overlap_x < overlap_y:
                shift_x1 = overlap_x * p1
                shift_x2 = overlap_x * p2

                if dx > 0:
                    pos1.x -= int(shift_x1)
                    pos2.x += int(shift_x2)
                else:
                    pos1.x += int(shift_x1)
                    pos2.x -= int(shift_x2)

                if m1 == 0 and m2 == 0:
                    pass
                elif m1 == 0:
                    if vel2 is not None and not is_kinematic2:
                        vel2.vx = -vel2.vx
                elif m2 == 0:
                    if vel1 is not None and not is_kinematic1:
                        vel1.vx = -vel1.vx
                else:
                    v1x = vel1.vx if vel1 is not None else 0.0
                    v2x = vel2.vx if vel2 is not None else 0.0
                    v1f_x = (v1x * (m1 - m2) + 2 * m2 * v2x) / (m1 + m2)
                    v2f_x = (v2x * (m2 - m1) + 2 * m1 * v1x) / (m1 + m2)
                    
                    if vel1 is not None and not is_kinematic1:
                        vel1.vx = v1f_x
                    if vel2 is not None and not is_kinematic2:
                        vel2.vx = v2f_x

            else:
                shift_y1 = overlap_y * p1
                shift_y2 = overlap_y * p2
                if dy > 0:
                    pos1.y -= int(shift_y1)
                    pos2.y += int(shift_y2)
                else:
                    pos1.y += int(shift_y1)
                    pos2.y -= int(shift_y2)

                if m1 == 0 and m2 == 0:
                    pass
                elif m1 == 0:
                    if vel2 is not None and not is_kinematic2:
                        vel2.vy = -vel2.vy
                elif m2 == 0:
                    if vel1 is not None and not is_kinematic1:
                        vel1.vy = -vel1.vy
                else:
                    v1y = vel1.vy if vel1 is not None else 0.0
                    v2y = vel2.vy if vel2 is not None else 0.0
                    v1f_y = (v1y * (m1 - m2) + 2 * m2 * v2y) / (m1 + m2)
                    v2f_y = (v2y * (m2 - m1) + 2 * m1 * v1y) / (m1 + m2)
                    
                    if vel1 is not None and not is_kinematic1:
                        vel1.vy = v1f_y
                    if vel2 is not None and not is_kinematic2:
                        vel2.vy = v2f_y


cpdef void integrate(list assets, float delta):
    cdef int shift
    cdef Position p
    cdef Velocity v
    for asset in assets:
        if getattr(asset.state, 'velocity', None) is not None:
            p = <Position>asset.state.position
            v = <Velocity>asset.state.velocity

            p.rx += v.vx * delta
            p.ry += v.vy * delta

            if p.rx >= 1.0 or p.rx <= -1.0:
                shift = int(p.rx)
                p.x += shift
                p.rx -= shift

            if p.ry >= 1.0 or p.ry <= -1.0:
                shift = int(p.ry)
                p.y += shift
                p.ry -= shift


cpdef void friction(Velocity vel, float fric, float delta):
    """
    Decays velocity vector magnitudes using environment friction.
    """
    cdef float dv = fric * delta
    cdef float vx = vel.vx
    cdef float vy = vel.vy
    cdef float vmag = sqrt((vx * vx) + (vy * vy))

    if vmag > 0:
        if dv >= vmag:
            vel.vx = 0.0
            vel.vy = 0.0
        else:
            vel.vx -= (vx / vmag) * dv
            vel.vy -= (vy / vmag) * dv


cpdef void kinematics(Velocity vel, float ix, float iy, float speed):
    """
    Snaps axis and applies strictly normalized target velocities.
    """
    cdef float mag

    if ix != 0.0 and iy == 0.0:
        vel.vy = 0.0
    if iy != 0.0 and ix == 0.0:
        vel.vx = 0.0

    if ix != 0.0 or iy != 0.0:
        mag = sqrt((ix * ix) + (iy * iy))
        vel.vx = (ix / mag) * speed
        vel.vy = (iy / mag) * speed
    else:
        vel.vx = 0.0
        vel.vy = 0.0


cpdef void dynamics(
    Velocity vel, 
    float sx, 
    float sy, 
    float tx, 
    float ty, 
    float speed, 
    float impulse, 
    float delta
):
    """
    Calculates dynamic acceleration vectors towards a target coordinate, 
    clamping maximum magnitude or snapping to exact arrival bounds.
    """
    cdef float dx = tx - sx
    cdef float dy = ty - sy
    cdef float mag, vmag

    if dx == 0 and dy == 0:
        vel.vx = 0.0
        vel.vy = 0.0
        return

    mag = sqrt((dx * dx) + (dy * dy))
    
    # Clamp velocity if within arrival threshold to prevent oscillation 
    if mag < speed * delta:
        vel.vx = dx / delta
        vel.vy = dy / delta
    else:
        vel.vx += (dx / mag) * impulse * delta
        vel.vy += (dy / mag) * impulse * delta

        vmag = sqrt((vel.vx * vel.vx) + (vel.vy * vel.vy))
        if vmag > speed:
            vel.vx = (vel.vx / vmag) * speed
            vel.vy = (vel.vy / vmag) * speed