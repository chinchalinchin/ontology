"""
# Ontology: libs.core.math.physics
"""
# cython: language_level=3
from libc.math cimport sqrt, cos, sin, atan2

from libs.core.models cimport Position, Dimensions, Hitbox, Velocity
from libs.core.math.space cimport Space
from libs.core.math.geometry cimport intersects, bounded

# -----------------------------------------------------------------------------
# COLLISION & MOTION INTEGRATION
# -----------------------------------------------------------------------------

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
            p = asset.state.position
            v = asset.state.velocity

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


cpdef list boundaries(list asset_data, list boundary_data, Space grid):
    """
    Evaluates Candidate Pairs for Environmental Boundaries using negative IDs.
    """
    grid.clear()
    cdef tuple b_data, a_data
    cdef int i
    
    for i in range(len(boundary_data)):
        b_data = boundary_data[i]
        grid.insert(-i - 1, b_data[1], b_data[2], b_data[3], b_data[4])
        
    for a_data in asset_data:
        grid.insert(a_data[0], a_data[1], a_data[2], a_data[3], a_data[4])
        
    cdef list candidate_pairs = grid.query()
    cdef list colliding = []
    cdef int id_a, id_b, asset_id, bound_id
    
    for pair in candidate_pairs:
        id_a = pair[0]
        id_b = pair[1]
        
        if (id_a < 0 and id_b >= 0) or (id_a >= 0 and id_b < 0):
            asset_id = id_b if id_a < 0 else id_a
            bound_id = (-id_a - 1) if id_a < 0 else (-id_b - 1)
            
            a_data = asset_data[asset_id]
            b_data = boundary_data[bound_id]
            
            if bounded(
                a_data[1], a_data[2], a_data[5], 
                b_data[1], b_data[2], b_data[3], b_data[4]
            ) is not None:
                colliding.append((asset_id, bound_id))
                
    return colliding


cpdef void constrain(
    Position pos, Hitbox hb, Velocity vel, bint is_kinematic, 
    int b_x, int b_y, int b_w, int b_l
):
    """
    Resolves overlap between a Dynamic Body and an infinitely massive Boundary.
    """
    cdef float cx_a = pos.x + hb.position.x + hb.dimensions.w / 2.0
    cdef float cy_a = pos.y + hb.position.y + hb.dimensions.l / 2.0
    cdef float cx_b = b_x + b_w / 2.0
    cdef float cy_b = b_y + b_l / 2.0

    cdef float dx = cx_b - cx_a
    cdef float dy = cy_b - cy_a

    if dx == 0 and dy == 0:
        dx = 1.0

    cdef float overlap_x = (hb.dimensions.w / 2.0 + b_w / 2.0) - abs(dx)
    cdef float overlap_y = (hb.dimensions.l / 2.0 + b_l / 2.0) - abs(dy)

    if overlap_x > 0 and overlap_y > 0:
        if overlap_x < overlap_y:
            if dx > 0:
                pos.x -= int(overlap_x)
            else:
                pos.x += int(overlap_x)
                
            if vel is not None and not is_kinematic:
                vel.vx = -vel.vx
        else:
            if dy > 0:
                pos.y -= int(overlap_y)
            else:
                pos.y += int(overlap_y)
                
            if vel is not None and not is_kinematic:
                vel.vy = -vel.vy

# -----------------------------------------------------------------------------
# RECIPROCAL VELOCITY OBSTACLES (RVO)
# -----------------------------------------------------------------------------

cpdef Velocity desired_velocity(Position pos, Position target, float speed):
    """
    Calculates preferred velocity vector pointing toward target clamped to speed.
    """
    cdef float dx = target.x - pos.x
    cdef float dy = target.y - pos.y
    cdef float dist = sqrt(dx * dx + dy * dy)
    if dist == 0.0:
        return Velocity(0.0, 0.0)
    return Velocity((dx / dist) * speed, (dy / dist) * speed)


cpdef Velocity avoid(
    object agent_primitive,
    Velocity pref_vel,
    list neighbors,
    float delta = 0.0,
    float time_horizon = 2.0
):
    """
    Reciprocal Velocity Obstacles (RVO) local collision avoidance steering.
    Evaluates candidate velocity vectors around pref_vel to find an optimal velocity
    outside reciprocal obstacle cones of neighboring agents.
    Kinematic agents (e.g. Player) impose full VO, forcing NPCs to steer around them.
    """
    cdef float ax, ay, ar
    cdef float pref_vx = pref_vel.vx if pref_vel is not None else 0.0
    cdef float pref_vy = pref_vel.vy if pref_vel is not None else 0.0
    cdef float pref_speed = sqrt(pref_vx * pref_vx + pref_vy * pref_vy)

    if pref_speed == 0.0 or not neighbors:
        return Velocity(pref_vx, pref_vy)

    if isinstance(agent_primitive, tuple):
        ax = agent_primitive[1] + agent_primitive[3] / 2.0
        ay = agent_primitive[2] + agent_primitive[4] / 2.0
        ar = (agent_primitive[3] if agent_primitive[3] > agent_primitive[4] else agent_primitive[4]) / 2.0
    else:
        ax = agent_primitive.state.position.x + agent_primitive.dimensions.w / 2.0
        ay = agent_primitive.state.position.y + agent_primitive.dimensions.l / 2.0
        ar = (agent_primitive.dimensions.w if agent_primitive.dimensions.w > agent_primitive.dimensions.l else agent_primitive.dimensions.l) / 2.0

    cdef int num_neighbors = len(neighbors)
    cdef object n
    cdef float nx, ny, nvx, nvy, nr
    cdef bint is_kinematic

    # Step 1: Validate if preferred velocity is already clear
    cdef bint pref_clear = True
    cdef float px, py, r_comb, dist, rel_vx, rel_vy, v_sq, dot, t_proj, d_sq, r_sq
    cdef int i

    for i in range(num_neighbors):
        n = neighbors[i]
        if isinstance(n, tuple):
            nx = float(n[0])
            ny = float(n[1])
            nvx = float(n[2])
            nvy = float(n[3])
            nr = float(n[4])
            is_kinematic = bool(n[5])
        else:
            nx = float(n.state.position.x + n.dimensions.w / 2.0)
            ny = float(n.state.position.y + n.dimensions.l / 2.0)
            nvx = float(n.state.velocity.vx if n.state.velocity else 0.0)
            nvy = float(n.state.velocity.vy if n.state.velocity else 0.0)
            nr = float(n.dimensions.w if n.dimensions.w > n.dimensions.l else n.dimensions.l) / 2.0
            is_kinematic = False

        px = nx - ax
        py = ny - ay
        r_comb = ar + nr
        dist = sqrt(px * px + py * py)

        if is_kinematic:
            rel_vx = pref_vx - nvx
            rel_vy = pref_vy - nvy
        else:
            rel_vx = 2.0 * pref_vx - (pref_vx + nvx)
            rel_vy = 2.0 * pref_vy - (pref_vy + nvy)

        if dist <= r_comb:
            if (rel_vx * px + rel_vy * py) > 0:
                pref_clear = False
                break
        else:
            v_sq = rel_vx * rel_vx + rel_vy * rel_vy
            if v_sq > 1e-6:
                dot = px * rel_vx + py * rel_vy
                if dot > 0:
                    t_proj = dot / v_sq
                    if t_proj <= time_horizon:
                        d_sq = (px * px + py * py) - (dot * dot) / v_sq
                        r_sq = r_comb * r_comb
                        if d_sq < r_sq:
                            pref_clear = False
                            break

    if pref_clear:
        return Velocity(pref_vx, pref_vy)

    # Step 2: Sample candidate avoidance velocities around base angle
    cdef float base_angle = atan2(pref_vy, pref_vx)
    cdef float PI = 3.141592653589793
    cdef float best_vx = 0.0
    cdef float best_vy = 0.0
    cdef float best_penalty = 1e12
    cdef bint found_clear = False

    cdef float cand_angle, cand_speed, cand_vx, cand_vy
    cdef float diff_vx, diff_vy, penalty
    cdef bint cand_clear
    cdef int a_step, s_step, side
    cdef float angle_rad

    for a_step in range(1, 13):
        angle_rad = (a_step * 15.0) * (PI / 180.0)
        for side in (1, -1):
            cand_angle = base_angle + side * angle_rad
            for s_step in range(4):
                cand_speed = pref_speed * (1.0 - s_step * 0.25)
                cand_vx = cand_speed * cos(cand_angle)
                cand_vy = cand_speed * sin(cand_angle)

                cand_clear = True
                for i in range(num_neighbors):
                    n = neighbors[i]
                    if isinstance(n, tuple):
                        nx = float(n[0])
                        ny = float(n[1])
                        nvx = float(n[2])
                        nvy = float(n[3])
                        nr = float(n[4])
                        is_kinematic = bool(n[5])
                    else:
                        nx = float(n.state.position.x + n.dimensions.w / 2.0)
                        ny = float(n.state.position.y + n.dimensions.l / 2.0)
                        nvx = float(n.state.velocity.vx if n.state.velocity else 0.0)
                        nvy = float(n.state.velocity.vy if n.state.velocity else 0.0)
                        nr = float(n.dimensions.w if n.dimensions.w > n.dimensions.l else n.dimensions.l) / 2.0
                        is_kinematic = False

                    px = nx - ax
                    py = ny - ay
                    r_comb = ar + nr
                    dist = sqrt(px * px + py * py)

                    if is_kinematic:
                        rel_vx = cand_vx - nvx
                        rel_vy = cand_vy - nvy
                    else:
                        rel_vx = 2.0 * cand_vx - (pref_vx + nvx)
                        rel_vy = 2.0 * cand_vy - (pref_vy + nvy)

                    if dist <= r_comb:
                        if (rel_vx * px + rel_vy * py) > 0:
                            cand_clear = False
                            break
                    else:
                        v_sq = rel_vx * rel_vx + rel_vy * rel_vy
                        if v_sq > 1e-6:
                            dot = px * rel_vx + py * rel_vy
                            if dot > 0:
                                t_proj = dot / v_sq
                                if t_proj <= time_horizon:
                                    d_sq = (px * px + py * py) - (dot * dot) / v_sq
                                    r_sq = r_comb * r_comb
                                    if d_sq < r_sq:
                                        cand_clear = False
                                        break

                if cand_clear:
                    diff_vx = cand_vx - pref_vx
                    diff_vy = cand_vy - pref_vy
                    penalty = diff_vx * diff_vx + diff_vy * diff_vy
                    if penalty < best_penalty:
                        best_penalty = penalty
                        best_vx = cand_vx
                        best_vy = cand_vy
                        found_clear = True
                        if a_step <= 3:
                            return Velocity(best_vx, best_vy)

    if found_clear:
        return Velocity(best_vx, best_vy)

    return Velocity(0.0, 0.0)