##### Refactor: Phase 09.04 - Optimization

**Overview** 

- Cythonize math in Actuator and Cartographer.

### Documentation Divergences

#### Draft: Shoreline Cardinal Orientation Alignment

* **Page**: `docs/01-assets.md`
* **Heading**: `Geography > Shorelines`

##### Drift

The documentation specifies `orientation` using geographical string literals (`north`, `west`, `south`, `east`), whereas the runtime implementation in `src/app/models/state/geography.py`, `ShorelineFrame`, `Cartographer`, and `fields.py` strictly uses `Directions` enum members (`up`, `left`, `down`, `right`).

##### Update

```markdown
### Shorelines

Shorelines are procedural, inanimate Geography sensors instantiated along unoccluded environmental water margins. Rather than belonging to individual fluid emitters, Shorelines are derived at the layer level: `FluidMechanics` aggregates all active fluid streams and annular pools on a layer, derives the outer perimeter hull via `geometry.contours()`, samples bordering substrate tiles from `Board`, and coalesces contiguous segments into cohesive shoreline entities.

**Frame: ShorelineFrame**

* Indexes 4 cardinal orientation rows:
    * Row 0: `up`    (Land North/Up, Water South/Down)
    * Row 1: `left`  (Land West/Left, Water East/Right)
    * Row 2: `down`  (Land South/Down, Water North/Up)
    * Row 3: `right` (Land East/Right, Water West/Left)
* `keys(id, state)` emits repeating full tiles along `state.length` and a fractional distal slice for remainders.

**State: ShorelineState**

* `layer: str`
* `position: Position`
* `orientation: str` (`up`, `left`, `down`, `right`)
* `length: int`
* `thickness: int`
* `bidirectional: bool = True`
* `hitboxes: List[Hitbox]`

```

---

#### Draft: Board Shorelines and Mass Filter Clarification

* **Page**: `docs/00-overview.md`
* **Heading**: `Application > Board`

##### Drift

`docs/00-overview.md` omits the public layer-scoped shoreline metadata interfaces (`board.shorelines`, `board.get_shorelines()`) introduced during Phase 09.03.03. Furthermore, `board.weights(layer)` is documented as returning assets with "positive mass", whereas the implementation queries non-negative mass (`asset.properties.mass >= 0`), which includes static bodies ($m = 0$).

##### Update

```markdown
**Interface: Queries**

The Board exposes spatial queries to evaluate dynamic environmental fields:

* Hierarchy Queries
    - `board.instances(key, layer)`: Returns a List of Assets on the given layer, filtered by Instance `key`.
    - `board.categories(key, layer)`: Returns a List of Assets on the given layer, filtered by Category `key`.
    - `board.get_shorelines(layer=None)`: Retrieves active procedural shoreline assets for a specific layer or across all layers.
* Physics Queries
    - `board.weights(layer)`: Returns a list of Assets with non-negative mass (\(m \ge 0\)) on the given layer (includes static and dynamic bodies; excludes sensors).
    - `board.obstacles(layer)`: Returns a list of Assets that qualify as Obstacles.
* Environment Queries
    - `board.tile(layer, position, instance)`: Retrieves background or foreground [Tiles](./01-assets.md#tiles) via \(O(1)\) spatial hash lookup.
    - `board.water(layer, position, exclude=None)`: Evaluates whether a coordinate intersects any active [Fluid](./01-assets.md#fluids) stream or annular pool across the layer, with an optional entity exclusion filter.

```

---

### Optimization & Cythonization Analysis (Phase 09.04)

```
+-----------------------------------------------------------------------------------+
| Python Overhead Bottlenecks in Cartographer                                       |
+------------------------------------+----------------------------------------------+
| Current Operation                  | Algorithmic Inefficiency                     |
+------------------------------------+----------------------------------------------+
| geometry.contours() -> Boundary    | Normal vector information is discarded during|
|                                    | interval XOR, forcing Python to probe        |
|                                    | board.water on both sides of every segment.  |
+------------------------------------+----------------------------------------------+
| board.water() in Cartographer loop | Performs an O(N) scan over all layer fluids  |
|                                    | for every 32px step and interval midpoint.   |
+------------------------------------+----------------------------------------------+
| board.remove(list(shores))         | O(M * N) linear list search across           |
|                                    | board._assets during layer re-sweeps.        |
+------------------------------------+----------------------------------------------+

```

#### 1. Directed Contours in Cython (`libs.core.math.geometry`)

In `geometry.pyx`, the sweep-line algorithm processes vertical and horizontal edge events with explicit entry/exit orientations:

* Vertical sweep: `v_events` with `+1` represents a **Left edge** (Land West, Water East $\to$ `Directions.LEFT`). `v_events` with `-1` represents a **Right edge** (Water West, Land East $\to$ `Directions.RIGHT`).
* Horizontal sweep: `h_events` with `+1` represents a **Bottom edge** (Land South, Water North $\to$ `Directions.DOWN`). `h_events` with `-1` represents a **Top edge** (Land North, Water South $\to$ `Directions.UP`).

Currently, `xor()` merges interval spans but strips this topological orientation, returning raw undirected `Boundary` objects with dimensions $(1, L)$ or $(W, 1)$. This forces `Cartographer._detect_boundary_orientation` in Python to sample coordinates on both sides of the segment via `board.water()` to reconstruct the normal vector.

**Proposal**: Refactor `geometry.contours()` to yield directed primitives: `(x, y, w, l, orientation)`. This completely eliminates `_detect_boundary_orientation` and all associated probe queries.

#### 2. $O(1)$ Water Grid Spatial Index on `Board`

`Board.water()` executes an $O(N)$ linear scan over all fluid entities on the layer, checking stream corridors and annular pools. In `Cartographer._coalesce_segments`, `_is_step_water` queries `board.water` at multiple points across every 32px step. For dense rivers or multiple converging streams, this becomes an inner-loop bottleneck.

**Proposal**: Maintain an $O(1)$ spatial occupancy grid or bitmask on `Board` (`_cached_watermap[layer][(cx, cy)]`), populated during `Actuator.propagate()`. `Board.water()` becomes a constant-time lookup.

#### 3. Set-Based Entity De-registration on `Board`

`Board.remove(removals)` iterates over `removals` and calls `self._assets.remove(asset)` and `self._cached_renderables[layer].remove(asset)`. Because `_assets` is a flat Python list of potentially thousands of entities, each call executes an $O(N)$ scan, resulting in $O(M \cdot N)$ complexity when purging large riverbanks ($M \ge 100$ shoreline segments).

**Proposal**: Transition internal entity tracking to fast ID lookup sets or replace iterative removals with single-pass filter comprehensions:

```python
removal_names = {a.name for a in removals}
self._assets = [a for a in self._assets if a.name not in removal_names]

```

---

### Backlog Proposals

#### Backlog: Phase 09.04 - Fluid & Geography Optimization

**Overview**

Eliminate high-frequency Python overhead in the fluid and geography generation pipeline. Export edge normal orientations directly from the Cython sweep-line contour algorithm to bypass Python water probing, introduce an $O(1)$ spatial grid for layer water checks on `Board`, and replace $O(M \cdot N)$ iterative entity removals with single-pass collection filtering.

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

* [ ] Subtask: Refactor `geometry.contours` in `src/libs/core/math/geometry.pyx` to return `(x, y, w, l, orientation)` tuples.
* [ ] Subtask: Remove `Cartographer._detect_boundary_orientation` in `src/app/services/generators/game/cartographer.py`.
* [ ] Subtask: Update `Cartographer.generate` to ingest directed boundary segments directly into descriptor generation.

**2. Task: Constant-Time Environmental Water Caching**

*Objective*: Replace $O(N)$ linear fluid bounding box checks with an $O(1)$ spatial coordinate hash.

* [ ] Subtask: Add `_cached_watermap: Dict[str, Set[Tuple[int, int]]]` to `Board` in `src/app/game/board.py`.
* [ ] Subtask: Populate `_cached_watermap` during `Board._cache()` and when `Actuator.propagate()` updates fluid states.
* [ ] Subtask: Optimize `Board.water()` to query `_cached_watermap` for unexcluded coordinate checks.

**3. Task: Bulk Entity Mutation on Board**

*Objective*: Eliminate $O(M \cdot N)$ list scans during `Cartographer.purge` and multi-entity removals.

* [ ] Subtask: Refactor `Board.remove()` to use set-membership list comprehensions across `_assets` and `_cached_renderables`.
* [ ] Subtask: Benchmark frame execution times during gate switch invalidations to verify zero-hitch shoreline regeneration.

---

#### Backlog: Phase 09.05 - Bridges, Bifurcation & Buoyancy

**Overview**

Expand the environmental mechanics to support recursive stream bifurcation across orthogonal axes, elevate characters and frictive assets over fluids via static architectural bridges, and generalize buoyancy properties across dynamic bodies.

##### Goal: Generic Buoyancy Mechanics

Decouple floating velocity assignment in `fields.py` from `AssetInstances.CRATES.value` by introducing a `buoyant: bool` property on dynamic objects ($m > 0$).

```python
# app/models/properties.py
@dataclass(slots=True)
class ObjectProperties(AssetProperties):
    dimensions: Dimensions
    mass: int = 0
    count: int = 1
    hitboxes: Optional[List[Hitbox]] = field(default_factory=list)
    buoyant: bool = False

```

##### Goal: Architectural Bridges and Elevation Decks

Introduce static bridge assets that define elevated surface planes across fluid corridors, intercepting character entities to suppress fluid velocity impulses and shoreline ledge drops.

```python
# app/game/logic/modules/motion/fields.py
# Bridges act as static surface interceptors, similar to Rafts but immovable (m = 0)
for bridge in layer_bridges:
    if _intersects(asset, bridge):
        on_bridge = True
        asset.state.mutators.triggers.submerged = False
        break

```

##### Tasks

**1. Task: Generalize Dynamic Buoyancy**

*Objective*: Allow any dynamic object to float in fluid currents based on properties rather than instance whitelisting.

* [ ] Subtask: Add `buoyant: bool = False` to `ObjectProperties` in `src/app/models/properties.py`.
* [ ] Subtask: Refactor `fields.py` to check `asset.properties.buoyant` when applying stream velocity and suppressing tile friction.

**2. Task: Static Bridge Surface Interception**

*Objective*: Prevent fluid immersion and shoreline triggering when traversing fluid streams via bridges.

* [ ] Subtask: Create `Bridge` instance under `Objects` hierarchy with static mass ($m = 0$).
* [ ] Subtask: Update `fields.update()` to evaluate Bridge intersections prior to shoreline and fluid immersion checks.

**3. Task: Recursive Stream Bifurcation**

*Objective*: Enable fluids striking static obstacles to branch into secondary corridors when unobstructed.

* [ ] Subtask: Implement orthogonal branch raycasting in `Actuator` when an obstacle is struck and `flow > 1`.
* [ ] Subtask: Partition compound hitboxes across bifurcated child streams.
* [ ] Subtask: Verify layer water rectangle collection ingests bifurcated branches for seamless contour shoreline generation.