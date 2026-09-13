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
    Ingests obstacle geometry into C structs, releases the GIL during tree exploration,
    and returns a reconstructed list of actionable Position models.
    """
    cdef int num_obstacles = len(obstacles)
    cdef RRTObstacle* c_obstacles = NULL
    cdef RRTNode* nodes = NULL
    cdef int* path_buf = NULL
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

    cdef object obs
    cdef int i, idx
    cdef int node_count = 0
    cdef bint found = False
    cdef int target_idx = -1
    cdef int nearest_idx, new_idx
    cdef float rnd_x, rnd_y, new_x, new_y
    cdef int iter_count, curr, path_len

    try:
        if num_obstacles > 0:
            c_obstacles = <RRTObstacle*>malloc(sizeof(RRTObstacle) * num_obstacles)
            if c_obstacles == NULL:
                raise MemoryError("Failed to allocate memory for obstacle buffer.")
            for i in range(num_obstacles):
                obs = obstacles[i]
                c_obstacles[i].x = float(obs[0])
                c_obstacles[i].y = float(obs[1])
                c_obstacles[i].w = float(obs[2])
                c_obstacles[i].l = float(obs[3])

        nodes = <RRTNode*>malloc(sizeof(RRTNode) * (max_iter + 2))
        if nodes == NULL:
            raise MemoryError("Failed to allocate memory for RRT node buffer.")

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

                if _is_segment_clear(nodes[nearest_idx].x, nodes[nearest_idx].y, new_x, new_y, c_obstacles, num_obstacles):
                    new_idx = node_count
                    nodes[new_idx].x = new_x
                    nodes[new_idx].y = new_y
                    nodes[new_idx].parent_idx = nearest_idx
                    node_count += 1

                    if hypotf(tx - new_x, ty - new_y) <= step_size:
                        if _is_segment_clear(new_x, new_y, tx, ty, c_obstacles, num_obstacles):
                            target_idx = node_count
                            nodes[target_idx].x = tx
                            nodes[target_idx].y = ty
                            nodes[target_idx].parent_idx = new_idx
                            node_count += 1
                            found = True
                            break

        if found:
            path_buf = <int*>malloc(sizeof(int) * (max_iter + 2))
            if path_buf == NULL:
                raise MemoryError("Failed to allocate memory for RRT path buffer.")

            path_len = 0
            curr = target_idx
            while curr > 0 and curr != -1:
                path_buf[path_len] = curr
                path_len += 1
                curr = nodes[curr].parent_idx

            for i in range(path_len - 1, -1, -1):
                idx = path_buf[i]
                result.append(Position(int(nodes[idx].x), int(nodes[idx].y)))

    finally:
        if c_obstacles != NULL:
            free(c_obstacles)
        if nodes != NULL:
            free(nodes)
        if path_buf != NULL:
            free(path_buf)

    return result