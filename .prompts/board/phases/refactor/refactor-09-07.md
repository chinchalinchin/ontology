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