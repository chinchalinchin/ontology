# cython: language_level=3
"""
@domain.system
@domain.logic
@app.library
@physics.motion
@workflow.combat
@workflow.collisions

# Ontology: Libraries - libs.core.math.physics

"""
from libc.math cimport sqrt, cos, sin, atan2

from libs.core.models cimport Position, Dimensions, Hitbox, Velocity
from libs.core.math.space cimport Space
from libs.core.math.geometry cimport c_intersects, c_bounded

# -----------------------------------------------------------------------------
# COLLISION & MOTION INTEGRATION
# -----------------------------------------------------------------------------

cdef inline bint _hitboxes_aabb(
    int ax,
    int ay,
    list hitboxes,
    int* out_x,
    int* out_y,
    int* out_w,
    int* out_l
):
    """
    Computes the enclosing world-space AABB for a list of relative hitboxes.
    Returns False if hitboxes is empty or degenerate.
    """
    cdef Hitbox hb
    cdef object item
    cdef int hx1, hy1, hx2, hy2
    cdef int min_x = 0, min_y = 0, max_x = 0, max_y = 0
    cdef bint first = True

    if not hitboxes:
        return False

    for item in hitboxes:
        hb = item
        if hb.dimensions.w <= 0 or hb.dimensions.l <= 0:
            continue
        hx1 = ax + hb.position.x
        hy1 = ay + hb.position.y
        hx2 = hx1 + hb.dimensions.w
        hy2 = hy1 + hb.dimensions.l

        if first:
            min_x = hx1
            min_y = hy1
            max_x = hx2
            max_y = hy2
            first = False
        else:
            if hx1 < min_x:
                min_x = hx1
            if hy1 < min_y:
                min_y = hy1
            if hx2 > max_x:
                max_x = hx2
            if hy2 > max_y:
                max_y = hy2

    if first:
        return False

    out_x[0] = min_x
    out_y[0] = min_y
    out_w[0] = max_x - min_x
    out_l[0] = max_y - min_y
    return True


cdef inline void _insert_hitboxes(
    Space grid,
    int entity_id,
    int ax,
    int ay,
    list hitboxes
):
    """
    Inserts each active hitbox of an entity into the broad-phase Space grid,
    providing tight cell coverage for compound multi-hitbox assets.
    """
    cdef Hitbox hb
    cdef object item
    cdef int w, l

    if not hitboxes:
        return

    for item in hitboxes:
        hb = item
        w = hb.dimensions.w
        l = hb.dimensions.l
        if w > 0 and l > 0:
            grid.insert(
                entity_id,
                ax + hb.position.x,
                ay + hb.position.y,
                w,
                l
            )


cpdef list collisions(list primitive_data, Space grid):
    """
    Evaluates all-pairs collisions using C-level Space pair buffers and
    zero-allocation narrow-phase c_intersects checks.
    """
    cdef list colliding_pairs = []
    cdef int n_items = len(primitive_data)
    cdef int i, k, n_pairs, id_a, id_b
    cdef tuple data, data_a, data_b

    grid.clear()
    if n_items < 2:
        return colliding_pairs

    for i in range(n_items):
        data = primitive_data[i]
        _insert_hitboxes(grid, data[0], data[1], data[2], data[5])

    n_pairs = grid.query_pairs()
    for k in range(n_pairs):
        id_a = grid.pair_a[k]
        id_b = grid.pair_b[k]
        data_a = primitive_data[id_a]
        data_b = primitive_data[id_b]

        if c_intersects(
            data_a[1], data_a[2], data_a[5],
            data_b[1], data_b[2], data_b[5]
        ):
            colliding_pairs.append((id_a, id_b))

    return colliding_pairs


cpdef list bipartite_collisions(list dynamics, list statics, Space grid):
    """
    Evaluates bipartite dynamic-vs-static collisions using negative IDs for
    static bodies and non-negative IDs for dynamic bodies. Zero static-vs-static
    or dynamic-vs-dynamic pairs are hashed or tested.
    Returns list of (dynamic_index, static_index) tuples.
    """
    cdef list colliding = []
    cdef int n_dyn = len(dynamics)
    cdef int n_stat = len(statics)
    cdef int i, k, n_pairs, dyn_idx, stat_idx
    cdef tuple d_data, s_data

    grid.clear()
    if n_dyn == 0 or n_stat == 0:
        return colliding

    for i in range(n_stat):
        s_data = statics[i]
        _insert_hitboxes(grid, -i - 1, s_data[1], s_data[2], s_data[5])

    for i in range(n_dyn):
        d_data = dynamics[i]
        _insert_hitboxes(grid, i, d_data[1], d_data[2], d_data[5])

    n_pairs = grid.query_bipartite_pairs()
    for k in range(n_pairs):
        stat_idx = -grid.pair_a[k] - 1
        dyn_idx = grid.pair_b[k]
        d_data = dynamics[dyn_idx]
        s_data = statics[stat_idx]

        if c_intersects(
            d_data[1], d_data[2], d_data[5],
            s_data[1], s_data[2], s_data[5]
        ):
            colliding.append((dyn_idx, stat_idx))

    return colliding


cpdef void populate_statics(list statics, Space grid):
    """
    Populates a persistent static Space grid with static asset primitives
    indexed by their list position 0..len(statics)-1.
    """
    cdef int i, n = len(statics)
    cdef tuple s_data

    grid.clear()
    for i in range(n):
        s_data = statics[i]
        _insert_hitboxes(grid, i, s_data[1], s_data[2], s_data[5])


cpdef list query_statics(list dynamics, list statics, Space static_grid):
    """
    Probes dynamic asset primitives against a pre-populated persistent static
    Space grid without clearing or re-inserting static bodies.
    Returns list of (dynamic_index, static_index) tuples.
    """
    cdef list colliding = []
    cdef int n_dyn = len(dynamics)
    cdef int i, k, n_hits, stat_idx
    cdef int ax, ay, bx, by, bw, bl
    cdef tuple d_data, s_data
    cdef list d_hbs

    if n_dyn == 0 or not statics or static_grid.active_count == 0:
        return colliding

    for i in range(n_dyn):
        d_data = dynamics[i]
        ax = d_data[1]
        ay = d_data[2]
        d_hbs = d_data[5]
        if not _hitboxes_aabb(ax, ay, d_hbs, &bx, &by, &bw, &bl):
            continue

        n_hits = static_grid.probe_aabb(bx, by, bw, bl)
        for k in range(n_hits):
            stat_idx = static_grid.pair_b[k]
            s_data = statics[stat_idx]
            if c_intersects(ax, ay, d_hbs, s_data[1], s_data[2], s_data[5]):
                colliding.append((i, stat_idx))

    return colliding


cpdef void populate_bounds(list targets, Space grid):
    """
    Populates a persistent Space grid with raw AABB target tuples
    (index, x, y, w, l, ...) keyed by list position 0..len(targets)-1.
    """
    cdef int i, n = len(targets)
    cdef tuple t_data

    grid.clear()
    for i in range(n):
        t_data = targets[i]
        grid.insert(i, t_data[1], t_data[2], t_data[3], t_data[4])


cpdef list query_bounds(list assets, list targets, Space static_grid):
    """
    Probes dynamic asset primitives against a pre-populated persistent AABB
    target Space grid without clearing or re-inserting static targets.
    Returns list of (asset_index, target_index) tuples.
    """
    cdef list matches = []
    cdef int n_assets = len(assets)
    cdef int i, k, n_hits, target_idx
    cdef int ax, ay, bx, by, bw, bl
    cdef tuple a_data, t_data
    cdef list a_hbs

    if n_assets == 0 or not targets or static_grid.active_count == 0:
        return matches

    for i in range(n_assets):
        a_data = assets[i]
        ax = a_data[1]
        ay = a_data[2]
        a_hbs = a_data[5]
        if not _hitboxes_aabb(ax, ay, a_hbs, &bx, &by, &bw, &bl):
            continue

        n_hits = static_grid.probe_aabb(bx, by, bw, bl)
        for k in range(n_hits):
            target_idx = static_grid.pair_b[k]
            t_data = targets[target_idx]
            if c_bounded(ax, ay, a_hbs, t_data[1], t_data[2], t_data[3], t_data[4]):
                matches.append((i, target_idx))

    return matches


cpdef void collide(
    Position pos1, Hitbox hb1, Velocity vel1, float m1, bint is_kinematic1,
    Position pos2, Hitbox hb2, Velocity vel2, float m2, bint is_kinematic2
):
    """
    Resolves spatial overlap via inverse-mass separation and applies 1D elastic
    momentum transfer along the collision normal only when bodies are approaching.
    """
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

    if overlap_x <= 0 or overlap_y <= 0:
        return

    cdef float inv_m1 = 1.0 / m1 if m1 > 0 else 0.0
    cdef float inv_m2 = 1.0 / m2 if m2 > 0 else 0.0
    cdef float inv_total = inv_m1 + inv_m2

    if inv_total <= 0:
        return

    cdef float p1 = inv_m1 / inv_total
    cdef float p2 = inv_m2 / inv_total
    cdef int total_shift, ishift_1, ishift_2
    cdef float normal, v1, v2, v_rel, v1f, v2f

    if overlap_x < overlap_y:
        total_shift = max(1, <int>overlap_x)
        if p1 <= p2:
            ishift_1 = <int>(total_shift * p1)
            ishift_2 = total_shift - ishift_1
        else:
            ishift_2 = <int>(total_shift * p2)
            ishift_1 = total_shift - ishift_2

        if dx > 0:
            normal = 1.0
            pos1.x -= ishift_1
            pos2.x += ishift_2
        else:
            normal = -1.0
            pos1.x += ishift_1
            pos2.x -= ishift_2

        # Clear stale sub-pixel carry along the resolved collision axis
        if ishift_1 > 0:
            pos1.rx = 0.0
        if ishift_2 > 0:
            pos2.rx = 0.0

        # Guard momentum transfer: only resolve when bodies are approaching along normal
        v1 = vel1.vx if (vel1 is not None and m1 > 0) else 0.0
        v2 = vel2.vx if (vel2 is not None and m2 > 0) else 0.0
        v_rel = (v2 - v1) * normal
        if v_rel >= 0.0:
            return

        if m1 == 0:
            if vel2 is not None and not is_kinematic2:
                vel2.vx = -v2
        elif m2 == 0:
            if vel1 is not None and not is_kinematic1:
                vel1.vx = -v1
        else:
            v1f = (v1 * (m1 - m2) + 2.0 * m2 * v2) / (m1 + m2)
            v2f = (v2 * (m2 - m1) + 2.0 * m1 * v1) / (m1 + m2)

            if vel1 is not None and not is_kinematic1:
                vel1.vx = v1f
            if vel2 is not None and not is_kinematic2:
                vel2.vx = v2f
    else:
        total_shift = max(1, <int>overlap_y)
        if p1 <= p2:
            ishift_1 = <int>(total_shift * p1)
            ishift_2 = total_shift - ishift_1
        else:
            ishift_2 = <int>(total_shift * p2)
            ishift_1 = total_shift - ishift_2

        if dy > 0:
            normal = 1.0
            pos1.y -= ishift_1
            pos2.y += ishift_2
        else:
            normal = -1.0
            pos1.y += ishift_1
            pos2.y -= ishift_2

        # Clear stale sub-pixel carry along the resolved collision axis
        if ishift_1 > 0:
            pos1.ry = 0.0
        if ishift_2 > 0:
            pos2.ry = 0.0

        # Guard momentum transfer: only resolve when bodies are approaching along normal
        v1 = vel1.vy if (vel1 is not None and m1 > 0) else 0.0
        v2 = vel2.vy if (vel2 is not None and m2 > 0) else 0.0
        v_rel = (v2 - v1) * normal
        if v_rel >= 0.0:
            return

        if m1 == 0:
            if vel2 is not None and not is_kinematic2:
                vel2.vy = -v2
        elif m2 == 0:
            if vel1 is not None and not is_kinematic1:
                vel1.vy = -v1
        else:
            v1f = (v1 * (m1 - m2) + 2.0 * m2 * v2) / (m1 + m2)
            v2f = (v2 * (m2 - m1) + 2.0 * m1 * v1) / (m1 + m2)

            if vel1 is not None and not is_kinematic1:
                vel1.vy = v1f
            if vel2 is not None and not is_kinematic2:
                vel2.vy = v2f


cpdef void integrate(list assets, float delta):
    """Executes Symplectic Euler integration with native C sub-pixel truncation."""
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
                shift = <int>p.rx
                p.x += shift
                p.rx -= shift

            if p.ry >= 1.0 or p.ry <= -1.0:
                shift = <int>p.ry
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


cpdef list bipartite(list assets, list targets, Space grid):
    """
    Unified bipartite negative-ID query evaluating intersections between
    dynamic asset primitives (non-negative IDs) and raw AABB targets (negative IDs).
    Returns list of (asset_index, target_index) tuples.
    """
    cdef list matches = []
    cdef int n_assets = len(assets)
    cdef int n_targets = len(targets)
    cdef int i, k, n_pairs, asset_idx, target_idx
    cdef tuple a_data, t_data

    grid.clear()
    if n_assets == 0 or n_targets == 0:
        return matches

    for i in range(n_targets):
        t_data = targets[i]
        grid.insert(-i - 1, t_data[1], t_data[2], t_data[3], t_data[4])

    for i in range(n_assets):
        a_data = assets[i]
        _insert_hitboxes(grid, i, a_data[1], a_data[2], a_data[5])

    n_pairs = grid.query_bipartite_pairs()
    for k in range(n_pairs):
        target_idx = -grid.pair_a[k] - 1
        asset_idx = grid.pair_b[k]
        a_data = assets[asset_idx]
        t_data = targets[target_idx]

        if c_bounded(
            a_data[1], a_data[2], a_data[5],
            t_data[1], t_data[2], t_data[3], t_data[4]
        ):
            matches.append((asset_idx, target_idx))

    return matches


cpdef list boundaries(list asset_data, list boundary_data, Space grid):
    """
    Evaluates Candidate Pairs for Environmental Boundaries using negative IDs.
    Delegates to the unified bipartite query.
    """
    return bipartite(asset_data, boundary_data, grid)


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
                pos.x -= <int>overlap_x
            else:
                pos.x += <int>overlap_x
                
            if vel is not None and not is_kinematic:
                vel.vx = -vel.vx
        else:
            if dy > 0:
                pos.y -= <int>overlap_y
            else:
                pos.y += <int>overlap_y
                
            if vel is not None and not is_kinematic:
                vel.vy = -vel.vy


cpdef list environment(list assets, list fields, Space grid):
    """
    Evaluates candidate intersections between dynamic entities (positive IDs)
    and environmental field sensors (negative IDs).
    Delegates to the unified bipartite query.
    """
    return bipartite(assets, fields, grid)


# -----------------------------------------------------------------------------
# RECIPROCAL VELOCITY OBSTACLES (RVO)
# -----------------------------------------------------------------------------

cpdef Velocity aim(Position pos, Position target, float speed):
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
    object asset,
    Velocity vel,
    list neighbors,
    float delta
):
    """
    Reciprocal Velocity Obstacles (RVO) local collision avoidance steering.
    Evaluates candidate velocity vectors around pref_vel to find an optimal velocity
    outside reciprocal obstacle cones of neighboring agents.
    Kinematic agents (e.g. Player) impose full VO, forcing NPCs to steer around them.
    """
    cdef float ax, ay, ar
    cdef float vx = vel.vx if vel is not None else 0.0
    cdef float vy = vel.vy if vel is not None else 0.0
    cdef float speed = sqrt(vx * vx + vy * vy)
    cdef float time_horizon = 2.0
    
    if speed == 0.0 or not neighbors:
        return Velocity(vx, vy)

    if isinstance(asset, tuple):
        ax = asset[1] + asset[3] / 2.0
        ay = asset[2] + asset[4] / 2.0
        ar = (asset[3] if asset[3] > asset[4] else asset[4]) / 2.0
    else:
        ax = asset.state.position.x + asset.dimensions.w / 2.0
        ay = asset.state.position.y + asset.dimensions.l / 2.0
        ar = (asset.dimensions.w if asset.dimensions.w > asset.dimensions.l else asset.dimensions.l) / 2.0

    cdef int num_neighbors = len(neighbors)
    cdef object n
    cdef float nx, ny, nvx, nvy, nr
    cdef bint is_kinematic

    # Step 1: Validate if preferred velocity is already clear
    cdef bint clear = True
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
            rel_vx = vx - nvx
            rel_vy = vy - nvy
        else:
            rel_vx = 2.0 * vx - (vx + nvx)
            rel_vy = 2.0 * vy - (vy + nvy)

        if dist <= r_comb:
            if (rel_vx * px + rel_vy * py) > 0:
                clear = False
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
                            clear = False
                            break

    if clear:
        return Velocity(vx, vy)

    # Step 2: Sample candidate avoidance velocities around base angle
    cdef float base_angle = atan2(vy, vx)
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
                cand_speed = speed * (1.0 - s_step * 0.25)
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
                        rel_vx = 2.0 * cand_vx - (vx + nvx)
                        rel_vy = 2.0 * cand_vy - (vy + nvy)

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
                    diff_vx = cand_vx - vx
                    diff_vy = cand_vy - vy
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