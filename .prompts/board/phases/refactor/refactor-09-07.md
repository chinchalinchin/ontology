#### Phase 09.07: Hydrological Frame Caching & Reactive Invalidation

The following command was run to profile the application runtime,

```bash
python -m cProfile -o engine_run.pstats src/cli.py start world-01
gprof2dot -f pstats engine_run.pstats --node-thres=1.0 --edge-thres=0.5
```
The results are summarized below,

| Subsystem / Function | % Total Time | Call Count | Hotspot Nature | Root Cause & Architectural Impact |
| --- | --- | --- | --- | --- |
| **`screen:220:draw`** | **17.64%** *(10.48% self)* | 868 | Inner-loop allocation & sorting | Evaluates dynamic tuple sort keys via lambda closures every frame; repeatedly decomposes static entities into millions of primitive tuples. |
| **`effects:134:keys` (`FluidFrame`)** | **3.79%** *(2.71% self)* | 3,472 | Decomposition churn | Emitted **1,042,468 `list.append` calls** recomputing static directional stream and annular pool slices on every tick, even when flow and geometry are static. |
| **`geography:93:keys` (`CardinalFrame`)** | **2.05%** *(1.25% self)* | 18,228 | Redundant slice generation | Emitted **578,956 `list.append` calls** calculating invariant cardinal slices for static, immutable Shoreline sensors on every frame. |
| **`engine:84:time` / `perf_counter**` | **3.66%** *(2.38% self)* | 1,840,915 | Busy-wait spin lock | Hybrid frame pacer executed **~76,700 calls/second** inside a tight `while` loop, thrashing CPU cycles to bridge sub-millisecond deltas. |
| **`fluid:74:update` $\to$ `Cartographer**` | **2.55%** *(2.35% in generate)* | 1,028 | Unfiltered reactive invalidation | Gates on active layers triggered full layer fluid invalidation and sweep-line contour derivation twice within 326ms without checking spatial intersection. |

**Overview**

Remediate runtime bottlenecks identified in profiling runs across rendering, hydrological evaluation, and frame pacing. Introduce memoized frame-key caching on static hydrological structures (`FluidFrame`, `CardinalFrame`), spatial boundary filtering and debouncing for reactive fluid invalidation in `FluidMechanics`, and calibrate the engine spin-lock pacer.

##### Architectural Analysis

The runtime profile of the `Ontology` engine reveals four distinct bottlenecks across three execution phases:

1. **Inner-Loop Engine Pacing (`Engine.start`)**: The pacer invokes `perf_counter` ~76,700 times/second in an unyielding `while` spin-lock, pegging CPU utilization to bridge sub-millisecond deltas.
2. **Dynamic Sort Key Allocation (`Screen.draw`)**: On every frame, an inline `lambda` closure re-allocates transient tuples for every renderable entity during Painter's Algorithm Z-sorting.
3. **Decomposition Churn (`FluidFrame.keys` & `CardinalFrame.keys`)**: Static shoreline margins and unchanging fluid corridors recompute geometry, string formatting, and tile offsets on every tick, emitting over 1.6 million `list.append` allocations per session.
4. **Unfiltered Reactive Invalidation (`FluidMechanics.update` $\to$ `Cartographer.generate`)**: Any gate state mutation triggers an unconditional full-layer wipe and sweep-line contour derivation (`geometry.contours`), recalculating 42+ transient shorelines even when the obstacle is spatially decoupled from the hydrological network.

##### Bug Reports

###### Bug B003: Painter's Algorithm String Exception

**STATUS**: OPEN
**SEVERITY**: Medium

**Description**

In `Screen.draw()`, assets are sorted using:

```python
assets.sort(key=lambda a: (
    a.state.height if a.state.height is not None else (
        (a.state.position.y + (a.dimensions.l if a.dimensions else 0))
    ),
    a.state.depth
))

```

`AssetState.height` is typed as `Optional[Union[int, str]]`. When an asset possesses a string-based height (e.g., from compositional late-binding), Python's Timsort evaluates comparisons between `str` and `int`, raising `TypeError: '<' not supported between instances of 'str' and 'int'`.

**Steps to Replicate**

Deploy an asset with an explicit `height: "0"` or string token alongside standard assets with geometric integer heights, then trigger `Screen.draw()`.

**Proposed Remediation**

Coerce `state.height` to integer in the sort key helper: `int(state.height) if state.height is not None else ...`.

###### Bug B014: FluidFrame Stale Cache via Eager Actuator Dirty Reset

**STATUS**: OPEN
**SEVERITY**: High

**Description**

`Actuator.propagate()` unconditionally sets `fluid.state.dirty = False` at the end of execution. Because `FluidMechanics.update()` executes during `Engine._play()`, `state.dirty` is reset before `Screen.draw()` calls `FluidFrame.keys()` during `Engine._render()`. Any memoization checking `if state.dirty:` inside `FluidFrame.keys()` fails to detect changes, resulting in stale rendered stream corridors.

**Steps to Replicate**

Memoize `FluidFrame.keys()` relying on `state.dirty` for cache eviction, mutate a gate obstacle, and observe that water graphics do not update to match physical hitboxes.

**Proposed Remediation**

Invalidate `fluid.state._cached_frame_keys` directly within `Actuator.propagate()` or `FluidMechanics.update()` when geometry is updated.

##### Goal: Memoized Frame-Key Caching for Invariant Entities

Eliminate decomposition churn by storing pre-computed frame-key tuples on state models:

* Add `_keys: Optional[List[Tuple[str, int, int]]] = None` to `ShorelineState`. Since shorelines are immutable once generated, compute once on initial evaluation in `CardinalFrame.keys()` and return in $O(1)$ time.
* Add `_keys: Dict[int, List[Tuple[str, int, int]]] = field(default_factory=dict)` to `FluidState`. Compute frame keys per animation frame index. Invalidate the dictionary in `Actuator.propagate()` when geometry is recomputed.

```python
# CardinalFrame.keys
if state._cached_keys is not None:
    return state._cached_keys
state._cached_keys = frame_keys
return state._cached_keys

# FluidFrame.keys
frame_idx = state.animation.frame
if frame_idx in state._cached_frame_keys:
    return state._cached_frame_keys[frame_idx]
state._cached_frame_keys[frame_idx] = frame_keys
return frame_keys
```

##### Goal: Spatial Bounding & Debouncing for Fluid Invalidation

Prevent unnecessary layer-wide fluid propagation and shoreline regeneration:

* **Spatial Bounding**: Filter gate invalidations by checking if the mutating obstacle's AABB intersects active fluid hitboxes (`fluid.hitboxes`) or the fluid corridor raycast before flagging `fluid.state.dirty = True`.
* **Shift Detection**: Compare updated stream lengths, pools, and branches post-propagation. If fluid geometry is identical, bypass `Cartographer.purge()` and `Cartographer.generate()`.
* **Debounce Window**: Introduce `settings.FLUID_INVALIDATION_DEBOUNCE_TICKS` to coalesce rapid gate toggling.

##### Goal: Calibrated Frame Pacing & Spin-Lock Tuning

Replace busy-waiting in `Engine.start()` with cooperative thread-yielding via `time.sleep(0)` within the spin loop, and evaluate tuning `settings.SPIN_RATE` to eliminate CPU core saturation while maintaining 60 FPS delivery.

##### Goal: Pre-Sorted Rendering & Reduced Allocation in Screen.draw

Replace the inline `lambda` closure in `Screen.draw()` and `Screen.export_map()` with a standalone sort function `_sort(asset)`. Coerce `height` to `int` when present to eliminate `Bug B003` (`TypeError` on mixed string/integer heights).

##### Tasks

**1. Task: State Model Cache Slots & Memoization**

*Objective*: Eliminate repeated dynamic key decomposition for static shoreline margins and unchanged fluid corridors.

* [x] Subtask: Add `_keys: Optional[List[Tuple[str, int, int]]] = None` to `ShorelineState` in `src/app/models/state/assets/geography.py`.
* [x] Subtask: Add `_keys: Dict[int, List[Tuple[str, int, int]]] = field(default_factory=dict)` to `FluidState` in `src/app/models/state/assets/effects.py`.
* [x] Subtask: Implement $O(1)$ memoized retrieval in `CardinalFrame.keys()`.
* [x] Subtask: Implement frame-indexed memoized retrieval in `FluidFrame.keys()`.
* [x] Subtask: Add cache invalidation (`fluid.state._keys.clear()`) inside `Actuator.propagate()`.
* [x] Subtask: Verify rendering output matches baseline textures without visual regression.

**2. Task: Spatial Filtering and Debouncing in FluidMechanics**

*Objective*: Prevent spurious layer-wide hydrological invalidations when distant or rapidly toggling obstacles switch state.

* [x] Subtask: Implement AABB intersection check between mutating gates and layer fluid hitboxes before flagging `fluid.state.dirty = True`.
* [x] Subtask: Implement geometric shift detection in `FluidMechanics.update()` to bypass `Cartographer.purge()` and `Cartographer.generate()` when water bounds remain unchanged.
* [x] Subtask: Introduce tick-based debounce accumulator (`settings.FLUID_INVALIDATION_DEBOUNCE_TICKS`) in `FluidMechanics` to coalesce consecutive gate oscillations.

**3. Task: Engine Pacing and Spin-Lock Optimization**

*Objective*: Reduce CPU busy-waiting in `Engine.start()`.

* [x] Subtask: Insert `time.sleep(0)` into the `while (self.time() - current_time) < delta:` spin loop in `Engine.start()`.
* [x] Subtask: Benchmark UPS and FPS consistency to confirm jitter-free 60 FPS delivery without excessive `perf_counter` calls.

**4. Task: Streamline Sorting in Screen.draw**

*Objective*: Eliminate per-frame closure allocations during Painter's Algorithm Z-sorting and resolve Bug B003.

* [x] Subtask: Implement module-level `_sort(asset)` in `src/app/game/screen.py` with integer coercion for `state.height`.
* [x] Subtask: Replace inline lambda sort keys in `Screen.draw()` and `Screen.export_map()` with `_sort`.
* [x] Subtask: Benchmark `Screen.draw` execution time before and after refactoring.

##### Profile Analysis

The new profile verifies that the Phase 09.07 optimizations successfully eliminated the targeted inner-loop bottlenecks:

1. **Spin-Lock Remediation**: `time.sleep` accounted for **39.98%** of total runtime (35,112 calls). Cooperative thread-yielding replaced the previous tight `perf_counter` busy-wait loop (~1.84M calls), eliminating CPU core saturation while maintaining targeted frame pacing.
2. **Decomposition Churn Elimination**:
    * `FluidFrame.keys` (previously 3.79%) and `CardinalFrame.keys` (previously 2.05%) dropped completely below the 1.0% node threshold (`--node-thres=1.0`). Memoized frame keys eliminated over 1.6 million dynamic slice allocations per session.
3. **Reactive Invalidation & Shift Detection**:
    * `FluidMechanics.update` and `Cartographer.generate` dropped below the 1.0% threshold. Shoreline contours were derived exactly once on initial hydration (generating 21 active shorelines), while subsequent frames safely bypassed contour sweeps via geometric shift detection.
4. **Painter's Algorithm Sorting**:
    * `Screen.draw` dropped from **17.64%** to **15.28%** total time despite rendering 21 additional active procedural shoreline entities.

| Subsystem / Function | Baseline % | New % | Baseline Calls | New Calls | Impact & Status |
| --- | --- | --- | --- | --- | --- |
| **`engine:start`** / **`time.sleep`** | 3.66% *(perf_counter)* | **39.98%** *(sleep)* | 1,840,915 | 35,112 | **Resolved.** Busy-wait spin loop replaced by cooperative yielding; CPU thrashing eliminated. |
| **`screen:draw`** | 17.64% | **15.28%** | 868 | 1,138 | **Improved.** Module-level sort resolved Bug B003 and reduced closure overhead across an expanded entity set. |
| **`effects:keys` (`FluidFrame`)** | 3.79% | **< 1.0%** *(pruned)* | 3,472 | — | **Resolved.** Frame-indexed memoization eliminated stream corridor and annular pool re-slicing churn. |
| **`geography:keys` (`CardinalFrame`)** | 2.05% | **< 1.0%** *(pruned)* | 18,228 | — | **Resolved.** $O(1)$ pre-computed cache returned static shoreline margin slices without recomputation. |
| **`fluid:update` $\to$ `Cartographer`** | 2.55% | **< 1.0%** *(pruned)* | 1,028 | 1 | **Resolved.** Spatially bounded; single generation on hydration (21 shorelines created); invariant ticks bypassed. |
| **`load:update` (`Migrator.step`)** | — | **19.33%** | — | 200 | **Expected.** Time-sliced hydration of physical assets and world metadata during startup. |
| **`screen:present`** | — | **3.29%** | — | 1,144 | **Baseline.** Hardware VRAM back-buffer presentation and SDL event pumping. |
| **`motion:update` (`fields.py`)** | — | **2.99%** | — | 1,288 | **Baseline.** Bipartite space hashing for raft drift, bridge surface interception, and immersion checks. |

---

##### Documentation Divergences

###### Draft: Geography & Shoreline State Specification

* **Page**: `docs/01-assets.md`
* **Heading**: `Geography` / `Shorelines`

###### Drift

The documentation in `01-assets.md` leaves `GeographyProperties` and `ShorelineState` marked as `TODO` in the Asset Hierarchy tables, and omits the explicit Z-ordering override (`height: 0`, `depth: 0`), property relations (`tile`, `fluid`, `thickness`), and the `_keys` cache slot implemented in Phase 09.07.

###### Update

```markdown
### Geography

Geography Assets represent inanimate, immutable structural and topographical landforms (e.g., shorelines, cliffs, ledges). Geography Assets define transition thresholds between differing biome zones, elevations, and fluid corridors.

**Properties: GeographyProperties**

* `dimensions: Dimensions`
* `hitboxes: List[Hitbox]`
* `tile: str`: Terrain tile ID to which this margin binds.
* `fluid: Optional[str] = None`: Optional fluid ID required to activate this margin.
* `thickness: int = 8`: Width/length of the sensor threshold strip.
* `mass: int = -1`: Sensor classification (bypasses collision resolution).

### Shorelines

Shorelines are procedural, inanimate Geography sensors instantiated along unoccluded environmental water margins.

**Frame: CardinalFrame**

* Indexes 4 cardinal orientation rows:
    * Row 0: `up`    (Land North/Up, Water South/Down)
    * Row 1: `left`  (Land West/Left, Water East/Right)
    * Row 2: `down`  (Land South/Down, Water North/Up)
    * Row 3: `right` (Land East/Right, Water West/Left)
* `keys(id, state)` emits repeating full tiles along `state.length` and a fractional distal slice for remainders, memoized to `state._keys`.

**State: ShorelineState**

* `layer: str`
* `position: Position`
* `orientation: str` (`up`, `left`, `down`, `right`)
* `length: int`
* `thickness: int = 8`
* `bidirectional: bool = True`
* `hitboxes: List[Hitbox]`
* `height: Optional[Union[int, str]] = 0`
* `depth: int = 0`
* `_keys: Optional[List[Tuple[str, int, int]]] = None`

```

---

###### Draft: Reactive Fluid Invalidation & Shift Detection

* **Page**: `docs/05-mechanics.md`
* **Heading**: `World` / `FluidMechanics`

###### Drift

`05-mechanics.md` describes an unconditional two-pass propagation pipeline where any gate switch immediately purges and regenerates layer shorelines. It omits the three-tier optimization introduced in Phase 09.07: spatial AABB/corridor intersection filtering, tick-based debounce windows, and geometric signature shift detection (`_fluid_signature`).

###### Update

```markdown
#### FluidMechanics

FluidMechanics governs fluid emission, recursive bifurcation, and procedural shoreline margins across active layers. It executes after physical momentum updates (`MotionMechanics` and `CollisionMechanics`) and uses a 3-tier reactive dirty-checking architecture:

1. **Spatial Corridor Filtering**: Inspects switch-linked gates (`AssetInstances.GATES`). A mutating gate only flags the layer's fluids as `dirty` if the gate's AABB intersects active fluid compound hitboxes or falls within downstream emission corridors.
2. **Debounce Accumulator**: Consecutive gate oscillations are coalesced using `settings.FLUID_INVALIDATION_DEBOUNCE_TICKS` before triggering propagation.
3. **Pass 1 (Fluid Propagation & Bifurcation)**: For invalidated layers, `Actuator.propagate()` updates stream lengths, expands annular pools around static obstacles (\(m = 0\)), derives secondary branch corridors, and updates `board.update_fluid_cache(layer)`. Cache slots (`fluid.state._keys`) are cleared.
4. **Pass 2 (Geometric Shift Detection & Shoreline Synthesis)**: Compares the pre- and post-propagation geometric signature (`_fluid_signature`: stream lengths, pool bounds, branch positions). If water geometry is invariant, shoreline regeneration is bypassed. If geometry shifted (or during hydration), `Cartographer.purge()` and `Cartographer.generate()` synthesize updated boundary contours.

```

---

###### Draft: Painter's Algorithm Sort Key & Integer Coercion

* **Page**: `docs/10-architecture.md`
* **Heading**: `Rendering` / `Depth & Height`

###### Drift

`10-architecture.md` documents Painter's Algorithm sorting using inline tuple evaluation. It fails to document the module-level static sort function `Screen._sort(asset)` introduced to eliminate per-frame closure allocations, and omits the integer coercion requirement for `state.height` that resolved Bug B003.

###### Update

```markdown
### Depth & Height

To accurately render perspective, the Screen `draw()` loop applies Painter's Algorithm sorting to all active assets before translating them to Cython primitives.

Sorting is evaluated via the module-level static method `Screen._sort(asset)`:

```python
@staticmethod
def _sort(asset: Asset) -> tuple[int, int]:
    height = int(asset.state.height) if asset.state.height is not None else (
        (asset.state.position.y + (asset.dimensions.l if asset.dimensions else 0))
    )
    return (height, asset.state.depth)
```

1. **Primary Key (Height)**: Evaluates dynamic geometric height ($y + l$). If an explicit `state.height` is present, it is coerced to an integer (`int(asset.state.height)`). Coercion prevents `TypeError` when late-binding compositions assign string tokens alongside integer positions (Bug B003).
2. **Secondary Key (Depth)**: Serves as a tie-breaker when assets share identical heights. Fluids declare `depth: -1`, Shorelines declare `depth: 0`, Bridges declare `depth: 1`, and standard entities default to `depth: 0`.
3. **Allocation Optimization**: Replacing per-frame `lambda` closures with `_sort` eliminates millions of transient function objects and reduces draw overhead across expanded entity sets.
```

---

## Bug Reports

##### Bug B015: Branch Corridor Hitbox Slicing Duplication in FluidFrame

**STATUS**: OPEN
**SEVERITY**: High

**Description**

In `FluidFrame.keys()` (`src/app/assets/frames/effects.py`), pooling decomposition assumes `state.hitboxes[1:]` contains only annular pool flanks:

```python
if state.pool:
    if len(state.hitboxes) > 1:
        for flank_hb in state.hitboxes[1:]:
            for px in range(0, flank_hb.dimensions.w, w):
                for py in range(0, flank_hb.dimensions.l, l):
                    frame_keys.append((full_key, flank_hb.position.x + px, flank_hb.position.y + py))

```

However, `Actuator.propagate()` constructs `state.hitboxes` by appending:

1. `stream_hb` (index 0)
2. `pool_hitboxes` (index 1: a single monolithic hitbox for the entire pool)
3. `branch_compound_hitboxes` (indices 2+: secondary stream corridors)

Consequently:

* Every branch corridor in `state.hitboxes[2:]` is sliced and added to `frame_keys` in Step 2.
* Right after, Step 3 (`if state.branches:`) iterates over `state.branches` and adds the branch tiles a second time.
* If `stream_length == 0` (emitter flush against obstacle), `hitboxes[0]` is the pool hitbox itself. Slicing `state.hitboxes[1:]` omits the pool completely while duplicating the branches.

**Steps to Replicate**

Deploy a fluid emitter with `flow = 2` that strikes an obstacle. Inspect the tuples emitted by `FluidFrame.keys()` for the child branch coordinates. Two identical frame key tuples will be emitted for every branch tile.

**Proposed Remediation**

In `FluidFrame.keys()`, decompose `state.pool` exclusively using `state.pool.x, state.pool.y, state.pool.w, state.pool.l` (or an explicit `pool.hitboxes` attribute), rather than slicing `state.hitboxes[1:]`.

---

##### Bug B016: Branch Corridor Fluid ID Resolution Miss in Cartographer

**STATUS**: OPEN
**SEVERITY**: Medium

**Description**

In `Cartographer._resolve_fluid_id()` (`src/app/services/generators/game/cartographer.py`), interior water coordinates are tested only against parent stream lengths and annular pools:

```python
for fluid in fluids:
    pool = fluid.state.pool
    if pool and pool.w > 0 and pool.l > 0:
        if geometry.inside(water_pos.x, water_pos.y, [(pool.x, pool.y, pool.x + pool.w, pool.y + pool.l)]):
            return fluid.id
    if fluid.state.length > 0 and predicates.in_stream(water_pos, fluid):
        return fluid.id
return None

```

Child branches (`fluid.state.branches`) are omitted from containment evaluation. When a bifurcated branch margin is inspected, `_resolve_fluid_id` returns `None`. `ShorelineIndex.resolve(tile_id, None)` is forced to fall back to generic terrain margins, failing to bind fluid-specific shoreline assets to secondary river branches.

**Steps to Replicate**

Configure a shoreline that binds specifically to `(tile='grass', fluid='river')`. Cause the river to bifurcate via an obstacle. Inspect the shoreline assets generated along the banks of the child branches. The branches will either fall back to default margins or fail to generate shorelines.

**Proposed Remediation**

In `Cartographer._resolve_fluid_id()`, iterate through `fluid.state.branches` and evaluate point containment against each branch corridor rectangle using `geometry.inside()`.

---

##### Bug B017: Redundant Delta Recalculation in Engine Hybrid Pacer

**STATUS**: OPEN
**SEVERITY**: Low

**Description**

In `Engine.start()` (`src/app/game/engine.py`), the hybrid frame pacing block contains duplicated assignments:

```python
work_time = self.time() - current_time
sleep_time = delta - work_time

work_time = self.time() - current_time
sleep_time = delta - work_time

```

This represents leftover development scaffolding from the Phase 09.07 pacer tuning.

**Steps to Replicate**

Inspect `src/app/game/engine.py` lines 213–218.

**Proposed Remediation**

Remove the duplicated calculation lines.

---

## Future Backlog

#### Backlog: Transverse Fluid Submersion & Buoyancy Dynamics

**Overview**

With hydrological frame caching and static shoreline synthesis stabilized in Phase 09.07, dynamic entities interacting with fluid fields require realistic physics resolution. Currently, non-raft dynamic bodies either sink or snap unconditionally to the stream flow vector. This backlog item integrates buoyancy evaluation (`properties.buoyant`), directional wading resistance, and gradual transverse submersion across variable river depths (closing Goal 09 and TODO 2).

##### Goal: Buoyant Flotation & Hydrodynamic Drag

Differentiate dynamic body behavior in fluids based on the static property `buoyant: bool`:

* Buoyant objects ($m > 0, \text{buoyant} = \text{True}$) float with zero friction decay along $\vec{v}_{\text{current}}$.
* Non-buoyant objects ($m > 0, \text{buoyant} = \text{False}$) sink to the riverbed, resisting current flow via water drag friction and ignoring drift.
* Characters wading against flow experience velocity damping along opposing normal vectors ($\vec{v} \cdot \vec{u}_{\text{current}} < 0$).

##### Goal: Transverse Depth Graduation & Visual Submersion Channels

Refine the `ChannelTypes.SUBMERGE` rendering directive. Instead of a fixed 50% split (`half_l = dimensions.l // 2`), calculate water immersion depth based on entity position relative to shoreline margins:

* Shoreline threshold (0–8px from edge): Ankle depth (15% height modulation).
* Corridor interior (> 8px from edge): Deep water (50%–70% modulation, color tinting).

##### Tasks

**1. Task: Buoyant Property Integration in MotionMechanics**

*Objective*: Apply selective drift and drag physics to floating vs. sinking bodies.

* [ ] Subtask: Add `buoyant: bool = False` to `ObjectProperties` and `CraftProperties`.
* [ ] Subtask: Update `src/app/game/logic/modules/motion/fields.py` to check `asset.properties.buoyant` before imparting `_fluid_velocity`.
* [ ] Subtask: Apply water drag deceleration in `frictive.py` for non-buoyant sinking crates.

**2. Task: Shoreline Proximity Depth Graduation in Frame Channels**

*Objective*: Dynamically modulate entity submersion depths in `Screen.draw`.

* [ ] Subtask: Define `ChannelPayload` dataclass in `src/app/models/adapters.py` replacing raw directive tuples.
* [ ] Subtask: Calculate proximity-based `split_y` in `Frame.channels()` using distance to nearest intersecting Shoreline sensor.
* [ ] Subtask: Verify visual transition for Sprites walking from dry land into shallow shoreline margins and deep river corridors.