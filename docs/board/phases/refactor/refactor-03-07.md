#### Refactor: Collision Optimization

**Overview** 

Resolves **Bug B053 (Items 1 & 2)** and the primary active CPU bottlenecks identified in the `world-01` `pstats` profile (`CollisionMechanics` at `6.27%` wall-clock / `24.0%` active CPU; `MaterialHitbox` at `3.47%` wall-clock / `13.3%` active CPU; `NavigationMechanics.obstacles` at `1.85%` wall-clock for 1 NPC; `fields._extract_compound_sensor_primitives` at `1.16%`). Eliminates static-vs-static hashing, per-tick static geometry re-extraction, `MaterialIndex()` singleton churn, and inner-loop heap allocations.

##### Specification

1. **Static vs. Dynamic Weight Partitioning**:
   * `Board._cache` partitions physical weights ($m \ge 0$) into:
     * `statics(layer, elevation)`: Immutable/semi-static bodies ($m = 0$), pre-indexed by normalized elevation on hydration/add/remove and updated on `SwitchMechanics` gate toggles.
     * `dynamics(layer)`: Motive/kinematic/frictive bodies ($m > 0$).
   * `CollisionMechanics` skips any `(layer, elevation)` tier with zero active non-falling dynamic bodies, reducing `15.03` tier passes/tick on `world-01` to only tiers with live dynamic bodies (`~1–2`/tick).
   * Phase 2 evaluates **dynamic-vs-dynamic** and **dynamic-vs-static** pairs exclusively; **zero static-vs-static** pairs are hashed or tested.
2. **Compound Multi-Hitbox Resolution (B053.2)**:
   * When a dynamic body overlaps multiple hitboxes of a compound static asset in a single tick, `_resolve` resolves all intersecting hitbox pairs rather than stopping at the first pair returned by `geometry.intersects`.
3. **DI-Compliant `HitboxSchema` & Zero-Allocation Lookups**:
   * `MaterialHitbox` receives `MaterialIndex` via `Builder` -> `AssetFactory` (never calling `MaterialIndex()` inside `elevations()`/`get()`).
   * Fallback dimension hitboxes and quantized `RotatedHitbox` tables are precomputed at hydration/indexing time rather than heap-allocated inside `get()`.
4. **Dirty-Flagged Static Obstacle & Sensor Caches**:
   * `Board` caches static obstacle + bridge-carved hazard fluid AABBs per `(layer, elevation)` (invalidated on `Board.add`/`remove`, `SwitchMechanics` toggles, and `FluidMechanics` rebuilds) for $O(1)$ retrieval by `NavigationMechanics.obstacles` and `MotionMechanics.fields`.
5. **Zero-Allocation Cython Broad/Narrow Phase**:
   * `Space` tracks `active_buckets` so `clear()` and `query()` run in $O(K_{\text{occupied}})$ instead of $O(\text{num\_buckets})$ and deduplicates pairs without allocating Python `set()` objects.
   * `physics.collisions` uses a `cdef inline bint c_intersects(int x1, int y1, list hbs1, int x2, int y2, list hbs2)` without allocating transient `Position` structs or discarded `(hb1, hb2)` tuples.
   * `SpatialMechanic` indexes `assets[idx]` directly instead of allocating `dict(enumerate(assets))`.

##### Architectural Analysis I

The `world-01` profile proves that `CollisionMechanics` (`6.27%`), `NavigationMechanics.obstacles` (`1.85%`), and `fields._extract_compound_sensor_primitives` (`1.16%`) all fail for the same architectural reason: **every spatial consumer re-derives identical static world geometry from scratch every tick**.

* **Why a `Board`-owned Static Spatial Cache + Invalidation Version Counter works best**:
  * Mutating events for static geometry are strictly bounded and infrequent: `Migrator` hydration, `Board.add`/`remove`/`relayer`, `SwitchMechanics` toggling a `Gate`, `SeasonMechanics` changing a `Resource` stage, and `FluidMechanics` updating fluid geometry.
  * Exposing a monotonic per-layer `static_version: int` (or dirty bitset) on `Board._cache` lets `CollisionMechanics` (persistent static `Space` or static primitive buffer), `NavigationMechanics` (cached static obstacle AABB tuples + per-padding-key LRU), and `MotionMechanics.fields` (cached static sensor primitives) invalidate lazily in $O(1)$ without tight cross-mechanic coupling.
* **Cython ABI & `.pxd` Scope**:
  * Adding `cdef int* active_buckets` and `cdef int active_count` (and a C pair dedup buffer) requires updating `src/libs/core/math/space.pxd` alongside `space.pyx`, plus adding a `query_dynamic_vs_static` entry point in `physics.pyx` (unifying the duplicated `physics.boundaries` and `physics.environment` implementations into one generic bipartite query `physics.bipartite`).
* **Factory & DI Cleanup**:
  * `AssetFactory._HITBOXES` is currently a class-level dict instantiated at import time (before `Builder.build_relations` compiles `MaterialIndex`). Converting `AssetFactory` hitbox registration (or injecting `MaterialIndex` into `MaterialHitbox` during `Builder.build_services`) eliminates the 3.33M global `MaterialIndex()` calls while enforcing strict DI. Also fail fast on unknown recipe/mechanic keys in `AssetFactory.hitbox` and `MechanicFactory.mechanics`, and normalize `Board.obstacles(layer=None)` to match all other `Board` query signatures.

##### Goals

###### Goal: Bipartite Dynamic-vs-Static Collision Query

```python
# CollisionMechanics.update (per layer)
dynamics = [
    d for d in board.dynamics(layer)
    if not d.state.mutators.triggers.falling
]
if not dynamics:
    continue  # Skip inactive layers entirely

# Partition only movers by elevation; query static cache per active tier
for elevation, tier_dynamics in group_by_elevation(dynamics).items():
    tier_statics = board.statics(layer, elevation)
    # 1. Dynamic-vs-Dynamic (small N)
    if len(tier_dynamics) > 1:
        for a, b in self.collisions(tier_dynamics, elevation=elevation):
            self._resolve(a, b, elevation=elevation)
    # 2. Dynamic-vs-Static (bipartite query: zero static-vs-static pairs)
    if tier_statics:
        for dyn, stat in self.bipartite(tier_dynamics, tier_statics, elevation=elevation):
            self._resolve(dyn, stat, elevation=elevation)
```

###### Goal: Active-Bucket `Space` & Zero-Allocation Narrow Phase

```cython
# Space (space.pxd / space.pyx)
# On first insert into bucket h (when bucket_counts[h] == 0):
#   active_buckets[active_count] = h
#   active_count += 1
# On clear():
#   for i in range(active_count): bucket_counts[active_buckets[i]] = 0
#   active_count = 0
# On query(): iterate only active_buckets[0..active_count-1]
```

###### Goal: Cached Static Obstacles for Multi-NPC `NavigationMechanics`

Cache un-inflated static obstacle + bridge-carved hazard fluid AABBs per `(layer, elevation)` keyed by `board.static_version(layer)`. In `NavigationMechanics.obstacles`, read the cached static list (with optional inflated cache per `(layer, elevation, pad_x, pad_y)`), and only append the handful of non-excluded `board.dynamics(layer)` hitboxes.

##### Tasks

**1. Task: Eliminate `MaterialHitbox` Singleton Overhead & Hitbox Allocations**

*Objective*: Remove the `3.33M` per-run `MaterialIndex()` calls (`13.3%` active CPU) and inner-loop hitbox allocations.

* [] Subtask: Inject the compiled `MaterialIndex` instance from `Builder.build_relations` into `MaterialHitbox` via `AssetFactory` so `elevations()` and `get()` reference `self._materials` directly.
* [] Subtask: Pre-normalize missing `properties.hitboxes` dimension fallbacks during `Loader`/hydration (or cache once per asset ID) across `StaticHitbox`, `DynamicHitbox`, `MaterialHitbox`, `StageHitbox`, and `LayeredHitbox`, and precompute quantized angle tables in `RotatedHitbox`.
* [] Subtask: Clamp `base_e = max(0, ...)` and align empty-hitbox fallback behavior in `ElevatedHitbox`.
* [] Subtask: Update `AssetFactory.hitbox` and `MechanicFactory.mechanics` to raise `KeyError` on unknown keys rather than silently falling back to `StaticHitbox`/`AnimationMechanics`.

**2. Task: Split Static and Dynamic Weights in `Board._cache`**

*Objective*: Pre-partition static colliders by `(layer, elevation)` with dirty-version invalidation.

* [] Subtask: Extend `app.game.board.modules.cache.Cache` to maintain `dynamics[layer]` ($m > 0$), `statics[layer][elevation]` ($m = 0$), and a per-layer `static_version` counter incremented on `index_batch`, `evict_batch`, `relayer`, and explicit invalidation calls.
* [] Subtask: Expose `board.dynamics(layer)`, `board.statics(layer, elevation)`, `board.invalidate_statics(layer)`, and normalize `board.obstacles(layer=None)` to aggregate across all layers.
* [!: Dependent On Other Task Completion] Subtask: Hook `SwitchMechanics` (Gate toggles), `SeasonMechanics` (Resource stage transitions), and `FluidMechanics` (fluid/shoreline rebuilds) to call `board.invalidate_statics(layer)`.

**3. Task: Upgrade `Space`, `physics.pyx`, and `SpatialMechanic` to Zero-Allocation Bipartite Queries**

*Objective*: Eliminate static-vs-static hashing, `70M+` empty-bucket scans, `dict(enumerate)` churn, and duplicate narrow-phase allocations.

* [] Subtask: Add `active_buckets` tracking to `src/libs/core/math/space.pxd` and `space.pyx` for $O(K)$ `clear()` and `query()`, replacing Python `set()` pair deduplication with a C-level pair buffer.
* [] Subtask: Add a zero-allocation `cdef inline bint c_intersects(int x1, int y1, list hbs1, int x2, int y2, list hbs2)` in `geometry.pxd`/`geometry.pyx` and consume it inside `physics.collisions` (eliminating per-call `Position` and tuple allocations).
* [] Subtask: Unify `physics.boundaries` and `physics.environment` into a single bipartite negative-ID Cython query and add `physics.bipartite_collisions(dynamics, statics, grid)` for dynamic-vs-static resolution.
* [] Subtask: Remove `dict(enumerate(...))` in `SpatialMechanic.{collisions, intersections, proximities, constrain}`, remove the duplicate `self.grid.clear()` in `intersections`, and use `<int>p.rx` in `physics.integrate`.

**4. Task: Refactor `CollisionMechanics` for Active-Tier Bipartite & Multi-Hitbox Resolution**

*Objective*: Eliminate inactive-layer physics execution (B053.1) and resolve multi-hitbox compound intersections (B053.2).

* [] Subtask: Update `CollisionMechanics.update` to skip layers and elevation tiers with zero active non-falling `dynamics`, run dynamic-vs-dynamic and dynamic-vs-static queries separately, and cache static `Space`/primitives per `(layer, elevation, static_version)`.
* [] Subtask: Update `CollisionMechanics._resolve` (and add a multi-hit helper in `geometry.pyx` if needed) to iterate and resolve *all* intersecting hitbox pairs for compound multi-hitbox obstacles instead of returning after the first hit.
* [] Subtask: Re-profile `world-01` via `cProfile` + `gprof2dot` to verify `CollisionMechanics` drops from `6.27%` to `< 1.5%` wall-clock.

**5. Task: Cache Static Obstacles for `NavigationMechanics` and Static Sensors for `MotionMechanics.fields`**

*Objective*: Prevent $O(N_{\text{sprites}} \times M_{\text{weights}})$ scaling collapse in `NavigationMechanics.obstacles` and eliminate per-tick sensor extraction in `fields.update`.

* [] Subtask: Cache static obstacle + bridge-carved hazard fluid AABBs per `(layer, elevation, static_version)` (and inflated copies keyed by `(pad_x, pad_y)`) in `NavigationMechanics`, appending only live `board.dynamics(layer)` hitboxes per call.
* [] Subtask: Cache static compound sensor primitives (bridges, stairs, walkable struts, shorelines, fluids) keyed by `static_version` in `app.game.logic.modules.motion.fields`.
* [] Subtask: Add multi-NPC stress benchmark (`15–30` autonomous sprites on `world-01`) to validate linear frame-time stability under `pstats`.