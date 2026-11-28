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