#### Refactor: Phase 09.06 - Cythonization

**Overview**

Eliminate per-frame Python interpretation overhead and garbage collection pressure in environmental field processing by moving sensor detection, point-in-stream lookups, and shoreline occlusions into Cython. Leverage the bipartite negative-ID hashing pattern in `libs/core/math/space.pyx` to evaluate bridges, rafts, shorelines, and fluid immersion in $O(N + M)$ time.

##### Goal: Point-in-AABB and Batch Occlusion Kernels in `geometry.pyx`

Expose compiled C-level primitives in `libs/core/math/geometry.pyx` for scalar point containment and batch AABB occlusion.

```cython
cpdef bint inside(int px, int py, list aabbs):
    cdef tuple box
    cdef int x1, y1, x2, y2
    for box in aabbs:
        x1 = box[0]
        y1 = box[1]
        x2 = box[2]
        y2 = box[3]
        if x1 <= px < x2 and y1 <= py < y2:
            return True
    return False

cpdef bint occluded(int qx, int qy, int qw, int ql, list obstacles):
    cdef tuple obs
    cdef int ox, oy, ow, ol
    for obs in obstacles:
        ox = obs[0]
        oy = obs[1]
        ow = obs[2]
        ol = obs[3]
        if qx < ox + ow and qx + qw > ox and qy < oy + ol and qy + ql > oy:
            return True
    return False

```

##### Goal: Bipartite Environmental Field Broad-Phase in `physics.pyx`

Implement a C-level broad-phase and narrow-phase query in `libs/core/math/physics.pyx` modeling environmental sensors as negative IDs in `Space`.

```cython
cpdef list environment(list assets, list fields, Space grid):
    """
    Evaluates candidate intersections between dynamic entities (positive IDs)
    and environmental field sensors (negative IDs).
    Returns list of (asset_index, field_index) tuples.
    """
    grid.clear()
    cdef tuple f_data, a_data
    cdef int i, id_a, id_b, asset_idx, field_idx
    cdef list matches = []

    for i in range(len(fields)):
        f_data = fields[i]
        grid.insert(-i - 1, f_data[1], f_data[2], f_data[3], f_data[4])

    for a_data in assets:
        grid.insert(a_data[0], a_data[1], a_data[2], a_data[3], a_data[4])

    cdef list candidate_pairs = grid.query()
    for pair in candidate_pairs:
        id_a = pair[0]
        id_b = pair[1]
        if (id_a < 0 and id_b >= 0) or (id_a >= 0 and id_b < 0):
            asset_idx = id_b if id_a < 0 else id_a
            field_idx = (-id_a - 1) if id_a < 0 else (-id_b - 1)
            
            a_data = assets[asset_idx]
            f_data = fields[field_idx]
            
            if bounded(a_data[1], a_data[2], a_data[5], f_data[1], f_data[2], f_data[3], f_data[4]) is not None:
                matches.append((asset_idx, field_idx))

    return matches

```

##### Goal: Streamlined Field Resolution in `fields.py` and Spatial Caches

Update `Board._cached_watermap` to store flattened primitive rectangles `(min_x, min_y, max_x, max_y)` directly in spatial buckets. Refactor `fields.py` to ingest intersection lists from `physics.environmental_intersections` rather than evaluating $O(N \times M)$ pairwise Python intersections.

##### Tasks

**1. Task: Geometric Spatial Kernels**

*Objective*: Implement and export compiled scalar containment and batch occlusion functions in `libs/core/math/geometry.pyx`.

* [x] Subtask: Implement `inside(int px, int py, list aabbs) -> bint` in `libs/core/math/geometry.pyx`.
* [x] Subtask: Implement `occluded(int qx, int qy, int qw, int ql, list obstacles) -> bint` in `libs/core/math/geometry.pyx`.
* [x] Subtask: Add Cython declarations for both functions to `libs/core/math/geometry.pxd`.
* [ ] Subtask: Write unit tests verifying point containment and occlusion edge cases.

**2. Task: Bipartite Environmental Field Query**

*Objective*: Implement `environment` in `libs/core/math/physics.pyx` using `Space` bipartite indexing.

* [x] Subtask: Add `environmental_intersections(list asset_primitives, list field_primitives, Space grid) -> list` to `libs/core/math/physics.pyx`.
* [x] Subtask: Export declaration in `libs/core/math/physics.pxd`.
* [x] Subtask: Allocate and persist a `Space` instance on `MotionMechanics` to avoid per-frame grid allocation.
* [ ] Subtask: Write unit tests validating bipartite retrieval against bridges, rafts, shorelines, and fluids.

**3. Task: Pipeline Refactoring**

*Objective*: Connect compiled kernels to `Board`, `Cartographer`, and `fields.py`.

* [x] Subtask: Refactor `Board._in_stream()` and `Board.fluid()` to use `geometry.point_in_aabbs`.
* [x] Subtask: Refactor `Cartographer._detect_flank_occlusions()` to delegate to `geometry.occluded`.
* [x] Subtask: Refactor `fields.update()` to query environmental overlaps via `physics.environmental_intersections`.