##### Refactor: Phase 09.04 - Optimization

**Overview**

Eliminate high-frequency Python overhead in the fluid and geography generation pipeline. Export edge normal orientations directly from the Cython sweep-line contour algorithm to bypass Python water probing, introduce an $O(1)$ spatial grid for layer water checks on `Board`, and replace $O(M \cdot N)$ iterative entity removals with single-pass collection filtering.

##### Inefficiencies: Python Overhead Bottlenecks in Cartographer

| Current Operation | Algorithmic Inefficiency |
| --- | --- |
| geometry.contours() -> Boundary | Normal vector information is discarded during interval XOR, forcing Python to probe board.water on both sides of every segment. |
| board.water() in Cartographer loop | Performs an O(N) scan over all layer fluids for every 32px step and interval midpoint. |
| board.remove(list(shores)) | O(M * N) linear list search across board._assets during layer re-sweeps. |

**1. Directed Contours in Cython (`libs.core.math.geometry`)**

In `geometry.pyx`, the sweep-line algorithm processes vertical and horizontal edge events with explicit entry/exit orientations:

* Vertical sweep: `v_events` with `+1` represents a **Left edge** (Land West, Water East $\to$ `Directions.LEFT`). `v_events` with `-1` represents a **Right edge** (Water West, Land East $\to$ `Directions.RIGHT`).
* Horizontal sweep: `h_events` with `+1` represents a **Bottom edge** (Land South, Water North $\to$ `Directions.DOWN`). `h_events` with `-1` represents a **Top edge** (Land North, Water South $\to$ `Directions.UP`).

Currently, `xor()` merges interval spans but strips this topological orientation, returning raw undirected `Boundary` objects with dimensions $(1, L)$ or $(W, 1)$. This forces `Cartographer._detect_boundary_orientation` in Python to sample coordinates on both sides of the segment via `board.water()` to reconstruct the normal vector.

**Proposal**: Refactor `geometry.contours()` to yield directed primitives: `(x, y, w, l, orientation)`. This completely eliminates `_detect_boundary_orientation` and all associated probe queries.

**2. $O(1)$ Water Grid Spatial Index on `Board`**

`Board.water()` executes an $O(N)$ linear scan over all fluid entities on the layer, checking stream corridors and annular pools. In `Cartographer._coalesce_segments`, `_is_step_water` queries `board.water` at multiple points across every 32px step. For dense rivers or multiple converging streams, this becomes an inner-loop bottleneck.

**Proposal**: Maintain an $O(1)$ spatial occupancy grid or bitmask on `Board` (`_cached_watermap[layer][(cx, cy)]`), populated during `Actuator.propagate()`. `Board.water()` becomes a constant-time lookup.

**3. Set-Based Entity De-registration on `Board`**

`Board.remove(removals)` iterates over `removals` and calls `self._assets.remove(asset)` and `self._cached_renderables[layer].remove(asset)`. Because `_assets` is a flat Python list of potentially thousands of entities, each call executes an $O(N)$ scan, resulting in $O(M \cdot N)$ complexity when purging large riverbanks ($M \ge 100$ shoreline segments).

**Proposal**: Transition internal entity tracking to fast ID lookup sets or replace iterative removals with single-pass filter comprehensions:

```python
removal_names = {a.name for a in removals}
self._assets = [a for a in self._assets if a.name not in removal_names]
```

##### Dependency Analysis

The `Perimeter` generator (`src/app/services/generators/game/perimeter.py`) derives the simply-connected outer boundary hull of an environment during layer bootstrapping/hydration and populates `board.perimeters[layer]`.

```python
# src/app/services/generators/game/perimeter.py
def generate(self, board: Board, layer: str) -> List[Boundary]:
    rects = self.extract(board, layer)
    if not rects:
        return []
    perimeter = geometry.contours(rects)
    return perimeter
```

**1. Downstream Coupling on `Boundary` Primitives**

`Perimeter.generate()` relies on `geometry.contours(rects)` returning concrete Cython extension type instances: `List[Boundary]`.

These `Boundary` objects are registered in `board.perimeters` and consumed across three distinct subsystems:

1. **`Actuator._collect_obstacles`**:

```python
perimeters = board.perimeters.get(layer, [])
for b in perimeters:
    # Expects .position and .dimensions attributes
    if direction == Directions.DOWN.value and (b.position.y <= fy): continue
    obstacle_tuples.append((b.position.x, b.position.y, b.dimensions.w, b.dimensions.l, None))

```

2. **`Cartographer._detect_flank_occlusions`**:

```python
perimeters = board.perimeters.get(layer, [])
for b in perimeters:
    bx, by = b.position.x, b.position.y
    bw, bl = b.dimensions.w, b.dimensions.l
    # Evaluates bounding intersections against map boundaries

```

3. **`NavigationMechanics` & Cython `physics.boundaries` / `constrain**`: Directly queries `Boundary.position` and `Boundary.dimensions` for spatial confinement and line-of-sight (`geometry.los`) raycasts.

**2. The Conflict with the Phase 09.04 Proposal**

In the Phase 09.04 optimization proposal:

> **Task 1: Cython Directed Contour Generation**
> *Objective*: Retain edge normal vectors during the sweep-line pass and eliminate Python boundary probing by refactoring `geometry.contours` to return `(x, y, w, l, orientation)` tuples.

If `geometry.contours` is modified directly to return primitive directed tuples `(x, y, w, l, orientation)`:

1. **Fatal Runtime Crash in `Perimeter` Consumers**: `Perimeter.generate()` would assign raw tuples into `board.perimeters[layer]`. On the subsequent frame, `Actuator`, `Cartographer`, `NavigationMechanics`, and `physics.boundaries` would raise:
`AttributeError: 'tuple' object has no attribute 'position'`
2. **Semantic Mismatch**: `Perimeter` computes the boundary of **solid dry terrain** (tiles + crafts + objects). In `Perimeter`, an edge's exterior points *away* from the map into void space, whereas in `Cartographer`, an edge's exterior points from *water onto dry substrate*. Forcing a shared "orientation" enum onto static map limits introduces conceptual drift into `Perimeter`.

###### Architectural Alternatives

* **Alternative A (Segregated C-Level Functions — Recommended)**:
Retain `geometry.contours(rects) -> List[Boundary]` unchanged for `Perimeter` and static boundary generation. Introduce a specialized `geometry.contours_directed(rects) -> List[Tuple[int, int, int, int, str]]` in `geometry.pyx` that shares the underlying C sweep-line kernel but outputs lightweight directed primitive tuples specifically for `Cartographer`.
    * *Advantage*: Zero risk of regressions across map physics, navigation, and `Perimeter`.
* **Alternative B (Universal Tuple Primitives with `Perimeter` Re-wrapping)**:
Refactor `geometry.contours(rects)` universally to return primitive integer tuples `(x, y, w, l, orientation)`. Update `Perimeter.generate()` to unpack the spatial components and explicitly instantiate `Boundary(Position(x, y), Dimensions(w, l))`.
    * *Advantage*: A single entry point in Cython; `Perimeter` adapts at bootstrap (where object instantiation overhead is negligible).

**SELECTION**: Option B!

##### Goal: Directed Contour Sweep in Cython

Refactor `libs.core.math.geometry.contours` to retain boundary normal vectors during sweep-line interval derivation, returning directed boundary primitives directly to `Cartographer`.

```cython
# libs/core/math/geometry.pyx
cpdef list contours_directed(list rects):
    """
    Executes a 2-pass Sweep-Line algorithm over primitive AABBs.
    Returns directed boundary segments (x, y, w, l, direction)
    preserving edge outward normals without secondary spatial probing.
    """
    ...
```

##### Goal: Board Spatial Water Grid Cache

Implement an $O(1)$ spatial tile-bucket cache for water corridors and pools on `Board`, updated during `Actuator.propagate()` and cleared during layer invalidation.

```python
# app/game/board.py
class Board:
    _cached_watermap: Dict[str, Set[Tuple[int, int]]]

    def water(self, layer: str, position: Position, exclude: Optional[str] = None) -> bool:
        if not exclude:
            cx = int(position.x) // settings.TILE_HASH_SIZE
            cy = int(position.y) // settings.TILE_HASH_SIZE
            return (cx, cy) in self._cached_watermap.get(layer, set())
        # Fallback to precise bounding-box evaluation when entity exclusion is required
        ...

```

##### Tasks

**1. Task: Cython Directed Contour Generation**

*Objective*: Retain edge normal vectors during the sweep-line pass and eliminate Python boundary probing.

* [x] Subtask: Refactor `geometry.contours` in `src/libs/core/math/geometry.pyx` to return `(x, y, w, l, orientation)` tuples.
* [x] Subtask: Remove `Cartographer._detect_boundary_orientation` in `src/app/services/generators/game/cartographer.py`.
* [x] Subtask: Update `Cartographer.generate` to ingest directed boundary segments directly into descriptor generation.

**2. Task: Constant-Time Environmental Water Caching**

*Objective*: Replace $O(N)$ linear fluid bounding box checks with an $O(1)$ spatial coordinate hash.

* [x] Subtask: Add `_cached_watermap: Dict[str, Set[Tuple[int, int]]]` to `Board` in `src/app/game/board.py`.
* [x] Subtask: Populate `_cached_watermap` during `Board._cache()` and when `Actuator.propagate()` updates fluid states.
* [x] Subtask: Optimize `Board.water()` to query `_cached_watermap` for unexcluded coordinate checks.

**3. Task: Bulk Entity Mutation on Board**

*Objective*: Eliminate $O(M \cdot N)$ list scans during `Cartographer.purge` and multi-entity removals.

* [x] Subtask: Refactor `Board.remove()` to use set-membership list comprehensions across `_assets` and `_cached_renderables`.
* [!] Subtask: Benchmark frame execution times during gate switch invalidations to verify zero-hitch shoreline regeneration.

**4. Task: Adapt Perimeter Boundary Generation for Contour Refactoring**

*Objective*: Update `Perimeter.generate` to preserve the `List[Boundary]` contract on `Board.perimeters` following contour sweep optimizations.

- [x] Subtask: Verify whether `geometry.contours` returns primitive tuples or concrete `Boundary` objects.
- [x] Subtask: If primitive tuples are returned, unpack `(x, y, w, l, *_)` in `Perimeter.generate` and construct `Boundary(Position(x, y), Dimensions(w, l))` instances.
- [x] Subtask: Add unit tests verifying `board.perimeters[layer]` retains typed `Boundary` models with valid `.position` and `.dimensions` attributes after layer extraction.