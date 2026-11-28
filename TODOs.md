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