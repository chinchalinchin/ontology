## 1. Engine Profile Analysis (`world-01` UAT)

At 6,059 rendered frames and 6,337 world simulation ticks (approximately 101 seconds at 60 FPS, averaging 1.05 fixed-timestep substeps per world frame), `Engine.start` spends **73.54%** of wall time idle in `time.sleep` (12,077 calls, or 1.99 calls/frame from hybrid sleep-plus-spin pacing) and **25.27%** in active execution.

### Active Frame Budget Breakdown

| Subsystem | Wall Time | Share of Active CPU (25.27%) | Calls | Calls / Tick or Frame |
| --- | --- | --- | --- | --- |
| **`Engine._play` (Total)** | **14.98%** | **59.3%** | 6,563 | 1.08 / frame |
| — `CollisionMechanics.update` | 6.05% | 23.9% | 6,337 | 1.00 / tick |
| — `MotionMechanics.update` | 2.71% | 10.7% | 6,337 | 1.00 / tick |
| — `NavigationMechanics.update` | 2.65% | 10.5% | 6,337 | 1.00 / tick |
| — All other Core + World Mechanics + `device.poll` | 3.44% | 13.6% | — | (each under 1.0% node / 0.5% edge) |
| **`Engine._render` (Total)** | **9.00%** | **35.6%** | 6,059 | 1.00 / frame |
| — `Screen.interface` (`_widgets` $\to$ `widgets.keys`) | 3.90% | 15.4% | 6,059 | 12.02 `keys` / frame |
| — `Screen.draw` (`_assemble`) | 3.77% | 14.9% | 6,053 | 1.00 / world frame |
| — `Screen.present` | 1.24% | 4.9% | 6,059 | 1.00 / frame |
| **`Device.pump`** | **1.11%** | **4.4%** | 6,059 | 1.00 / frame |
| **`Engine.start` bookkeeping / `_drain` / `_telemetry**` | **0.18%** | **0.7%** | — | — |

*Measurement caveat:* `cProfile` instruments Python function entry/exit, inflating the relative cost of high-call-count pure-Python methods relative to Cython `nogil` and C/SDL routines. However, the raw call counts are exact and reveal five concrete structural inefficiencies.

### Primary Bottlenecks & Inefficiencies

#### 1. Redundant Per-Tick Querying of Immutable Craft Hitboxes (1.94 Million Python Calls)

* **Evidence:** `crafts:elevations` is invoked **1,027,576×** (1.42%) and `crafts:get` is invoked **910,106×** (2.01%)—together accounting for **3.43% of total wall time (13.6% of active CPU)**.
* **Root cause:** `Board.weights(layer, elevation)` filters `self._cache.get_weights(layer)` with a list comprehension calling `w.hitbox.elevations(w.properties, w.state)` on every call, and `base.collisions` calls `crafts.get(...)` on every pass. From `collision:update` alone, both methods execute **583,004×** (`92.00` calls/tick), meaning 92 static Craft assets have their elevation membership and hitbox lists re-evaluated on every tick.
* **Additional amplification in `CollisionMechanics`:** `base.collisions` is called **95,853×** (`15.13` calls/tick). Running broad-phase/narrow-phase collision across every `(layer, elevation)` partition—including static-only elevation tiers or inactive layers with zero dynamic bodies—drives `CollisionMechanics` to **40.4% of all `_play` time**.
* **Fix direction:** Index static `weights` by `(layer, elevation)` inside `Board._cache` (rebuilding only on `add`/`remove`/`relayer` or elevation change), cache static Craft primitive tuples, and skip `base.collisions` for any `(layer, elevation)` bucket containing zero dynamic ($m \gt 0$) bodies.

#### 2. Per-Sprite Obstacle Rebuilding in `NavigationMechanics` (#1 Scaling Hazard)

* **Evidence:** `navigation:_navigate` is called **6,337×** across 6,337 ticks—confirming this UAT trace ran with **$N = 1$ autonomous Sprite**. For that single Sprite, `navigation:obstacles` ran **6,079×** (95.9% of ticks) and consumed **1.94%** wall time (**74.3%** of all navigation cost), contributing the remaining ~444k calls to `crafts:elevations` and ~327k calls to `crafts:get`.
* **Root cause:** `NavigationMechanics._navigate` invokes `self.obstacles(...)` on every tick *inside the per-sprite loop*, even when line-of-sight is clear and RRT never executes. Each call re-extracts all weights, allocates new Minkowski-inflated Python float tuples for every static obstacle and perimeter, and recomputes `_fluid_obstacles` (including 2D AABB bridge `subtract` carving) from scratch.
* **Scaling impact:** At $O(N \cdot |\mathcal{O}|)$ per tick, scaling `world-01` from $N = 1$ to **$N = 15\text{--}20$ Sprites** drives `navigation:obstacles` alone to **29%–39% of wall time**, saturating the frame budget before RRT or collisions even scale.
* **Fix direction:** Cache uninflated static weight, perimeter, and bridge-carved fluid AABBs per `(layer, elevation)` (invalidating only on Fluid dirty-check shifts or `add`/`remove`), and memoize inflated obstacle lists per `(layer, elevation, pad_x, pad_y)` across sprites within a tick.

#### 3. Per-Tick Sensor Primitive Extraction in `MotionMechanics`

* **Evidence:** `fields:update` accounts for **2.40%** of wall time (**88.6%** of `MotionMechanics.update`), leaving just **0.31%** for actual velocity integration, kinematics, dynamics, and friction. Nearly half of `fields:update` (**1.13%**) is spent in `_extract_compound_sensor_primitives`, called **19,010×** (`3.00` calls/tick).
* **Root cause:** Walkable elevation substrates (Bridges, Stairs, non-obstacle Struts) are re-extracted into primitive lists three times per tick despite being static geometry.
* **Fix direction:** Cache substrate sensor primitives by `(layer, elevation)` in `Board._cache`.

#### 4. UI Overlay Assembly Out-Costing World Rendering

* **Evidence:** `Screen.interface` (**3.90%**) costs more than rendering the entire game world (`Screen.draw` at **3.77%**). Within `interface`, `widgets:keys` is invoked **72,830×** (`12.02` calls/frame), consuming **2.12%** of wall time (54.4% of UI time).
* **Root cause:** Persistent HUD overlays (meters, panes, borders, labels) recompute frame keys via `SEPARATOR.join` and rebuild widget render lists every frame even when their underlying bound state (`health`, `magic`, `focus`) has not mutated.
* **Fix direction:** Cache resolved widget frame keys on widget state and invalidate only when `Binder` or `MenuMechanics` mutates widget state.

#### 5. Python-Side World Render Assembly

* **Evidence:** `Screen._assemble` consumes **3.55%** (**3.27% self**), representing **94.2%** of `Screen.draw`. The Cython/SDL draw submission itself is under 0.25%.
* **Root cause:** Per-frame Python iteration over `board.renderables(layer)` to cull onscreen assets, compute `(elevation, substrate, ground, priority)` sort keys, and pack tuples across the Cython boundary.
* **Fix direction:** Spatial-grid culling before sorting (so off-screen entities never enter Python's `sort` or key extraction) and caching static ground baselines for immobile assets.

---

## 2. Phase 06.06 Impact Analysis: Removing Transition Short-Circuiting

### Current Cost Baseline in `pstats`

Neither `TransitionMechanics.update`, `CognitionMechanics.update`, `TransitionExecutor.evaluate`, nor `Backend.evaluate` crosses the `--node-thres=1.0` or `--edge-thres=0.5` thresholds in the profile. The **entirety** of `TransitionMechanics.update` (transition evaluation, `board.states()` lookup, `AnimationMap.action`, `AnimationMap.direction`, and trigger updates) costs strictly **less than 0.5% of total wall time** (and less than 2.0% of active CPU) for $N = 1$ Sprite.

### Distinguishing Inner vs. Outer Short-Circuiting

There are two distinct loops in transition evaluation, and they have very different consequences:

1. **Inner conjunction short-circuiting (`Backend.evaluate` over a single transition's `conditions` list):**
* **Must be preserved.** Removing it breaks ISL null-safety (e.g., evaluating `sprite.goal.category == ...` when `sprite.goal is None` raises `AttributeError`) and forces unnecessary evaluation of `is_near()` / dictionary lookups on disqualified transitions.


2. **Outer transition short-circuiting (`TransitionExecutor` stopping at the first matching `Transition` in `transitions[current_state]`):**
* Removing outer short-circuiting to collect the full candidate set (`candidates()`) has a **much smaller runtime impact than intuition suggests**, for two reasons:
* **Steady-state ticks already do exhaustive evaluation:** During active navigation (`wander`, `find`, `hunt`, `follow`), no outgoing transition matches until arrival, interruption, or loss. `TransitionExecutor.evaluate` *already* evaluates every outgoing rule to `False` on almost every tick.
* **Low fan-out per state:** In `automata/intentions/main.yaml`, non-`idle` states carry only 1–4 outgoing transitions. Even if Phase 06.06 expands `idle` from 4 to ~9 outgoing transitions (adding `mine`, `build`, `barter`, `mock`, `threaten`), inner short-circuiting rejects mismatched categories on conjunct #2 (`sprite.goal.category == ...`) in nanoseconds.





### Quantitative Effect on Engine Performance

| Scenario | Estimated `TransitionMechanics` Wall Time | Effect on 60 FPS Budget |
| --- | --- | --- |
| **Current UAT ($N = 1$, short-circuited)** | $\lt 0.5\%$ (est. $\sim 0.1\text{--}0.2\%$) | Negligible |
| **Phase 06.06 ($N = 1$, exhaustive outer `candidates()`)** | $\sim 0.2\text{--}0.5\%$ ($\approx 1.2\times\text{--}2.5\times$ on transition/self-loop ticks; $\approx 1.0\times$ on steady navigation ticks) | Imperceptible; dwarfed by `collision` (6.05%), `_widgets` (3.89%), `_assemble` (3.55%), `fields` (2.40%), `navigation:obstacles` (1.94%) |
| **Scaled World ($N = 50$ Sprites, exhaustive outer, unoptimized)** | $\sim 10\text{--}20\%$ (linear in $N \times k_q$, amplified by `eval()` / `**locals` kwargs unpacking and per-tick `locals` dict allocation) | Noticeable once `navigation:obstacles` and `collision` are fixed; easily mitigated by indexing/gating |

### Two Non-Obvious Risks Exposed by Combining `pstats` With Phase 06.06

1. **Semantic hazard on existing self-loops (`attack -> attack`, `escape -> escape`, `mine -> mine`):**
* In `automata/intentions/main.yaml`, self-loops currently rely on outer short-circuiting to mask lower-priority rules. Under exhaustive `candidates()`, if a state contains both a self-loop (`next == current_state`) and a non-disjoint exit or branch rule, both will enter the candidate set simultaneously. `TacticalSelector` must explicitly define whether `current_state` participates as a "stay" candidate or whether self-loops are removed in favor of strictly disjoint exit conditions.


2. **`GoalResolver` `PREREQUISITE` amplification risk (the real Phase 06.06 perf hazard):**
* `TransitionExecutor` is cheap because its conditions are pure memory/attribute checks. By contrast, `PrerequisiteOutcome` invokes `Locator` spatial scans (`board.categories`, `board.characters`, distance loops). If `PREREQUISITE` runs before cheap guards or re-runs failed locators every tick, it will replicate the exact per-tick call-amplification pattern already visible in `navigation:obstacles` and `crafts:get`.




## Part 1: Engine Profile Analysis (`pstats`)

### Executive Summary

During the `world-01` acceptance run (`11,104` render frames, `11,986` `_play` ticks, `11,651` active world ticks), `engine.start` accounts for **99.32%** of total runtime. Of that time, **73.22%** is spent idling in `time.sleep` (`22,135` calls, averaging ~2.0 sleep calls per frame via hybrid sleep/spin pacing), leaving **26.10%** wall-clock time as **active CPU execution**.

Normalizing against active CPU time (`26.10%` wall-clock = `100%` active budget):

| Subsystem / Call Site | Wall-Clock % | Active CPU % | Calls | Calls / World Tick | Primary Bottleneck |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`engine:_play` (Total Logic)** | **14.86%** | **56.9%** | 11,986 | 1.03 | Physics, spatial queries, obstacle extraction |
| ↳ **`collision:update`** | **6.27%** | **24.0%** | 11,651 | 1.00 | All-layer tier partitioning, static-vs-static broad/narrow phase, `MaterialHitbox` |
| &nbsp;&nbsp;&nbsp;&nbsp;↳ `base:collisions` | 2.71% | 10.4% | 175,084 | **15.03** | Per-tier `Space` hashing (`70M+` bucket scans), `dict(enumerate)`, `MaterialHitbox.get` |
| &nbsp;&nbsp;&nbsp;&nbsp;↳ `crafts:elevations` (via `collision`) | 0.98% | 3.8% | 1,071,892 | **92.00** | Repeated `MaterialIndex()` Singleton resolution across static crafts |
| ↳ **`motion:update`** | **2.79%** | **10.7%** | 11,651 | 1.00 | `fields:update` (`2.48%`) -> `_extract_compound_sensor_primitives` (`1.16%`, `3.00`/tick) |
| ↳ **`navigation:update`** | **2.46%** | **9.4%** | 11,651 | 1.00 | Single NPC (`1.00` `_navigate`/tick); `navigation:obstacles` (`1.85%`, `10,607` calls) |
| ↳ *All other ~15 Mechanics combined* | *3.22%* | *12.3%* | — | — | Healthy baseline |
| **`engine:_render` (Total Graphics)** | **9.87%** | **37.8%** | 11,104 | 0.95 | World assembly + uncached HUD widget assembly |
| ↳ `screen:draw` -> `_assemble` | 4.20% | 16.1% | 11,098 | 0.95 | Cython `render.assemble` (`3.88%`) |
| ↳ `screen:interface` -> `_widgets` | 4.11% | 15.7% | 11,104 | 0.95 | `widgets:keys` (`2.23%`, `137,434` calls) — nearly equals world rendering |
| ↳ `screen:present` | 1.47% | 5.6% | 11,104 | 0.95 | SDL2 frame presentation |
| **`devices:pump`** | **1.20%** | **4.6%** | 11,104 | 0.95 | OS / SDL event polling |

---

### Collision Subsystem Bottleneck Diagnosis

1. **`CollisionMechanics` Dominates Simulation Cost (`6.27%` wall-clock | `42.2%` of `_play` | `24.0%` of all active CPU)**:
   * `CollisionMechanics` alone consumes more CPU than `MotionMechanics` (`2.79%`) and `NavigationMechanics` (`2.46%`) combined, and nearly **2x** all other ~15 mechanics combined (`3.22%`).
   * **Continuity of Open Bug B053**: Across `11,651` world ticks, `SpatialMechanic.collisions` executes **`175,084` times** (`15.03` elevation-tier passes per tick — virtually unchanged from B053's `15.04`). Every single layer on the Board is ticked every frame, and Phase 2 invokes `self.collisions(tier_weights, elevation=elevation)` even on tiers containing **zero dynamic entities ($m > 0$)**, hashing static-vs-static pairs that `physics.collide` later no-ops.
   * With `CollisionMechanics` configuring `Space(max_entities=200)` (`400` buckets), `175,084` calls to `Space.query()` perform **`70,033,600` empty/occupied bucket checks**, allocate `175,084` `dict(enumerate(assets))` maps, `175,084` `set()` dedup tables, and `700,336` transient Cython `Position`/`Dimensions` structs in `physics.collisions`.

2. **The `MaterialHitbox` Singleton Tax (`3.47%` wall-clock | `13.3%` of all active CPU)**:
   * Combining `crafts:64:elevations` (`1.39%`, `1,685,288` calls) and `crafts:73:get` (`2.08%`, `1,644,962` calls) reveals **`3,330,250` calls** to `MaterialHitbox` in a single run — **more than one-eighth of the entire Engine's active CPU time**.
   * The exact call ratios expose the root cause:
     * `collision.update` calls `MaterialHitbox.elevations` `1,071,892` times (`92.00` crafts/tick) and `base.collisions` calls `MaterialHitbox.get` `1,071,892` times (`92.00` crafts/tick). Every static obstacle craft across every layer is re-queried twice per tick.
     * The remaining `613,396` `elevations` calls and `573,070` `get` calls (~`54–58` crafts/call across `10,607` calls) come primarily from `NavigationMechanics.obstacles` -> `board.weights(layer, elevation=elevation)`.
   * Inside *every single call*, `MaterialHitbox` executes `MaterialIndex().is_obstacle(state.blueprint)` — repeatedly invoking `Singleton.__new__`, `MaterialIndex.__init__`, and `hasattr(self, "_material_partitions")` inside the hottest loop in the Engine.

3. **Un-Cached Obstacle Extraction in `NavigationMechanics` (`1.85%` wall-clock for 1 NPC)**:
   * `navigation.update` (`11,651` calls) invokes `_navigate` (`11,651` calls) — proving `world-01` has **only 1 active autonomous NPC**.
   * Yet `navigation.obstacles` executes **`10,607` times** (`91%` of world ticks), rebuilding the entire layer's obstacle AABB list (querying `board.weights(layer, elevation)`, re-evaluating `hitbox.elevations()` and `hitbox.get()`, reading `board.perimeters`, extracting fluid corridors/pools, subtracting bridges, and applying Minkowski inflation) from scratch on every tick.
   * The same architectural pattern appears in `fields:332:update` (`2.48%`), where `_extract_compound_sensor_primitives` runs **`34,952` times** (`3.00` calls/tick, `1.16%`) re-extracting static environmental sensor geometry.

4. **Deceptive Headroom & Scaling Cliff**:
   * While `73.22%` idle sleep looks comfortable on `world-01`, the cost profile scales poorly with world size and agent density:
     * `NavigationMechanics` scales $O(N_{\text{sprites}} \times M_{\text{weights}})$: scaling from `1` NPC to `15` NPCs in a town pushes `navigation.obstacles` alone from `1.85%` to **`~27.8%` wall-clock**.
     * `CollisionMechanics` scales $O(L_{\text{layers}} \times W_{\text{static}} + W_{\text{tier}}^2)$: scaling from `92` crafts / `15` active tiers to a mid-sized RPG world (`400+` crafts / `40+` tiers) pushes `CollisionMechanics` past **`25–30%` wall-clock**, breaching the `16.67ms` (60 FPS) frame budget.

5. **Non-Collision Hotspot Worth Tracking**:
   * `screen._widgets` (`4.10%` wall-clock, `15.7%` of active CPU) and `widgets:keys` (`2.23%`, `137,434` calls) cost nearly as much as rendering the entire game world (`screen.draw` at `4.20%`) because HUD overlay primitives are re-resolved in Python every frame instead of cached/dirty-flagged.

---

## Part 2: Code Review

##### Review: Ontology Collision Subsystems & Spatial Pipeline

###### Overview

Ontology's spatial stack cleanly separates **data/policy** (`Asset`, `HitboxSchema`, `Board`), **orchestration/logic** (`CollisionMechanics`, `SpatialMechanic`, `NavigationMechanics`, `Perimeter`), and **native computation** (`libs.core.math.{space, geometry, physics}`). That layering is well-conceived and keeps high-level game rules readable.

However, the `pstats` profile and codebase audit expose a single overarching structural tension: **immutable static topology (walls, obstacle struts, buildings, perimeters, static doors, bridges) is treated as volatile per-tick state across every spatial consumer**, while **geometric metadata and sensor contracts erode across module boundaries**. Specifically:
* `Board` collapses static ($m = 0$) and dynamic ($m > 0$) weights into a single flat list without elevation pre-partitioning, forcing `CollisionMechanics`, `NavigationMechanics`, and `MotionMechanics.fields` to re-derive identical static world geometry tens of thousands of times per second.
* Crucial geometric semantics — such as `LayeredHitbox` `OUT` sensor exclusion, `geometry.contours` outward boundary normals, and hitbox-anchored stair foot positions — are lost or contradicted as data crosses from `HitboxSchema`/`Perimeter` into `CollisionMechanics`/`physics.pyx`.
* All three inefficiencies documented in open **Bug B053** remain unresolved in the post-Phase-06.02 codebase and directly account for the largest active CPU share in the Engine.

###### Review: Implementation

* **Specification Violations & Doc-Code Drift**:
  * **`LayeredHitbox.elevations()` (`src/app/assets/hitboxes/objects.py:65-71`)**: Fails to return `[]` when `state.projection == LayerProjections.OUT`. This directly violates both `docs/01-assets.md` (`Object: Doors`) and the explicit contract relied on by `SpatialMechanic._elevations()` (`src/app/game/logic/mechanics/spatial/base.py:55-66`), leaking `OUT` door shadow footprints into solid collision resolution and RRT navigation obstacles (see **Bug NEW-01**).
  * **`LayeredHitbox.get()` vs. Docs**: `docs/01-assets.md` specifies indexing `properties.hitboxes[state.layer]` / `properties.hitboxes[state.outlayer]`, while `objects.py` indexes by categorical projection (`'in'` / `'out'`). The code's categorical keying is cleaner and better decoupled from layer names — the documentation should be updated to match.
  * **`CollisionMechanics._traverse_stairs()` vs. Docs (`src/app/game/logic/mechanics/spatial/collision.py:134-165`)**: `docs/01-assets.md` (`Craft: Stairs`) specifies `Directions.DOWN` and inverted velocity signs for `Directions.LEFT`/`RIGHT`, whereas `collision.py` handles `Directions.UP` (explicitly noting `DOWN` is impossible under LPC perspective) with the opposite `LEFT`/`RIGHT` velocity signs.
  * **`Perimeter.generate()` vs. Docs (`src/app/services/generators/game/perimeter.py:124-127`)**: `docs/12-architecture.md` states *"Environmental perimeters act as directed barriers"*, and `geometry.contours` carefully computes directed `(x, y, w, l, orientation)` tuples — yet `Perimeter.generate` discards `orientation` (`*_`) when instantiating `Boundary`, breaking directed containment (see **Bug NEW-02**).
  * **`Perimeter.extract()` vs. Gravity Spec**: `docs/05-mechanics.md` (`Field: Gravity`) defines elevated `BRIDGES`, `STAIRS`, and walkable `STRUTS` as valid $E > 0$ substrates, yet `Perimeter.extract` omits `BRIDGES` at $E > 0$, sealing off elevated bridge crossings for `NavigationMechanics` (see **Bug NEW-06**). Note also an important refinement to **B053.3**: while `CollisionMechanics` Phase 1 skips $E > 0$ perimeters intentionally so entities can fall off ledges, **`NavigationMechanics.obstacles()` (`navigation.py:351`) actively consumes `board.perimeters[layer][elevation]` for $E > 0$** to keep NPCs from pathing off ledges. Any fix to B053.3 must preserve clean walkable-deck perimeters for $E > 0$ navigation.
  * **`AttackHitbox.get()` vs. Docs (`src/app/assets/hitboxes/sheets.py:36-49`)**: `docs/01-assets.md` documents `SheetProperties.attackboxes`, while `AttackHitbox.get` queries `properties.hitboxes`.

* **Unhandled Edge Cases**:
  * **`ElevatedHitbox` Elevation Normalization (`src/app/assets/hitboxes/crafts.py:34-56`)**: Unlike every other `HitboxSchema`, `ElevatedHitbox` does not clamp `base_e` with `max(0, ...)`. If `state.elevation < 0`, `CollisionMechanics` clamps the tier key to `0`, then queries `get(..., elevation=0)`, computing `0 - base_e > 0` and looking up the wrong tier offset. Additionally, when `properties.hitboxes` is empty/`None`, `elevations()` returns `[base_e]` while `get()` returns `[]`, inserting empty-hitbox assets into `weights_by_elevation`.
  * **`Board.weights()` / `Board.obstacles()` Clamping & `layer=None` Asymmetry (`src/app/game/board/core.py:206-220`)**: `Board.weights(layer, elevation)` clamps `target_e = max(0, elevation)` but checks `target_e in w.hitbox.elevations(...)` without clamping the returned values. Also, `Board.obstacles(layer=None)` silently returns `[]`, whereas every other `Board` query (`weights`, `assets`, `categories`, `instances`, `bridges`, `shorelines`) aggregates across all layers when `layer is None`.
  * **Multiplied Crafts (`CraftState.multiple`)**: `CollisionMechanics._stair_hitboxes`, `Perimeter.extract` (Step 3), and `NavigationMechanics._fluid_obstacles` (bridge cutout fallback) fall back to unit `asset.dimensions` without scaling by `state.multiple.nx` / `ny`. If `Decomposer` does not split all multiplied `Stairs`/`Bridges`/`Struts` into unit `1x1` assets before hydration, multi-tile crafts will have truncated footprints.
  * **Sub-Pixel Remainder Retention**: Neither `physics.collide` nor `physics.constrain` clears `Position.rx` / `Position.ry` on the resolved collision axis, allowing accumulated sub-pixel remainder to persist after wall arrest.
  * **Unguarded `action` Parameter in `NavigationMechanics`**: Line `747` accesses `sprite.state.mutators.parameters.action.radius` directly without the `None` checks used in `SpatialMechanic.proximities` (`base.py:163-167`).
  * **`geometry.raycast` Strict Inequalities (`src/libs/core/math/geometry.pyx:439-473`)**: Strict `<` / `>` checks (`oy > sy`, `oy + ol < sy`, `ox > sx`, `ox + ow < sx`) ignore obstacles overlapping or flush with the stream origin `(sx, sy)`.

###### Review: Quality

* **Constraint Violations ("Zero Heap Allocation in the Inner Loop" & Dependency Injection)**:
  * **`MaterialHitbox` Global Singleton Access (`crafts.py:69, 78`)**: `Builder` compiles `MaterialIndex` as a managed Relation and injects it into services (`Materializer`, `Decomposer`, `Cradle`, `Migrator`) and Mechanics, yet `MaterialHitbox` circumvents DI to invoke `MaterialIndex()` globally inside `elevations()` and `get()`.
  * **Inner-Loop Heap Allocations**:
    * `SpatialMechanic.{collisions, intersections, proximities, constrain}` allocates `dict(enumerate(assets))` (and `dict(enumerate(boundaries))`) on every call solely to index lists by their own integer offsets (`assets[i]` is already $O(1)$).
    * `physics.collisions` allocates 4 Cython objects (`Position`, `Dimensions`, `Position`, `Dimensions`) per call (`700k+` allocations in `world-01`) and discards a newly allocated `(hb1, hb2)` tuple from `geometry.intersects` on every broad-phase hit.
    * `Space.query` allocates a Python `set()` (`seen`) and 2-tuples for every pair in every occupied bucket.
    * `StaticHitbox`, `DynamicHitbox`, `MaterialHitbox`, `StageHitbox`, `LayeredHitbox`, and `RotatedHitbox` instantiate fresh `Hitbox(Position(...), Dimensions(...))` objects on every fallback/rotated `get()` call.
    * `SpatialMechanic.intersections` allocates new padded `Hitbox`, `Position`, and `Dimensions` instances for every Player/Sprite hitbox on every call.
* **Dead & Unwired Code**:
  * `OrientedHitbox` and `DirectedHitbox` (`src/app/assets/hitboxes/core.py:72-135`) are defined but never imported or registered in `AssetFactory._HITBOXES`.
  * `Screen._sort` and `Screen._in_viewport` (`src/app/game/screen.py:60-64, 113-138`) are unused dead methods superseded by Cython `render.assemble`.
  * `Builder.materializer` (`src/app/services/orchestration/builder.py:251`) is instantiated in `build_services()` but never injected into `Board` (`Board.materializer` remains `None` with no setter).
  * `geometry.intersects` (`geometry.pyx:98-105`) accepts `dim1` and `dim2` parameters that are completely unused in its body.
* **Silent Misconfiguration Fallbacks**:
  * `AssetFactory.hitbox` (`src/app/services/factories/assets.py:124`) silently falls back to `StaticHitbox` on an unrecognized recipe key (turning a typo into a solid collider), whereas `frame` and `animation` default to `NONE`.
  * `MechanicFactory.mechanics` (`src/app/services/factories/mechanics.py:120`) silently falls back to `AnimationMechanics` on an unknown mechanic key, inconsistent with `backend()`, `executors`, and `relations` which properly fail fast with `ValueError`/`KeyError`.
  * `Space.insert` (`space.pyx:41`) silently drops entities beyond `max_per_bucket = 50` with no logging or resize.
* **Code Smells & Duplication**:
  * `physics.boundaries` (`physics.pyx:240-282`) and `physics.environment` (`physics.pyx:323-355`) are near-verbatim duplicates implementing the identical negative-ID `Space` insertion and `bounded()` check.
  * `Builder.build_board` (`builder.py:293-312`) constructs `EquipmentGroup` `Asset`s manually instead of delegating to `AssetFactory.asset()`.
  * `SpatialMechanic.intersections` calls `self.grid.clear()` at line `108` and immediately calls `self.grid.clear()` again at line `122` inside the tier loop.
  * Minor hygiene: duplicate `# Standard Libraries` comment in `collision.py:15-16`; inconsistent `w.properties.mass` vs `getattr(w.properties, 'mass', 0)` within the same method (`collision.py:286, 324`); `AttackHitbox.get` joins a new string via `settings.SEPARATOR.join(...)` on every call.

###### Review: Logic

* **Phase 1 -> Phase 2 Ordering Hazard (`CollisionMechanics.update`)**:
  * Boundary constraints (Phase 1) run *before* body-vs-body collision resolution (Phase 2). When two bodies separate near a map edge during Phase 2 (e.g., pushing a crate or sprite against a corner), Phase 2 can displace an entity across the 1px perimeter strip. Because `Perimeter` discards outward normals, Phase 1 on the subsequent tick then pushes the entity *further outside* the map rather than back inside (**Bug NEW-02**).
* **Stair Foot-Anchor Frame Mismatch & Missing Hysteresis (`CollisionMechanics._traverse_stairs`)**:
  * Phase 0 enters `_traverse_stairs` via hitbox overlap (`mover.hitboxes`), yet `_traverse_stairs` computes `(foot_x, foot_y)` from full frame `dimensions` (`dim_l`), placing the foot point `20px` below an LPC sprite's hitbox bottom (**Bug NEW-04**). Furthermore, the transition thresholds (`<= 0.85` vs `>= 0.85`, `>= 0.15` vs `<= 0.15`) share an identical boundary point with zero hysteresis deadzone.
* **Missing Separating-Velocity Guard (`physics.collide` & `physics.constrain`)**:
  * Both solvers unconditionally negate normal velocity against static obstacles/boundaries and unconditionally execute elastic momentum transfer between dynamic pairs without verifying that the bodies are approaching along the collision normal (`(v2 - v1) · n < 0`). Already-separating overlapping bodies get pulled back together or reversed into walls (**Bug NEW-03**).
* **Double-Counted Action Radius in `SpatialMechanic.proximities`**:
  * Every asset in `assets` is padded symmetrically by its own `action.radius` on all four sides (`base.py:169-175`). For Sprite-vs-Object, interaction reach is a Chebyshev square of half-width `R` (diagonal reach $\sqrt{2}R$). For Sprite-vs-Sprite (where both carry `action.radius = R`), their padded boxes intersect at cardinal distance **`2R`** and diagonal distance **`2\sqrt{2}R`** — double the declared radius.
* **Conflated Semantics in `Perimeter.extract`**:
  * Merging walkable terrain (`ENVIRON`), overhead visual canopy (`CANOPY`), and solid architectural blockers (`OBJECTS` + wall `STRUTS`) into one rectangle union (`geometry.contours`) conflates two incompatible concepts: *outer walkable floor bounds* vs. *solid interior obstacles*. Interior static obstacles vanish into the tile union (B053.3), while overhead canopies expand the walkable hull into void space.
* **Polymorphic `CraftProperties.hitboxes` Schema Ambiguity**:
  * `MaterialHitbox` expects `properties.hitboxes` keyed by `str` blueprint names (`Dict[str, List[Hitbox]]`), while `ElevatedHitbox` expects integer relative tier offsets (`Dict[int, List[Hitbox]]`) and computes `base_e + k`. Using a single untagged polymorphic field for two structurally different lookup spaces is error-prone.
* **Redundant `Board.weights` vs. `Board.obstacles` Semantics**:
  * `Board` maintains a dedicated `obstacles` cache, yet `NavigationMechanics.obstacles()` ignores `board.obstacles()` in favor of `board.weights()`, mixing static world geometry with volatile movers on every call.

###### Review: Architecture

The collision and navigation subsystems suffer from one primary architectural gap: **there is no first-class separation between Static World Topology and Dynamic Bodies in `Board` or `SpatialMechanic`.**

Today's per-tick data flow:
```text
Every Tick x Every Layer:
  Board.weights(layer) [static + dynamic mixed]
    -> CollisionMechanics: re-evaluate hitbox.elevations() for ALL weights
    -> Space.clear() + re-insert ALL static + dynamic weights -> Space.query() [includes static-vs-static]
    -> SpatialMechanic: allocate dict + primitives + hitbox.get() for ALL weights
    -> NavigationMechanics (per NPC): re-call board.weights(layer, e) + hitbox.get() + fluids - bridges + inflate
```

**Recommended Architectural Evolution**:

1. **Split `Board._cache` into Static vs. Dynamic Physics Indices**:
   * Partition cached weights on registration (`index_batch` / `evict_batch` / `relayer`) into:
     * `static_weights[layer][elevation]` ($m = 0$, pre-bucketed by elevation at hydration time; invalidated only when assets are added/removed or a `SwitchHitbox` Gate toggles).
     * `dynamic_weights[layer]` ($m > 0$, typically a handful of players, sprites, and crates).
   * Expose `board.dynamics(layer)` and `board.statics(layer, elevation)` so `CollisionMechanics` can immediately skip any `(layer, elevation)` with `len(dynamics) == 0` and never re-partition static geometry on every tick.

2. **Introduce a Persistent Static Spatial Index (or Cached Static Grid) per `(layer, elevation)`**:
   * Static bodies ($m = 0$) almost never move. Maintain a dirty-flagged static spatial index (or pre-extracted primitive array) per `(layer, elevation)`, invalidated only on structural events (`Board.add`/`remove`, `SwitchMechanics` gate toggles, `FluidMechanics` rebuilds).
   * In `CollisionMechanics` Phase 2, perform **only**:
     1. **Dynamic-vs-Dynamic** collision queries (tiny grid of $m > 0$ bodies).
     2. **Dynamic-vs-Static** queries against the cached static index (zero static-vs-static pairs, zero per-tick re-insertion of walls/buildings/resources).

3. **Unify Static Obstacle & Bridge-Carved Fluid Caching for `NavigationMechanics`**:
   * Cache un-inflated static obstacle AABBs `(x, y, w, l)` (static weights + perimeters + bridge-carved hazard fluids) per `(layer, elevation)` on `Board`, dirty-flagged by `FluidMechanics`, `SwitchMechanics`, and `Board.add`/`remove`.
   * In `NavigationMechanics.obstacles()`, read the cached static tuple list (or cache inflated lists keyed by `(layer, elevation, pad_x, pad_y)` since most NPCs share identical hitbox/squeeze dimensions!), and append only the few nearby dynamic weights. This collapses `NavigationMechanics` from $O(N_{\text{sprites}} \times M_{\text{weights}})$ down to $O(N_{\text{sprites}} \times M_{\text{dynamic}})$.

4. **Preserve Directed `Boundary` Normals & Separate Walkable Hull Extraction**:
   * Add `orientation` (or unit normal `(nx, ny)`) to `libs.core.models.Boundary`, preserve it in `Perimeter.generate`, and enforce one-way half-plane containment in `physics.constrain`.
   * Restrict `Perimeter.extract` strictly to walkable floor substrates (`ENVIRON` at $E = 0$; walkable `STRUTS`, `STAIRS`, and `BRIDGES` at $E > 0$), excluding `CANOPY` tiles and solid wall blockers. Run Phase 1 boundary constraints **after** Phase 2 collisions (or as a final clamp pass) so body separation cannot push entities past the perimeter.

5. **Restore DI Discipline on `HitboxSchema` & Pre-Bake Static Hitbox Geometry**:
   * Inject `MaterialIndex` into `MaterialHitbox` via `Builder` -> `AssetFactory` (or resolve obstacle status directly when hydrating `CraftProperties`/cache) rather than calling `MaterialIndex()` per tick.
   * Normalize default dimension-fallback hitboxes (`Hitbox(Position(0, 0), properties.dimensions)`) once during `Loader`/hydration so `HitboxSchema.get()` returns immutable references without heap allocations. Precompute quantized rotated hitboxes per `(id, angle)` for `RotatedHitbox`.

###### Review: Optimization

Prioritized optimization roadmap directly grounded in the `world-01` `pstats` profile:

1. **Priority 0 — Eliminate `MaterialHitbox` Singleton Overhead (`~3.47%` wall-clock | `13.3%` active CPU)**:
   * Inject/cache the `MaterialIndex` reference on `MaterialHitbox` (avoiding `3.33M` calls to `MaterialIndex().__new__/__init__/hasattr`), and pair with `Board`'s elevation-partitioned static weight cache so `MaterialHitbox.elevations` and `MaterialHitbox.get` are not called `92x` + `58x` per tick for immobile walls.
2. **Priority 0 — Short-Circuit Zero-Dynamic Tiers & Eliminate Static-vs-Static Hashing (`~4–5%` wall-clock | `~18%` active CPU)**:
   * In `CollisionMechanics.update`, skip Phase 1 and Phase 2 for any `(layer, elevation)` containing zero dynamic ($m > 0$) bodies — eliminating the majority of the `175,084` `SpatialMechanic.collisions` calls (`15.03`/tick -> `~1–2`/tick).
   * Query only dynamic-vs-dynamic and dynamic-vs-static pairs (eliminating B053.2 static-vs-static broad/narrow-phase work).
3. **Priority 1 — Cache Static Obstacles for `NavigationMechanics` & Static Sensors for `MotionMechanics.fields` (`~3.01%` wall-clock | `11.5%` active CPU, prevents multi-NPC scaling cliff)**:
   * Cache static obstacle + bridge-carved fluid AABBs per `(layer, elevation)` for `navigation:326:obstacles` (`1.85%` for 1 NPC; scales linearly with NPC count).
   * Apply the same dirty-flagged static sensor cache to `fields:74:_extract_compound_sensor_primitives` (`1.16%`, `34,952` calls).
4. **Priority 1 — Eliminate Python/Cython Boundary Allocations & Full-Table Scans (`~1–2%` wall-clock + GC reduction)**:
   * **Remove `dict(enumerate(...))`** in `SpatialMechanic.{collisions, intersections, proximities, constrain}`; index `assets[id_a]` directly.
   * **Dirty-Bucket Tracking in `Space` (`space.pyx`)**: Maintain an `int* active_buckets` array and `int active_count` populated on first insertion into an empty bucket. Both `Space.clear()` and `Space.query()` drop from $O(\text{num\_buckets})$ (`70M+` bucket checks in `world-01`) to $O(\text{active\_count})$. Replace the Python `seen = set()` and tuple allocations in `Space.query()` with C-level pair buffering/deduplication.
   * **Zero-Allocation C Narrow-Phase (`physics.pyx` & `geometry.pyx`)**: Add a `cdef inline bint c_intersects(int x1, int y1, list hbs1, int x2, int y2, list hbs2)` called by `physics.collisions` so it stops allocating 4 Cython `Position`/`Dimensions` structs per call (`700k+` allocations) and stops allocating/discarding `(hb1, hb2)` tuples. Remove the unused `dim1, dim2` parameters from `geometry.intersects`.
   * **Cython Inner-Loop Micro-Optimizations**: Unify duplicated `physics.boundaries`/`physics.environment`; use C cast `<int>p.rx` instead of Python `int(p.rx)` in `physics.integrate`; hoist neighbor float unpacking out of the 96-iteration candidate search loop in `physics.avoid` (currently unpacks every neighbor up to 96x per call).
   * **Align `Space` Capacity**: Remove the `max_entities=200` downgrade in `CollisionMechanics.__init__` once active-bucket iteration makes a larger table free to clear/query, and handle bucket growth dynamically.
5. **Priority 2 — Non-Collision Profile Win (`~4.10%` wall-clock | `15.7%` active CPU)**:
   * Dirty-flag/cache static HUD widget primitive tuples in `Screen._widgets` (`widgets:67:keys` alone takes `2.23%` across `137,434` calls, rivaling world rendering).

---

## Part 3: New Bug Reports

*(Note: **Bug B053** remains OPEN and verified by the latest `pstats` profile; the following reports document distinct, newly identified bugs discovered during this audit.)*

##### Bug NEW-01: `LayeredHitbox.elevations()` Does Not Exclude `OUT` Door Projections from Solid Collision and Obstacle Queries

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

`LayeredHitbox.elevations()` in `src/app/assets/hitboxes/objects.py` unconditionally returns `[max(0, state.elevation if state.elevation is not None else 0)]` regardless of `state.projection`. This contradicts both the specification in `docs/01-assets.md` (`Object: Doors` -> `LayeredHitbox`: *"returns `[]` if `state.projection == LayerProjection.OUT.value`"*), and `SpatialMechanic._elevations()` in `src/app/game/logic/mechanics/spatial/base.py`, which explicitly relies on `OUT` Door projections reporting `[]` from `elevations()` while preserving their sensor hitboxes for interaction checks.

Because reciprocal `OUT` shadow Doors share immutable `ObjectProperties` (`mass == 0`) with their parent `IN` Door, they are returned by `Board.weights(outlayer)`. Returning a non-empty elevation causes `OUT` shadow footprints to be bucketed into `CollisionMechanics.update` (Phase 2 solid collision resolution) and `NavigationMechanics.obstacles()` (inflated RRT obstacles). As a result, a Player or Sprite transitioning through an `IN` Door onto `outlayer` at `door.state.out` overlaps a solid collider on arrival, and NPCs cannot pathfind cleanly across exit door footprints.

**Steps to Replicate** 

1. Deploy a Door with `mass: 0` on `layer_a` targeting `outlayer: layer_b` at coordinate `out`.
2. During hydration, allow the reciprocal `OUT` Door projection (`state.projection == LayerProjections.OUT`) to be placed on `layer_b`.
3. Call `door_out.hitbox.elevations(door_out.properties, door_out.state)` — observe it returns `[0]` instead of `[]`.
4. Query `board.weights('layer_b', elevation=0)` or step `CollisionMechanics.update` / `NavigationMechanics.obstacles('layer_b', board, ...)` — observe `door_out` is included as a solid colliding weight and inflated RRT obstacle.

**Proposed Remediation**

Update `LayeredHitbox.elevations()` in `src/app/assets/hitboxes/objects.py` to return `[]` whenever `state.projection == LayerProjections.OUT`, matching `docs/01-assets.md` and `SpatialMechanic._elevations()`. Verify that `SpatialMechanic.intersections()` continues to detect `OUT` Door footprints via its `if include_empty or asset.hitboxes:` fallback.

##### Bug NEW-02: `Perimeter.generate()` Discards Outward Normals and `physics.constrain()` Ejects Entities Out of Bounds

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

There are three compounding defects in perimeter containment:

1. **Discarded Outward Normals**: `geometry.contours()` (`src/libs/core/math/geometry.pyx:369-372, 406-409`) computes directed 1px boundary segments `(x, y, w, l, orientation)` encoding outward edge normals (`LEFT`, `RIGHT`, `UP`, `DOWN`). However, `Perimeter.generate()` (`src/app/services/generators/game/perimeter.py:124-127`) discards `orientation` via `for x, y, w, l, *_ in raw_contours: Boundary(Position(x, y), Dimensions(w, l))`.
2. **Directionless Displacement & Phase Ordering**: `physics.constrain()` (`src/libs/core/math/physics.pyx:285-320`) resolves overlap solely using the sign of `dx = cx_b - cx_a` / `dy = cy_b - cy_a`. Because `CollisionMechanics.update` runs Phase 1 (`constrain`) *before* Phase 2 (`collisions`), Phase 2 separation (or high velocity / spawning near an edge) can displace an entity's hitbox center past the midpoint of the 1px boundary strip. On the next tick, `dx`/`dy` flips sign and `physics.constrain` pushes the entity **outward past the perimeter into the void** rather than back into the playable area. Additionally, `physics.constrain` truncates `int(overlap_x)` without `max(1, ...)` and unconditionally negates velocity without checking approach direction.
3. **1px North/West Interior Encroachment**: `geometry.contours()` emits `LEFT` (`entries_v`) at `[min_x, min_x + 1)` and `UP` (`entries_h`) at `[min_y, min_y + 1)` (**1px inside** the walkable tile union), while emitting `RIGHT` (`exits_v`) at `[max_x, max_x + 1)` and `DOWN` (`exits_h`) at `[max_y, max_y + 1)` (**1px outside**), causing entities flush with `x = 0` or `y = 0` to collide with the perimeter while right/bottom flush entities do not.

**Steps to Replicate** 

1. Create a walkable Tier-0 tile map spanning `[0, 320) x [0, 320)` and generate perimeters via `Perimeter.generate(board, layer)`.
2. Observe the generated `LEFT`/`UP` boundaries lie at `x = 0, w = 1` and `y = 0, l = 1` (inside `[0, 320)`), and `Boundary` retains no orientation field.
3. Position a dynamic entity (e.g., a Crate or Sprite with `w = 22`) so its hitbox center crosses past the right perimeter midpoint (`cx_a = 321`, `cx_b = 320.5`) — for example via a Phase 2 collision push from a second body near the right wall.
4. Execute `physics.constrain(...)` (or tick `CollisionMechanics.update`) — observe `dx = 320.5 - 321 = -0.5 < 0`, causing `pos.x += int(overlap_x)` to push the entity **rightward out of bounds** instead of leftward back inside `[0, 320)`.

**Proposed Remediation**

1. Add an `orientation` (or outward normal) field to `libs.core.models.Boundary` and preserve the 5th tuple element returned by `geometry.contours()` in `Perimeter.generate()`.
2. Offset `entries_v` to `x - 1` and `entries_h` to `y - 1` in `geometry.contours()` so all four 1px perimeter hulls sit consistently outside the walkable union.
3. Update `physics.constrain()` to push strictly along the inward normal (`-orientation`), clamp velocity only when moving outward (`v · n_out > 0`), and execute boundary clamping **after** Phase 2 collisions in `CollisionMechanics.update` (or as an additional post-Phase-2 pass).

##### Bug NEW-03: `physics.collide()` Lacks a Separating-Velocity Guard, Causing Reverse-Bounce Attraction and Sticking

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/libs/core/math/physics.pyx` (`collide`, lines `129-151` and `169-191`), after resolving spatial overlap along the minimum penetration axis, velocity resolution is executed unconditionally without verifying that the two bodies are approaching along the collision normal:

* Against a static body (`m1 == 0` or `m2 == 0`), `vel.vx = -vel.vx` (or `vel.vy = -vel.vy`) runs even if the dynamic body is already moving *away* from the static body — reversing its velocity **back into the wall**.
* Between two dynamic bodies (`m1 > 0` and `m2 > 0`), the 1D elastic momentum-transfer formula executes even if `(v2 - v1)` already points away along the separation normal — swapping velocities so the trailing body accelerates **back into** the leading body on the following frame.

This manifests whenever a third body pushes an already-retreating entity into contact with a wall or neighbor, or when two moving bodies momentarily overlap while separating.

**Steps to Replicate** 

1. Instantiate two equal-mass dynamic entities (`m1 = m2 = 10`, non-kinematic) overlapping by 1px on the X-axis with `cx_a < cx_b` (`dx > 0`).
2. Set velocities so they are already separating: `vel1.vx = 10.0`, `vel2.vx = 40.0` (relative velocity `v2 - v1 = +30.0 > 0`).
3. Call `physics.collide(...)`.
4. Observe that after separation, `vel1.vx` becomes `40.0` and `vel2.vx` becomes `10.0` — driving entity 1 back into entity 2 on the next integration tick.
5. Repeat with `m1 = 10, vel1.vx = -20.0` (moving left, away from wall) and static wall `m2 = 0` positioned to the right (`dx > 0`): observe `vel1.vx` flips to `+20.0` (directly into the wall).

**Proposed Remediation**

Compute the signed normal direction (`nx = 1.0 if dx > 0 else -1.0` for X-axis, `ny = 1.0 if dy > 0 else -1.0` for Y-axis) and relative normal velocity `v_rel = (v2 - v1) * n`. Guard both the static reflection branches and the 1D elastic exchange branch with `if v_rel < 0:` (only resolve impulse when the bodies are actually approaching).

##### Bug NEW-04: `CollisionMechanics._traverse_stairs()` Computes Foot Anchor from Full Frame Dimensions Instead of Hitbox Bounds

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/game/logic/mechanics/spatial/collision.py` (`_traverse_stairs`, lines `101-106`), the entity's ground contact point is computed from full un-cropped sprite frame dimensions:

```python
foot_x = sprite.state.position.x + (dim_w // 2)
foot_y = sprite.state.position.y + dim_l
```

However, Phase 0 stair intersection detection (`collision.py:293`) and Phase 2 solid wall collisions both operate on `mover.hitboxes`. For standard 64x64 LPC Sprites (`dimensions = (64, 64)`, `hitbox = (x: 21, y: 23, w: 22, l: 21)` per `docs/00-overview.md`), the hitbox bottom sits at `position.y + 44` — **20px above** `foot_y = position.y + 64`.

On a 32px-tall `Directions.UP` stair (`min_y = 100, max_y = 132`), ascending (`tread_progress <= 0.85`) requires `foot_y <= 127.2`, i.e., `position.y <= 63`. At `position.y = 63`, the sprite's hitbox spans `[86, 107)`, already `14px` beyond the top edge of the stair. If a Tier-0 cliff wall or platform facade sits flush at `y = 100`, Phase 2 stops the sprite's hitbox at `position.y = 77` (`foot_y = 141`, `tread_progress = 1.28`), permanently blocking the entity from transitioning to `e_top` and ascending the stairs. Conversely, descending (`tread_progress >= 0.85`) transitions prematurely to `e_base` near the top of the stair.

*(Related documentation inconsistency: `docs/01-assets.md` also lists `Directions.DOWN` and inverted `LEFT`/`RIGHT` velocity signs compared to `collision.py`.)*

**Steps to Replicate** 

1. Place a 32x32 `Directions.UP` Stair at `(x=100, y=100)` (`e_base=0, delta=1`) with a solid Tier-0 cliff obstacle directly north at `y = [68, 100)`.
2. Place an LPC Player (`dimensions=64x64`, `hitbox=(21, 23, 22, 21)`, `elevation=0`) south of the stair and move continuously North (`vy < 0`).
3. Observe the Player's hitbox contacts the Tier-0 cliff obstacle at `position.y = 77` (`hitbox.y = 100`), where `foot_y = 77 + 64 = 141` yields `tread_progress = 1.28 > 0.85`.
4. Observe `sprite.elevation` remains `0` and the Player is blocked from climbing the stair.

**Proposed Remediation**

Compute `(foot_x, foot_y)` from the entity's active `hitboxes` (e.g., horizontal midpoint and bottom edge of `mover.hitboxes[0]`, falling back to `dimensions` only when `hitboxes` is empty), aligning `_traverse_stairs` with `NavigationMechanics.anchor()` and Phase 0/Phase 2 collision geometry. Additionally, introduce a small hysteresis band between ascent and descent thresholds (e.g., `<= 0.80` vs `>= 0.90` for `UP`) to eliminate exact-boundary oscillation, and reconcile `docs/01-assets.md` with the LPC stair direction rules.

##### Bug NEW-05: `Space.insert()` Over-Inserts Half-Open AABBs and Silently Drops Entities on Bucket Overflow

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

`Space.insert()` in `src/libs/core/math/space.pyx` (lines `29-43`) exhibits two spatial hashing defects:

1. **Half-Open AABB Over-Insertion**: Ontology defines AABBs as half-open intervals $[x, x + w) \times [y, y + l)$ (`docs/12-architecture.md`). However, `Space.insert()` computes `max_x = (x + w) // self.cell_size` and `max_y = (y + l) // self.cell_size`. A cell-aligned 64x64 asset at `(0, 0)` with `cell_size = 64` spans `[0, 64) x [0, 64)` (strictly inside cell `(0, 0)`), yet `insert()` registers it into **4 cells** `(0,0), (1,0), (0,1), (1,1)`. Flush-adjacent 32x32 tiles similarly spill into neighboring cells, inflating bucket occupancy and generating false-positive broad-phase candidate pairs.
2. **Silent Entity Dropping on Overflow**: `Space` allocates a fixed `max_per_bucket = 50` slots per hash bucket. When a bucket reaches `50` entries, `if count < self.max_per_bucket:` silently skips insertion with no warning, error, or overflow fallback. Compounding this, `CollisionMechanics.__init__` (`src/app/game/logic/mechanics/spatial/collision.py:74`) overrides `SpatialMechanic`'s default `max_entities = 2000` down to `max_entities = 200` (`num_buckets = 400`), increasing hash collision rates across dense regions or long perimeter segments and risking silent collision tunneling.

**Steps to Replicate** 

1. Instantiate `grid = Space(cell_size=64, max_entities=200)`.
2. Insert two non-overlapping adjacent 64x64 AABBs: `grid.insert(0, 0, 0, 64, 64)` and `grid.insert(1, 64, 0, 64, 64)`.
3. Call `grid.query()` — observe `(0, 1)` is returned as a false-positive colliding candidate pair because entity `0` spilled into cell `(1, 0)`.
4. Insert 51 overlapping entities at `(0, 0, 32, 32)` into `grid` and call `grid.query()` — observe entity `50` is absent from all returned pairs with no error raised.

**Proposed Remediation**

1. Guard against non-positive extents (`if w <= 0 or l <= 0: return`) and compute `max_x = (x + w - 1) // self.cell_size` and `max_y = (y + l - 1) // self.cell_size` in `Space.insert()`.
2. Remove the `max_entities = 200` downgrade in `CollisionMechanics.__init__` (especially once `Space` uses active-bucket tracking so larger bucket tables carry zero `clear()`/`query()` overhead), and either dynamically grow bucket capacity/overflow chains or emit an explicit error/warning if bucket capacity is ever exceeded.

##### Bug NEW-06: `Perimeter.extract()` Omits Elevated `BRIDGES` at $E > 0$, Blocking Elevated Bridge Navigation

**STATUS**: OPEN
**SEVERITY**: LOW

**Description**

Per `docs/05-mechanics.md` (`Field: Gravity` -> `Behavior: Substrate Support`), walkable surfaces at elevated tiers ($E > 0$) consist of **Bridges** at $e_{\text{base}} = E$, **Stairs** spanning $e_{\text{base}} < E \le e_{\text{base}} + \Delta e$, and walkable **Struts** at $e_{\text{base}} = E$.

In `src/app/services/generators/game/perimeter.py`, `Perimeter.extract()` includes elevated `STAIRS` in Step 2 (lines `68-82`) and `STRUTS` in Step 3 (lines `85-103`), but explicitly filters out `AssetInstances.BRIDGES` in Step 3 (`lines 90-96`) without including them in Step 2. Because `NavigationMechanics.obstacles()` (`src/app/game/logic/mechanics/intentional/navigation.py:351-357`) consumes `board.perimeters.get(layer, {}).get(elevation, [])` for all elevations including $E > 0$, `geometry.contours` generates a closing perimeter boundary directly across the junction where an elevated Strut platform connects to an elevated Bridge — blocking NPC RRT pathfinding from crossing elevated bridges.

**Steps to Replicate** 

1. Deploy two elevated walkable floor `STRUTS` at `elevation = 1` separated by a gap, connected by a `BRIDGE` deployed at `elevation = 1`.
2. Call `Perimeter.generate(board, layer)` and inspect `perimeters[1]`.
3. Observe that `Bridge` bounds were omitted from `rects`, producing closed perimeter `Boundary` segments sealing both ends of the bridge gap.
4. Query `NavigationMechanics.obstacles(layer, board, exclude=[], elevation=1)` and attempt to plan an RRT path across the elevated bridge — observe line-of-sight and RRT planning are blocked by the perimeter boundary at the bridge entrance.

**Proposed Remediation**

In `Perimeter.extract()` (`src/app/services/generators/game/perimeter.py`), include elevated `AssetInstances.BRIDGES` matching `base_e == elevation` (and only walkable, non-obstacle `STRUTS` rather than all static crafts/objects) inside Step 2's elevated walkable substrate union so elevated bridge decks merge seamlessly with adjacent platform decks.





























Below is the complete implementation for **Phase 03-07 (Refactor: Collision Optimization)** across **Tasks 1–5**. Per the Task Board directive (`[!: Dependent On Other Task Completion]`), hooks inside `SwitchMechanics`, `SeasonMechanics`, and `FluidMechanics` are intentionally left untouched, while `Board.invalidate_statics(layer)` and `Cache.rebuild_fluid(layer)` are exposed and wired for immediate consumption.

---

### Task 1: Eliminate `MaterialHitbox` Singleton Overhead & Hitbox Allocations

#### `src/app/assets/base.py`
Adds a shared, content-addressed `_DIMENSION_FALLBACKS` cache on `HitboxSchema` so missing `properties.hitboxes` dimension fallbacks never mutate `AssetProperties` and never re-allocate `Hitbox`/`Position` objects in inner loops.

```python
"""
@domain.abstract
@app.asset
@app.component
@app.base

# Ontology: Source - app.assets.base

Base Asset Interfaces.
"""
# Standard Libraries
from abc import abstractmethod
from dataclasses import dataclass
from typing import (
    Dict,
    List,
    Tuple,
    Optional,
)

# Application Libraries
from app.static.semantics import (
    ChannelTypes,
    Substrates
)
from app.models.abstracts import Singleton
from app.models.properties import (
    AssetProperties
)
from app.models.state import (
    AssetState,
    CalendarState
)

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Hitbox,
    Position,
)

# -------------------------------------------------

@dataclass(slots=True)
class Taxonomy:
    id: str
    name: str
    category: str
    instance: str


class Frame(Singleton):
    """
    Foundational interface for Assets.
    """

    @abstractmethod
    def keys(self, 
        id: str, 
        state: AssetState
    ) -> List[Tuple[str, int, int]]:
        pass

    @abstractmethod
    def index(self, 
        id: str, 
        properties: AssetProperties
    ) -> Dict[str, Tuple[int, int, int, int]]:
        """
        Generates a mapping of all possible frame keys to their crop coordinates (sx, sy, w, l).
        """
        pass

    def channels(self, 
        id: str, 
        state: AssetState, 
        properties: AssetProperties
    ) -> List[Tuple]:
        directives = []
        if state.mutators.triggers.submerged:
            if properties.dimensions:
                half_l = properties.dimensions.l // 2
                # (CHANNEL_SUBMERGE, split_y, r, g, b, a)
                # e.g., deep aquatic modulation: RGBA(40, 110, 180, 170)
                # TODO: this should be codified in a ChannelPayload data structure 
                #       to pass to the screen. Screen should unpack channel payload 
                #       into Cython primitives.  
                directives.append((
                    ChannelTypes.SUBMERGE,
                    (half_l, 40, 110, 180, 170)
                ))
        return directives

    def eras(self, 
        id: str, 
        calendar: CalendarState
    ) -> List[Tuple[str, int, int]]:
        """
        Macro-temporal epochal projection for static pre-rendered canvas baking.
        Default implementation falls back to static frame resolution.
        """
        return self.keys(id, None)

    
class Animation(Singleton):
    """
    Foundational interface for Assets with animate states.
    """

    @abstractmethod
    def animate(self, 
        state: AssetState, 
        properties: AssetProperties
    ) -> AssetState:
        """
        Abstract method for incrementing Asset's frame key. 
        """
        pass


class HitboxSchema(Singleton):
    """
    Foundational interface for Assets that participate in collisions and interactions.
    """
    _DIMENSION_FALLBACKS: Dict[Tuple[int, int], List[Hitbox]] = {}

    @classmethod
    def _dimension_fallback(cls, dimensions: Optional[Dimensions]) -> List[Hitbox]:
        """
        Returns a cached full-frame Hitbox list keyed by (w, l) without
        mutating immutable AssetProperties or allocating per-tick objects.
        """
        if not dimensions:
            return []
        key = (dimensions.w, dimensions.l)
        cached = cls._DIMENSION_FALLBACKS.get(key)
        if cached is None:
            cached = [Hitbox(Position(0, 0), Dimensions(dimensions.w, dimensions.l))]
            cls._DIMENSION_FALLBACKS[key] = cached
        return cached

    @abstractmethod
    def elevations(
        self,
        properties: AssetProperties,
        state: AssetState
    ) -> List[int]:
        """Returns all discrete elevation tiers this asset participates in."""
        pass

    @abstractmethod
    def get(
        self,
        properties: AssetProperties,
        state: AssetState,
        elevation: int
    ) -> List[Hitbox]:
        """Resolves active physical hitboxes at the specified elevation plane."""
        pass


class Asset:
    """
    Foundational class for all game Assets.
    """
    taxonomy: Taxonomy
    properties: AssetProperties
    state: AssetState
    frame:  Frame
    animation: Animation
    hitbox: HitboxSchema
    substrate: int

    def __init__(self,
        taxonomy: Taxonomy,
        properties: AssetProperties, 
        state: AssetState, 
        frame: Frame=None, 
        animation: Animation=None,
        hitbox: HitboxSchema=None,
        substrate: int = Substrates.STANDARD
    ):
        self.taxonomy = taxonomy
        self.properties = properties
        self.state = state
        self.frame = frame
        self.animation = animation
        self.hitbox = hitbox
        self.substrate = substrate

    @property
    def id(self) -> str: 
        return self.taxonomy.id

    @property
    def name(self) -> str:
        return self.taxonomy.name

    @property
    def category(self) -> str:
        return self.taxonomy.category

    @property
    def instance(self) -> str:
        return self.taxonomy.instance
    
    @property
    def dimensions(self) -> Dimensions:
        """Unified spatial retrieval for rendering and camera culling."""
        return self.properties.dimensions

    @property
    def elevation(self) -> int:
        return self.state.elevation if self.state.elevation is not None else 0

    
    @elevation.setter
    def elevation(self, value: Optional[int]) -> None:
        self.state.elevation = value

    @property
    def hitboxes(self) -> List[Hitbox]:
        """Default physical footprint resolved at the asset's deployed elevation."""
        return self.hitbox.get(self.properties, self.state, self.elevation)

    def primitive(self, index: int = 0, hitboxes: List[Hitbox] = None) -> Tuple:
        """
        Extracts spatial attributes into primitive integers for Cython math operations.

        - hitboxes: List of Hitbox overrides.

        Returns: (index, x, y, w, l, hitboxes)
        """
        return (
            index,
            self.state.position.x,
            self.state.position.y,
            self.dimensions.w,
            self.dimensions.l,
            hitboxes if hitboxes is not None else self.hitboxes
        )
```

---

#### `src/app/assets/hitboxes/core.py`
Replaces per-call fallback `Hitbox` allocations in `StaticHitbox` and `DynamicHitbox` with `_dimension_fallback`.

```python
"""
@domain.concrete
@app.asset
@app.core
@asset.hitbox

# Ontology: Source - app.assets.hitboxes.core

Core HitboxSchema implementations.
"""
# Standard Libraries
from typing import List

# Application Libraries
from app.assets.base import HitboxSchema
from app.models.properties import AssetProperties
from app.models.state import AssetState

# Cython Libraries
from libs.core.models import Hitbox


class StaticHitbox(HitboxSchema):
    """
    Resolves static hitboxes declared on immutable AssetProperties.
    """

    def elevations(self, 
        properties: AssetProperties, 
        state: AssetState
    ) -> List[int]:
        return [max(0, state.elevation if state.elevation is not None else 0)]
    
    def get(
        self,
        properties: AssetProperties,
        state: AssetState,
        elevation: int
    ) -> List[Hitbox]:
        target_e = max(0, state.elevation if state.elevation is not None else 0)
        if max(0, elevation) != target_e:
            return []
        if properties.hitboxes is None:
            return self._dimension_fallback(properties.dimensions)
        return properties.hitboxes

    
class DynamicHitbox(HitboxSchema):
    """
    Resolves mutable hitboxes declared on AssetState.
    """

    def elevations(self, 
        properties: AssetProperties, 
        state: AssetState
    ) -> List[int]:
        return [max(0, state.elevation if state.elevation is not None else 0)]
    
    def get(
        self,
        properties: AssetProperties,
        state: AssetState,
        elevation: int
    ) -> List[Hitbox]:
        target_e = max(0, state.elevation if state.elevation is not None else 0)
        if max(0, elevation) != target_e:
            return []
        if state.hitboxes is None:
            if properties.hitboxes is None:
                return self._dimension_fallback(properties.dimensions)
            return properties.hitboxes
        return state.hitboxes
    
    
class NoHitbox(HitboxSchema):
    """
    Null strategy for passable assets (tiles, passive effects, overlays).
    """

    def elevations(self, 
        properties: AssetProperties,
        state: AssetState
    ) -> List[int]:
        return []

    def get(
        self,
        properties: AssetProperties,
        state: AssetState,
        elevation: int
    ) -> List[Hitbox]:
        return []
```

---

#### `src/app/assets/hitboxes/crafts.py`
* Clamps `base_e = max(0, ...)` and aligns `None` vs `{}` empty-hitbox fallback behavior in `ElevatedHitbox`.
* Injects `MaterialIndex` into `MaterialHitbox` via `set_materials(...)` / constructor so `elevations()`, `get()`, and `is_obstacle()` reference `self._materials` directly without per-call `MaterialIndex()` singleton churn.

```python
"""
@domain.concrete
@app.asset
@asset.hitbox
@category.crafts
@modality.material

# Ontology: Source - app.assets.hitboxes.crafts

Craft HitboxSchema implementations.
"""
# Standard Libraries
from typing import (
    List,
    Optional,
)
import logging

# Application Libraries
from app.assets.base import HitboxSchema
from app.game.logic.relations import MaterialIndex
from app.models.properties import CraftProperties
from app.models.state import (
    CraftState,
)

# Cython Libraries
from libs.core.models import Hitbox

logger = logging.getLogger(__name__)


class ElevatedHitbox(HitboxSchema):
    """
    Resolves relative tier-indexed hitboxes from CraftProperties.
    """

    def elevations(
        self,
        properties: CraftProperties,
        state: CraftState
    ) -> List[int]:
        base_e = max(0, state.elevation if state.elevation is not None else 0)
        if properties.hitboxes is None:
            return [base_e] if properties.dimensions else []
        if not properties.hitboxes:
            return []
        return [max(0, base_e + k) for k in properties.hitboxes.keys()]

    def get(
        self,
        properties: CraftProperties,
        state: CraftState,
        elevation: int
    ) -> List[Hitbox]:
        base_e = max(0, state.elevation if state.elevation is not None else 0)
        target_e = max(0, elevation)
        if properties.hitboxes is None:
            if target_e != base_e:
                return []
            return self._dimension_fallback(properties.dimensions)
        if not properties.hitboxes:
            return []
        return properties.hitboxes.get(target_e - base_e, []) or []


class MaterialHitbox(HitboxSchema):
    """
    Resolves blueprint-dependent hitboxes for Crafts via MaterialIndex.
    Passable blueprints emit [] while obstacle blueprints emit active hitboxes.
    """
    _materials: Optional[MaterialIndex]

    def __init__(self, materials: Optional[MaterialIndex] = None) -> None:
        """Initializes flyweight MaterialHitbox with an optional injected MaterialIndex."""
        if not hasattr(self, "_materials") or materials is not None:
            self._materials = materials

    def set_materials(self, materials: MaterialIndex) -> None:
        """Injects the compiled MaterialIndex relation from orchestration."""
        self._materials = materials

    def _resolve_materials(self) -> MaterialIndex:
        """Returns the injected MaterialIndex, binding once on unconfigured test paths."""
        materials = self._materials
        if materials is None:
            materials = MaterialIndex()
            self._materials = materials
        return materials

    def is_obstacle(self, blueprint: Optional[str]) -> bool:
        """Evaluates blueprint obstacle classification via the injected MaterialIndex."""
        return self._resolve_materials().is_obstacle(blueprint)

    def elevations(
        self,
        properties: CraftProperties,
        state: CraftState
    ) -> List[int]:
        if not self.is_obstacle(state.blueprint):
            return []
        return [max(0, state.elevation if state.elevation is not None else 0)]

    def get(
        self,
        properties: CraftProperties,
        state: CraftState,
        elevation: int,
    ) -> List[Hitbox]:
        if not self.is_obstacle(state.blueprint):
            return []

        target_e = max(0, state.elevation if state.elevation is not None else 0)
        if max(0, elevation) != target_e:
            return []

        if properties.hitboxes is None:
            return self._dimension_fallback(properties.dimensions)

        return properties.hitboxes.get(state.blueprint, []) or []
```

---

#### `src/app/assets/hitboxes/cursors.py`
Precomputes quantized rotation tables per `CursorProperties` (`precompute`), avoiding trigonometric calls and `Hitbox`/`Position`/`Dimensions` allocations during `RotatedHitbox.get()`.

```python
"""
@domain.concrete
@app.asset
@category.cursors
@asset.hitbox

# Ontology: Source - app.assets.hitboxes.cursors

Cursor HitboxSchema implementations.
"""
# Standard Libraries
import math
from typing import (
    Dict,
    List,
    Tuple,
)

# Application Libraries
from app.assets.base import HitboxSchema
from app.models.properties import CursorProperties
from app.models.state import MotorState

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Hitbox,
    Position
)

# ---------------------------------------------------------

MAX_CACHED_CURSOR_TABLES = 512

# ---------------------------------------------------------


class RotatedHitbox(HitboxSchema):
    """
    Projects canonical 0-degree CursorProperties hitboxes clockwise around
    the frame center (W / 2, L / 2) by MotorState.angle into tight AABBs.
    """
    _angle_tables: Dict[int, Tuple[CursorProperties, Dict[int, List[Hitbox]]]]

    def __init__(self) -> None:
        """Initializes quantized angle lookup tables keyed by CursorProperties identity."""
        if not hasattr(self, "_angle_tables"):
            self._angle_tables = {}

    @staticmethod
    def _rotate(
        base_hitboxes: List[Hitbox],
        w: int,
        l: int,
        angle: int
    ) -> List[Hitbox]:
        """Projects base hitboxes clockwise about frame center (w / 2, l / 2) by angle."""
        if angle == 0:
            cos_t, sin_t = 1.0, 0.0
        elif angle == 90:
            cos_t, sin_t = 0.0, 1.0
        elif angle == 180:
            cos_t, sin_t = -1.0, 0.0
        elif angle == 270:
            cos_t, sin_t = 0.0, -1.0
        else:
            rad = math.radians(angle)
            cos_t = math.cos(rad)
            sin_t = math.sin(rad)

        abs_cos = abs(cos_t)
        abs_sin = abs(sin_t)
        cx = w / 2.0
        cy = l / 2.0

        rotated: List[Hitbox] = []
        for hb in base_hitboxes:
            w0 = hb.dimensions.w
            l0 = hb.dimensions.l

            h_cx = (hb.position.x + (w0 / 2.0)) - cx
            h_cy = (hb.position.y + (l0 / 2.0)) - cy

            rot_cx = (cos_t * h_cx) - (sin_t * h_cy)
            rot_cy = (sin_t * h_cx) + (cos_t * h_cy)

            rot_w = max(1, round((w0 * abs_cos) + (l0 * abs_sin)))
            rot_l = max(1, round((w0 * abs_sin) + (l0 * abs_cos)))

            rot_x = round(cx + rot_cx - (rot_w / 2.0))
            rot_y = round(cy + rot_cy - (rot_l / 2.0))

            rotated.append(Hitbox(Position(rot_x, rot_y), Dimensions(rot_w, rot_l)))

        return rotated

    def precompute(self, properties: CursorProperties) -> Dict[int, List[Hitbox]]:
        """
        Precomputes and caches the quantized angle hitbox table for a CursorProperties instance.
        """
        if not properties.dimensions:
            return {}

        if properties.hitboxes is None:
            base_hitboxes = self._dimension_fallback(properties.dimensions)
        elif not properties.hitboxes:
            return {}
        else:
            base_hitboxes = properties.hitboxes

        w = properties.dimensions.w
        l = properties.dimensions.l
        step = properties.rotation
        table: Dict[int, List[Hitbox]] = {}

        if step and step > 0 and (360 % step) == 0:
            for angle in range(0, 360, step):
                table[angle] = self._rotate(base_hitboxes, w, l, angle)

        if len(self._angle_tables) >= MAX_CACHED_CURSOR_TABLES:
            self._angle_tables.clear()

        self._angle_tables[id(properties)] = (properties, table)
        return table

    def elevations(
        self,
        properties: CursorProperties,
        state: MotorState
    ) -> List[int]:
        """
        Returns the discrete elevation plane occupied by the projectile.
        """
        return [max(0, state.elevation if state.elevation is not None else 0)]

    def get(
        self,
        properties: CursorProperties,
        state: MotorState,
        elevation: int
    ) -> List[Hitbox]:
        """
        Retrieves precomputed rotated AABB hitboxes at the requested elevation plane.
        Falls back to the full frame dimensions when properties.hitboxes is None.
        """
        target_e = max(0, state.elevation if state.elevation is not None else 0)
        if max(0, elevation) != target_e:
            return []

        if not properties.dimensions:
            return []

        if properties.hitboxes is not None and not properties.hitboxes:
            return []

        entry = self._angle_tables.get(id(properties))
        if entry is not None and entry[0] is properties:
            table = entry[1]
        else:
            table = self.precompute(properties)

        angle = state.angle % 360
        cached = table.get(angle)
        if cached is not None:
            return cached

        base_hitboxes = (
            self._dimension_fallback(properties.dimensions)
            if properties.hitboxes is None
            else properties.hitboxes
        )
        rotated = self._rotate(
            base_hitboxes,
            properties.dimensions.w,
            properties.dimensions.l,
            angle
        )
        table[angle] = rotated
        return rotated
```

---

#### `src/app/assets/hitboxes/objects.py`
Caches default `IN` and `OUT` projection fallbacks keyed by `(projection, w, l)` inside `LayeredHitbox`.

```python
"""
@domain.concrete
@app.asset
@asset.hitbox
@category.objects
@modality.material

# Ontology: Source - app.assets.hitboxes.objects

Object HitboxSchema implementations.
"""
# Standard Libraries
from typing import (
    Dict,
    List,
    Tuple,
)

# Application Libraries
from app.assets.base import HitboxSchema
from app.assets.hitboxes.core import StaticHitbox
from app.static.semantics import LayerProjections
from app.models.properties import ObjectProperties
from app.models.state import (
    DoorState,
    SwitchState
)

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Hitbox,
    Position
)

# ---------------------------------------------------------

DEFAULT_IN_THRESHOLD_CLEARANCE = 12
DEFAULT_OUT_SENSOR_THICKNESS = 16

# ---------------------------------------------------------


class SwitchHitbox(StaticHitbox):
    """
    Resolves dynamic hitboxes for binary switchable obstacles (Gates).
    Emits [] when state.switch is True (open) and active hitboxes when False (closed).
    """

    def elevations(
        self,
        properties: ObjectProperties,
        state: SwitchState
    ) -> List[int]:
        if state.switch:
            return []
        return super().elevations(properties, state)

    def get(
        self,
        properties: ObjectProperties,
        state: SwitchState,
        elevation: int
    ) -> List[Hitbox]:
        if state.switch:
            return []
        return super().get(properties, state, elevation)


class LayeredHitbox(HitboxSchema):
    """
    Resolves categorical layer-relative hitboxes for Doors across their deployed
    layer ('in') and connected outlayer shadow footprint ('out').
    """
    _fallback_cache: Dict[Tuple[str, int, int], List[Hitbox]]

    def __init__(self) -> None:
        """Initializes cached default projection hitboxes keyed by (projection, w, l)."""
        if not hasattr(self, "_fallback_cache"):
            self._fallback_cache = {}

    def _projection_fallback(self, projection: str, w: int, l: int) -> List[Hitbox]:
        """Returns a cached default IN/OUT hitbox list for Doors lacking explicit hitboxes."""
        key = (projection, w, l)
        cached = self._fallback_cache.get(key)
        if cached is not None:
            return cached

        if projection == LayerProjections.OUT:
            sensor_l = min(l, DEFAULT_OUT_SENSOR_THICKNESS)
            cached = [
                Hitbox(
                    Position(0, l - sensor_l),
                    Dimensions(w, sensor_l)
                )
            ]
        else:
            cached = [
                Hitbox(
                    Position(0, 0),
                    Dimensions(w, max(1, l - DEFAULT_IN_THRESHOLD_CLEARANCE))
                )
            ]
        self._fallback_cache[key] = cached
        return cached

    def elevations(
        self,
        properties: ObjectProperties,
        state: DoorState
    ) -> List[int]:
        return [max(0, state.elevation if state.elevation is not None else 0)]

    def get(
        self,
        properties: ObjectProperties,
        state: DoorState,
        elevation: int
    ) -> List[Hitbox]:
        target_e = max(0, state.elevation if state.elevation is not None else 0)
        if max(0, elevation) != target_e:
            return []

        projection = state.projection or LayerProjections.IN

        if isinstance(properties.hitboxes, dict):
            return properties.hitboxes.get(projection, []) or []

        if properties.hitboxes is not None and projection == LayerProjections.IN:
            return properties.hitboxes

        if not properties.dimensions:
            return []

        return self._projection_fallback(
            projection,
            properties.dimensions.w,
            properties.dimensions.l
        )
```

---

#### `src/app/assets/hitboxes/resources.py`
Uses cached `_dimension_fallback` in `StageHitbox`.

```python
"""
@domain.concrete
@app.asset
@asset.hitbox
@category.resources

# Ontology: Source - app.assets.hitboxes.resources

Resource HitboxSchema implementations.
"""
# Standard Libraries
from typing import List
import logging

# Application Libraries
from app.assets.base import HitboxSchema
from app.models.properties import ResourceProperties
from app.models.state import ResourceState

# Cython Libraries
from libs.core.models import Hitbox
# ---------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------


class StageHitbox(HitboxSchema):
    """
    Resolves biological/geological stage-indexed hitboxes from ResourceProperties.
    """

    def elevations(self, properties: ResourceProperties, state: ResourceState) -> List[int]:
        return [max(0, state.elevation if state.elevation is not None else 0)]

    def get(
        self,
        properties: ResourceProperties,
        state: ResourceState,
        elevation: int
    ) -> List[Hitbox]:
        """
        Resolves active hitboxes matching state.stage at the requested elevation.
        Falls back to full frame dimensions when properties.hitboxes is None.
        """
        target_e = max(0, state.elevation if state.elevation is not None else 0)
        if max(0, elevation) != target_e:
            return []
        if properties.hitboxes is None:
            return self._dimension_fallback(properties.dimensions)
        return properties.hitboxes.get(state.stage, []) or []
```

---

#### `src/app/assets/hitboxes/sheets.py`
Avoids transient list allocation when assembling `frame_key`.

```python
"""
@domain.concrete
@app.asset
@asset.hitbox
@category.sheets

# Ontology: Source - app.assets.hitboxes.sheets

Sheet HitboxSchema implementations.
"""
# Standard Libraries
from typing import List

# Application Libraries
import app.static.settings as settings
from app.assets.base import HitboxSchema
from app.models.properties import SheetProperties
from app.models.state import SheetState

# Cython Libraries
from libs.core.models import Hitbox

# ---------------------------------------------------------


class AttackHitbox(HitboxSchema):
    """
    Resolves directional and frame-keyed attackboxes from SheetProperties.
    """

    def elevations(self, properties: SheetProperties, state: SheetState) -> List[int]:
        return [max(0, state.elevation if state.elevation is not None else 0)]

    def get(
        self,
        properties: SheetProperties,
        state: SheetState,
        elevation: int
    ) -> List[Hitbox]:
        if not properties or not isinstance(properties.hitboxes, dict):
            return []
        target_e = max(0, state.elevation if state.elevation is not None else 0)
        if max(0, elevation) != target_e:
            return []
        sep = settings.SEPARATOR
        anim = state.animation
        frame_key = f"{anim.action}{sep}{anim.direction}{sep}{anim.frame}"
        return properties.hitboxes.get(frame_key, [])
```

---

#### `src/app/services/factories/assets.py`
Adds `AssetFactory.configure(materials=..., projectiles=...)` for DI into `MaterialHitbox` and precomputation of `RotatedHitbox`, and updates `AssetFactory.hitbox` to raise `KeyError` on unknown recipe keys.

```python
"""
@domain.system
@app.service
@app.asset
@workflow.injection
@workflow.compositions

# Ontology: Source - app.services.factories.assets

Factory for instantiating Assets and flyweight Asset components.
"""
# Standard Libraries
from typing import (
    Dict,
    Optional,
)

# Application Libraries
from app.assets.base import (
    Asset,
    Taxonomy,
    Frame,
    Animation,
    HitboxSchema
)
from app.assets.animations import (
    CharacterAnimation,
    FrequencyAnimation,
    StateAnimation,
    SpriteAnimation,
    NoAnimation
)
from app.assets.frames import (
    BinaryFrame,
    CardinalFrame,
    CharacterFrame,
    FluidFrame,
    IconFrame,
    IterableFrame,
    MaterialFrame,
    MeterFrame,
    NoFrame,
    ObjectFrame,
    PaneFrame,
    ProjectileFrame,
    SeasonalFrame,
    SingleFrame,
    SpriteFrame,
    StageFrame,
    StateFrame,
    TraversalFrame
)
from app.assets.hitboxes import (
    AttackHitbox,
    DynamicHitbox,
    ElevatedHitbox,
    LayeredHitbox,
    MaterialHitbox,
    NoHitbox,
    RotatedHitbox,
    StageHitbox,
    StaticHitbox,
    SwitchHitbox
)
from app.game.logic.relations import MaterialIndex
from app.game.menus.bindings import Binding
from app.game.menus.core import Widget
from app.models.configurations import (
    Recipe,
    MenuNode
)
from app.models.properties import (
    AssetProperties,
    CursorProperties,
    WidgetProperties
)
from app.models.state import (
    AssetState,
    WidgetState
)
from app.static.semantics import (
    AssetCategories,
    AnimationRecipe,
    FrameRecipe,
    HitboxRecipe,
    Substrates
)


class AssetFactory:
    """
    Central factory for Asset assembly and flyweight component resolution.
    """
    # ----------- FLYWEIGHT COMPONENTS
    _FRAMES = {
        FrameRecipe.BINARY: BinaryFrame(),
        FrameRecipe.CARDINAL: CardinalFrame(),
        FrameRecipe.CHARACTER: CharacterFrame(),
        FrameRecipe.FLUID: FluidFrame(),
        FrameRecipe.ICON: IconFrame(),
        FrameRecipe.ITERABLE: IterableFrame(),
        FrameRecipe.MATERIAL: MaterialFrame(),
        FrameRecipe.METER: MeterFrame(),
        FrameRecipe.NONE: NoFrame(),
        FrameRecipe.OBJECT: ObjectFrame(),
        FrameRecipe.PANE: PaneFrame(),
        FrameRecipe.PROJECTILE: ProjectileFrame(),
        FrameRecipe.SEASONAL: SeasonalFrame(),
        FrameRecipe.SINGLE: SingleFrame(),
        FrameRecipe.SPRITE: SpriteFrame(),
        FrameRecipe.STAGE: StageFrame(),
        FrameRecipe.STATE: StateFrame(),
        FrameRecipe.TRAVERSAL: TraversalFrame(),
    }

    _ANIMATIONS = {
        AnimationRecipe.FREQUENCY: FrequencyAnimation(),
        AnimationRecipe.NONE: NoAnimation(),
        AnimationRecipe.CHARACTER: CharacterAnimation(),
        AnimationRecipe.SPRITE: SpriteAnimation(),
        AnimationRecipe.STATE: StateAnimation(),
    }

    _HITBOXES = {
        HitboxRecipe.ATTACK: AttackHitbox(),
        HitboxRecipe.DYNAMIC: DynamicHitbox(),
        HitboxRecipe.ELEVATED: ElevatedHitbox(),
        HitboxRecipe.LAYERED: LayeredHitbox(),
        HitboxRecipe.MATERIAL: MaterialHitbox(),
        HitboxRecipe.NONE: NoHitbox(),
        HitboxRecipe.STAGE: StageHitbox(),
        HitboxRecipe.STATIC: StaticHitbox(),
        HitboxRecipe.SWITCH: SwitchHitbox(),
        HitboxRecipe.ROTATED: RotatedHitbox()
    }

    @classmethod
    def configure(
        cls,
        materials: Optional[MaterialIndex] = None,
        projectiles: Optional[Dict[str, CursorProperties]] = None
    ) -> None:
        """
        Injects compiled runtime relations and precomputes flyweight hitbox tables.
        """
        if materials is not None:
            cls._HITBOXES[HitboxRecipe.MATERIAL].set_materials(materials)

        if projectiles:
            rotated = cls._HITBOXES[HitboxRecipe.ROTATED]
            for props in projectiles.values():
                rotated.precompute(props)

    @classmethod
    def frame(cls, recipe: str) -> Frame:
        return cls._FRAMES.get(recipe, cls._FRAMES[FrameRecipe.NONE])

    @classmethod
    def animation(cls, recipe: str) -> Animation:
        return cls._ANIMATIONS.get(recipe, cls._ANIMATIONS[AnimationRecipe.NONE])

    @classmethod
    def hitbox(cls, recipe: str) -> HitboxSchema:
        """Resolves a flyweight HitboxSchema by recipe key, raising KeyError if unknown."""
        if recipe not in cls._HITBOXES:
            raise KeyError(f"Unknown hitbox recipe: '{recipe}'")
        return cls._HITBOXES[recipe]

    @classmethod
    def asset(cls,
        category: str,
        instance: str,
        properties: AssetProperties,
        state: AssetState,
        recipe: Recipe,
        substrate: int = Substrates.STANDARD
    ) -> Asset:
        """
        Unified point of instantiation for all in-game Assets.
        """
        animation = cls.animation(recipe.animation)
        frame = cls.frame(recipe.frame)
        hitbox = cls.hitbox(recipe.hitbox)
        taxonomy = Taxonomy(state.id, state.name, category, instance)
        return Asset(
            taxonomy=taxonomy,
            properties=properties,
            state=state,
            frame=frame,
            animation=animation,
            hitbox=hitbox,
            substrate=substrate
        )

    @classmethod
    def widget(cls,
        node: MenuNode,
        properties: WidgetProperties,
        state: WidgetState,
        recipe: Recipe,
        binding: Optional[Binding] = None           
    ) -> Widget:
        animation = cls.animation(recipe.animation)
        frame = cls.frame(recipe.frame)
        taxonomy = Taxonomy(
            node.id, 
            node.name, 
            AssetCategories.WIDGETS, 
            node.instance
        )
        return Widget(
            taxonomy=taxonomy,
            properties=properties,
            state=state,
            frame=frame,
            animation=animation,
            binding=binding
        )
```

---

#### `src/app/services/factories/mechanics.py`
Fails fast with `KeyError` on unknown mechanic keys instead of silently falling back to `AnimationMechanics`.

```python
"""
@domain.system
@app.service
@app.mechanic
@workflow.injection

# Ontology: Source - app.services.factories.mechanics

Factory for instantiating Mechanics, Translators, and Input Devices.
"""
from __future__ import annotations

# Standard Libraries
from typing import (
    Any,
    Dict,
    Optional
)

# Application Libraries
from app.game.devices import (
    Controller,
    Device,
    Keyboard
)
from app.game.logic.mechanics import (
    AnimationMechanics,
    CognitionMechanics,
    CollisionMechanics,
    CombatMechanics,
    FluidMechanics,
    InteractionMechanics,
    Mechanic,
    MenuMechanics,
    MotionMechanics,
    NavigationMechanics,
    PlayerMechanics,
    PlotMechanics,
    ProjectileMechanics,
    RemoveMechanics,
    SeasonMechanics,
    SocialMechanics,
    SwitchMechanics,
    TelemetryMechanics,
    TransitionMechanics
)
from app.models.configurations import MechanicsInstance
from app.services.automaton import (
    Backend, 
    Compiler,
    Lambda,
    TransitionTranslator,
    GoalTranslator
)
from app.static.semantics import (
    Devices,
    Mechanics,
    Translators
)


class MechanicFactory:
    """
    Factory for constructing engine pipeline Mechanics, Translators, and Devices.
    """
    DEVICE_MAP = {
        Devices.KEYBOARD: Keyboard,
        Devices.CONTROLLER: Controller,
    }

    MECHANICS_MAP = {
        Mechanics.ANIMATION: AnimationMechanics,
        Mechanics.COGNITION: CognitionMechanics,
        Mechanics.COLLISION: CollisionMechanics,
        Mechanics.COMBAT: CombatMechanics,
        Mechanics.FLUID: FluidMechanics,
        Mechanics.INTERACTION: InteractionMechanics,
        Mechanics.MENU: MenuMechanics,
        Mechanics.MOTION: MotionMechanics,
        Mechanics.NAVIGATION: NavigationMechanics,
        Mechanics.PLAYER: PlayerMechanics,
        Mechanics.PLOT: PlotMechanics,
        Mechanics.PROJECTILE: ProjectileMechanics,
        Mechanics.REMOVE: RemoveMechanics,
        Mechanics.SEASON: SeasonMechanics,
        Mechanics.SOCIAL: SocialMechanics,
        Mechanics.SWITCH: SwitchMechanics,
        Mechanics.TELEMETRY: TelemetryMechanics,
        Mechanics.TRANSITION: TransitionMechanics,
    }

    TRANSLATOR_MAP = {
        Translators.LAMBDA: Lambda,
        Translators.COMPILER: Compiler,
    }

    @classmethod
    def device(cls, dev: str, mapping: dict) -> Device:
        target_cls = cls.DEVICE_MAP.get(dev, Keyboard)
        return target_cls(mapping)

    @classmethod
    def backend(cls, implementation: str) -> Backend:
        """Instantiates the configured ISL condition Backend via TRANSLATOR_MAP."""
        target_cls = cls.TRANSLATOR_MAP.get(implementation)
        if target_cls is None:
            raise ValueError(
                f"Unsupported translator implementation: '{implementation}'"
            )
        return target_cls()
    
    @staticmethod
    def transitions(implementation: str) -> TransitionTranslator:
        return TransitionTranslator(backend=MechanicFactory.backend(implementation))

    @staticmethod
    def goals(implementation: str) -> GoalTranslator:
        return GoalTranslator(backend=MechanicFactory.backend(implementation))
    
    @classmethod
    def mechanics(
        cls,
        config: MechanicsInstance,
        executors: Optional[Dict[str, Any]] = None,
        relations: Optional[Dict[str, Any]] = None
    ) -> Mechanic:
        """Instantiates a configured Mechanic and injects its executors and relations."""
        key = config.key
        if key not in cls.MECHANICS_MAP:
            raise KeyError(f"Unknown mechanic key: '{key}'")
        target_cls = cls.MECHANICS_MAP[key]
        mechanic_instance = target_cls()

        # 1. Resolve and inject executors
        executor_keys = config.executors
        if executor_keys:
            if executors is None:
                raise KeyError(
                    f"Mechanic '{key}' declared executors {executor_keys}, "
                    f"but no executor registry was provided."
                )
            for executor_key in executor_keys:
                executor = executors.get(executor_key)
                if executor is None:
                    raise KeyError(
                        f"Mechanic '{key}' requested executor '{executor_key}', "
                        f"but it is not registered in the active executor map."
                    )
                mechanic_instance.set_executor(executor_key, executor)

        # 2. Resolve and inject relations
        relation_keys = config.relations
        if relation_keys:
            if relations is None:
                raise KeyError(
                    f"Mechanic '{key}' declared relations {relation_keys}, "
                    f"but no relations registry was provided."
                )
            for relation_key in relation_keys:
                relation = relations.get(relation_key)
                if relation is None:
                    raise KeyError(
                        f"Mechanic '{key}' requested relation '{relation_key}', "
                        f"but it is not registered in the active relations map."
                    )
                mechanic_instance.set_relation(relation_key, relation)

        return mechanic_instance
```

---

#### `src/app/services/orchestration/builder.py`
Injects the compiled `MaterialIndex` and precomputes `RotatedHitbox` projectile tables in `Builder.build_relations()`.

```python
    def build_relations(self) -> None:
        """Compiles relational indices and configures flyweight AssetFactory hitbox schemas."""
        logger.info("Compiling relational indices...")
        materials = MaterialIndex.from_configuration(
            self.context.configurations.materials
        )
        projectiles = self.context.properties.cursors.projectiles
        self.relations = {
            Relations.SHORELINES: ShorelineIndex.from_properties(
                self.context.properties.geography.shorelines
            ),
            Relations.MATERIALS: materials,
            Relations.PROJECTILES: ProjectileIndex.from_properties(
                projectiles
            )
        }
        AssetFactory.configure(
            materials=materials,
            projectiles=projectiles
        )
```

---

#### `src/app/game/logic/predicates.py`
Uses `asset.hitbox.is_obstacle(...)` directly inside `is_weight()` so weight indexing never invokes `MaterialIndex()`.

```python
"""
@domain.logic
@app.module
@app.semantics

# Ontology: Source - app.game.logic.modules.predicates

Stateless Predicates for making assertions of Assets.
"""

# Application Libraries
from app.assets.base import Asset
from app.assets.hitboxes.core import NoHitbox
from app.assets.hitboxes.crafts import MaterialHitbox
from app.assets.hitboxes.objects import LayeredHitbox
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Directions,
    LayerProjections
)

# Cython Libraries
from libs.core.models import Position


def is_weight(asset: Asset) -> bool:
    """
    Evaluates physical candidate qualification for weight caching, excluding
    sensors, non-physical categories, NoHitbox assets, passable MaterialHitbox
    crafts, and non-blocking Door out-projections.
    """
    if asset.category in (
        AssetCategories.CURSORS,
        AssetCategories.EFFECTS,
        AssetCategories.GEOGRAPHY,
        AssetCategories.TILES,
        AssetCategories.WIDGETS
    ):
        return False

    if asset.properties.mass < 0:
        return False

    if isinstance(asset.hitbox, NoHitbox):
        return False

    if (
        isinstance(asset.hitbox, MaterialHitbox)
        and not asset.hitbox.is_obstacle(asset.state.blueprint)
    ):
        return False

    if (
        isinstance(asset.hitbox, LayeredHitbox)
        and asset.state.projection == LayerProjections.OUT
    ):
        return False

    return True


def is_obstacle(asset: Asset) -> bool:
    """
    Evaluates whether an entity instance qualifies as a physical navigational obstacle.
    """
    return asset.instance in (
        AssetInstances.CHESTS,
        AssetInstances.SIGNS,
        AssetInstances.CRATES,
        AssetInstances.GATES,
        AssetInstances.STRUTS,
        AssetInstances.OBSTACLES,
        AssetInstances.TREES,
    )


def is_hazard(asset: Asset) -> bool:
    """
    Evaluates whether a non-weight sensor Asset represents an environmental
    navigational hazard (such as active Fluid corridors) that autonomous
    pathfinding should avoid without blocking solid collision physics.
    """
    return asset.instance == AssetInstances.FLUIDS

def _in_corridor(
    px: int,
    py: int,
    ox: int,
    oy: int,
    w: int,
    l: int,
    length: int,
    direction: str
) -> bool:
    """
    Evaluates whether integer coordinate (px, py) intersects a single directional
    fluid corridor using half-open AABB bounds without heap allocation.
    """
    if length <= 0:
        return False

    if direction == Directions.DOWN:
        return ox <= px < ox + w and oy <= py < oy + length
    if direction == Directions.UP:
        return ox <= px < ox + w and oy - length <= py < oy
    if direction == Directions.RIGHT:
        return ox <= px < ox + length and oy <= py < oy + l
    if direction == Directions.LEFT:
        return ox - length <= px < ox and oy <= py < oy + l

    return False


def in_pool(position: Position, fluid: Asset) -> bool:
    """
    Evaluates whether a Cartesian coordinate intersects the annular pool of a fluid entity.
    """
    pool = fluid.state.pool
    if not pool or pool.w <= 0 or pool.l <= 0:
        return False

    px = int(position.x)
    py = int(position.y)
    return (
        pool.x <= px < pool.x + pool.w
        and pool.y <= py < pool.y + pool.l
    )


def in_stream(position: Position, fluid: Asset) -> bool:
    """
    Evaluates whether a Cartesian coordinate intersects the parent corridor or
    any active child branch corridor of the specified fluid entity.
    """
    px = int(position.x)
    py = int(position.y)
    fw = fluid.properties.dimensions.w
    fl = fluid.properties.dimensions.l

    if _in_corridor(
        px,
        py,
        int(fluid.state.position.x),
        int(fluid.state.position.y),
        fw,
        fl,
        fluid.state.length,
        fluid.state.source
    ):
        return True

    branches = fluid.state.branches
    if not branches:
        return False

    for branch in branches:
        if _in_corridor(
            px,
            py,
            int(branch.position.x),
            int(branch.position.y),
            fw,
            fl,
            branch.length,
            branch.source
        ):
            return True

    return False


def in_fluid(position: Position, fluid: Asset) -> bool:
    """
    Evaluates whether a Cartesian coordinate intersects either the annular pool
    or directional stream corridors of a fluid entity.
    """
    hitboxes = fluid.state.hitboxes
    if hitboxes:
        px = int(position.x)
        py = int(position.y)
        fx = int(fluid.state.position.x)
        fy = int(fluid.state.position.y)
        for hb in hitboxes:
            hx = fx + hb.position.x
            hy = fy + hb.position.y
            if (
                hx <= px < hx + hb.dimensions.w
                and hy <= py < hy + hb.dimensions.l
            ):
                return True

        for branch in fluid.state.branches or ():
            if not branch.hitboxes:
                continue
            bx = int(branch.position.x)
            by = int(branch.position.y)
            for hb in branch.hitboxes:
                hx = bx + hb.position.x
                hy = by + hb.position.y
                if (
                    hx <= px < hx + hb.dimensions.w
                    and hy <= py < hy + hb.dimensions.l
                ):
                    return True
        return False

    if in_pool(position, fluid):
        return True
    return in_stream(position, fluid)
```

---

### Task 2: Split Static and Dynamic Weights in `Board._cache`

#### `src/app/game/board/modules/cache.py`
Partitions physical weights into `cached_dynamics[layer]` ($m > 0$) and elevation-indexed `cached_statics[layer][elevation]` ($m = 0$), tracks monotonic `static_versions[layer]` with lazy dirty rebuilding on invalidation, bumps `static_versions` on static geometry mutations (`index_batch`, `evict_batch`, `relayer`, `rebuild_fluid`, `invalidate_statics`), and normalizes `get_obstacles(layer=None)`.

```python
"""
@domain.system
@app.module
@app.board

# Ontology: Source - app.game.board.modules.caches

Acceleration structures and caching container for the Board.
"""
# Standard Libraries
import logging
from typing import (
    List,
    Dict,
    Set,
    Tuple,
    Any,
    Optional
)

# Application Libraries
import app.static.settings as settings
import app.game.logic.predicates as predicates
from app.assets.base import Asset
from app.models.state.core import AssetState
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Directions
)

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Position
)

logger = logging.getLogger(__name__)

# -------------------------------------------


class Cache:
    """
    Encapsulates all categorical, instance, spatial grid, and layer-scoped caches.
    """
    cached_categories: Dict[str, Dict[str, List[Asset]]]
    cached_instances: Dict[str, Dict[str, List[Asset]]]
    cached_layers: Dict[str, List[Asset]]
    cached_renderables: Dict[str, List[Asset]]
    cached_weights: Dict[str, List[Asset]]
    cached_dynamics: Dict[str, List[Asset]]
    cached_static_weights: Dict[str, List[Asset]]
    cached_statics: Dict[str, Dict[int, List[Asset]]]
    static_versions: Dict[str, int]
    _statics_dirty: Set[str]
    cached_tilemap: Dict[str, Dict[str, Dict[Tuple[int, int], Asset]]]
    cached_fluidmap: Dict[str, Dict[Tuple[int, int], List[Asset]]]
    cached_characters: Dict[str, Any]
    cached_states: Dict[str, Dict[str, AssetState]]
    cached_sizes: Dict[str, Dimensions]
    assets_by_name: Dict[str, Asset]
    shorelines: Dict[str, List[Asset]]
    all_categories: Dict[str, List[Asset]]
    all_instances: Dict[str, List[Asset]]

    def __init__(self) -> None:
        """Initializes all categorical, instance, spatial grid, and layer-scoped stores."""
        self.clear()

    @staticmethod
    def _affects_statics(asset: Asset) -> bool:
        """
        Returns True if adding, removing, or relayering this asset alters
        static colliders, navigational obstacles, or static environmental sensors.
        Excludes transient effects (splashes), projectiles, and dynamic bodies (m > 0).
        """
        if predicates.is_weight(asset):
            return asset.properties.mass == 0
        return (
            asset.category in (
                AssetCategories.CRAFTS,
                AssetCategories.GEOGRAPHY,
                AssetCategories.TILES,
                AssetCategories.RESOURCES,
            )
            or asset.instance == AssetInstances.FLUIDS
        )

    @staticmethod
    def _asset_extent(asset: Asset) -> Tuple[int, int]:
        """
        Computes the far-corner (max_x, max_y) world extent contributed by an asset.
        """
        position = asset.state.position
        if position is None:
            return (0, 0)

        if asset.category == AssetCategories.TILES:
            multiple = asset.state.multiple
            if multiple is None:
                return (0, 0)
            ext_w = int(position.x) + (multiple.nx * asset.properties.dimensions.w)
            ext_l = int(position.y) + (multiple.ny * asset.properties.dimensions.l)
            return (ext_w, ext_l)

        if asset.dimensions:
            ext_w = int(position.x) + asset.dimensions.w
            ext_l = int(position.y) + asset.dimensions.l
            return (ext_w, ext_l)

        return (0, 0)

    def _index_static_elevations(self, layer: str, asset: Asset) -> None:
        """Registers a single static weight (m == 0) into its normalized elevation tier lists."""
        elevs = asset.hitbox.elevations(asset.properties, asset.state)
        if not elevs:
            return
        tier_map = self.cached_statics.setdefault(layer, {})
        if len(elevs) == 1:
            tier = max(0, elevs[0])
            tier_map.setdefault(tier, []).append(asset)
            return

        seen_tiers: Set[int] = set()
        for t in elevs:
            tier = max(0, t)
            if tier not in seen_tiers:
                seen_tiers.add(tier)
                tier_map.setdefault(tier, []).append(asset)

    def _rebuild_statics(self, layer: str) -> None:
        """Re-indexes all static weights (m == 0) by normalized elevation tier for a layer."""
        tier_map: Dict[int, List[Asset]] = {}
        for asset in self.cached_static_weights.get(layer, ()):
            elevs = asset.hitbox.elevations(asset.properties, asset.state)
            if not elevs:
                continue
            if len(elevs) == 1:
                tier = max(0, elevs[0])
                tier_map.setdefault(tier, []).append(asset)
            else:
                seen_tiers: Set[int] = set()
                for t in elevs:
                    tier = max(0, t)
                    if tier not in seen_tiers:
                        seen_tiers.add(tier)
                        tier_map.setdefault(tier, []).append(asset)
        self.cached_statics[layer] = tier_map
        self._statics_dirty.discard(layer)

    def init_layer(self, layer: str) -> None:
        """
        Initializes cache buckets for a specific layer.
        """
        if layer is None:
            return

        self.cached_categories.setdefault(layer, {})
        self.cached_instances.setdefault(layer, {})
        self.cached_layers.setdefault(layer, [])
        self.cached_renderables.setdefault(layer, [])
        self.cached_weights.setdefault(layer, [])
        self.cached_dynamics.setdefault(layer, [])
        self.cached_static_weights.setdefault(layer, [])
        self.cached_statics.setdefault(layer, {})
        self.static_versions.setdefault(layer, 0)
        self.cached_tilemap.setdefault(layer, {
            AssetInstances.ENVIRON: {},
            AssetInstances.CANOPY: {}
        })
        self.cached_fluidmap.setdefault(layer, {})
        self.cached_states.setdefault(layer, {})
        self.cached_sizes.setdefault(layer, Dimensions(w=0, l=0))
        self.shorelines.setdefault(layer, [])

    def map_fluid(self, layer: str, fluid: Asset) -> None:
        """
        Indexes parent corridors, annular pools, and all active branch corridors
        into the O(1) broad-phase fluid spatial hash grid.
        """
        if layer not in self.cached_fluidmap:
            self.cached_fluidmap[layer] = {}

        fx = fluid.state.position.x
        fy = fluid.state.position.y
        fw = fluid.properties.dimensions.w
        fl = fluid.properties.dimensions.l
        length = fluid.state.length
        direction = fluid.state.source

        def _index_box(x1: int, y1: int, x2: int, y2: int) -> None:
            if x2 > x1 and y2 > y1:
                start_cx = int(x1) // settings.TILE_HASH_SIZE
                end_cx = (int(x2) - 1) // settings.TILE_HASH_SIZE + 1
                start_cy = int(y1) // settings.TILE_HASH_SIZE
                end_cy = (int(y2) - 1) // settings.TILE_HASH_SIZE + 1
                for cx in range(start_cx, end_cx):
                    for cy in range(start_cy, end_cy):
                        bucket = self.cached_fluidmap[layer].setdefault((cx, cy), [])
                        if fluid not in bucket:
                            bucket.append(fluid)

        # 1. Parent directional stream corridor
        if length > 0:
            if direction == Directions.DOWN:
                _index_box(fx, fy, fx + fw, fy + length)
            elif direction == Directions.UP:
                _index_box(fx, fy - length, fx + fw, fy)
            elif direction == Directions.RIGHT:
                _index_box(fx, fy, fx + length, fy + fl)
            elif direction == Directions.LEFT:
                _index_box(fx - length, fy, fx, fy + fl)

        # 2. Annular pool
        pool = fluid.state.pool
        if pool and pool.w > 0 and pool.l > 0:
            _index_box(pool.x, pool.y, pool.x + pool.w, pool.y + pool.l)

        # 3. Child branch corridors
        branches = fluid.state.branches
        if branches:
            for branch in branches:
                if branch.length <= 0:
                    continue
                bx = branch.position.x
                by = branch.position.y
                b_dir = branch.source

                if b_dir == Directions.DOWN:
                    _index_box(bx, by, bx + fw, by + branch.length)
                elif b_dir == Directions.UP:
                    _index_box(bx, by - branch.length, bx + fw, by)
                elif b_dir == Directions.RIGHT:
                    _index_box(bx, by, bx + branch.length, by + fl)
                elif b_dir == Directions.LEFT:
                    _index_box(bx - branch.length, by, bx, by + fl)

    def rebuild_fluid(self, layer: str) -> None:
        """
        Rebuilds the O(1) spatial fluid grid cache for the specified layer and
        increments the layer's static geometry version counter.
        """
        if layer not in self.cached_fluidmap:
            self.cached_fluidmap[layer] = {}
        else:
            self.cached_fluidmap[layer].clear()

        fluids = self.get_instances(AssetInstances.FLUIDS, layer)
        for fluid in fluids:
            self.map_fluid(layer, fluid)

        self.static_versions[layer] = self.static_versions.get(layer, 0) + 1

    def invalidate_statics(self, layer: Optional[str] = None) -> None:
        """
        Marks static collider elevation buckets dirty and increments the
        monotonic static_version counter for one layer or all layers.
        """
        if layer is None:
            for l_key in self.cached_layers:
                self._statics_dirty.add(l_key)
                self.static_versions[l_key] = self.static_versions.get(l_key, 0) + 1
            return

        self._statics_dirty.add(layer)
        self.static_versions[layer] = self.static_versions.get(layer, 0) + 1

    def index_batch(self, assets: List[Asset]) -> None:
        """
        Indexes a batch of assets across all multi-tier dictionaries and spatial grids.
        """
        affected_fluid_layers: Set[str] = set()
        affected_static_layers: Set[str] = set()
        batch_extents: Dict[str, List[int]] = {}

        for asset in assets:
            layer = asset.state.layer
            cat = asset.category
            inst = asset.instance

            # Always register in global catalogues regardless of layer deployment
            self.all_categories.setdefault(cat, []).append(asset)
            self.all_instances.setdefault(inst, []).append(asset)

            if asset.name:
                self.assets_by_name[asset.name] = asset

            if cat == AssetCategories.SHEETS and inst in (
                AssetInstances.SPRITES,
                AssetInstances.PLAYERS
            ):
                if asset.name:
                    self.cached_characters[asset.name] = asset.state

            # Layerless assets (e.g., stateless Equipment wrappers) skip layer-scoped caches
            if layer is None:
                continue

            if layer not in self.cached_categories:
                self.init_layer(layer)

            self.cached_categories[layer].setdefault(cat, []).append(asset)
            self.cached_instances[layer].setdefault(inst, []).append(asset)
            self.cached_layers[layer].append(asset)

            if asset.name:
                self.cached_states[layer][asset.name] = asset.state

            if cat != AssetCategories.TILES:
                self.cached_renderables[layer].append(asset)

            if predicates.is_weight(asset):
                self.cached_weights[layer].append(asset)
                if asset.properties.mass > 0:
                    self.cached_dynamics[layer].append(asset)
                else:
                    self.cached_static_weights[layer].append(asset)
                    if layer not in self._statics_dirty:
                        self._index_static_elevations(layer, asset)
                    affected_static_layers.add(layer)
            elif self._affects_statics(asset):
                affected_static_layers.add(layer)

            if inst == AssetInstances.SHORELINES:
                self.shorelines[layer].append(asset)

            if inst == AssetInstances.FLUIDS:
                affected_fluid_layers.add(layer)

            # Update cached layer dimensions monotonically when the layer is not dirty
            if layer in self.cached_sizes:
                ext_w, ext_l = self._asset_extent(asset)
                bounds = batch_extents.get(layer)
                if bounds is None:
                    cur = self.cached_sizes[layer]
                    bounds = [cur.w, cur.l]
                    batch_extents[layer] = bounds
                if ext_w > bounds[0]:
                    bounds[0] = ext_w
                if ext_l > bounds[1]:
                    bounds[1] = ext_l

            if cat == AssetCategories.TILES:
                w = asset.properties.dimensions.w
                l = asset.properties.dimensions.l

                start_x = int(asset.state.position.x)
                start_y = int(asset.state.position.y)
                end_x = start_x + (asset.state.multiple.nx * w)
                end_y = start_y + (asset.state.multiple.ny * l)

                for cx in range(
                    start_x // settings.TILE_HASH_SIZE,
                    (end_x - 1) // settings.TILE_HASH_SIZE + 1
                ):
                    for cy in range(
                        start_y // settings.TILE_HASH_SIZE,
                        (end_y - 1) // settings.TILE_HASH_SIZE + 1
                    ):
                        if inst not in self.cached_tilemap[layer]:
                            self.cached_tilemap[layer][inst] = {}
                        self.cached_tilemap[layer][inst][(cx, cy)] = asset

        # Commit updated layer dimensions once per modified layer
        for layer, (max_w, max_l) in batch_extents.items():
            cur = self.cached_sizes[layer]
            if max_w > cur.w or max_l > cur.l:
                self.cached_sizes[layer] = Dimensions(w=max_w, l=max_l)

        for layer in affected_fluid_layers:
            self.rebuild_fluid(layer)

        for layer in affected_static_layers - affected_fluid_layers:
            self.static_versions[layer] = self.static_versions.get(layer, 0) + 1

    def evict_batch(self, removals: List[Asset]) -> None:
        """
        Evicts a batch of assets across all dictionaries, resolving B012 by avoiding method collision.
        """
        if not removals:
            return

        removal_set = set(removals)
        removal_names = {
            a.name for a in removals 
            if a.name
        }
        affected_layers = {
            a.state.layer for a in removals 
            if a.state and a.state.layer
        }
        affected_static_layers = {
            a.state.layer for a in removals
            if a.state and a.state.layer and self._affects_statics(a)
        }
        affected_categories = {
            a.category for a in removals 
            if a.category
        }
        affected_instances = {
            a.instance for a in removals 
            if a.instance
        }

        # 1. Layer-scoped cache filters
        for layer in affected_layers:
            if layer in self.cached_categories:
                for cat in affected_categories:
                    if cat in self.cached_categories[layer]:
                        self.cached_categories[layer][cat] = [
                            a for a in self.cached_categories[layer][cat]
                            if a not in removal_set
                        ]

            if layer in self.cached_instances:
                for inst in affected_instances:
                    if inst in self.cached_instances[layer]:
                        self.cached_instances[layer][inst] = [
                            a for a in self.cached_instances[layer][inst]
                            if a not in removal_set
                        ]

            if layer in self.cached_layers:
                self.cached_layers[layer] = [
                    a for a in self.cached_layers[layer]
                    if a not in removal_set
                ]

            if layer in self.cached_renderables:
                self.cached_renderables[layer] = [
                    a for a in self.cached_renderables[layer]
                    if a not in removal_set
                ]

            if layer in self.cached_weights:
                self.cached_weights[layer] = [
                    a for a in self.cached_weights[layer]
                    if a not in removal_set
                ]

            if layer in self.cached_dynamics:
                self.cached_dynamics[layer] = [
                    a for a in self.cached_dynamics[layer]
                    if a not in removal_set
                ]

            if layer in self.cached_static_weights:
                self.cached_static_weights[layer] = [
                    a for a in self.cached_static_weights[layer]
                    if a not in removal_set
                ]

            if layer in self.shorelines:
                self.shorelines[layer] = [
                    a for a in self.shorelines[layer]
                    if a not in removal_set
                ]

            # Invalidate cached layer size so extents recompute lazily after eviction
            self.cached_sizes.pop(layer, None)

        # 2. Global catalogue filters
        for cat in affected_categories:
            if cat in self.all_categories:
                self.all_categories[cat] = [
                    a for a in self.all_categories[cat]
                    if a not in removal_set
                ]

        for inst in affected_instances:
            if inst in self.all_instances:
                self.all_instances[inst] = [
                    a for a in self.all_instances[inst]
                    if a not in removal_set
                ]

        for asset in removals:
            if asset.name and self.assets_by_name.get(asset.name) is asset:
                del self.assets_by_name[asset.name]

            # Identity-safe eviction preserves reciprocal Door projections on other layers
            layer = asset.state.layer
            if (
                layer is not None
                and asset.name
                and layer in self.cached_states
                and self.cached_states[layer].get(asset.name) is asset.state
            ):
                del self.cached_states[layer][asset.name]

        # 3. Character cache evictions
        for name in removal_names:
            if name in self.cached_characters:
                del self.cached_characters[name]

        # 4. Invalidate fluid and static caches for modified layers
        rebuilt_fluid_layers: Set[str] = set()
        if AssetInstances.FLUIDS in affected_instances:
            for layer in affected_layers:
                self.rebuild_fluid(layer)
                rebuilt_fluid_layers.add(layer)

        for layer in affected_static_layers:
            self._statics_dirty.add(layer)
            if layer not in rebuilt_fluid_layers:
                self.static_versions[layer] = self.static_versions.get(layer, 0) + 1

    def relayer(self, asset: Asset, new_layer: Optional[str]) -> None:
        """
        Atomically shifts an asset's cache indexing across layers.
        """
        old_layer = asset.state.layer
        if old_layer == new_layer:
            return

        logger.debug(f"Relayering asset '{asset.taxonomy.name}' from layer '{old_layer}' -> '{new_layer}'.")

        cat = asset.category
        inst = asset.instance
        is_weight = predicates.is_weight(asset)
        affects_static = self._affects_statics(asset)

        if old_layer is not None:
            if old_layer in self.cached_categories and cat in self.cached_categories[old_layer]:
                if asset in self.cached_categories[old_layer][cat]:
                    self.cached_categories[old_layer][cat].remove(asset)

            if old_layer in self.cached_instances and inst in self.cached_instances[old_layer]:
                if asset in self.cached_instances[old_layer][inst]:
                    self.cached_instances[old_layer][inst].remove(asset)

            if old_layer in self.cached_layers and asset in self.cached_layers[old_layer]:
                self.cached_layers[old_layer].remove(asset)

            if old_layer in self.cached_renderables and asset in self.cached_renderables[old_layer]:
                self.cached_renderables[old_layer].remove(asset)

            if old_layer in self.cached_weights and asset in self.cached_weights[old_layer]:
                self.cached_weights[old_layer].remove(asset)

            if old_layer in self.cached_dynamics and asset in self.cached_dynamics[old_layer]:
                self.cached_dynamics[old_layer].remove(asset)

            if old_layer in self.cached_static_weights and asset in self.cached_static_weights[old_layer]:
                self.cached_static_weights[old_layer].remove(asset)

            if old_layer in self.shorelines and asset in self.shorelines[old_layer]:
                self.shorelines[old_layer].remove(asset)

            if (
                old_layer in self.cached_states
                and asset.name
                and self.cached_states[old_layer].get(asset.name) is asset.state
            ):
                del self.cached_states[old_layer][asset.name]

            self.cached_sizes.pop(old_layer, None)

            if affects_static:
                self._statics_dirty.add(old_layer)
                if inst != AssetInstances.FLUIDS:
                    self.static_versions[old_layer] = self.static_versions.get(old_layer, 0) + 1

        asset.state.layer = new_layer

        # Detaching an asset from all layers requires no target layer registration
        if new_layer is None:
            if inst == AssetInstances.FLUIDS and old_layer is not None:
                self.rebuild_fluid(old_layer)
            return

        if new_layer not in self.cached_categories:
            self.init_layer(new_layer)

        self.cached_categories[new_layer].setdefault(cat, []).append(asset)
        self.cached_instances[new_layer].setdefault(inst, []).append(asset)
        self.cached_layers[new_layer].append(asset)

        if asset.name:
            self.cached_states[new_layer][asset.name] = asset.state

        if cat != AssetCategories.TILES:
            self.cached_renderables[new_layer].append(asset)

        if is_weight:
            self.cached_weights[new_layer].append(asset)
            if asset.properties.mass > 0:
                self.cached_dynamics[new_layer].append(asset)
            else:
                self.cached_static_weights[new_layer].append(asset)
                if new_layer not in self._statics_dirty:
                    self._index_static_elevations(new_layer, asset)

        if inst == AssetInstances.SHORELINES:
            self.shorelines[new_layer].append(asset)

        if new_layer in self.cached_sizes:
            ext_w, ext_l = self._asset_extent(asset)
            cur = self.cached_sizes[new_layer]
            if ext_w > cur.w or ext_l > cur.l:
                self.cached_sizes[new_layer] = Dimensions(
                    w=max(cur.w, ext_w),
                    l=max(cur.l, ext_l)
                )

        if inst == AssetInstances.FLUIDS:
            if old_layer is not None:
                self.rebuild_fluid(old_layer)
            self.rebuild_fluid(new_layer)
        elif affects_static:
            self.static_versions[new_layer] = self.static_versions.get(new_layer, 0) + 1

    def clear(self) -> None:
        """
        Clears all indices and resets layer stores.
        """
        self.cached_categories = {}
        self.cached_instances = {}
        self.cached_layers = {}
        self.cached_renderables = {}
        self.cached_weights = {}
        self.cached_dynamics = {}
        self.cached_static_weights = {}
        self.cached_statics = {}
        self.static_versions = {}
        self._statics_dirty = set()
        self.cached_tilemap = {}
        self.cached_fluidmap = {}
        self.cached_characters = {}
        self.cached_states = {}
        self.cached_sizes = {}
        self.assets_by_name = {}
        self.shorelines = {}
        self.all_categories = {}
        self.all_instances = {}

    # ------------------------------------------------ GETTERS

    def get_asset(self, name: str, layer: Optional[str] = None) -> Optional[Asset]:
        """
        Retrieves an asset in O(1) by unique deployment name, optionally
        verifying membership on the specified layer.
        """
        asset = self.assets_by_name.get(name)
        if asset is None:
            return None
        if layer is not None and asset.state.layer != layer:
            return None
        return asset

    def get_size(self, layer: str) -> Dimensions:
        """
        Returns cached layer dimensions in O(1), lazily recomputing after
        evictions or relayer invalidations.
        """
        cached = self.cached_sizes.get(layer)
        if cached is not None:
            return cached

        layer_assets = self.cached_layers.get(layer)
        if layer_assets is None:
            return Dimensions(w=0, l=0)

        max_w = 0
        max_l = 0
        for asset in layer_assets:
            ext_w, ext_l = self._asset_extent(asset)
            if ext_w > max_w:
                max_w = ext_w
            if ext_l > max_l:
                max_l = ext_l

        size = Dimensions(w=max_w, l=max_l)
        self.cached_sizes[layer] = size
        return size

    def get_categories(self, category: str, layer: Optional[str] = None) -> List[Asset]:
        if layer is not None:
            return self.cached_categories.get(layer, {}).get(category, [])
        return self.all_categories.get(category, [])

    def get_instances(self, instance: str, layer: Optional[str] = None) -> List[Asset]:
        if layer is not None:
            return self.cached_instances.get(layer, {}).get(instance, [])
        return self.all_instances.get(instance, [])

    def get_layers(self) -> List[str]:
        return list(self.cached_categories.keys())

    def get_layer_assets(self, layer: str) -> List[Asset]:
        return self.cached_layers.get(layer, [])

    def get_renderables(self, layer: Optional[str] = None) -> List[Asset]:
        if layer is not None:
            return self.cached_renderables.get(layer, [])
        all_renderables: List[Asset] = []
        for layer_list in self.cached_renderables.values():
            all_renderables.extend(layer_list)
        return all_renderables

    def get_weights(self, layer: Optional[str] = None) -> List[Asset]:
        if layer is not None:
            return self.cached_weights.get(layer, [])
        all_weights: List[Asset] = []
        for layer_list in self.cached_weights.values():
            all_weights.extend(layer_list)
        return all_weights

    def get_dynamics(self, layer: Optional[str] = None) -> List[Asset]:
        """Returns dynamic weight assets (m > 0) for a layer or across all layers."""
        if layer is not None:
            return self.cached_dynamics.get(layer, [])
        all_dynamics: List[Asset] = []
        for layer_list in self.cached_dynamics.values():
            all_dynamics.extend(layer_list)
        return all_dynamics

    def get_statics(
        self,
        layer: Optional[str] = None,
        elevation: Optional[int] = None
    ) -> List[Asset]:
        """Returns pre-indexed static weight assets (m == 0) for a layer and optional elevation."""
        if layer is not None:
            if layer in self._statics_dirty:
                self._rebuild_statics(layer)
            if elevation is not None:
                return self.cached_statics.get(layer, {}).get(max(0, elevation), [])
            return self.cached_static_weights.get(layer, [])

        all_statics: List[Asset] = []
        for l_key in self.cached_layers:
            if l_key in self._statics_dirty:
                self._rebuild_statics(l_key)
            if elevation is not None:
                all_statics.extend(self.cached_statics.get(l_key, {}).get(max(0, elevation), []))
            else:
                all_statics.extend(self.cached_static_weights.get(l_key, []))
        return all_statics

    def get_static_version(self, layer: str) -> int:
        """Returns the monotonic static geometry version counter for a layer."""
        return self.static_versions.get(layer, 0)

    def get_obstacles(self, layer: Optional[str] = None) -> List[Asset]:
        """Retrieves navigational obstacle assets for a specific layer or across all layers."""
        obstacle_keys = (
            AssetInstances.CRATES,
            AssetInstances.GATES,
            AssetInstances.STRUTS,
            AssetInstances.SIGNS,
            AssetInstances.CHESTS
        )
        obstacles: List[Asset] = []
        if layer is not None:
            layer_inst = self.cached_instances.get(layer, {})
            for inst_key in obstacle_keys:
                obstacles.extend(layer_inst.get(inst_key, []))
            return obstacles

        for layer_inst in self.cached_instances.values():
            for inst_key in obstacle_keys:
                obstacles.extend(layer_inst.get(inst_key, []))
        return obstacles

    def get_shorelines(self, layer: Optional[str] = None) -> List[Asset]:
        if layer is not None:
            return self.shorelines.get(layer, [])
        all_shores: List[Asset] = []
        for l_shores in self.shorelines.values():
            all_shores.extend(l_shores)
        return all_shores

    def get_tile(
        self,
        layer: str,
        position: Position,
        instance: str = AssetInstances.ENVIRON
    ) -> Optional[Asset]:
        cx = int(position.x) // settings.TILE_HASH_SIZE
        cy = int(position.y) // settings.TILE_HASH_SIZE
        return self.cached_tilemap.get(layer, {}).get(instance, {}).get((cx, cy))

    def get_character(self, name: str) -> Optional[Any]:
        return self.cached_characters.get(name)

    def get_characters(self) -> Dict[str, Any]:
        return self.cached_characters

    def get_states(self, layer: str) -> Dict[str, AssetState]:
        """Returns the O(1) layer-scoped mapping of asset names to AssetStates."""
        return self.cached_states.get(layer, {})

    def get_fluid_bucket(self, layer: str, cx: int, cy: int) -> Optional[List[Asset]]:
        return self.cached_fluidmap.get(layer, {}).get((cx, cy))
```

---

#### `src/app/game/board/core.py`
Exposes `dynamics`, `statics`, `static_version`, `invalidate_statics`, and normalizes `obstacles(layer=None)` to aggregate across all layers.

```python
    def weights(self, layer: Optional[str] = None, elevation: Optional[int] = None) -> List[Asset]:
        """Retrieves physical weight candidates, optionally filtered by layer and elevation."""
        weights = self._cache.get_weights(layer)
        if elevation is not None:
            target_e = max(0, elevation)
            return [w for w in weights if target_e in w.hitbox.elevations(w.properties, w.state)]
        return weights

    def dynamics(self, layer: Optional[str] = None, elevation: Optional[int] = None) -> List[Asset]:
        """Retrieves dynamic physical weights (m > 0), optionally filtered by layer and elevation."""
        dynamics = self._cache.get_dynamics(layer)
        if elevation is not None:
            target_e = max(0, elevation)
            return [d for d in dynamics if target_e in d.hitbox.elevations(d.properties, d.state)]
        return dynamics

    def statics(self, layer: Optional[str] = None, elevation: Optional[int] = None) -> List[Asset]:
        """Retrieves static physical weights (m == 0), pre-indexed by normalized elevation."""
        return self._cache.get_statics(layer, elevation)

    def static_version(self, layer: str) -> int:
        """Returns the monotonic static geometry version counter for the specified layer."""
        return self._cache.get_static_version(layer)

    def invalidate_statics(self, layer: Optional[str] = None) -> None:
        """Marks static collider indices dirty and increments the per-layer static version."""
        self._cache.invalidate_statics(layer)

    def obstacles(self, layer: Optional[str] = None, elevation: Optional[int] = None) -> List[Asset]:
        """Retrieves navigational obstacle candidates across one or all layers."""
        obstacles = self._cache.get_obstacles(layer)
        if elevation is not None:
            target_e = max(0, elevation)
            return [o for o in obstacles if target_e in o.hitbox.elevations(o.properties, o.state)]
        return obstacles
```

---

### Task 3: Upgrade `Space`, `physics.pyx`, and `SpatialMechanic` to Zero-Allocation Bipartite Queries

#### `src/libs/core/math/space.pxd`
Declares `active_buckets`, `active_count`, C-level epoch-stamped pair deduplication tables, output pair buffers, and zero-allocation Cython query interfaces (`query_pairs`, `query_bipartite_pairs`, `probe_aabb`).

```cython
# cython: language_level=3
"""
@domain.logic
@domain.system
@app.library
@physics.space
@workflow.combat
@workflow.collisions

# Ontology: Libraries - libs.core.math.space

Cython header for spatial hash grid broad-phase collision queries.
"""

cdef class Space:
    cdef public int cell_size
    cdef public int max_entities
    cdef int num_buckets
    cdef int max_per_bucket
    cdef int* bucket_counts
    cdef int* bucket_data
    cdef int* active_buckets
    cdef int active_count
    cdef unsigned long long* pair_keys
    cdef unsigned int* pair_stamps
    cdef unsigned int pair_epoch
    cdef int pair_cap
    cdef int pair_count
    cdef int* pair_a
    cdef int* pair_b
    cdef int pair_out_cap

    cdef int query_pairs(self) except -1
    cdef int query_bipartite_pairs(self) except -1
    cdef int probe_aabb(self, int x, int y, int w, int l) except -1
    cpdef void clear(self)
    cpdef void insert(self, int entity_id, int x, int y, int w, int l)
    cpdef list query(self)
```

---

#### `src/libs/core/math/space.pyx`
Implements $O(K_{\text{occupied}})$ `clear()` and `query()`, replaces Python `set()` deduplication with a reusable C open-addressing epoch-stamped hash table and flat pair buffers (`pair_a`, `pair_b`), and provides `query_bipartite_pairs()` and `probe_aabb()` for persistent static grids.

```cython
"""
@domain.logic
@domain.system
@app.library
@physics.space
@workflow.combat
@workflow.collisions

# Ontology: Libraries - libs.core.math.space

Spatial hash grid for broad-phase collision candidate queries.
"""
# cython: language_level=3

from libc.stdlib cimport malloc, calloc, free
from libc.string cimport memset, memcpy


cdef class Space:
    """
    Uniform grid spatial hash storing integer entity IDs in flat C buckets
    with active-bucket tracking, dynamic per-bucket capacity expansion, and
    zero-allocation C-level pair deduplication.
    """

    def __init__(self, int cell_size=64, int max_entities=2000):
        """Allocates flat C-backed spatial hash bucket and pair buffers."""
        if cell_size <= 0:
            cell_size = 64
        if max_entities <= 0:
            max_entities = 1

        self.cell_size = cell_size
        self.max_entities = max_entities
        self.num_buckets = max_entities * 2
        self.max_per_bucket = 50
        self.active_count = 0
        self.pair_cap = 256
        self.pair_out_cap = 256
        self.pair_count = 0
        self.pair_epoch = 0

        self.bucket_counts = <int*>calloc(<size_t>self.num_buckets, sizeof(int))
        self.bucket_data = <int*>malloc(
            <size_t>self.num_buckets * <size_t>self.max_per_bucket * sizeof(int)
        )
        self.active_buckets = <int*>malloc(<size_t>self.num_buckets * sizeof(int))
        self.pair_keys = <unsigned long long*>malloc(
            <size_t>self.pair_cap * sizeof(unsigned long long)
        )
        self.pair_stamps = <unsigned int*>calloc(
            <size_t>self.pair_cap, sizeof(unsigned int)
        )
        self.pair_a = <int*>malloc(<size_t>self.pair_out_cap * sizeof(int))
        self.pair_b = <int*>malloc(<size_t>self.pair_out_cap * sizeof(int))

        if (
            self.bucket_counts is NULL
            or self.bucket_data is NULL
            or self.active_buckets is NULL
            or self.pair_keys is NULL
            or self.pair_stamps is NULL
            or self.pair_a is NULL
            or self.pair_b is NULL
        ):
            raise MemoryError()

    def __dealloc__(self):
        if self.bucket_counts is not NULL:
            free(self.bucket_counts)
            self.bucket_counts = NULL
        if self.bucket_data is not NULL:
            free(self.bucket_data)
            self.bucket_data = NULL
        if self.active_buckets is not NULL:
            free(self.active_buckets)
            self.active_buckets = NULL
        if self.pair_keys is not NULL:
            free(self.pair_keys)
            self.pair_keys = NULL
        if self.pair_stamps is not NULL:
            free(self.pair_stamps)
            self.pair_stamps = NULL
        if self.pair_a is not NULL:
            free(self.pair_a)
            self.pair_a = NULL
        if self.pair_b is not NULL:
            free(self.pair_b)
            self.pair_b = NULL

    cpdef void clear(self):
        """Resets only occupied buckets in O(active_count) time."""
        cdef int i
        if self.bucket_counts is not NULL and self.active_buckets is not NULL:
            for i in range(self.active_count):
                self.bucket_counts[self.active_buckets[i]] = 0
        self.active_count = 0

    cdef inline int _hash(self, int cx, int cy) noexcept nogil:
        cdef unsigned int h = (<unsigned int>cx * 73856093u) ^ (<unsigned int>cy * 19349663u)
        return <int>(h % <unsigned int>self.num_buckets)

    cdef inline void _reset_pair_table(self) noexcept:
        self.pair_epoch += 1
        if self.pair_epoch == 0:
            memset(self.pair_stamps, 0, <size_t>self.pair_cap * sizeof(unsigned int))
            self.pair_epoch = 1
        self.pair_count = 0

    cdef void _grow_pair_table(self) except *:
        cdef int old_cap = self.pair_cap
        cdef int new_cap = old_cap * 2
        cdef unsigned long long* new_keys = <unsigned long long*>malloc(
            <size_t>new_cap * sizeof(unsigned long long)
        )
        cdef unsigned int* new_stamps = <unsigned int*>calloc(
            <size_t>new_cap, sizeof(unsigned int)
        )
        if new_keys is NULL or new_stamps is NULL:
            if new_keys is not NULL:
                free(new_keys)
            if new_stamps is not NULL:
                free(new_stamps)
            raise MemoryError()

        cdef unsigned long long mask = <unsigned long long>(new_cap - 1)
        cdef unsigned int epoch = self.pair_epoch
        cdef unsigned long long key
        cdef int i, slot

        for i in range(old_cap):
            if self.pair_stamps[i] == epoch:
                key = self.pair_keys[i]
                slot = <int>(((key ^ (key >> 33)) * 11400714819323198485ULL) & mask)
                while new_stamps[slot] == epoch:
                    slot = (slot + 1) & <int>mask
                new_stamps[slot] = epoch
                new_keys[slot] = key

        free(self.pair_keys)
        free(self.pair_stamps)
        self.pair_keys = new_keys
        self.pair_stamps = new_stamps
        self.pair_cap = new_cap

    cdef void _grow_pair_out(self) except *:
        cdef int new_cap = self.pair_out_cap * 2
        cdef int* new_a = <int*>malloc(<size_t>new_cap * sizeof(int))
        cdef int* new_b = <int*>malloc(<size_t>new_cap * sizeof(int))
        if new_a is NULL or new_b is NULL:
            if new_a is not NULL:
                free(new_a)
            if new_b is not NULL:
                free(new_b)
            raise MemoryError()

        if self.pair_count > 0:
            memcpy(new_a, self.pair_a, <size_t>self.pair_count * sizeof(int))
            memcpy(new_b, self.pair_b, <size_t>self.pair_count * sizeof(int))

        free(self.pair_a)
        free(self.pair_b)
        self.pair_a = new_a
        self.pair_b = new_b
        self.pair_out_cap = new_cap

    cdef bint _record_pair(self, int id1, int id2) except -1:
        if (self.pair_count + 1) * 2 >= self.pair_cap:
            self._grow_pair_table()

        cdef unsigned long long key = (
            (<unsigned long long>(<unsigned int>id1) << 32)
            | <unsigned long long>(<unsigned int>id2)
        )
        cdef int mask = self.pair_cap - 1
        cdef unsigned int epoch = self.pair_epoch
        cdef int slot = <int>(
            ((key ^ (key >> 33)) * 11400714819323198485ULL)
            & <unsigned long long>mask
        )

        while self.pair_stamps[slot] == epoch:
            if self.pair_keys[slot] == key:
                return False
            slot = (slot + 1) & mask

        self.pair_stamps[slot] = epoch
        self.pair_keys[slot] = key

        if self.pair_count >= self.pair_out_cap:
            self._grow_pair_out()

        self.pair_a[self.pair_count] = id1
        self.pair_b[self.pair_count] = id2
        self.pair_count += 1
        return True

    # Promoted to cpdef for Python test accessibility
    cpdef void insert(self, int entity_id, int x, int y, int w, int l):
        """
        Inserts an entity into all grid cells overlapped by its half-open AABB
        [x, x + w) x [y, y + l), expanding bucket stride dynamically on overflow.
        """
        if w <= 0 or l <= 0:
            return

        cdef int min_x = x // self.cell_size
        cdef int min_y = y // self.cell_size
        cdef int max_x = (x + w - 1) // self.cell_size
        cdef int max_y = (y + l - 1) // self.cell_size
        cdef int cx, cy, h, count, idx
        cdef int old_cap, new_cap, b_idx, b, cnt
        cdef int* new_data

        for cx in range(min_x, max_x + 1):
            for cy in range(min_y, max_y + 1):
                h = self._hash(cx, cy)
                count = self.bucket_counts[h]
                if count == 0:
                    self.active_buckets[self.active_count] = h
                    self.active_count += 1
                elif self.bucket_data[h * self.max_per_bucket + count - 1] == entity_id:
                    continue
                elif count >= self.max_per_bucket:
                    # Double per-bucket stride to prevent silent entity dropping
                    old_cap = self.max_per_bucket
                    new_cap = old_cap * 2
                    new_data = <int*>malloc(
                        <size_t>self.num_buckets * <size_t>new_cap * sizeof(int)
                    )
                    if new_data is NULL:
                        raise MemoryError()
                    for b_idx in range(self.active_count):
                        b = self.active_buckets[b_idx]
                        cnt = self.bucket_counts[b]
                        if cnt > 0:
                            memcpy(
                                &new_data[b * new_cap],
                                &self.bucket_data[b * old_cap],
                                <size_t>cnt * sizeof(int)
                            )
                    free(self.bucket_data)
                    self.bucket_data = new_data
                    self.max_per_bucket = new_cap

                idx = h * self.max_per_bucket + count
                self.bucket_data[idx] = entity_id
                self.bucket_counts[h] = count + 1

    cdef int query_pairs(self) except -1:
        """
        Populates self.pair_a / self.pair_b with all unique unordered candidate
        pairs across active buckets and returns the pair count without Python allocations.
        """
        cdef int a_idx, b, base, i, j, count, id1, id2

        self._reset_pair_table()
        for a_idx in range(self.active_count):
            b = self.active_buckets[a_idx]
            count = self.bucket_counts[b]
            if count > 1:
                base = b * self.max_per_bucket
                for i in range(count):
                    for j in range(i + 1, count):
                        id1 = self.bucket_data[base + i]
                        id2 = self.bucket_data[base + j]
                        if id1 == id2:
                            continue
                        if id1 > id2:
                            id1, id2 = id2, id1
                        self._record_pair(id1, id2)

        return self.pair_count

    cdef int query_bipartite_pairs(self) except -1:
        """
        Populates self.pair_a (< 0) and self.pair_b (>= 0) with unique bipartite
        candidate pairs across active buckets, skipping negative-vs-negative and
        positive-vs-positive pairs entirely.
        """
        cdef int a_idx, b, base, i, j, count, id_pos, id_neg

        self._reset_pair_table()
        for a_idx in range(self.active_count):
            b = self.active_buckets[a_idx]
            count = self.bucket_counts[b]
            if count > 1:
                base = b * self.max_per_bucket
                for i in range(count):
                    id_pos = self.bucket_data[base + i]
                    if id_pos < 0:
                        continue
                    for j in range(count):
                        id_neg = self.bucket_data[base + j]
                        if id_neg < 0:
                            self._record_pair(id_neg, id_pos)

        return self.pair_count

    cdef int probe_aabb(self, int x, int y, int w, int l) except -1:
        """
        Probes buckets overlapped by half-open AABB [x, x + w) x [y, y + l)
        against a pre-populated Space without mutating buckets. Writes unique
        stored IDs into self.pair_b[0..n-1] and returns n.
        """
        if w <= 0 or l <= 0 or self.active_count == 0:
            return 0

        self._reset_pair_table()

        cdef int min_x = x // self.cell_size
        cdef int min_y = y // self.cell_size
        cdef int max_x = (x + w - 1) // self.cell_size
        cdef int max_y = (y + l - 1) // self.cell_size
        cdef int cx, cy, h, count, i, base

        for cx in range(min_x, max_x + 1):
            for cy in range(min_y, max_y + 1):
                h = self._hash(cx, cy)
                count = self.bucket_counts[h]
                if count > 0:
                    base = h * self.max_per_bucket
                    for i in range(count):
                        self._record_pair(0, self.bucket_data[base + i])

        return self.pair_count

    # Promoted to cpdef for Python test accessibility
    cpdef list query(self):
        """Returns unique unordered candidate (id1, id2) pairs across occupied buckets."""
        cdef int n = self.query_pairs()
        cdef list pairs = []
        cdef int k
        for k in range(n):
            pairs.append((self.pair_a[k], self.pair_b[k]))
        return pairs
```

---

#### `src/libs/core/math/geometry.pxd`
Defines zero-allocation `cdef inline bint c_intersects` and `cdef inline bint c_bounded` for direct inlining in `physics.pyx`, and declares `intersections` alongside all existing `geometry` entry points.

```cython
# cython: language_level=3
"""
@domain.system
@domain.logic
@app.library
@workflow.combat
@workflow.collisions
@workflow.navigation
@workflow.rendering

# Ontology: Libraries - libs.core.math.geometry

Cython header for geometrical calculations and inline narrow-phase predicates.
"""
from libs.core.models cimport (
    Position,
    Dimensions,
    Hitbox,
    Boundary
)


cdef inline bint c_intersects(
    int x1,
    int y1,
    list hbs1,
    int x2,
    int y2,
    list hbs2
):
    """
    Zero-allocation narrow-phase AABB overlap predicate across two hitbox lists.
    """
    cdef int ax1, ay1, w1, h1
    cdef int ax2, ay2, w2, h2
    cdef Hitbox hb1, hb2
    cdef object item1, item2

    if not hbs1 or not hbs2:
        return False

    for item1 in hbs1:
        hb1 = item1
        ax1 = x1 + hb1.position.x
        ay1 = y1 + hb1.position.y
        w1 = hb1.dimensions.w
        h1 = hb1.dimensions.l

        for item2 in hbs2:
            hb2 = item2
            ax2 = x2 + hb2.position.x
            ay2 = y2 + hb2.position.y
            w2 = hb2.dimensions.w
            h2 = hb2.dimensions.l

            if (
                ax1 < ax2 + w2 and ax1 + w1 > ax2
                and ay1 < ay2 + h2 and ay1 + h1 > ay2
            ):
                return True

    return False


cdef inline bint c_bounded(
    int a_x,
    int a_y,
    list hitboxes,
    int b_x,
    int b_y,
    int b_w,
    int b_l
):
    """
    Zero-allocation narrow-phase predicate evaluating Asset hitboxes against a raw AABB.
    """
    cdef int x1, y1, w1, h1
    cdef Hitbox hb
    cdef object item

    if not hitboxes:
        return False

    for item in hitboxes:
        hb = item
        x1 = a_x + hb.position.x
        y1 = a_y + hb.position.y
        w1 = hb.dimensions.w
        h1 = hb.dimensions.l

        if (
            x1 < b_x + b_w and x1 + w1 > b_x
            and y1 < b_y + b_l and y1 + h1 > b_y
        ):
            return True

    return False


cpdef Position camera(Position focus, Dimensions dim, Dimensions screen, Dimensions board)
cpdef bint onscreen(Position pos, Dimensions dim, Position p_pos, Dimensions p_dim, Dimensions screen, Dimensions board)
cpdef tuple intersects(Position pos1, list hitboxes1, Position pos2, list hitboxes2)
cpdef list intersections(Position pos1, list hitboxes1, Position pos2, list hitboxes2)
cpdef bint cone(int sx, int sy, int tx, int ty, int radius, double cos_threshold, str direction)
cpdef bint nearby(int sx, int sy, int tx, int ty, int radius)
cpdef tuple bounded(int a_x, int a_y, list hitboxes, int b_x, int b_y, int b_w, int b_l)
cpdef bint inside(int px, int py, list aabbs)
cpdef bint occluded(int qx, int qy, int qw, int ql, list obstacles)
cdef bint c_punctures(float x1, float y1, float x2, float y2, float rx, float ry, float rw, float rl) noexcept nogil
cpdef bint punctures(float x1, float y1, float x2, float y2, float rx, float ry, float rw, float rl)
cpdef bint los(float x1, float y1, float x2, float y2, list rects)
cpdef list contours(list rects)
cpdef tuple raycast(int sx, int sy, int sw, int sl, str direction, list obstacles, int max_dist)
```

---

#### `src/libs/core/math/geometry.pyx`
Adds `intersections(...)` directly below `intersects(...)` to return all overlapping `(hb1, hb2)` pairs for compound multi-hitbox resolution (B053.2).

```cython
cpdef list intersections(
    Position pos1,
    list hitboxes1,
    Position pos2,
    list hitboxes2
):
    """
    Returns all intersecting (hb1, hb2) pairs across two hitbox collections
    to support compound multi-hitbox collision resolution.
    """
    cdef int x1, y1, w1, h1
    cdef int x2, y2, w2, h2
    cdef Hitbox hb1, hb2
    cdef list hits = []

    if not hitboxes1 or not hitboxes2:
        return hits

    for item1 in hitboxes1:
        hb1 = item1
        x1 = pos1.x + hb1.position.x
        y1 = pos1.y + hb1.position.y
        w1 = hb1.dimensions.w
        h1 = hb1.dimensions.l

        for item2 in hitboxes2:
            hb2 = item2
            x2 = pos2.x + hb2.position.x
            y2 = pos2.y + hb2.position.y
            w2 = hb2.dimensions.w
            h2 = hb2.dimensions.l

            if (x1 < x2 + w2 and x1 + w1 > x2 and
                y1 < y2 + h2 and y1 + h1 > y2):
                hits.append((hb1, hb2))

    return hits
```

---

#### `src/libs/core/math/physics.pyx`
* Consumes `c_intersects`, `c_bounded`, and `Space`'s C-level pair buffers (`query_pairs`, `query_bipartite_pairs`, `probe_aabb`).
* Unifies `boundaries` and `environment` into `bipartite`.
* Adds `bipartite_collisions(dynamics, statics, grid)` plus persistent static-grid entry points (`populate_statics`, `query_statics`, `populate_bounds`, `query_bounds`).
* Inserts compound hitboxes tightly per hitbox in `_insert_hitboxes`.
* Uses `<int>p.rx` / `<int>p.ry` in `integrate` and `<int>overlap_x` / `<int>overlap_y` in `constrain`.

```cython
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
```

---

#### `src/app/game/logic/mechanics/spatial/base.py`
Removes all `dict(enumerate(...))` allocations, removes the duplicate `self.grid.clear()` in `intersections`, and adds `bipartite(dynamics, statics, elevation)`.

```python
"""
@domain.concrete
@domain.logic
@app.base
@app.mechanic
@physics.space
@workflow.collisions
@workflow.combat
@workflow.interactions

# Ontology: Source - app.game.logic.mechanics.spatial.base

SpatialMechanic implementation base class.
"""
# Standard Libraries
import collections
from typing import (
    Dict,
    List, 
    Set,
    Tuple,
    Optional
)
import logging

# Application Libraries
from app.static.semantics import AssetInstances
from app.assets.base import Asset
from app.game.logic.mechanics import Mechanic

# Cython Libraries
import libs.core.math.physics as physics
from libs.core.math.space import Space
from libs.core.models import (
    Position, 
    Dimensions, 
    Hitbox,
    Boundary
)

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------------------


class SpatialMechanic(Mechanic):
    """
    ## SpatialMechanic

    Base mechanic for systems requiring broad-phase spatial hashing and geometry resolution.
    """
    grid: Space

    @staticmethod
    def _elevations(asset: Asset, include_empty: bool = False) -> Set[int]:
        """
        Resolves normalized non-negative elevation tiers occupied by an asset.
        When include_empty is False, preserves sensor schemas (such as LayeredHitbox
        OUT projections) that report no solid collision elevations while still
        exposing active hitboxes, and excludes intentionally empty hitbox schemas.
        """
        tiers = {
            max(0, t)
            for t in asset.hitbox.elevations(asset.properties, asset.state)
        }
        if tiers:
            return tiers
        if include_empty or asset.hitboxes:
            return {max(0, asset.elevation)}
        return set()

    def __init__(self, cell_size: int = 64, max_entities: int = 2000):
        # Allocated exactly once in memory during orchestration
        super().__init__()
        self.grid = Space(cell_size=cell_size, max_entities=max_entities)

    def center(self, position: Position, dimensions: Dimensions):
        return (position.x + dimensions.w / 2, position.y + dimensions.l / 2)

    def collisions(self, assets: List[Asset], elevation: Optional[int] = None) -> List[Tuple[Asset, Asset]]:
        """
        Extracts primitives using standard physics hitboxes, queries the C-grid, 
        and returns colliding Asset pairs.
        """
        if len(assets) < 2:
            return []
        primitive_data = [
            asset.primitive(
                i,
                asset.hitbox.get(asset.properties, asset.state, elevation)
            )
            if elevation is not None else 
            asset.primitive(i)
            for i, asset in enumerate(assets)
        ]
        colliding_indices = physics.collisions(primitive_data, self.grid)
        return [(assets[id_a], assets[id_b]) for id_a, id_b in colliding_indices]

    def bipartite(
        self,
        dynamics: List[Asset],
        statics: List[Asset],
        elevation: Optional[int] = None
    ) -> List[Tuple[Asset, Asset]]:
        """
        Evaluates dynamic-vs-static candidate collisions without hashing or
        evaluating static-vs-static or dynamic-vs-dynamic pairs.
        """
        if not dynamics or not statics:
            return []
        dynamic_primitives = [
            asset.primitive(
                i,
                asset.hitbox.get(asset.properties, asset.state, elevation)
            )
            if elevation is not None else
            asset.primitive(i)
            for i, asset in enumerate(dynamics)
        ]
        static_primitives = [
            asset.primitive(
                i,
                asset.hitbox.get(asset.properties, asset.state, elevation)
            )
            if elevation is not None else
            asset.primitive(i)
            for i, asset in enumerate(statics)
        ]
        colliding_indices = physics.bipartite_collisions(
            dynamic_primitives,
            static_primitives,
            self.grid
        )
        return [(dynamics[id_a], statics[id_b]) for id_a, id_b in colliding_indices]

    def intersections(self, assets: List[Asset]) -> List[Tuple[Asset, Asset]]:
        """
        Evaluates spatial intersections across active asset hitboxes partitioned by
        shared elevation tiers, applying a 2px contact margin to motive entities so
        flush post-collision contact registers while preserving target HitboxSchema
        geometry (such as LayeredHitbox) and respecting intentionally empty hitboxes.
        """
        if len(assets) < 2:
            return []

        by_elevation: Dict[int, List[Asset]] = collections.defaultdict(list)
        for asset in assets:
            for tier in self._elevations(asset, include_empty=False):
                by_elevation[tier].append(asset)

        results: List[Tuple[Asset, Asset]] = []
        seen: Set[Tuple[int, int]] = set()

        for tier, tier_assets in by_elevation.items():
            if len(tier_assets) < 2:
                continue

            primitive_data = []
            for i, asset in enumerate(tier_assets):
                base_hbs = asset.hitbox.get(asset.properties, asset.state, tier)

                if asset.instance in (
                    AssetInstances.PLAYERS, 
                    AssetInstances.SPRITES
                ):
                    padded_hbs = [
                        Hitbox(
                            position=Position(x=hb.position.x - 2, y=hb.position.y - 2),
                            dimensions=Dimensions(w=hb.dimensions.w + 4, l=hb.dimensions.l + 4)
                        )
                        for hb in base_hbs
                    ]
                    primitive_data.append(asset.primitive(i, hitboxes=padded_hbs))
                else:
                    primitive_data.append(asset.primitive(i, hitboxes=base_hbs))

            colliding_indices = physics.collisions(primitive_data, self.grid)
            for id_a, id_b in colliding_indices:
                asset_a = tier_assets[id_a]
                asset_b = tier_assets[id_b]
                pair_key = (min(id(asset_a), id(asset_b)), max(id(asset_a), id(asset_b)))
                if pair_key not in seen:
                    seen.add(pair_key)
                    results.append((asset_a, asset_b))

        return results

    def proximities(self, assets: List[Asset]) -> List[Tuple[Asset, Asset]]:
        """
        Bypasses physics hitboxes, constructing a virtual hitbox padded by 
        the entity's action radius. This determines interaction reach,
        filtered to candidate pairs sharing an elevation tier.
        """
        if len(assets) < 2:
            return []

        primitive_data = []
        for i, asset in enumerate(assets):
            # Extract action radius safely, defaulting to 0 when parameters are absent
            # so static targets remain indexed 1:1 with assets for physics.collisions
            params = asset.state.mutators.parameters
            radius = (
                params.action.radius
                if params is not None and params.action is not None
                else 0
            )

            # Pad the dimensions by the radius in all directions
            pad_hb = Hitbox(
                position=Position(x=-radius, y=-radius), 
                dimensions=Dimensions(
                    w=asset.dimensions.w + (radius * 2), 
                    l=asset.dimensions.l + (radius * 2)
                )
            )
            primitive_data.append(asset.primitive(i, hitboxes=[pad_hb]))

        colliding_indices = physics.collisions(primitive_data, self.grid)
        results: List[Tuple[Asset, Asset]] = []
        for id_a, id_b in colliding_indices:
            asset_a = assets[id_a]
            asset_b = assets[id_b]
            if (
                self._elevations(asset_a, include_empty=True)
                & self._elevations(asset_b, include_empty=True)
            ):
                results.append((asset_a, asset_b))

        return results

    def constrain(
        self, 
        assets: List[Asset], 
        boundaries: List[Boundary], 
        elevation: Optional[int] = None
    ) -> List[Tuple[Asset, Boundary]]:        
        """
        Extracts primitives, queries the C-grid for Negative IDs (Boundaries), 
        and returns colliding constraint pairs.
        """
        if not assets or not boundaries:
            return []
        primitive_assets = [
            asset.primitive(
                i,
                asset.hitbox.get(asset.properties, asset.state, elevation)
            )
            if elevation is not None else 
            asset.primitive(i)
            for i, asset in enumerate(assets)
        ]
        primitive_bounds = [
            (i, b.position.x, b.position.y, b.dimensions.w, b.dimensions.l)
            for i, b in enumerate(boundaries)
        ]
        colliding_indices = physics.bipartite(primitive_assets, primitive_bounds, self.grid)
        return [(assets[id_a], boundaries[id_b]) for id_a, id_b in colliding_indices]
```

---

### Task 4: Refactor `CollisionMechanics` for Active-Tier Bipartite & Multi-Hitbox Resolution

#### `src/app/game/logic/mechanics/spatial/collision.py`
* **B053.1**: Skips any layer or elevation tier with zero active non-falling dynamic bodies.
* Caches static primitives and persistent static `Space` grids per `(layer, elevation, static_version)` (reusing C buffers on rebuild) plus persistent perimeter `Space` grids.
* Runs dynamic-vs-dynamic (`physics.collisions`) and dynamic-vs-static (`physics.query_statics`) separately, refreshing dynamic primitive coordinates only when Phase 1 or Phase 2A resolves a shift.
* **B053.2**: Resolves *all* intersecting hitbox pairs from `geometry.intersections(...)` in `_resolve`, ordered by descending overlap area to resolve corners cleanly without internal-seam snags.

```python
"""
@domain.concrete
@domain.logic
@app.mechanic
@physics.space
@workflow.collisions

# Ontology: Source - app.game.logic.mechanics.spatial.collision

CollisionMechanics implementation.
"""
from __future__ import annotations

# Standard Libraries
from typing import (
    Dict,
    List,
    Optional,
    Tuple,
    TYPE_CHECKING
)
import collections
import logging

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board

from app.assets.base import Asset
from app.static.semantics import (
    AssetInstances,
    Directions
)
from app.game.logic.mechanics.spatial import SpatialMechanic
from app.models.state import (
    DevicePayload,
    MotiveState,
    SheetState
)

# Cython Libraries
import libs.core.math.physics as physics
import libs.core.math.geometry as geometry
from libs.core.math.space import Space
from libs.core.models import (
    Boundary,
    Hitbox,
    Position
)
# -----------------------------------------------

logger = logging.getLogger(__name__)

# Stair tread hysteresis thresholds preventing exact-boundary tier oscillation
STAIR_ASCENT_LOW: float = 0.15
STAIR_DESCENT_LOW: float = 0.10
STAIR_ASCENT_HIGH: float = 0.85
STAIR_DESCENT_HIGH: float = 0.90

# -----------------------------------------------


class CollisionMechanics(SpatialMechanic):
    """
    ## CollisionMechanics

    Mechanic responsible for resolving Asset collisions natively.
    """
    _board_ref: Optional[Board]
    _static_cache: Dict[Tuple[str, int], Tuple[int, List[Asset], List[Tuple], Space]]
    _perimeter_cache: Dict[str, Tuple[Optional[List[Boundary]], int, List[Tuple], Space]]

    @staticmethod
    def _stair_hitboxes(stairs: Asset) -> List[Hitbox]:
        """
        Resolves active blueprint hitboxes for a stair asset, falling back to full
        frame dimensions only when its HitboxSchema returns an empty list.
        """
        hitboxes = stairs.hitboxes
        if hitboxes:
            return hitboxes
        if stairs.dimensions:
            return [Hitbox(Position(0, 0), stairs.dimensions)]
        return []

    def __init__(self, cell_size: int = 64, max_entities: int = 2000):
        """Initializes the broad-phase spatial grid and versioned static caches."""
        super().__init__(cell_size=cell_size, max_entities=max_entities)
        self._board_ref = None
        self._static_cache = {}
        self._perimeter_cache = {}

    def _static_tier(
        self,
        board: Board,
        layer: str,
        elevation: int
    ) -> Tuple[List[Asset], List[Tuple], Space]:
        """
        Retrieves or builds the cached static asset list, Cython primitive buffer,
        and pre-populated Space grid for a (layer, elevation) tier keyed by
        Board.static_version(layer).
        """
        version = board.static_version(layer)
        key = (layer, elevation)
        cached = self._static_cache.get(key)
        if cached is not None and cached[0] == version:
            return cached[1], cached[2], cached[3]

        tier_statics = board.statics(layer, elevation)
        active_statics: List[Asset] = []
        static_primitives: List[Tuple] = []
        idx = 0
        for asset in tier_statics:
            hbs = asset.hitbox.get(asset.properties, asset.state, elevation)
            if not hbs:
                continue
            static_primitives.append(asset.primitive(idx, hbs))
            active_statics.append(asset)
            idx += 1

        static_grid = (
            cached[3]
            if cached is not None
            else Space(
                cell_size=self.grid.cell_size,
                max_entities=max(self.grid.max_entities, len(active_statics) + 64)
            )
        )
        physics.populate_statics(static_primitives, static_grid)
        self._static_cache[key] = (version, active_statics, static_primitives, static_grid)
        return active_statics, static_primitives, static_grid

    def _perimeter_tier(
        self,
        layer: str,
        perimeters: List[Boundary]
    ) -> Tuple[List[Tuple], Space]:
        """
        Retrieves or builds the cached perimeter primitive buffer and pre-populated
        Space grid for base terrain (elevation == 0) boundary constraints.
        """
        cached = self._perimeter_cache.get(layer)
        perim_len = len(perimeters)
        if cached is not None and cached[0] is perimeters and cached[1] == perim_len:
            return cached[2], cached[3]

        bound_primitives = [
            (i, b.position.x, b.position.y, b.dimensions.w, b.dimensions.l)
            for i, b in enumerate(perimeters)
        ]
        bound_grid = (
            cached[3]
            if cached is not None
            else Space(
                cell_size=self.grid.cell_size,
                max_entities=max(256, perim_len + 32)
            )
        )
        physics.populate_bounds(bound_primitives, bound_grid)
        self._perimeter_cache[layer] = (perimeters, perim_len, bound_primitives, bound_grid)
        return bound_primitives, bound_grid

    def _traverse_stairs(self, sprite: Asset, stairs: Asset) -> None:
        """
        Evaluates dynamic body progression across stair tread bounds and shifts elevation.
        Combines normalized sensory foot-anchor positioning with directional velocity
        gating to prevent premature tier transitions and boundary snapping.
        """
        e_base = stairs.elevation
        e_top = e_base + stairs.state.delta
        curr_e = sprite.elevation
        prev_e = sprite.elevation

        # Entity must be on either the base or summit tier of the stair incline
        if curr_e != e_base and curr_e != e_top:
            return

        direction = stairs.state.blueprint

        vel = (
            sprite.state.velocity
            if isinstance(sprite.state, (SheetState, MotiveState))
            else None
        )
        vx = vel.vx if vel is not None else 0.0
        vy = vel.vy if vel is not None else 0.0

        # Calculate sensory ground contact point (center-x, bottom-y) from active hitboxes
        mover_hbs = sprite.hitboxes
        if mover_hbs:
            hb_min_x = min(
                sprite.state.position.x + hb.position.x
                for hb in mover_hbs
            )
            hb_max_x = max(
                sprite.state.position.x + hb.position.x + hb.dimensions.w
                for hb in mover_hbs
            )
            hb_max_y = max(
                sprite.state.position.y + hb.position.y + hb.dimensions.l
                for hb in mover_hbs
            )
            foot_x = (hb_min_x + hb_max_x) // 2
            foot_y = hb_max_y
        else:
            dim_w = sprite.dimensions.w if sprite.dimensions else 0
            dim_l = sprite.dimensions.l if sprite.dimensions else 0
            foot_x = sprite.state.position.x + (dim_w // 2)
            foot_y = sprite.state.position.y + dim_l

        # Resolve active stair tread bounds from blueprint hitboxes (fallback to dimensions)
        stair_hbs = self._stair_hitboxes(stairs)
        if not stair_hbs:
            return

        min_x = min(stairs.state.position.x + hb.position.x for hb in stair_hbs)
        min_y = min(stairs.state.position.y + hb.position.y for hb in stair_hbs)
        max_x = max(
            stairs.state.position.x + hb.position.x + hb.dimensions.w
            for hb in stair_hbs
        )
        max_y = max(
            stairs.state.position.y + hb.position.y + hb.dimensions.l
            for hb in stair_hbs
        )
        stair_w = max_x - min_x
        stair_l = max_y - min_y

        # -----------------------------------------------------------------
        # VERTICAL STAIRS (UP)
        # -----------------------------------------------------------------
        # NOTE: DOWN is impossible due to LPC perspective specification.
        if direction == Directions.UP:
            if stair_l == 0:
                return

            tread_progress = (foot_y - min_y) / stair_l

            # Ascent moves North (vy < 0); Descent moves South (vy > 0)
            if tread_progress <= STAIR_ASCENT_HIGH and vy < 0:
                sprite.elevation = e_top
            elif tread_progress >= STAIR_DESCENT_HIGH and vy > 0:
                sprite.elevation = e_base

        # -----------------------------------------------------------------
        # HORIZONTAL STAIRS (LEFT / RIGHT)
        # -----------------------------------------------------------------
        elif direction in (
            Directions.LEFT,
            Directions.RIGHT
        ):
            if stair_w == 0:
                return

            tread_progress = (foot_x - min_x) / stair_w

            if direction == Directions.RIGHT:
                # Ascent moves East (vx > 0); Descent moves West (vx < 0)
                if tread_progress >= STAIR_ASCENT_LOW and vx > 0:
                    sprite.elevation = e_top
                elif tread_progress <= STAIR_DESCENT_LOW and vx < 0:
                    sprite.elevation = e_base

            elif direction == Directions.LEFT:
                # Ascent moves West (vx < 0); Descent moves East (vx > 0)
                if tread_progress <= STAIR_ASCENT_HIGH and vx < 0:
                    sprite.elevation = e_top
                elif tread_progress >= STAIR_DESCENT_HIGH and vx > 0:
                    sprite.elevation = e_base

        if sprite.elevation != prev_e:
            logger.info(
                f"Telemetry:Stairs:{sprite.name} traversed {stairs.name} "
                f"dir={direction} progress={tread_progress:.2f} "
                f"foot=({foot_x},{foot_y}) vel=({vx:.1f},{vy:.1f}) "
                f"elevation: {prev_e} -> {sprite.elevation}"
            )

    def _boundary(self, asset: Asset, boundary: Boundary, elevation: int) -> None:
        """
        Delegates Asset vs Boundary interaction to the specialized Cython constraint solver,
        evaluating hitboxes specific to the active elevation tier.
        """
        is_kinematic = asset.taxonomy.instance == AssetInstances.PLAYERS
        mass = asset.properties.mass

        # Static environment architecture (m == 0) cannot be shifted by boundary hulls
        if mass == 0 and not is_kinematic:
            return

        vel = (
            asset.state.velocity
            if isinstance(asset.state, (SheetState, MotiveState))
            else None
        )
        hitboxes = (
            asset.hitbox.get(asset.properties, asset.state, elevation)
            if elevation is not None
            else asset.hitboxes
        )

        intersection = geometry.bounded(
            int(asset.state.position.x),
            int(asset.state.position.y),
            hitboxes,
            boundary.position.x,
            boundary.position.y,
            boundary.dimensions.w,
            boundary.dimensions.l
        )

        if not intersection:
            return

        hb = intersection[0]
        physics.constrain(
            asset.state.position,
            hb,
            vel,
            is_kinematic,
            boundary.position.x,
            boundary.position.y,
            boundary.dimensions.w,
            boundary.dimensions.l
        )

    def _resolve(self, asset_a: Asset, asset_b: Asset, elevation: int) -> None:
        """
        Extract variables logically and defer matrix shifts to Cython,
        resolving all intersecting hitbox pairs at the active collision elevation
        tier so compound multi-hitbox obstacles resolve cleanly in a single tick.
        """
        m1 = asset_a.properties.mass
        m2 = asset_b.properties.mass

        is_kinematic1 = asset_a.taxonomy.instance == AssetInstances.PLAYERS
        is_kinematic2 = asset_b.taxonomy.instance == AssetInstances.PLAYERS

        vel1 = (
            asset_a.state.velocity
            if isinstance(asset_a.state, (SheetState, MotiveState))
            else None
        )
        vel2 = (
            asset_b.state.velocity
            if isinstance(asset_b.state, (SheetState, MotiveState))
            else None
        )

        hitboxes_a = (
            asset_a.hitbox.get(asset_a.properties, asset_a.state, elevation)
            if elevation is not None
            else asset_a.hitboxes
        )
        hitboxes_b = (
            asset_b.hitbox.get(asset_b.properties, asset_b.state, elevation)
            if elevation is not None
            else asset_b.hitboxes
        )

        pairs = geometry.intersections(
            asset_a.state.position,
            hitboxes_a,
            asset_b.state.position,
            hitboxes_b
        )

        if not pairs:
            return

        # Resolve deepest overlap area first to prevent internal-seam ghost nudges
        if len(pairs) > 1:
            pos_a = asset_a.state.position
            pos_b = asset_b.state.position
            pairs.sort(
                key=lambda pair: (
                    min(
                        pos_a.x + pair[0].position.x + pair[0].dimensions.w,
                        pos_b.x + pair[1].position.x + pair[1].dimensions.w
                    ) - max(
                        pos_a.x + pair[0].position.x,
                        pos_b.x + pair[1].position.x
                    )
                ) * (
                    min(
                        pos_a.y + pair[0].position.y + pair[0].dimensions.l,
                        pos_b.y + pair[1].position.y + pair[1].dimensions.l
                    ) - max(
                        pos_a.y + pair[0].position.y,
                        pos_b.y + pair[1].position.y
                    )
                ),
                reverse=True
            )

        for hb_a, hb_b in pairs:
            physics.collide(
                asset_a.state.position,
                hb_a,
                vel1,
                m1,
                is_kinematic1,
                asset_b.state.position,
                hb_b,
                vel2,
                m2,
                is_kinematic2
            )

    def update(self,
        board: Board,
        delta: float,
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
        """
        Executes the physics loop partitioned by active dynamic elevation tiers,
        skipping layers and tiers without non-falling dynamic bodies and avoiding
        static-vs-static hashing or resolution.
        """
        if self._board_ref is not board:
            self._static_cache.clear()
            self._perimeter_cache.clear()
            self._board_ref = board

        for layer in board.layers():
            dynamics = [
                d for d in board.dynamics(layer)
                if not d.state.mutators.triggers.falling
            ]
            if not dynamics:
                continue

            # -------------------------------------------------------------
            # PHASE 0: Incline Traversal & Elevation State Mutation
            # -------------------------------------------------------------
            stairs = board.instances(AssetInstances.STAIRS, layer)
            if stairs:
                for stair in stairs:
                    stair_hbs = self._stair_hitboxes(stair)
                    if not stair_hbs:
                        continue
                    for mover in dynamics:
                        if geometry.intersects(
                            mover.state.position,
                            mover.hitboxes,
                            stair.state.position,
                            stair_hbs,
                        ):
                            self._traverse_stairs(mover, stair)

            # -------------------------------------------------------------
            # ACTIVE-TIER PARTITIONING (Dynamic Bodies Only)
            # -------------------------------------------------------------
            dynamics_by_elevation: Dict[int, List[Asset]] = collections.defaultdict(list)
            for dyn in dynamics:
                elevs = dyn.hitbox.elevations(dyn.properties, dyn.state)
                if len(elevs) == 1:
                    dynamics_by_elevation[max(0, elevs[0])].append(dyn)
                elif elevs:
                    # Deduplicate tiers that collapse to <= 0
                    for tier in {max(0, t) for t in elevs}:
                        dynamics_by_elevation[tier].append(dyn)

            for elevation, tier_dynamics in dynamics_by_elevation.items():
                tier_dyn_primitives = [
                    asset.primitive(
                        i,
                        asset.hitbox.get(asset.properties, asset.state, elevation)
                    )
                    for i, asset in enumerate(tier_dynamics)
                ]

                # Phase 1: Boundary Constraints (restricted to base terrain elevation == 0)
                if elevation == 0:
                    layer_perims = board.perimeters.get(layer)
                    perimeters = layer_perims.get(elevation) if layer_perims is not None else None
                    if perimeters:
                        bound_prims, bound_grid = self._perimeter_tier(layer, perimeters)
                        bound_hits = physics.query_bounds(
                            tier_dyn_primitives,
                            bound_prims,
                            bound_grid
                        )
                        if bound_hits:
                            shifted = set()
                            for dyn_idx, bound_idx in bound_hits:
                                self._boundary(
                                    tier_dynamics[dyn_idx],
                                    perimeters[bound_idx],
                                    elevation=elevation
                                )
                                shifted.add(dyn_idx)
                            for dyn_idx in shifted:
                                tier_dyn_primitives[dyn_idx] = tier_dynamics[dyn_idx].primitive(
                                    dyn_idx,
                                    tier_dyn_primitives[dyn_idx][5]
                                )

                # Phase 2A: Dynamic-vs-Dynamic Collisions
                if len(tier_dynamics) > 1:
                    dyn_hits = physics.collisions(tier_dyn_primitives, self.grid)
                    if dyn_hits:
                        shifted = set()
                        for id_a, id_b in dyn_hits:
                            self._resolve(
                                tier_dynamics[id_a],
                                tier_dynamics[id_b],
                                elevation=elevation
                            )
                            shifted.add(id_a)
                            shifted.add(id_b)
                        for dyn_idx in shifted:
                            tier_dyn_primitives[dyn_idx] = tier_dynamics[dyn_idx].primitive(
                                dyn_idx,
                                tier_dyn_primitives[dyn_idx][5]
                            )

                # Phase 2B: Dynamic-vs-Static Bipartite Collisions (persistent static Space)
                tier_statics, static_primitives, static_grid = self._static_tier(
                    board,
                    layer,
                    elevation
                )
                if tier_statics:
                    for dyn_idx, stat_idx in physics.query_statics(
                        tier_dyn_primitives,
                        static_primitives,
                        static_grid
                    ):
                        self._resolve(
                            tier_dynamics[dyn_idx],
                            tier_statics[stat_idx],
                            elevation=elevation
                        )
```

---

### Task 5: Cache Static Obstacles for `NavigationMechanics` and Static Sensors for `MotionMechanics.fields`

#### `src/app/game/logic/mechanics/intentional/navigation.py`
Caches un-inflated static weights, perimeters, and bridge-carved Fluid hazards per `(layer, elevation, static_version)` alongside a bounded `(pad_x, pad_y, fluid_pad_x, fluid_pad_y)` inflated cache. Supports an $O(1)$ copy fast path when `exclude` contains no static names (wander/follow/hunt/escape), exact name filtering when targeting a static asset (Door/Chest/Sign/Tree), and appends only live `board.dynamics(layer)` hitboxes per call.

```python
"""
@domain.concrete
@domain.logic
@app.mechanic
@category.sheets
@modality.intention
@workflow.navigation

# Ontology: Source - app.game.logic.mechanics.intentional.navigation

NavigationMechanics implementation. Manages Sprite Trajectories.
"""
from __future__ import annotations

# Standard Libraries
import collections
from dataclasses import (
    dataclass,
    field,
)
import logging
import math
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    FrozenSet,
    List,
    Optional,
    Set,
    Tuple,
)

if TYPE_CHECKING:
    from app.game.board import Board

# Application Libraries
from app.assets.base import Asset
from app.static.semantics import (
    AssetInstances,
    Directions,
    Goals,
    NavigationIntentions,
)
import app.static.settings as settings
from app.game.logic.mechanics import Mechanic
from app.game.logic.modules.paths.plan import Planner
from app.game.logic import predicates
from app.models.state import DevicePayload

# Cython Libraries
import libs.core.math.geometry as geometry
from libs.core.models import Position

# -----------------------------------------------------

logger = logging.getLogger(__name__)

GoalSignature = Tuple[Optional[str], Optional[Goals], Optional[str]]

HEADING_VECTORS: Dict[Directions, Tuple[float, float]] = {
    Directions.UP: (0.0, -1.0),
    Directions.DOWN: (0.0, 1.0),
    Directions.LEFT: (-1.0, 0.0),
    Directions.RIGHT: (1.0, 0.0),
}

MAX_INFLATED_PAD_VARIANTS = 64

# -----------------------------------------------------


@dataclass(slots=True)
class _InflatedObstacles:
    """Pre-inflated static obstacle AABBs for a specific padding signature."""
    all_rects: List[Tuple[float, float, float, float]]
    named_weights: List[Tuple[str, Tuple[float, float, float, float]]]
    fixed_rects: List[Tuple[float, float, float, float]]


@dataclass(slots=True)
class _StaticObstacleCache:
    """Versioned un-inflated static geometry and per-padding inflated cache for a tier."""
    version: int
    perimeters_ref: Optional[List[Any]]
    perimeters_len: int
    static_names: FrozenSet[str]
    static_weights: List[Tuple[str, float, float, float, float]]
    perimeter_rects: List[Tuple[float, float, float, float]]
    fluid_rects: List[Tuple[float, float, float, float]]
    inflated: Dict[Tuple[float, float, float, float], _InflatedObstacles] = field(default_factory=dict)


class NavigationMechanics(Mechanic):
    """
    ## NavigationMechanics

    Tactical navigation system executing between TransitionMechanics and MotionMechanics.
    Manages sensory anchors, line-of-sight validation, RRT path generation, dynamic
    waypoint progression, and impassable geometry stall handling.
    """
    _active_goals: Dict[str, GoalSignature]
    _cached_board: Optional[Board] = None
    _static_cache: Dict[Tuple[str, int], _StaticObstacleCache] = {}

    def __init__(self):
        super().__init__()
        self._active_goals = {}

    @classmethod
    def clear_cache(cls) -> None:
        """Clears cached static navigational obstacle tables."""
        cls._static_cache.clear()
        cls._cached_board = None

    @staticmethod
    def corridor(
        ox: int,
        oy: int,
        w: int,
        l: int,
        length: int,
        direction: str
    ) -> Optional[Tuple[int, int, int, int]]:
        """
        Computes half-open world-space AABB bounds (x1, y1, x2, y2) for a single
        directional fluid corridor, matching _in_corridor semantics.
        """
        if length <= 0:
            return None

        if direction == Directions.DOWN:
            return (ox, oy, ox + w, oy + length)
        if direction == Directions.UP:
            return (ox, oy - length, ox + w, oy)
        if direction == Directions.RIGHT:
            return (ox, oy, ox + length, oy + l)
        if direction == Directions.LEFT:
            return (ox - length, oy, ox, oy + l)

        return None

    @staticmethod
    def anchor(asset: Asset) -> Position:
        """
        Calculates the physical sensory origin (footprint center) of an asset.
        """
        hbs = asset.hitboxes
        if not hbs:
            return Position(
                x=asset.state.position.x + asset.dimensions.w // 2,
                y=asset.state.position.y + asset.dimensions.l // 2,
            )
        hb = hbs[0]
        return Position(
            x=asset.state.position.x + hb.position.x + hb.dimensions.w // 2,
            y=asset.state.position.y + hb.position.y + hb.dimensions.l // 2,
        )

    @staticmethod
    def footprint(asset: Asset) -> Tuple[float, float]:
        """
        Calculates the physical hitbox half-extents (half_w, half_l) of a
        navigating asset without squeeze padding.
        """
        hbs = asset.hitboxes
        if hbs:
            return (hbs[0].dimensions.w / 2.0, hbs[0].dimensions.l / 2.0)
        return (asset.dimensions.w / 2.0, asset.dimensions.l / 2.0)

    @classmethod
    def fluids(cls, fluid: Asset) -> List[Tuple[int, int, int, int]]:
        """
        Extracts world-space AABB rectangles (x1, y1, x2, y2) covering a Fluid
        entity's active stream corridors, annular pool, and branches. Uses compiled
        state.hitboxes when populated, falling back to pool/stream/branch bounds.
        """
        fx = int(fluid.state.position.x)
        fy = int(fluid.state.position.y)
        hitboxes = fluid.state.hitboxes

        if hitboxes:
            return [
                (
                    fx + hb.position.x,
                    fy + hb.position.y,
                    fx + hb.position.x + hb.dimensions.w,
                    fy + hb.position.y + hb.dimensions.l,
                )
                for hb in hitboxes
                if hb.dimensions.w > 0 and hb.dimensions.l > 0
            ]

        rects: List[Tuple[int, int, int, int]] = []
        pool = fluid.state.pool
        if pool and pool.w > 0 and pool.l > 0:
            rects.append((pool.x, pool.y, pool.x + pool.w, pool.y + pool.l))

        fw = fluid.properties.dimensions.w
        fl = fluid.properties.dimensions.l
        parent = cls.corridor(
            fx, 
            fy, 
            fw, 
            fl, 
            fluid.state.length, 
            fluid.state.source
        )
        if parent is not None:
            rects.append(parent)

        for branch in fluid.state.branches:
            rect = cls.corridor(
                int(branch.position.x),
                int(branch.position.y),
                fw,
                fl,
                branch.length,
                branch.source
            )
            if rect is not None:
                rects.append(rect)

        return rects

    @classmethod
    def padding(cls, asset: Asset) -> Tuple[float, float]:
        """
        Calculates the Minkowski inflation half-extents (hitbox half-dimensions + squeeze radius)
        for a navigating asset.
        """
        half_w, half_l = cls.footprint(asset)

        squeeze = 0.0
        if (
            asset.state.mutators
            and asset.state.mutators.parameters
            and asset.state.mutators.parameters.squeeze
        ):
            squeeze = float(asset.state.mutators.parameters.squeeze.radius)

        return (half_w + squeeze, half_l + squeeze)

    @staticmethod
    def subtract(
        rect: Tuple[int, int, int, int],
        cutout: Tuple[int, int, int, int]
    ) -> List[Tuple[int, int, int, int]]:
        """
        Computes the exact disjoint 2D AABB difference rect \\ cutout, returning
        up to four residual (x1, y1, x2, y2) rectangles.
        """
        ax1, ay1, ax2, ay2 = rect
        bx1, by1, bx2, by2 = cutout

        if bx2 <= ax1 or bx1 >= ax2 or by2 <= ay1 or by1 >= ay2:
            return [rect]

        ix1 = max(ax1, bx1)
        iy1 = max(ay1, by1)
        ix2 = min(ax2, bx2)
        iy2 = min(ay2, by2)

        residuals: List[Tuple[int, int, int, int]] = []
        if iy1 > ay1:
            residuals.append((ax1, ay1, ax2, iy1))
        if iy2 < ay2:
            residuals.append((ax1, iy2, ax2, ay2))
        if ix1 > ax1:
            residuals.append((ax1, iy1, ix1, iy2))
        if ix2 < ax2:
            residuals.append((ix2, iy1, ax2, iy2))
        return residuals

    @staticmethod
    def heading(sprite: Asset) -> Tuple[float, float]:
        """
        Resolves a unit heading vector from live velocity when moving,
        falling back to the Sprite's current AnimationState direction.
        """
        vel = sprite.state.velocity
        mag = math.hypot(vel.vx, vel.vy)
        if mag > 1e-3:
            return (vel.vx / mag, vel.vy / mag)
        return HEADING_VECTORS.get(
            sprite.state.animation.direction,
            (0.0, 0.0)
        )

    @classmethod
    def _raw_fluid_obstacles(
        cls,
        layer: str,
        board: Board,
        elevation: int
    ) -> List[Tuple[float, float, float, float]]:
        """
        Builds un-inflated (x, y, w, l) hazard AABBs for same-elevation Fluid
        corridors and pools with same-elevation Bridge footprints subtracted.
        """
        fluids = board.instances(AssetInstances.FLUIDS, layer, elevation=elevation)
        if not fluids:
            return []

        bridge_rects: List[Tuple[int, int, int, int]] = []
        for bridge in board.bridges(layer):
            if bridge.elevation != elevation:
                continue
            bx = int(bridge.state.position.x)
            by = int(bridge.state.position.y)
            hbs = bridge.hitbox.get(bridge.properties, bridge.state, elevation)
            if hbs:
                for hb in hbs:
                    bridge_rects.append((
                        bx + hb.position.x,
                        by + hb.position.y,
                        bx + hb.position.x + hb.dimensions.w,
                        by + hb.position.y + hb.dimensions.l,
                    ))
            else:
                bridge_rects.append((
                    bx,
                    by,
                    bx + bridge.dimensions.w,
                    by + bridge.dimensions.l,
                ))

        raw_obstacles: List[Tuple[float, float, float, float]] = []
        for fluid in fluids:
            if not predicates.is_hazard(fluid):
                continue

            rects = cls.fluids(fluid)
            if not rects:
                continue

            for cutout in bridge_rects:
                next_rects: List[Tuple[int, int, int, int]] = []
                for rect in rects:
                    next_rects.extend(cls.subtract(rect, cutout))
                rects = next_rects
                if not rects:
                    break

            for x1, y1, x2, y2 in rects:
                raw_obstacles.append((
                    float(x1),
                    float(y1),
                    float(x2 - x1),
                    float(y2 - y1),
                ))

        return raw_obstacles

    @classmethod
    def _fluid_obstacles(
        cls,
        layer: str,
        board: Board,
        elevation: int,
        pad_x: float,
        pad_y: float
    ) -> List[Tuple[float, float, float, float]]:
        """
        Builds Minkowski-inflated obstacle AABBs for same-elevation Fluid
        corridors and pools, subtracting same-elevation Bridge footprints prior
        to inflation so river crossings remain navigable.
        """
        raw_rects = cls._raw_fluid_obstacles(layer, board, elevation)
        if not raw_rects:
            return []
        two_px = 2.0 * pad_x
        two_py = 2.0 * pad_y
        return [
            (x - pad_x, y - pad_y, w + two_px, l + two_py)
            for x, y, w, l in raw_rects
        ]

    @classmethod
    def _get_static_obstacles(
        cls,
        board: Board,
        layer: str,
        elevation: int
    ) -> _StaticObstacleCache:
        """
        Retrieves or compiles the un-inflated static obstacle cache for
        (layer, elevation), invalidated lazily by Board.static_version(layer)
        and perimeter reference changes.
        """
        if cls._cached_board is not board:
            cls._static_cache.clear()
            cls._cached_board = board

        version = board.static_version(layer)
        layer_perims = board.perimeters.get(layer)
        perimeters = layer_perims.get(elevation) if layer_perims is not None else None
        perimeters_len = len(perimeters) if perimeters is not None else 0

        key = (layer, elevation)
        cached = cls._static_cache.get(key)
        if (
            cached is not None
            and cached.version == version
            and cached.perimeters_ref is perimeters
            and cached.perimeters_len == perimeters_len
        ):
            return cached

        static_weights: List[Tuple[str, float, float, float, float]] = []
        static_names_set: Set[str] = set()
        for asset in board.statics(layer, elevation):
            hbs = asset.hitbox.get(asset.properties, asset.state, elevation)
            if not hbs:
                continue
            name = asset.name
            if name:
                static_names_set.add(name)
            ax = asset.state.position.x
            ay = asset.state.position.y
            for hb in hbs:
                static_weights.append((
                    name,
                    float(ax + hb.position.x),
                    float(ay + hb.position.y),
                    float(hb.dimensions.w),
                    float(hb.dimensions.l),
                ))

        perimeter_rects: List[Tuple[float, float, float, float]] = (
            [
                (
                    float(bound.position.x),
                    float(bound.position.y),
                    float(bound.dimensions.w),
                    float(bound.dimensions.l),
                )
                for bound in perimeters
            ]
            if perimeters
            else []
        )

        fluid_rects = cls._raw_fluid_obstacles(layer, board, elevation)

        entry = _StaticObstacleCache(
            version=version,
            perimeters_ref=perimeters,
            perimeters_len=perimeters_len,
            static_names=frozenset(static_names_set),
            static_weights=static_weights,
            perimeter_rects=perimeter_rects,
            fluid_rects=fluid_rects,
        )
        cls._static_cache[key] = entry
        return entry

    @staticmethod
    def _get_inflated_statics(
        base: _StaticObstacleCache,
        pad_x: float,
        pad_y: float,
        fluid_pad_x: float,
        fluid_pad_y: float
    ) -> _InflatedObstacles:
        """
        Retrieves or builds the Minkowski-inflated static obstacle list for
        the requested (pad_x, pad_y, fluid_pad_x, fluid_pad_y) signature.
        """
        pad_key = (pad_x, pad_y, fluid_pad_x, fluid_pad_y)
        cached = base.inflated.get(pad_key)
        if cached is not None:
            return cached

        if len(base.inflated) >= MAX_INFLATED_PAD_VARIANTS:
            base.inflated.clear()

        two_px = 2.0 * pad_x
        two_py = 2.0 * pad_y
        two_fpx = 2.0 * fluid_pad_x
        two_fpy = 2.0 * fluid_pad_y

        named_weights: List[Tuple[str, Tuple[float, float, float, float]]] = []
        all_rects: List[Tuple[float, float, float, float]] = []
        for name, x, y, w, l in base.static_weights:
            rect = (x - pad_x, y - pad_y, w + two_px, l + two_py)
            named_weights.append((name, rect))
            all_rects.append(rect)

        fixed_rects: List[Tuple[float, float, float, float]] = []
        for x, y, w, l in base.perimeter_rects:
            rect = (x - pad_x, y - pad_y, w + two_px, l + two_py)
            fixed_rects.append(rect)
            all_rects.append(rect)

        for x, y, w, l in base.fluid_rects:
            rect = (x - fluid_pad_x, y - fluid_pad_y, w + two_fpx, l + two_fpy)
            fixed_rects.append(rect)
            all_rects.append(rect)

        inflated = _InflatedObstacles(
            all_rects=all_rects,
            named_weights=named_weights,
            fixed_rects=fixed_rects,
        )
        base.inflated[pad_key] = inflated
        return inflated

    @classmethod
    def obstacles(
        cls,
        layer: str,
        board: Board,
        exclude: list,
        elevation: int = 0,
        pad_x: float = 0.0,
        pad_y: float = 0.0,
        fluid_pad_x: Optional[float] = None,
        fluid_pad_y: Optional[float] = None,
    ) -> list:
        """
        Transforms board weights, perimeters, and bridge-carved Fluid hazards
        for the specified elevation tier into flat C-primitive tuples,
        optionally inflated by Minkowski padding. Reuses cached static obstacle
        tables per (layer, elevation, static_version) and appends only live
        dynamic bodies per call.
        """
        target_e = max(0, elevation)
        eff_fluid_pad_x = pad_x if fluid_pad_x is None else fluid_pad_x
        eff_fluid_pad_y = pad_y if fluid_pad_y is None else fluid_pad_y

        base = cls._get_static_obstacles(board, layer, target_e)
        inflated = cls._get_inflated_statics(
            base,
            pad_x,
            pad_y,
            eff_fluid_pad_x,
            eff_fluid_pad_y,
        )

        exclude_set = set(exclude) if exclude else set()
        if not exclude_set or not (exclude_set & base.static_names):
            obstacles = list(inflated.all_rects)
        else:
            obstacles = [
                rect
                for name, rect in inflated.named_weights
                if name not in exclude_set
            ]
            obstacles.extend(inflated.fixed_rects)

        # Append only live dynamic weights (m > 0) matching this elevation tier
        two_px = 2.0 * pad_x
        two_py = 2.0 * pad_y
        for asset in board.dynamics(layer):
            if asset.name in exclude_set:
                continue
            hbs = asset.hitbox.get(asset.properties, asset.state, target_e)
            if not hbs:
                continue
            ax = asset.state.position.x
            ay = asset.state.position.y
            for hb in hbs:
                obstacles.append((
                    float(ax + hb.position.x) - pad_x,
                    float(ay + hb.position.y) - pad_y,
                    float(hb.dimensions.w) + two_px,
                    float(hb.dimensions.l) + two_py,
                ))

        return obstacles

    @staticmethod
    def navigating(sprite: Asset) -> bool:
        """
        Verifies if the sprite is pursuing a goal under an active navigation intention.
        """
        if not sprite.state.goal:
            return False
        
        return sprite.state.intention in NavigationIntentions

    @staticmethod
    def _tracks(sprite: Asset) -> bool:
        """
        Determines whether navigation may resolve a Goal's live deployed Asset
        footprint. Static non-position Goals track directly; mobile Character
        Goals require active visual perception (B082).
        """
        goal = sprite.state.goal
        if not goal or not goal.name or goal.category == Goals.POSITION:
            return False

        if goal.category in (Goals.TARGET, Goals.SUBJECT):
            return sprite.state.mutators.triggers.vision

        return True

    @staticmethod
    def _goal(sprite: Asset) -> Optional[GoalSignature]:
        """Builds an identity tuple for detecting Goal substitutions within an Intention."""
        goal = sprite.state.goal
        if not goal:
            return None
        return (goal.name, goal.category, goal.layer)

    @staticmethod
    def _contains(
        x: float,
        y: float,
        obstacle: Tuple[float, float, float, float],
        eps: float = 1e-3
    ) -> bool:
        """Returns True if (x, y) lies inside or on the border of an obstacle AABB."""
        ox, oy, ow, ol = obstacle
        return (
            (ox - eps) <= x <= (ox + ow + eps)
            and (oy - eps) <= y <= (oy + ol + eps)
        )

    @classmethod
    def _project(
        cls,
        point: Position,
        obstacles: List[Tuple[float, float, float, float]],
        max_w: int = 0,
        max_l: int = 0,
        max_depth: int = 3
    ) -> Position:
        """
        Projects an anchor coordinate contained within Minkowski-inflated walls
        or perimeters (e.g., wall-embedded IN Doors, wall-adjacent Characters, or
        squeeze-zone spawns) to the nearest unobstructed integer coordinate inside
        Layer bounds. Returns point unchanged if already clear or unresolvable.
        """
        px = int(point.x)
        py = int(point.y)
        if not any(cls._contains(px, py, obs) for obs in obstacles):
            return point

        frontier: List[Tuple[int, int]] = [(px, py)]
        visited: Set[Tuple[int, int]] = {(px, py)}
        best_pos: Optional[Tuple[int, int]] = None
        best_dist_sq: Optional[int] = None

        for _ in range(max_depth):
            next_frontier: List[Tuple[int, int]] = []
            for cx, cy in frontier:
                containing = next(
                    (obs for obs in obstacles if cls._contains(cx, cy, obs)),
                    None
                )
                if containing is None:
                    continue

                ox, oy, ow, ol = containing
                candidates = (
                    (cx, math.floor(oy) - 1),
                    (cx, math.ceil(oy + ol) + 1),
                    (math.floor(ox) - 1, cy),
                    (math.ceil(ox + ow) + 1, cy),
                )
                for nx, ny in candidates:
                    if nx < 0 or ny < 0:
                        continue
                    if max_w > 0 and nx > max_w:
                        continue
                    if max_l > 0 and ny > max_l:
                        continue
                    if (nx, ny) in visited:
                        continue
                    visited.add((nx, ny))

                    if not any(cls._contains(nx, ny, obs) for obs in obstacles):
                        dx = nx - px
                        dy = ny - py
                        dist_sq = dx * dx + dy * dy
                        if best_dist_sq is None or dist_sq < best_dist_sq:
                            best_dist_sq = dist_sq
                            best_pos = (nx, ny)
                    else:
                        next_frontier.append((nx, ny))

            if best_pos is not None:
                return Position(x=best_pos[0], y=best_pos[1])
            if not next_frontier:
                break
            frontier = next_frontier

        return point

    def _clear(self, sprite: Asset) -> None:
        """
        Resets tactical trajectory buffers and stall cooldown when an entity
        ceases navigation or clears a prior Goal (B089).
        """
        sprite.state.trajectory.target = None
        sprite.state.trajectory.vertices.clear()
        sprite.state.trajectory.stalled = False
        sprite.state.trajectory.cooldown = 0

    def _target(self, sprite: Asset, board: Board) -> Optional[Position]:
        """
        Resolves the physical anchor coordinate of the sprite's goal.
        Bypasses board asset lookup for synthetic Goals.POSITION coordinates (B072)
        and unseen same-layer Characters so frozen last-known coordinates are respected (B082).
        """
        goal = sprite.state.goal
        if not goal:
            return None

        # Same-layer deployed asset: track physical footprint center when epistemically allowed
        if self._tracks(sprite):
            target_asset = board.asset(goal.name, sprite.state.layer) or \
                           board.asset(goal.name)
            if target_asset and target_asset.state.layer == sprite.state.layer:
                return self.anchor(target_asset)

        if goal.position is None:
            return None

        # Coordinate destination: apply sprite footprint displacement
        anchor = self.anchor(sprite)
        offset_x = anchor.x - sprite.state.position.x
        offset_y = anchor.y - sprite.state.position.y
        return Position(
            x=goal.position.x + offset_x,
            y=goal.position.y + offset_y,
        )

    def _plan(self, 
        sprite: Asset, 
        anchor: Position, 
        target: Position,
        obstacles: List[Tuple[float, float, float, float]],
        offset: Tuple[int, int]
    ) -> bool:
        """
        Executes RRT planning and populates trajectory waypoints or stall state.
        """
        planner = Planner(
            start=anchor,
            target=target,
            obstacles=obstacles,
            step_size=32.0,
            max_iter=300,
            heading=self.heading(sprite),
            inertia=0.75,
        )
        path = planner.plan()

        if path:
            # Subtract anchor offset to steer canvas origin cleanly
            sprite.state.trajectory.vertices = [
                Position(x=int(wp.x - offset[0]), y=int(wp.y - offset[1]))
                for wp in path
            ]
            sprite.state.trajectory.target = sprite.state.trajectory.vertices[0]
            sprite.state.trajectory.stalled = False
            sprite.state.trajectory.cooldown = 0
            return True

        # Stall Handling
        sprite.state.trajectory.stalled = True
        sprite.state.trajectory.target = None
        sprite.state.trajectory.vertices.clear()
        sprite.state.trajectory.cooldown = settings.PATH_RETRY_INTERVAL
        logger.info(f"Pathfinding stalled for {sprite.name}; no valid route found.")
        return False

    def _navigate(self, sprite: Asset, board: Board) -> None:
        """
        Tactical trajectory update frequency for an individual sprite.
        """
        # Dead sprites cease tactical pathfinding immediately (B085)
        if sprite.state.mutators.triggers.dead:
            self._clear(sprite)
            self._active_goals.pop(sprite.name, None)
            return

        if sprite.state.mutators.triggers.falling:
            return
        
        # 1. Goal Verification
        if not self.navigating(sprite):
            self._clear(sprite)
            self._active_goals.pop(sprite.name, None)
            return

        # Cross-layer destinations are managed via door subsumption in CognitionMechanics
        if sprite.state.goal.layer and (
            sprite.state.goal.layer != sprite.state.layer
        ):
            self._clear(sprite)
            self._active_goals.pop(sprite.name, None)
            return

        # Clear stale stall/cooldown/waypoints whenever the active Goal changes
        # within the same NavigationIntention (e.g. SUBJECT -> DOOR in FIND)
        signature = self._goal(sprite)
        prev_signature = self._active_goals.get(sprite.name)
        if prev_signature is not None and prev_signature != signature:
            self._clear(sprite)
        if signature is not None:
            self._active_goals[sprite.name] = signature

        # 2. Anchor Computation
        anchor = self.anchor(sprite)
        offset_x = anchor.x - sprite.state.position.x
        offset_y = anchor.y - sprite.state.position.y
        target = self._target(sprite, board)
        if target is None:
            self._clear(sprite)
            self._active_goals.pop(sprite.name, None)
            return

        tracks_live = self._tracks(sprite)
        exclude = [sprite.name]
        if tracks_live:
            exclude.append(sprite.state.goal.name)

        pad_x, pad_y = self.padding(sprite)
        obstacles = self.obstacles(
            sprite.state.layer,
            board,
            exclude=exclude,
            elevation=sprite.elevation,
            pad_x=pad_x,
            pad_y=pad_y,
        )

        # 3. Free-Space Endpoint Projection (wall-embedded IN Doors & squeeze zones)
        layer_sizes = board.size(sprite.state.layer)
        max_w = layer_sizes[0].w if layer_sizes else 0
        max_l = layer_sizes[0].l if layer_sizes else 0

        plan_start = self._project(anchor, obstacles, max_w, max_l)
        plan_target = (
            self._project(target, obstacles, max_w, max_l)
            if tracks_live
            else target
        )

        goal_x = int(plan_target.x - offset_x)
        goal_y = int(plan_target.y - offset_y)
        if (
            sprite.state.goal.position is not None
            and sprite.state.goal.position.x == goal_x
            and sprite.state.goal.position.y == goal_y
        ):
            goal_target = sprite.state.goal.position
        else:
            goal_target = Position(x=goal_x, y=goal_y)

        escape_target = (
            Position(
                x=int(plan_start.x - offset_x),
                y=int(plan_start.y - offset_y),
            )
            if plan_start is not anchor
            else None
        )

        planned = False

        # 4. Path Maintenance
        if geometry.los(
            float(plan_start.x),
            float(plan_start.y),
            float(plan_target.x),
            float(plan_target.y),
            obstacles,
        ):
            # Line of sight is clear from plan_start: step out of squeeze zone first if needed
            self._clear(sprite)
            sprite.state.trajectory.target = (
                escape_target if escape_target is not None else goal_target
            )

        else:
            # Line of sight is blocked
            if not sprite.state.trajectory.vertices:
                # No active path: evaluate cooldown before planning
                if sprite.state.trajectory.cooldown > 0:
                    sprite.state.trajectory.cooldown -= 1
                    return

                if not self._plan(
                    sprite,
                    plan_start,
                    plan_target,
                    obstacles,
                    offset=(offset_x, offset_y)
                ):
                    return

                if escape_target is not None:
                    sprite.state.trajectory.vertices.insert(0, escape_target)
                    sprite.state.trajectory.target = escape_target

                planned = True

            else:
                # Active waypoints exist: validate LOS to immediate waypoint
                if (
                    escape_target is None
                    or sprite.state.trajectory.target != escape_target
                ):
                    target_anchor_x = sprite.state.trajectory.target.x + offset_x
                    target_anchor_y = sprite.state.trajectory.target.y + offset_y

                    if not geometry.los(
                        float(plan_start.x),
                        float(plan_start.y),
                        float(target_anchor_x),
                        float(target_anchor_y),
                        obstacles,
                    ):
                        # Waypoint path is blocked by dynamic obstacle: replan
                        logger.info(f"Waypoint path occluded for {sprite.name}. Replanning.")
                        sprite.state.trajectory.vertices.clear()
                        sprite.state.trajectory.target = None

                        if not self._plan(
                            sprite,
                            plan_start,
                            plan_target,
                            obstacles,
                            offset=(offset_x, offset_y)
                        ):
                            return

                        if escape_target is not None:
                            sprite.state.trajectory.vertices.insert(0, escape_target)
                            sprite.state.trajectory.target = escape_target

                        planned = True

        # 5. Waypoint Arrival
        if not planned and \
            sprite.state.trajectory.target \
                and sprite.state.trajectory.vertices:
            arrival_radius = sprite.state.mutators.parameters.action.radius

            if geometry.nearby(
                int(sprite.state.position.x),
                int(sprite.state.position.y),
                int(sprite.state.trajectory.target.x),
                int(sprite.state.trajectory.target.y),
                arrival_radius,
            ):
                # Require clear LOS to the subsequent corner vertex before popping early
                if len(sprite.state.trajectory.vertices) > 1:
                    next_wp = sprite.state.trajectory.vertices[1]
                    if not geometry.los(
                        float(anchor.x),
                        float(anchor.y),
                        float(next_wp.x + offset_x),
                        float(next_wp.y + offset_y),
                        obstacles,
                    ):
                        return

                if sprite.state.trajectory.vertices and (
                    sprite.state.trajectory.target == sprite.state.trajectory.vertices[0]
                ):
                    sprite.state.trajectory.vertices.pop(0)
                
                if sprite.state.trajectory.vertices:
                    sprite.state.trajectory.target = sprite.state.trajectory.vertices[0]
                    return
                
                sprite.state.trajectory.target = goal_target
                return

    def update(
        self,
        board: Board,
        delta: float,
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
        """
        Mechanic update loop iterating over all autonomous sprites.
        """
        player = board.player()
        for sprite in board.instances(AssetInstances.SPRITES):

            if player and sprite.name == player.name: 
                continue

            self._navigate(sprite, board)
```

---

#### `src/app/game/logic/modules/motion/fields.py`
Caches static compound sensor bundles (`bridges`, `shorelines`, `fluids`) with pre-populated persistent `Space` grids and cached elevated substrate AABBs (`bridges`, `stairs`, walkable `struts`) keyed by `board.static_version(layer)`, eliminating per-tick `_extract_compound_sensor_primitives` and `_extract_tier_support_aabbs` recomputation.

```python
"""
@domain.logic
@app.module
@physics.fields
@workflow.fluids
@workflow.gravity

# Ontology: Source - app.game.logic.modules.motion.fields
"""
from __future__ import annotations

# Standard Libraries
from dataclasses import (
    dataclass,
    field,
)
import logging
from typing import (
    List, 
    Tuple, 
    Dict,
    Optional,
    Any, 
    TYPE_CHECKING
)

# Application Libraries
import app.static.settings as settings
from app.assets.base import Asset
from app.assets.hitboxes.crafts import MaterialHitbox
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Directions,
    EffectsPalette
)
from app.game.logic.relations import MaterialIndex

if TYPE_CHECKING:
    from app.game.board import Board

# Cython Libraries
import libs.core.math.geometry as geometry
import libs.core.math.physics as physics
from libs.core.math.space import Space
from libs.core.models import Position

logger = logging.getLogger(__name__)

DIRECTION_VECTORS = {
    Directions.UP: (0.0, -1.0),
    Directions.DOWN: (0.0, 1.0),
    Directions.LEFT: (-1.0, 0.0),
    Directions.RIGHT: (1.0, 0.0),
}

SHORELINE_NORMALS = {
    Directions.UP: (0.0, 1.0),     # Land North -> Inward water normal points South (+Y)
    Directions.DOWN: (0.0, -1.0),  # Land South -> Inward water normal points North (-Y)
    Directions.LEFT: (1.0, 0.0),   # Land West  -> Inward water normal points East (+X)
    Directions.RIGHT: (-1.0, 0.0), # Land East  -> Inward water normal points West (-X)
}

# -----------------------------------------------------------------------------
# VERSIONED STATIC SENSOR CACHES
# -----------------------------------------------------------------------------


@dataclass(slots=True)
class _SensorBundle:
    """Cached primitive tuples, parent lookup list, and pre-populated Space grid."""
    primitives: List[Tuple]
    lookup: List[Asset]
    grid: Optional[Space]


@dataclass(slots=True)
class _LayerFieldCache:
    """Per-layer static environmental sensor and elevated substrate support cache."""
    version: int
    bridges: Optional[_SensorBundle] = None
    shorelines: Optional[_SensorBundle] = None
    fluids: Optional[_SensorBundle] = None
    support_aabbs: Dict[int, List[Tuple[int, int, int, int]]] = field(default_factory=dict)


_CACHED_BOARD_REF: Optional[Board] = None
_LAYER_CACHES: Dict[str, _LayerFieldCache] = {}


def clear_cache() -> None:
    """Clears all cached static field sensor bundles and elevated support tables."""
    global _CACHED_BOARD_REF
    _LAYER_CACHES.clear()
    _CACHED_BOARD_REF = None


def _get_layer_cache(board: Board, layer: str) -> _LayerFieldCache:
    """
    Retrieves or resets the per-layer static field cache when the active Board
    or Board.static_version(layer) advances, preserving existing Space allocations.
    """
    global _CACHED_BOARD_REF
    if _CACHED_BOARD_REF is not board:
        _LAYER_CACHES.clear()
        _CACHED_BOARD_REF = board

    version = board.static_version(layer)
    entry = _LAYER_CACHES.get(layer)
    if entry is not None and entry.version == version:
        return entry

    # Retain prior Space instances for reuse on rebuild
    fresh = _LayerFieldCache(version=version)
    if entry is not None:
        if entry.bridges is not None and entry.bridges.grid is not None:
            fresh.bridges = _SensorBundle([], [], entry.bridges.grid)
        if entry.shorelines is not None and entry.shorelines.grid is not None:
            fresh.shorelines = _SensorBundle([], [], entry.shorelines.grid)
        if entry.fluids is not None and entry.fluids.grid is not None:
            fresh.fluids = _SensorBundle([], [], entry.fluids.grid)

    _LAYER_CACHES[layer] = fresh
    return fresh


def _build_sensor_bundle(
    sensors: List[Asset],
    existing: Optional[_SensorBundle],
    cell_size: int
) -> _SensorBundle:
    """Compiles compound sensor primitives and populates a persistent Space grid."""
    if not sensors:
        return _SensorBundle([], [], existing.grid if existing is not None else None)

    primitives, lookup = _extract_compound_sensor_primitives(sensors)
    if not primitives:
        return _SensorBundle([], [], existing.grid if existing is not None else None)

    sensor_grid = (
        existing.grid
        if existing is not None and existing.grid is not None
        else Space(cell_size=cell_size, max_entities=max(256, len(primitives) + 64))
    )
    physics.populate_bounds(primitives, sensor_grid)
    return _SensorBundle(primitives, lookup, sensor_grid)


def _get_bridges_bundle(
    layer_cache: _LayerFieldCache,
    board: Board,
    layer: str,
    cell_size: int
) -> _SensorBundle:
    """Lazily builds and caches the Bridge sensor bundle for a layer version."""
    bundle = layer_cache.bridges
    if bundle is not None and (bundle.primitives or bundle.grid is None):
        return bundle
    # Empty list + non-None grid signals recycled Space awaiting rebuild
    if bundle is not None and bundle.lookup:
        return bundle
    sensors = board.instances(AssetInstances.BRIDGES, layer)
    built = _build_sensor_bundle(sensors, bundle, cell_size)
    if not built.primitives:
        built = _SensorBundle([], [], None)
    layer_cache.bridges = built
    return built


def _get_shorelines_bundle(
    layer_cache: _LayerFieldCache,
    board: Board,
    layer: str,
    cell_size: int
) -> _SensorBundle:
    """Lazily builds and caches the Shoreline sensor bundle for a layer version."""
    bundle = layer_cache.shorelines
    if bundle is not None and (bundle.primitives or bundle.grid is None):
        return bundle
    sensors = board.instances(AssetInstances.SHORELINES, layer)
    built = _build_sensor_bundle(sensors, bundle, cell_size)
    if not built.primitives:
        built = _SensorBundle([], [], None)
    layer_cache.shorelines = built
    return built


def _get_fluids_bundle(
    layer_cache: _LayerFieldCache,
    board: Board,
    layer: str,
    cell_size: int
) -> _SensorBundle:
    """Lazily builds and caches the Fluid sensor bundle for a layer version."""
    bundle = layer_cache.fluids
    if bundle is not None and (bundle.primitives or bundle.grid is None):
        return bundle
    sensors = board.instances(AssetInstances.FLUIDS, layer)
    built = _build_sensor_bundle(sensors, bundle, cell_size)
    if not built.primitives:
        built = _SensorBundle([], [], None)
    layer_cache.fluids = built
    return built


def _direction_vector(source: Any) -> Tuple[float, float]:
    return DIRECTION_VECTORS.get(source, (0.0, 0.0))


def _shoreline_normal(orientation: Any) -> Tuple[float, float]:
    return SHORELINE_NORMALS.get(orientation, (0.0, 0.0))


def _fluid_velocity(fluid: Asset) -> Tuple[float, float]:
    ux, uy = _direction_vector(fluid.state.source)
    speed = fluid.state.flow * settings.BASE_FLOW_SPEED
    return ux * speed, uy * speed


def _extract_compound_sensor_primitives(
    sensors: List[Asset]
) -> Tuple[List[Tuple], List[Asset]]:
    """
    Decomposes assets with compound hitboxes into discrete primitive tuples
    while maintaining a 1:1 lookup index to parent entities.
    """
    primitives: List[Tuple] = []
    lookup: List[Asset] = []
    idx = 0
    for sensor in sensors:
        sx = sensor.state.position.x
        sy = sensor.state.position.y
        for hb in sensor.hitboxes:
            primitives.append((
                idx,
                sx + hb.position.x,
                sy + hb.position.y,
                hb.dimensions.w,
                hb.dimensions.l,
                [hb]
            ))
            lookup.append(sensor)
            idx += 1
    return primitives, lookup


def _extract_tier_support_aabbs(
    board: Board,
    layer: str,
    elevation: int
) -> List[Tuple[int, int, int, int]]:
    """
    Extracts primitive (x, y, w, l) AABB tuples for all walkable substrates
    at discrete elevation tier E > 0.
    """
    aabbs: List[Tuple[int, int, int, int]] = []
    materials: Optional[MaterialIndex] = None

    for craft in board.categories(AssetCategories.CRAFTS, layer):
        inst = craft.taxonomy.instance
        base_e = craft.elevation

        if inst == AssetInstances.STAIRS:
            # Use full stair tread bounds so ascending/descending entities remain supported
            if base_e < elevation <= base_e + craft.state.delta:
                aabbs.append((
                    int(craft.state.position.x),
                    int(craft.state.position.y),
                    int(craft.dimensions.w),
                    int(craft.dimensions.l)
                ))

        elif inst == AssetInstances.BRIDGES:
            if base_e == elevation:
                aabbs.append((
                    int(craft.state.position.x),
                    int(craft.state.position.y),
                    int(craft.dimensions.w),
                    int(craft.dimensions.l)
                ))

        elif inst == AssetInstances.STRUTS:
            # Support sensor struts (mass < 0) and passable surface blueprints at tier E
            if base_e == elevation:
                if craft.properties.mass < 0:
                    walkable = True
                elif isinstance(craft.hitbox, MaterialHitbox):
                    walkable = not craft.hitbox.is_obstacle(craft.state.blueprint)
                else:
                    if materials is None:
                        materials = MaterialIndex()
                    walkable = (
                        not materials.is_obstacle(craft.state.blueprint)
                        or not craft.hitbox.elevations(craft.properties, craft.state)
                    )
                if walkable:
                    aabbs.append((
                        int(craft.state.position.x),
                        int(craft.state.position.y),
                        int(craft.dimensions.w),
                        int(craft.dimensions.l)
                    ))

    return aabbs


def _is_supported_at_tier(
    asset: Asset,
    elevation: int,
    support_cache: Dict[int, List[Tuple[int, int, int, int]]],
    board: Board,
    layer: str
) -> bool:
    """
    Returns True if any active hitbox (or bounding box) of the asset overlaps
    a walkable substrate AABB at the given elevation tier.
    Tier 0 (base terrain) is unconditionally supported.
    """
    if elevation <= 0:
        return True
    if elevation not in support_cache:
        support_cache[elevation] = _extract_tier_support_aabbs(board, layer, elevation)
    support_aabbs = support_cache[elevation]
    if not support_aabbs:
        return False

    ax = int(asset.state.position.x)
    ay = int(asset.state.position.y)
    hbs = (
        asset.hitbox.get(asset.properties, asset.state, elevation)
        if asset.hitbox is not None
        else []
    )
    if hbs:
        for hb in hbs:
            if geometry.occluded(
                ax + hb.position.x,
                ay + hb.position.y,
                hb.dimensions.w,
                hb.dimensions.l,
                support_aabbs
            ):
                return True
        return False

    return bool(
        geometry.occluded(ax, ay, asset.dimensions.w, asset.dimensions.l, support_aabbs)
    )


def _update_gravity(
    l_assets: List[Asset],
    board: Board,
    layer: str,
    delta: float,
    support_cache: Optional[Dict[int, List[Tuple[int, int, int, int]]]] = None
) -> set[int]:
    """
    Evaluates elevated support, accelerates unsupported entities downward (+Y),
    and decrements elevation E -> E - 1 per geometric TIER_DROP_DISTANCE.
    """
    falling_indices: set[int] = set()
    if support_cache is None:
        support_cache = {}

    for i, asset in enumerate(l_assets):
        if asset.elevation <= 0 and not asset.state.mutators.triggers.falling:
            continue

        if asset.elevation <= 0:
            asset.elevation = 0
            asset.state.mutators.triggers.falling = False
            asset.state.mutators.parameters.descension = 0.0
            continue

        is_falling = asset.state.mutators.triggers.falling

        # 1. Check if entity at E > 0 has stepped off its supporting substrate
        if not is_falling:
            if not _is_supported_at_tier(asset, asset.elevation, support_cache, board, layer):
                asset.state.mutators.triggers.falling = True
                asset.state.mutators.parameters.descension = 0.0
                asset.state.position.ry = 0.0
                asset.state.velocity.vy = max(0.0, asset.state.velocity.vy)
                is_falling = True

        if not is_falling:
            continue

        # 2. Integrate constant gravitational acceleration (+Y) while preserving vx
        asset.state.velocity.vy = min(
            settings.TERMINAL_VELOCITY,
            asset.state.velocity.vy + (settings.GRAVITY_ACCELERATION * delta)
        )

        # Compute integer vertical step matching physics.integrate sub-pixel accumulation
        total_ry = asset.state.position.ry + (asset.state.velocity.vy * delta)
        step_y = int(total_ry)
        rem_to_tier = int(settings.TIER_DROP_DISTANCE - asset.state.mutators.parameters.descension)

        # 3. Evaluate discrete tier transitions (E -> E - 1)
        if step_y >= rem_to_tier and asset.elevation > 0:
            orig_y = asset.state.position.y
            rem_y = step_y
            advanced_y = 0
            landed = False

            while rem_y >= rem_to_tier and asset.elevation > 0:
                advanced_y += rem_to_tier
                rem_y -= rem_to_tier
                asset.state.position.y = orig_y + advanced_y
                asset.elevation -= 1

                if _is_supported_at_tier(asset, asset.elevation, support_cache, board, layer):
                    # Landed on supported plane E - 1: clamp exact drop and zero velocity
                    asset.state.mutators.triggers.falling = False
                    asset.state.mutators.parameters.descension = 0.0
                    asset.state.position.ry = 0.0
                    asset.state.velocity.vy = 0.0
                    landed = True
                    break

                rem_to_tier = settings.TIER_DROP_DISTANCE

            if not landed:
                # Unsupported at intermediate plane: restore y for full physics.integrate step
                asset.state.position.y = orig_y
                asset.state.mutators.parameters.descension = float(rem_y)
                falling_indices.add(i)
        else:
            asset.state.mutators.parameters.descension += float(step_y)
            falling_indices.add(i)

    return falling_indices


def _update_rafts(rafts: List[Asset], board: Board, grid: Space) -> None:
    """
    Passively accelerates dynamic Rafts along intersecting fluid current vectors.
    """
    if not rafts:
        return

    layer_rafts: Dict[str, List[Asset]] = {}
    for raft in rafts:
        layer_rafts.setdefault(raft.state.layer, []).append(raft)

    for layer, l_rafts in layer_rafts.items():
        layer_cache = _get_layer_cache(board, layer)
        fluid_bundle = _get_fluids_bundle(layer_cache, board, layer, grid.cell_size)

        if not fluid_bundle.primitives:
            for raft in l_rafts:
                raft.state.velocity.vx = 0.0
                raft.state.velocity.vy = 0.0
            continue

        raft_primitives = [r.primitive(i) for i, r in enumerate(l_rafts)]
        matches = physics.query_bounds(
            raft_primitives,
            fluid_bundle.primitives,
            fluid_bundle.grid
        )

        raft_flows: Dict[int, Tuple[float, float]] = {
            i: (0.0, 0.0) for i in range(len(l_rafts))
        }
        intersected: set[int] = set()

        for r_idx, f_prim_idx in matches:
            fluid = fluid_bundle.lookup[f_prim_idx]
            fvx, fvy = _fluid_velocity(fluid)
            cvx, cvy = raft_flows[r_idx]
            raft_flows[r_idx] = (cvx + fvx, cvy + fvy)
            intersected.add(r_idx)

        for i, raft in enumerate(l_rafts):
            if i in intersected:
                flow_vx, flow_vy = raft_flows[i]
                raft.state.velocity.vx = flow_vx
                raft.state.velocity.vy = flow_vy
            else:
                raft.state.velocity.vx = 0.0
                raft.state.velocity.vy = 0.0


def update(
    assets: List[Asset], 
    board: Board, 
    delta: float, 
    grid: Optional[Space] = None
) -> None:
    """
    Executes environmental field resolution pass across active mutable entities
    using versioned persistent static Space grids and bipartite queries:
    0. Geometric gravity evaluation and multi-tier freefall stepping.
    1. Passive hydrodynamic drift for Rafts.
    2. Surface Interception (Bridges & Rafts) suppressing submersion and shoreline edge checks.
    3. Virtual Edge Traversals (Shorelines) with drop nudges and splash particles.
    4. Direct Immersion (Fluids) with vector superposition and submerged activation.
    """
    if grid is None:
        grid = Space()

    rafts = [
        a for a in assets 
        if a.instance == AssetInstances.RAFTS
    ]
    _update_rafts(rafts, board, grid)

    target_assets = [
        a for a in assets 
        if a.instance not in (
            AssetInstances.RAFTS, 
            AssetInstances.PROJECTILES
        )
    ]

    if not target_assets:
        return

    # Partition targets by layer
    layer_assets: Dict[str, List[Asset]] = {}
    for asset in target_assets:
        layer_assets.setdefault(asset.state.layer, []).append(asset)

    cell_size = grid.cell_size

    for layer, l_assets in layer_assets.items():
        layer_cache = _get_layer_cache(board, layer)

        # -------------------------------------------------------------
        # 0. GRAVITY & ELEVATION TIER SUPPORT
        # -------------------------------------------------------------
        falling_indices = _update_gravity(
            l_assets,
            board,
            layer,
            delta,
            support_cache=layer_cache.support_aabbs
        )
        l_assets = [
            a for i, a in enumerate(l_assets)
            if i not in falling_indices
        ]
        if not l_assets:
            continue

        asset_primitives = [a.primitive(i) for i, a in enumerate(l_assets)]
        on_surface_indices: set[int] = set()

        # -------------------------------------------------------------
        # 1. SURFACE HIERARCHY INTERCEPTION (BRIDGES & RAFTS)
        # -------------------------------------------------------------
        bridge_bundle = _get_bridges_bundle(layer_cache, board, layer, cell_size)
        if bridge_bundle.primitives:
            bridge_matches = physics.query_bounds(
                asset_primitives,
                bridge_bundle.primitives,
                bridge_bundle.grid
            )
            for a_idx, _ in bridge_matches:
                on_surface_indices.add(a_idx)
                asset = l_assets[a_idx]
                asset.state.mutators.triggers.submerged = False

        layer_rafts = board.instances(AssetInstances.RAFTS, layer)
        if layer_rafts:
            raft_prims = [r.primitive(i) for i, r in enumerate(layer_rafts)]
            raft_matches = physics.bipartite(asset_primitives, raft_prims, grid)
            for a_idx, r_idx in raft_matches:
                if a_idx not in on_surface_indices:
                    on_surface_indices.add(a_idx)
                    asset = l_assets[a_idx]
                    raft = layer_rafts[r_idx]
                    asset.state.velocity.vx += raft.state.velocity.vx
                    asset.state.velocity.vy += raft.state.velocity.vy
                    asset.state.mutators.triggers.submerged = False

        # Filter out assets on surfaces for shoreline and fluid passes
        immersible_indices = [i for i in range(len(l_assets)) if i not in on_surface_indices]
        if not immersible_indices:
            continue

        immersible_primitives = [
            l_assets[orig_i].primitive(sub_i) 
            for sub_i, orig_i in enumerate(immersible_indices)
        ]

        # -------------------------------------------------------------
        # 2. VIRTUAL EDGE CROSSING (SHORELINES)
        # -------------------------------------------------------------
        in_shoreline_indices: set[int] = set()
        shore_bundle = _get_shorelines_bundle(layer_cache, board, layer, cell_size)
        if shore_bundle.primitives:
            shore_matches = physics.query_bounds(
                immersible_primitives,
                shore_bundle.primitives,
                shore_bundle.grid
            )
            for sub_idx, s_prim_idx in shore_matches:
                orig_idx = immersible_indices[sub_idx]
                in_shoreline_indices.add(orig_idx)
                asset = l_assets[orig_idx]
                shore = shore_bundle.lookup[s_prim_idx]

                nx, ny = _shoreline_normal(shore.state.orientation)
                vx = asset.state.velocity.vx
                vy = asset.state.velocity.vy
                v_dot = vx * nx + vy * ny

                if v_dot > 0 and not asset.state.mutators.triggers.submerged:
                    t = shore.properties.thickness
                    step_x = int(nx * (t + (asset.dimensions.w // 2))) if nx != 0.0 else 0
                    step_y = int(ny * (t + (asset.dimensions.l // 2))) if ny != 0.0 else 0
                    asset.state.position.x += step_x
                    asset.state.position.y += step_y
                    asset.state.mutators.triggers.submerged = True

                    splash_pos = Position(
                        int(asset.state.position.x),
                        int(asset.state.position.y + (asset.dimensions.l // 2))
                    )
                    splash = board.cradle.spawn_passive(
                        EffectsPalette.SPLASH, 
                        layer, 
                        splash_pos
                    )
                    board.add([splash])

        # -------------------------------------------------------------
        # 3. DIRECT ENVIRONMENTAL FLUID IMMERSION
        # -------------------------------------------------------------
        in_fluid_indices: set[int] = set()
        fluid_flows: Dict[int, Tuple[float, float]] = {
            orig_idx: (0.0, 0.0) for orig_idx in immersible_indices
        }

        fluid_bundle = _get_fluids_bundle(layer_cache, board, layer, cell_size)
        if fluid_bundle.primitives:
            fluid_matches = physics.query_bounds(
                immersible_primitives,
                fluid_bundle.primitives,
                fluid_bundle.grid
            )
            for sub_idx, f_prim_idx in fluid_matches:
                orig_idx = immersible_indices[sub_idx]
                in_fluid_indices.add(orig_idx)
                fluid = fluid_bundle.lookup[f_prim_idx]
                fvx, fvy = _fluid_velocity(fluid)
                cvx, cvy = fluid_flows[orig_idx]
                fluid_flows[orig_idx] = (cvx + fvx, cvy + fvy)

        for orig_idx in immersible_indices:
            asset = l_assets[orig_idx]
            if orig_idx in in_fluid_indices:
                flow_vx, flow_vy = fluid_flows[orig_idx]
                if asset.instance == AssetInstances.CRATES:
                    asset.state.velocity.vx = flow_vx
                    asset.state.velocity.vy = flow_vy
                else:
                    asset.state.velocity.vx += flow_vx
                    asset.state.velocity.vy += flow_vy

                was_submerged = asset.state.mutators.triggers.submerged
                asset.state.mutators.triggers.submerged = True

                if not was_submerged:
                    splash_pos = Position(
                        int(asset.state.position.x),
                        int(asset.state.position.y + (asset.dimensions.l // 2))
                    )
                    splash = board.cradle.spawn_passive(
                        EffectsPalette.SPLASH, 
                        layer, 
                        splash_pos
                    )
                    board.add([splash])
            else:
                if orig_idx not in in_shoreline_indices:
                    asset.state.mutators.triggers.submerged = False
```

---

### Verification: Unit Tests & Multi-NPC Stress Benchmark

#### `tests/unit/app/game/logic/mechanics/test_collision_optimization.py`
Covers all new invariants across Tasks 1–5 (Hitbox DI & fallback caching, `ElevatedHitbox` clamping, `RotatedHitbox` precomputation, `AssetFactory`/`MechanicFactory` `KeyError` fail-fast, `Board`/`Cache` static/dynamic splitting & `static_version` & `obstacles(layer=None)`, `Space` active buckets & C-level pair dedup, `physics.bipartite` / `bipartite_collisions` / `query_statics`, B053.1 inactive-layer skipping, B053.2 multi-hitbox compound resolution, `NavigationMechanics` cached static obstacles with static goal exclusion, and `fields` static sensor caching).

```python
"""
@domain.test
@test.unit
@workflow.collisions
@workflow.navigation
@physics.fields

# Ontology: Tests - tests.unit.app.game.logic.mechanics.test_collision_optimization

Unit tests for Phase 03-07 Collision Optimization across Tasks 1-5.
"""
# Standard Libraries
import collections
from types import SimpleNamespace
from unittest.mock import patch

# Third-Party Libraries
import pytest

# Application Libraries
from app.assets.base import Asset, Taxonomy
from app.assets.hitboxes import (
    DynamicHitbox,
    ElevatedHitbox,
    LayeredHitbox,
    MaterialHitbox,
    RotatedHitbox,
    StageHitbox,
    StaticHitbox,
    SwitchHitbox,
)
from app.game.board import Board
from app.game.logic.mechanics.intentional.navigation import NavigationMechanics
from app.game.logic.mechanics.spatial.collision import CollisionMechanics
from app.game.logic.modules.motion import fields
from app.game.logic.relations import MaterialIndex
from app.models.configurations import MechanicsInstance
from app.models.state import (
    AssetState,
    CraftState,
    DevicePayload,
    DoorState,
    MotiveState,
    MotorState,
    Mutators,
    ResourceState,
    SwitchState,
)
from app.services.factories import AssetFactory, MechanicFactory
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    HitboxRecipe,
    LayerProjections,
)

# Cython Libraries
import libs.core.math.geometry as geometry
import libs.core.math.physics as physics
from libs.core.math.space import Space
from libs.core.models import (
    Boundary,
    Dimensions,
    Hitbox,
    Position,
    Velocity,
)


def _mock_materials(obstacles=frozenset({"walls"})) -> MaterialIndex:
    """Builds a lightweight MaterialIndex stand-in for isolated DI tests."""
    idx = MaterialIndex()
    idx._obstacle_blueprints = frozenset(obstacles)
    return idx


def _make_asset(
    name: str,
    category: str,
    instance: str,
    x: int,
    y: int,
    w: int = 32,
    l: int = 32,
    mass: int = 0,
    layer: str = "layer-0",
    elevation: int = 0,
    hitboxes=None,
    hitbox_schema=None,
    state=None,
) -> Asset:
    props = SimpleNamespace(
        dimensions=Dimensions(w, l),
        mass=mass,
        hitboxes=hitboxes,
        priority=0,
        thickness=8,
    )
    if state is None:
        if mass > 0:
            state = MotiveState(
                id=name,
                name=name,
                layer=layer,
                elevation=elevation,
                position=Position(x, y),
                velocity=Velocity(0.0, 0.0),
                mutators=Mutators(),
            )
        else:
            state = AssetState(
                id=name,
                name=name,
                layer=layer,
                elevation=elevation,
                position=Position(x, y),
                mutators=Mutators(),
            )
    return Asset(
        taxonomy=Taxonomy(id=name, name=name, category=category, instance=instance),
        properties=props,
        state=state,
        hitbox=hitbox_schema or StaticHitbox(),
    )


# -----------------------------------------------------------------------------
# TASK 1: MaterialHitbox DI, Hitbox Caching, ElevatedHitbox, Factory Fail-Fast
# -----------------------------------------------------------------------------

def test_material_hitbox_uses_injected_index_without_singleton_churn():
    materials = _mock_materials({"walls"})
    AssetFactory.configure(materials=materials)
    schema = AssetFactory.hitbox(HitboxRecipe.MATERIAL)

    props = SimpleNamespace(dimensions=Dimensions(32, 32), hitboxes=None)
    wall_state = CraftState(id="w", name="w", layer="l0", elevation=0, blueprint="walls")
    floor_state = CraftState(id="f", name="f", layer="l0", elevation=0, blueprint="floors")

    with patch("app.assets.hitboxes.crafts.MaterialIndex") as ctor_spy:
        assert schema.elevations(props, wall_state) == [0]
        assert schema.elevations(props, floor_state) == []
        hb_first = schema.get(props, wall_state, 0)
        hb_second = schema.get(props, wall_state, 0)
        assert hb_first is hb_second
        assert ctor_spy.call_count == 0


def test_elevated_hitbox_clamping_and_fallback_alignment():
    schema = ElevatedHitbox()
    props_none = SimpleNamespace(dimensions=Dimensions(32, 32), hitboxes=None)
    props_empty = SimpleNamespace(dimensions=Dimensions(32, 32), hitboxes={})
    props_tiers = SimpleNamespace(
        dimensions=Dimensions(32, 32),
        hitboxes={0: [Hitbox(Position(0, 0), Dimensions(32, 32))], 1: [Hitbox(Position(4, 4), Dimensions(24, 24))]},
    )
    neg_state = CraftState(id="c", name="c", layer="l0", elevation=-3)

    assert schema.elevations(props_none, neg_state) == [0]
    assert len(schema.get(props_none, neg_state, 0)) == 1
    assert schema.get(props_none, neg_state, 0) is schema.get(props_none, neg_state, -2)

    assert schema.elevations(props_empty, neg_state) == []
    assert schema.get(props_empty, neg_state, 0) == []

    assert schema.elevations(props_tiers, neg_state) == [0, 1]
    assert len(schema.get(props_tiers, neg_state, 1)) == 1


def test_rotated_hitbox_precomputes_quantized_table():
    schema = RotatedHitbox()
    props = SimpleNamespace(
        dimensions=Dimensions(32, 32),
        rotation=90,
        hitboxes=[Hitbox(Position(4, 12), Dimensions(24, 8))],
    )
    table = schema.precompute(props)
    assert set(table.keys()) == {0, 90, 180, 270}

    state = MotorState(id="arrow", name="arrow", layer="l0", elevation=0, angle=90)
    first = schema.get(props, state, 0)
    second = schema.get(props, state, 0)
    assert first is second
    assert first[0].dimensions == Dimensions(8, 24)


def test_fallback_caches_do_not_reallocate():
    props = SimpleNamespace(dimensions=Dimensions(48, 48), hitboxes=None)
    state = AssetState(id="a", name="a", layer="l0", elevation=0)
    assert StaticHitbox().get(props, state, 0) is StaticHitbox().get(props, state, 0)

    dyn_state = SimpleNamespace(elevation=0, hitboxes=None)
    assert DynamicHitbox().get(props, dyn_state, 0) is DynamicHitbox().get(props, dyn_state, 0)

    res_state = ResourceState(id="r", name="r", layer="l0", elevation=0)
    assert StageHitbox().get(props, res_state, 0) is StageHitbox().get(props, res_state, 0)

    door_in = DoorState(id="d", name="d", layer="l0", elevation=0, projection=LayerProjections.IN)
    door_out = DoorState(id="d", name="d", layer="l0", elevation=0, projection=LayerProjections.OUT)
    layered = LayeredHitbox()
    assert layered.get(props, door_in, 0) is layered.get(props, door_in, 0)
    assert layered.get(props, door_out, 0) is layered.get(props, door_out, 0)


def test_factories_fail_fast_on_unknown_keys():
    with pytest.raises(KeyError):
        AssetFactory.hitbox("nonexistent-hitbox-key")

    with pytest.raises(KeyError):
        MechanicFactory.mechanics(MechanicsInstance(key="nonexistent-mechanic-key"))


# -----------------------------------------------------------------------------
# TASK 2: Board / Cache Static & Dynamic Partitioning
# -----------------------------------------------------------------------------

def test_board_splits_statics_and_dynamics_with_versioning_and_obstacles():
    wall_e0 = _make_asset("wall-0", AssetCategories.OBJECTS, AssetInstances.OBSTACLES, 0, 0, mass=0, layer="l0", elevation=0)
    wall_e1 = _make_asset("wall-1", AssetCategories.OBJECTS, AssetInstances.OBSTACLES, 0, 0, mass=0, layer="l0", elevation=1)
    chest_l1 = _make_asset("chest-1", AssetCategories.OBJECTS, AssetInstances.CHESTS, 0, 0, mass=0, layer="l1", elevation=0)
    crate = _make_asset("crate-0", AssetCategories.OBJECTS, AssetInstances.CRATES, 100, 100, mass=5, layer="l0", elevation=0)

    board = Board([wall_e0, wall_e1, chest_l1, crate], SimpleNamespace(), SimpleNamespace())
    assert board.dynamics("l0") == [crate]
    assert board.statics("l0", 0) == [wall_e0]
    assert board.statics("l0", 1) == [wall_e1]
    assert len(board.obstacles()) == 2  # crate + chest across all layers

    v0 = board.static_version("l0")
    # Adding a dynamic body should not bump static_version
    crate2 = _make_asset("crate-2", AssetCategories.OBJECTS, AssetInstances.CRATES, 200, 200, mass=5, layer="l0", elevation=0)
    board.add([crate2])
    assert board.static_version("l0") == v0

    # Adding/invalidating static geometry increments static_version monotonically
    gate_state = SwitchState(id="gate-1", name="gate-1", layer="l0", elevation=0, position=Position(64, 64), switch=True)
    gate = _make_asset(
        "gate-1",
        AssetCategories.OBJECTS,
        AssetInstances.GATES,
        64,
        64,
        mass=0,
        layer="l0",
        hitbox_schema=SwitchHitbox(),
        state=gate_state,
    )
    board.add([gate])
    v1 = board.static_version("l0")
    assert v1 > v0
    assert gate not in board.statics("l0", 0)  # open gate has no active elevations

    gate.state.switch = False
    board.invalidate_statics("l0")
    assert board.static_version("l0") > v1
    assert gate in board.statics("l0", 0)


# -----------------------------------------------------------------------------
# TASK 3 & TASK 4: Space, Bipartite Physics, Active-Tier Skipping & Multi-Hitbox
# -----------------------------------------------------------------------------

def test_space_active_buckets_and_c_dedup():
    grid = Space(cell_size=64, max_entities=128)
    grid.insert(0, 0, 0, 128, 128)
    grid.insert(1, 32, 32, 128, 128)
    grid.insert(2, 500, 500, 32, 32)
    assert grid.query() == [(0, 1)]

    grid.clear()
    assert grid.query() == []


def test_physics_bipartite_collisions_excludes_static_vs_static():
    grid = Space(cell_size=64, max_entities=128)
    hb = [Hitbox(Position(0, 0), Dimensions(32, 32))]
    # Two overlapping statics far from the dynamic body
    statics = [
        (0, 500, 500, 32, 32, hb),
        (1, 510, 510, 32, 32, hb),
        (2, 10, 10, 32, 32, hb),
    ]
    dynamics = [(0, 20, 20, 32, 32, hb)]
    assert physics.bipartite_collisions(dynamics, statics, grid) == [(0, 2)]

    static_grid = Space(cell_size=64, max_entities=128)
    physics.populate_statics(statics, static_grid)
    assert physics.query_statics(dynamics, statics, static_grid) == [(0, 2)]


def test_collision_mechanics_skips_inactive_layers_and_resolves_compound_corners():
    # Inactive layer with two overlapping statics (must never be resolved)
    s1 = _make_asset("s1", AssetCategories.OBJECTS, AssetInstances.OBSTACLES, 0, 0, mass=0, layer="inactive")
    s2 = _make_asset("s2", AssetCategories.OBJECTS, AssetInstances.OBSTACLES, 8, 8, mass=0, layer="inactive")

    # Active layer with an L-shaped compound obstacle (2 hitboxes) + dynamic mover overlapping both
    l_hitboxes = [
        Hitbox(Position(0, 0), Dimensions(64, 16)),   # Horizontal leg: [100,164) x [100,116)
        Hitbox(Position(0, 0), Dimensions(16, 64)),   # Vertical leg:   [100,116) x [100,164)
    ]
    corner = _make_asset(
        "corner",
        AssetCategories.OBJECTS,
        AssetInstances.OBSTACLES,
        100,
        100,
        w=64,
        l=64,
        mass=0,
        layer="active",
        hitboxes=l_hitboxes,
    )
    mover = _make_asset(
        "crate",
        AssetCategories.OBJECTS,
        AssetInstances.CRATES,
        112,
        112,
        w=32,
        l=32,
        mass=10,
        layer="active",
        hitboxes=[Hitbox(Position(0, 0), Dimensions(32, 32))],
    )
    mover.state.velocity = Velocity(-10.0, -10.0)

    board = Board([s1, s2, corner, mover], SimpleNamespace(), SimpleNamespace())
    mech = CollisionMechanics()
    mech.update(board, 1.0 / 60.0, collections.deque(), DevicePayload())

    # After a single tick, mover must clear BOTH legs of the compound L-corner (B053.2)
    assert geometry.intersections(
        mover.state.position,
        mover.hitboxes,
        corner.state.position,
        corner.hitboxes,
    ) == []
    # Inactive layer was never inserted into static cache (B053.1)
    assert ("inactive", 0) not in mech._static_cache


# -----------------------------------------------------------------------------
# TASK 5: Cached Navigation Obstacles & Cached Motion Field Sensors
# -----------------------------------------------------------------------------

def test_navigation_obstacles_cache_respects_static_exclusions_and_invalidation():
    NavigationMechanics.clear_cache()
    wall = _make_asset("wall-a", AssetCategories.OBJECTS, AssetInstances.OBSTACLES, 0, 0, mass=0, layer="l0")
    chest = _make_asset("chest-a", AssetCategories.OBJECTS, AssetInstances.CHESTS, 64, 0, mass=0, layer="l0")
    mover = _make_asset("crate-a", AssetCategories.OBJECTS, AssetInstances.CRATES, 200, 200, mass=5, layer="l0")
    board = Board([wall, chest, mover], SimpleNamespace(), SimpleNamespace())
    board.perimeters["l0"] = {0: [Boundary(Position(0, 500), Dimensions(500, 1))]}

    obs_all = NavigationMechanics.obstacles("l0", board, exclude=["crate-a"], elevation=0, pad_x=4.0, pad_y=4.0)
    assert len(obs_all) == 3  # wall + chest + perimeter

    obs_target_chest = NavigationMechanics.obstacles(
        "l0", board, exclude=["crate-a", "chest-a"], elevation=0, pad_x=4.0, pad_y=4.0
    )
    assert len(obs_target_chest) == 2  # wall + perimeter only

    wall2 = _make_asset("wall-b", AssetCategories.OBJECTS, AssetInstances.OBSTACLES, 128, 0, mass=0, layer="l0")
    board.add([wall2])
    obs_after = NavigationMechanics.obstacles("l0", board, exclude=["crate-a"], elevation=0, pad_x=4.0, pad_y=4.0)
    assert len(obs_after) == 4


def test_fields_caches_static_sensors_across_ticks():
    fields.clear_cache()
    bridge = _make_asset(
        "bridge-1",
        AssetCategories.CRAFTS,
        AssetInstances.BRIDGES,
        100,
        100,
        mass=-1,
        layer="l0",
        hitboxes=[Hitbox(Position(0, 0), Dimensions(64, 32))],
    )
    mover = _make_asset(
        "crate-1",
        AssetCategories.OBJECTS,
        AssetInstances.CRATES,
        110,
        110,
        mass=5,
        layer="l0",
        hitboxes=[Hitbox(Position(0, 0), Dimensions(16, 16))],
    )
    board = Board([bridge, mover], SimpleNamespace(), SimpleNamespace())
    grid = Space(cell_size=64, max_entities=128)

    with patch(
        "app.game.logic.modules.motion.fields._extract_compound_sensor_primitives",
        wraps=fields._extract_compound_sensor_primitives,
    ) as extract_spy:
        fields.update([mover], board, 1.0 / 60.0, grid=grid)
        fields.update([mover], board, 1.0 / 60.0, grid=grid)
        fields.update([mover], board, 1.0 / 60.0, grid=grid)
        # Bridges extracted exactly once across 3 ticks for invariant static_version
        assert extract_spy.call_count == 1
```

---

#### `tests/exploratory/algorithms/benchmark_multi_npc.py`
Multi-NPC stress benchmark (`1`, `15`, and `30` autonomous sprites on `world-01`) to validate linear frame-time stability under `cProfile` / `pstats`.

```python
"""
@domain.test
@test.unit
@workflow.collisions
@workflow.navigation
@physics.motion

# Ontology: Tests - tests.exploratory.algorithms.benchmark_multi_npc

Multi-NPC (1, 15, 30 autonomous sprites) stress benchmark on world-01 under cProfile/pstats.
"""
# Standard Libraries
import copy
import cProfile
import pstats
import time
from typing import List

# Application Libraries
from app.assets.base import Asset, Taxonomy
from app.services.orchestration.orchestrator import Orchestrator
from app.static.semantics import (
    AssetInstances,
    Devices,
)

# Cython Libraries
from libs.core.models import Dimensions


def _hydrate_world(state_key: str = "world-01", delta: float = 1.0 / 60.0):
    """Boots and headlessly hydrates the target world state."""
    engine = Orchestrator().orchestrate(
        state_key=state_key,
        screensize=Dimensions(w=800, l=600),
        device=Devices.KEYBOARD,
        headless=True,
    )
    guard = 0
    while not engine.board.loaded and guard < 10_000:
        engine._play(delta)
        engine._drain()
        guard += 1
    assert engine.board.loaded, f"Failed to hydrate world '{state_key}'"
    return engine


def _spawn_npc_clones(engine, target_count: int) -> None:
    """Clones an existing autonomous Sprite on the active layer up to target_count."""
    player = engine.board.player()
    sprites = [
        s for s in engine.board.instances(AssetInstances.SPRITES)
        if not player or s.name != player.name
    ]
    if not sprites:
        raise RuntimeError("No template Sprite available on hydrated board.")

    template = sprites[0]
    additions: List[Asset] = []
    existing = len(sprites)

    for idx in range(existing, target_count):
        cloned_state = copy.deepcopy(template.state)
        cloned_state.name = f"{template.name}-bench-{idx}"
        cloned_state.position.x = template.state.position.x + ((idx % 6) * 48)
        cloned_state.position.y = template.state.position.y + ((idx // 6) * 48)
        additions.append(
            Asset(
                taxonomy=Taxonomy(
                    id=template.id,
                    name=cloned_state.name,
                    category=template.category,
                    instance=template.instance,
                ),
                properties=template.properties,
                state=cloned_state,
                frame=template.frame,
                animation=template.animation,
                hitbox=template.hitbox,
                substrate=template.substrate,
            )
        )

    if additions:
        engine.board.add(additions)


def run_benchmark(
    npc_counts=(1, 15, 30),
    ticks: int = 600,
    delta: float = 1.0 / 60.0
) -> None:
    """Runs headless multi-NPC benchmarks and prints per-tick timing and pstats."""
    timings = {}

    for count in npc_counts:
        engine = _hydrate_world("world-01", delta=delta)
        try:
            _spawn_npc_clones(engine, count)

            # Warmup caches
            for _ in range(10):
                engine._play(delta)
                engine._drain()

            profiler = cProfile.Profile()
            start = time.perf_counter()
            profiler.enable()
            for _ in range(ticks):
                engine._play(delta)
                engine._drain()
            profiler.disable()
            elapsed = time.perf_counter() - start
            ms_per_tick = (elapsed / ticks) * 1000.0
            timings[count] = ms_per_tick

            print(f"\n=== world-01 | NPCs={count} | {ticks} ticks | {ms_per_tick:.3f} ms/tick ===")
            stats = pstats.Stats(profiler).sort_stats("cumtime")
            stats.print_stats(15)
        finally:
            engine.stop()

    print("\nSummary (ms/tick):", timings)


if __name__ == "__main__":
    run_benchmark()
```

---

### Build & Verification Commands

Because `.pxd` and `.pyx` modules were modified (`space.pxd`, `space.pyx`, `geometry.pxd`, `geometry.pyx`, `physics.pyx`), rebuild the Cython extensions before running tests and profiling:

```bash
# 1. Recompile Cython extensions
python setup.py build_ext --inplace

# 2. Run unit tests (including new Phase 03-07 test suite)
pytest

# 3. Run multi-NPC stress benchmark (1, 15, 30 sprites on world-01)
PYTHONPATH=src python tests/exploratory/algorithms/benchmark_multi_npc.py

# 4. Re-profile world-01 and regenerate call graph to verify CollisionMechanics < 1.5%
python -m cProfile -o docs/static/pstats/latest.pstats src/main.py start world-01
gprof2dot -f pstats --node-thres=1.0 --edge-thres=0.5 docs/static/pstats/latest.pstats
```