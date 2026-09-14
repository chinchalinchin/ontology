"""
# Ontology: libs.core.math.paths
"""
# cython: language_level=3
from libc.math cimport fabsf, fminf, fmaxf, atan2f, cosf, sinf, hypotf
from libc.stdlib cimport malloc, free, rand, RAND_MAX

from libs.core.models cimport Position
from libs.core.math.geometry cimport c_punctures
from libs.core.math.paths cimport RRTNode, RRTObstacle


cdef inline bint _is_segment_clear(
    float x1, 
    float y1, 
    float x2, 
    float y2, 
    RRTObstacle* obstacles, 
    int num_obstacles
) noexcept nogil:
    cdef int i
    for i in range(num_obstacles):
        if c_punctures(x1, y1, x2, y2, obstacles[i].x, obstacles[i].y, obstacles[i].w, obstacles[i].l):
            return False
    return True


cdef inline void _sample_point(
    float min_x, 
    float max_x, 
    float min_y, 
    float max_y, 
    float tx, 
    float ty, 
    float* out_x, 
    float* out_y
) noexcept nogil:
    cdef float roll = rand() / (RAND_MAX * 1.0)
    if roll <= 0.05:
        out_x[0] = tx
        out_y[0] = ty
    else:
        out_x[0] = min_x + (rand() / (RAND_MAX * 1.0)) * (max_x - min_x)
        out_y[0] = min_y + (rand() / (RAND_MAX * 1.0)) * (max_y - min_y)


cdef inline int _get_nearest_node_idx(
    RRTNode* nodes, 
    int num_nodes, 
    float qx, 
    float qy
) noexcept nogil:
    cdef int best_idx = 0
    cdef float dx = nodes[0].x - qx
    cdef float dy = nodes[0].y - qy
    cdef float best_dist_sq = dx * dx + dy * dy
    cdef float cur_dist_sq
    cdef int i

    for i in range(1, num_nodes):
        dx = nodes[i].x - qx
        dy = nodes[i].y - qy
        cur_dist_sq = dx * dx + dy * dy
        if cur_dist_sq < best_dist_sq:
            best_dist_sq = cur_dist_sq
            best_idx = i

    return best_idx


cdef inline void _steer(
    float from_x, 
    float from_y, 
    float to_x, 
    float to_y, 
    float step_size, 
    float* out_x, 
    float* out_y
) noexcept nogil:
    cdef float theta = atan2f(to_y - from_y, to_x - from_x)
    out_x[0] = from_x + step_size * cosf(theta)
    out_y[0] = from_y + step_size * sinf(theta)


cdef inline int _prune_path(
    int* forward_buf,
    int forward_len,
    int* pruned_buf,
    RRTNode* nodes,
    RRTObstacle* c_obstacles,
    int num_obstacles
) noexcept nogil:
    """
    Zero-allocation greedy raycast string-pulling (nogil).
    Scans forward from current anchor index to the furthest unobstructed waypoint,
    collapsing intermediate collinear and redundant vertices.
    """
    cdef int pruned_len = 0
    cdef int anchor_idx = 0
    cdef int scan_idx
    cdef bint clear

    if forward_len <= 0:
        return 0

    pruned_buf[pruned_len] = forward_buf[0]
    pruned_len += 1

    while anchor_idx < forward_len - 1:
        scan_idx = forward_len - 1
        clear = False
        while scan_idx > anchor_idx + 1:
            if _is_segment_clear(
                nodes[forward_buf[anchor_idx]].x,
                nodes[forward_buf[anchor_idx]].y,
                nodes[forward_buf[scan_idx]].x,
                nodes[forward_buf[scan_idx]].y,
                c_obstacles,
                num_obstacles
            ):
                clear = True
                break
            scan_idx -= 1

        if clear:
            pruned_buf[pruned_len] = forward_buf[scan_idx]
            pruned_len += 1
            anchor_idx = scan_idx
        else:
            anchor_idx += 1
            pruned_buf[pruned_len] = forward_buf[anchor_idx]
            pruned_len += 1

    return pruned_len


cpdef list rrt(
    float sx, 
    float sy, 
    float tx, 
    float ty, 
    list obstacles, 
    float step_size = 32.0, 
    int max_iter = 300
):
    """
    Zero-allocation Rapidly-exploring Random Tree (RRT) pathfinding engine.
    Ingests obstacle geometry into C structs, culls non-local obstacles outside the
    search window, releases the GIL during tree exploration, prunes waypoints via
    raycast string-pulling, and returns a reconstructed list of actionable Position models.
    """
    cdef int num_obstacles = len(obstacles)
    cdef RRTObstacle* c_obstacles = NULL
    cdef RRTNode* nodes = NULL
    cdef int* path_buf = NULL
    cdef int* forward_buf = NULL
    cdef int* pruned_buf = NULL
    cdef list result = []

    if max_iter <= 0:
        return result

    # AABB search bounds with 20% padding + 2 steps buffer
    cdef float pad_w = fabsf(tx - sx) * 0.2 + step_size * 2.0
    cdef float pad_h = fabsf(ty - sy) * 0.2 + step_size * 2.0
    cdef float min_x = fminf(sx, tx) - pad_w
    cdef float max_x = fmaxf(sx, tx) + pad_w
    cdef float min_y = fminf(sy, ty) - pad_h
    cdef float max_y = fmaxf(sy, ty) + pad_h

    # Fallback padding adjustments when bounds clamp to map boundaries (origin 0, 0)
    if min_x < 0.0:
        max_x += fabsf(min_x)
        min_x = 0.0
    if min_y < 0.0:
        max_y += fabsf(min_y)
        min_y = 0.0

    cdef object obs
    cdef int i, idx
    cdef int culled_count = 0
    cdef float ox, oy, ow, ol

    # Broad-phase search-space obstacle partitioning: count intersecting AABBs
    if num_obstacles > 0:
        for i in range(num_obstacles):
            obs = obstacles[i]
            ox = float(obs[0])
            oy = float(obs[1])
            ow = float(obs[2])
            ol = float(obs[3])
            if (ox + ow >= min_x and ox <= max_x and
                oy + ol >= min_y and oy <= max_y):
                culled_count += 1

    cdef int node_count = 0
    cdef bint found = False
    cdef int target_idx = -1
    cdef int nearest_idx, new_idx
    cdef float rnd_x, rnd_y, new_x, new_y
    cdef int iter_count, curr, path_len, forward_len, pruned_len

    try:
        # Pack only search-space intersecting obstacles into contiguous C-buffer
        if culled_count > 0:
            c_obstacles = <RRTObstacle*>malloc(sizeof(RRTObstacle) * culled_count)
            if c_obstacles == NULL:
                raise MemoryError("Failed to allocate memory for culled obstacle buffer.")
            idx = 0
            for i in range(num_obstacles):
                obs = obstacles[i]
                ox = float(obs[0])
                oy = float(obs[1])
                ow = float(obs[2])
                ol = float(obs[3])
                if (ox + ow >= min_x and ox <= max_x and
                    oy + ol >= min_y and oy <= max_y):
                    c_obstacles[idx].x = ox
                    c_obstacles[idx].y = oy
                    c_obstacles[idx].w = ow
                    c_obstacles[idx].l = ol
                    idx += 1

        nodes = <RRTNode*>malloc(sizeof(RRTNode) * (max_iter + 2))
        if nodes == NULL:
            raise MemoryError("Failed to allocate memory for RRT node buffer.")

        path_buf = <int*>malloc(sizeof(int) * (max_iter + 2))
        if path_buf == NULL:
            raise MemoryError("Failed to allocate memory for RRT path buffer.")

        forward_buf = <int*>malloc(sizeof(int) * (max_iter + 2))
        if forward_buf == NULL:
            raise MemoryError("Failed to allocate memory for forward buffer.")

        pruned_buf = <int*>malloc(sizeof(int) * (max_iter + 2))
        if pruned_buf == NULL:
            raise MemoryError("Failed to allocate memory for pruned buffer.")

        # Root node
        nodes[0].x = sx
        nodes[0].y = sy
        nodes[0].parent_idx = -1
        node_count = 1

        with nogil:
            for iter_count in range(max_iter):
                _sample_point(min_x, max_x, min_y, max_y, tx, ty, &rnd_x, &rnd_y)
                nearest_idx = _get_nearest_node_idx(nodes, node_count, rnd_x, rnd_y)
                _steer(nodes[nearest_idx].x, nodes[nearest_idx].y, rnd_x, rnd_y, step_size, &new_x, &new_y)

                if _is_segment_clear(nodes[nearest_idx].x, nodes[nearest_idx].y, new_x, new_y, c_obstacles, culled_count):
                    new_idx = node_count
                    nodes[new_idx].x = new_x
                    nodes[new_idx].y = new_y
                    nodes[new_idx].parent_idx = nearest_idx
                    node_count += 1

                    if hypotf(tx - new_x, ty - new_y) <= step_size:
                        if _is_segment_clear(new_x, new_y, tx, ty, c_obstacles, culled_count):
                            target_idx = node_count
                            nodes[target_idx].x = tx
                            nodes[target_idx].y = ty
                            nodes[target_idx].parent_idx = new_idx
                            node_count += 1
                            found = True
                            break

            if found:
                # 1. Backtrace from target_idx to root node 0 (parent_idx == -1)
                path_len = 0
                curr = target_idx
                while curr != -1:
                    path_buf[path_len] = curr
                    path_len += 1
                    curr = nodes[curr].parent_idx

                # 2. Reverse index chain to obtain forward route: start -> target
                forward_len = path_len
                for i in range(path_len):
                    forward_buf[i] = path_buf[path_len - 1 - i]

                # 3. Greedy string-pulling pruning pass (nogil)
                pruned_len = _prune_path(
                    forward_buf,
                    forward_len,
                    pruned_buf,
                    nodes,
                    c_obstacles,
                    culled_count
                )

        # 4. Construct Position instances across Python boundary
        if found and pruned_len > 1:
            for i in range(1, pruned_len):
                idx = pruned_buf[i]
                result.append(Position(int(nodes[idx].x), int(nodes[idx].y)))

    finally:
        if c_obstacles != NULL:
            free(c_obstacles)
        if nodes != NULL:
            free(nodes)
        if path_buf != NULL:
            free(path_buf)
        if forward_buf != NULL:
            free(forward_buf)
        if pruned_buf != NULL:
            free(pruned_buf)

    return result