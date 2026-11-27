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



---

## 3. Updated Phase 06.06 Backlog

The backlog below updates **Specification**, adds **Architectural Analysis II** (incorporating the `pstats` findings), and refines **Goals** and **Tasks** to enforce inner short-circuiting, self-loop hygiene, selective candidate evaluation, and zero-scan steady-state `PREREQUISITE` guards.

#### Phase 06.06: Online Hierarchical Goal Decomposition & Multi-Transition Selection

**Overview**

Elevate Ontology's Sprite AI from a single-method reactive policy into a stratified two-layer deliberative architecture grounded in HTN task decomposition and Utility-scored finite-state selection—while strictly preserving epistemic boundedness, Separation of Duties, and low per-tick Python call overhead.

At the **Goal layer** (`CognitionMechanics` / `GoalResolver`), generalize `memory.stack` subsumption beyond spatial `LAYERED` door traversal into a declarative, multi-method online decomposition framework (`PREREQUISITE` outcomes, pluggable `Locator` operators, Motivation-weighted method selection, and failed-method rollback exclusion). At the **Intention layer** (`TransitionMechanics` / `TransitionExecutor`), replace outer first-match short-circuiting with admissible candidate-set evaluation and Motivation-driven tactical selection across competing loops that satisfy the *same* active `Goal`, while removing cross-Goal category transitions (`mine` to `build`, `barter` to `threaten`) and redundant short-circuit self-loops.

##### Specification

**1. Architectural Separation of Planning Concerns**

| Planning Construct | Ontology Layer | Mechanism |
| --- | --- | --- |
| Compound Task | `CognitionMechanics` | Active `sprite.state.goal` with unmet preconditions |
| Decomposition Methods ($M$) | `GoalResolver` + `automata/goals/main.yaml` | Ordered/scored `MethodConfiguration` entries under `Outcomes.PREREQUISITE` (and `Outcomes.LAYERED`) |
| Task Stack (`TasksToProcess`) | `SpriteState.memory.stack` | LIFO `PUSH` on decomposition, `Recall.remember()` pop on `COMPLETE`, `UNWIND` on `LOST` |
| Online Backtracking | `Perception` + `ResolutionContext` | Per-parent excluded method/asset sets populated when a pushed subgoal resolves `LOST` |
| Leaf Primitive Execution | `TransitionMechanics` + `automata/intentions/main.yaml` | Single-goal reactive Intention loop rooted at `idle` |
| Tactical Style Selection | `TransitionExecutor` + `TacticalSelector` | Exhaustive outer candidate evaluation over competing same-Goal loops weighted by `Psyche.motivation` |

**2. Outcome Precedence & Generalized Decomposition**

Extend `OUTCOME_PRECEDENCE` in `app.services.automaton.executors.resolutions`:

$$\text{COMPLETE} \succ \text{LAYERED} \succ \text{PREREQUISITE} \succ \text{LOST}$$

* `COMPLETE`: Objective satisfied; evicts active Goal (`TerminalOutcome`) so `Recall.remember` pops any suspended parent from `memory.stack`.
* `LAYERED`: Cross-layer mismatch; retains specialized `DoorLocator` BFS routing over `memory.doors`.
* `PREREQUISITE`: Same-layer compound Goal missing material, inventory, or relational preconditions (e.g., `Goals.PROPERTY` lacking build materials in `inventory.pack`). Its top-level ISL guard must be an $O(1)$ state check (no Board scans) so satisfied Goals incur zero `Locator` overhead. When triggered, `PrerequisiteOutcome` evaluates candidate `MethodRule` entries, filters out excluded/unlocatable/inadmissible methods, selects the highest-utility method via `Psyche.motivation`, pushes the parent onto `memory.stack`, and installs the located child `Goal`.
* `LOST`: Unreachable or stalled Goal; executes `UNWIND` and records the failed method/asset against the unwound parent so subsequent ticks select an alternate method instead of oscillating.

**3. Multi-Candidate Transition Evaluation & Performance Guardrails**

* **Preserve inner short-circuiting:** `Backend.evaluate(conditions, locals)` continues to short-circuit on the first falsy conjunct (mandatory for ISL null-safety and fast category rejection).
* **Exhaustive outer collection (`candidates`) scoped to `TransitionMechanics`:**
* `TransitionExecutor.evaluate(...)` remains short-circuited for single-path automata (`PlotMechanics`, `SeasonMechanics`).
* `TransitionExecutor.candidates(current_state, locals) -> List[Transition]` evaluates all outgoing transitions from `current_state` and returns every satisfied `Transition`.
* In `TransitionMechanics.update`:
1. **Idle-no-goal fast path:** If `current_state == Intentions.IDLE and sprite.state.goal is None`, skip `candidates()` entirely (zero `eval()`/lambda calls for idle unengaged sprites).
2. **Reuse `locals` dict per tick:** Mutate `'sprite'` and `'assets'` keys in a single pre-allocated dict across the sprite loop instead of constructing a fresh dict per sprite per tick, and cache `board.states(layer)` per layer per tick.
3. **Zero-allocation fast path on singleton matches:** Filter candidates via `AnimationMap.action(..., intention=t.next)`; bypass `TacticalSelector` whenever `len(admissible) <= 1`.
4. **Explicit self-loop contract:** Audit and remove short-circuit-only self-loops (`attack -> attack`, `escape -> escape`, `mine -> mine`) where exit rules are already disjoint, ensuring `candidates()` only returns genuine state-change alternatives.





**4. Epistemic Constraint (No Offline Lookahead)**

Decomposition remains strictly **online and epistemically bounded**: method preconditions and `Locator` queries read solely from `sprite.state` (`inventory`, `memory`, `slots`) and same-layer `vision.radius` perceptions.

##### Architectural Analysis I

Comparing Ontology's current cognitive stack against Classical Planning (STRIPS), GOAP, and HTN reveals three structural findings:

1. **Ontology Is Currently a Teleo-Reactive Policy Over a 1-Method Stack Decomposer:** `TransitionMechanics` senses live `Board` state each tick and selects the first matching edge without lookahead. Implicit traversal through `automata/intentions/main.yaml` cannot perform multi-step Goal decomposition because `TransitionMechanics` is prohibited from mutating `sprite.state.goal`.
2. **Cross-Goal Leakage Exists in `automata/intentions/main.yaml`:** `mine -> build` (`RESOURCE` to `PROPERTY`) and `barter -> threaten` (`RESOURCE` to `TARGET`) immediately abort to `idle` because switching targets changes the Goal category. These belong to `GoalResolver` method decomposition rather than `TransitionMechanics`.
3. **Splitting Upgrades Across Both Layers Preserves Separation of Duties:** Generalizing `memory.stack` subsumption in `GoalResolver` handles multi-step decomposition, while multi-candidate scoring in `TransitionMechanics` handles same-Goal tactical style branching.

##### Architectural Analysis II

Empirical profiling via `cProfile` / `gprof2dot` (`world-01` UAT, 6,337 ticks, 6,059 frames, $N = 1$ Sprite) establishes the performance context for Phase 06.06:

1. **Exhaustive Outer Transition Evaluation Is Safe Within the Current Budget:** `TransitionMechanics.update` falls below the 1.0% node / 0.5% edge reporting threshold (under 0.5% total wall time). Because steady-state navigation ticks already evaluate all outgoing transitions to `False`, switching to `candidates()` adds marginal cost only on transition ticks (roughly $1.2\times\text{--}2.5\times$ on a sub-0.5% baseline).
2. **Scale-Sensitivity Requires Lightweight Guardrails:** Because `world-01` profiles $N = 1$ Sprite, linear $O(N)$ costs in `TransitionMechanics` and `CognitionMechanics` must be kept lean ahead of multi-agent worlds ($N \ge 20$). Preserving inner short-circuiting, skipping `candidates()` on goal-less `IDLE` ticks, reusing the `locals` dictionary, and enforcing $O(1)$ top-level `PREREQUISITE` guards ensure Phase 06.06 does not introduce a new bottleneck alongside `navigation:obstacles` (1.94% at $N = 1$) or `crafts` hitbox queries (3.43%).
3. **Engine Hotspots Outside Phase 06.06 Scope:** The dominant active CPU costs (`CollisionMechanics` 6.05%, `Screen.interface` 3.90%, `Screen._assemble` 3.55%, `fields.update` 2.40%, `navigation:obstacles` 1.94%) are independent caching/batching issues that should be tracked in a dedicated optimization pass rather than conflated with Phase 06.06.

##### Goals

###### Goal: Generalized Multi-Method Prerequisite Decomposition (`GoalResolver`)

Extend the declarative Goal schema (`app.models.configurations.automata.goals`) and `GoalEvaluator` so a Goal category can declare multiple named decomposition methods under `Outcomes.PREREQUISITE`, each binding a `Locator`, child `Goals` category, ISL preconditions, and `Motivations` affinity weights. Top-level `PREREQUISITE` conditions must remain $O(1)$ state checks so `Locator` scans execute strictly on unsatisfied compound Goals.

###### Goal: Online Rollback & Failed-Method Exclusion (`Perception` + `UnwindResponse`)

Generalize `Perception._stalled_doors` into parent-scoped method/asset failure tracking (`_failed_methods`, `_active_method`) so `LOST` child Goals unwind cleanly, exclude the failed method, and fall back to the next highest-ranked method before demoting the parent to `dormant = True`.

###### Goal: Multi-Candidate Transition Selection (`TransitionExecutor` + `TransitionMechanics`)

Add `TransitionExecutor.candidates(current_state, locals) -> List[Transition]` while keeping `evaluate()` intact for single-path automata (`plot`, `season`) and preserving inner conjunction short-circuiting in `Backend.evaluate`. Filter candidates through `AnimationMap.action` and dispatch multi-candidate sets through `TacticalSelector` using `Psyche.motivation` weights with declaration-order tie-breaking, short-circuiting `TacticalSelector` whenever at most one admissible transition exists.

###### Goal: Clean Single-Goal Intention Topology & Self-Loop Audit (`automata/intentions/main.yaml`)

Normalize `src/data/configurations/automata/intentions/main.yaml` so every Intention loop strictly preserves its Goal category invariant, removes cross-category bridges (`mine` to `build`, `barter` to `threaten`), eliminates short-circuit-dependent self-loops (`attack -> attack`, `escape -> escape`, `mine -> mine`) in favor of disjoint exit guards, and exposes Motivation-weighted competing loops where applicable (e.g., `idle` to `{hunt, threaten, mock}` for `Goals.TARGET`).

##### Tasks

**1. Task: Extend Automata Configuration & Executor Models**

*Objective*: Add typed `MethodConfiguration` / `MethodRule` support for `Outcomes.PREREQUISITE` and Motivation `weights` on `IntentionConfiguration` / `Transition`.

* [ ] Subtask: Add `Outcomes.PREREQUISITE` and new `Locators` keys (`RESOURCE`, `MERCHANT`, `RIVAL`) to `app.static.semantics`.
* [ ] Subtask: Define frozen `dataclass(slots=True)` `MethodConfiguration` (`key`, `locator`, `category`, `weights`, `conditions`) and add `methods: List[MethodConfiguration]` to `GoalConfiguration` in `src/app/models/configurations/automata/goals.py`.
* [ ] Subtask: Add `weights: Dict[Enumerated[Motivations], float]` to `IntentionConfiguration` in `src/app/models/configurations/automata/transitions.py`.
* [ ] Subtask: Update `OUTCOME_PRECEDENCE`, `GoalRule`, and `GoalTranslator.compile` in `src/app/services/automaton/executors/resolutions.py` to compile `MethodRule` tuples via the active `Backend` (`Compiler` / `Lambda`) with fail-fast validation.
* [ ] Subtask: Add `TransitionExecutor.candidates(current_state, locals) -> List[Transition]` alongside short-circuiting `evaluate()` in `src/app/services/automaton/executors/transitions.py`, preserving inner conjunction short-circuiting and AST/Lambda backend parity.

**2. Task: Implement Generalized Stack Subsumption & Locators**

*Objective*: Enable `GoalResolver` to decompose compound Goals into prerequisite subgoals via pluggable `Locator` strategies and Motivation-weighted method ranking without per-tick scan overhead.

* [ ] Subtask: Implement `ResourceLocator` (nearest visible/remembered matching `AssetCategories.RESOURCES` on the current layer) and register it in `LocatorOperator.defaults()` in `src/app/game/logic/modules/cognition/goals/locators.py`.
* [ ] Subtask: Implement `MethodSelector` in `src/app/game/logic/modules/cognition/goals/` to score viable `(MethodRule, Asset)` candidates using `Psyche.motivation` weights, `AnimationMap` equipment admissibility, and distance tie-breaking.
* [ ] Subtask: Implement `PrerequisiteOutcome` in `src/app/game/logic/modules/cognition/goals/outcomes.py` and register it under `Outcomes.PREREQUISITE` in `OutcomeOperator.defaults()`, pushing the parent onto `memory.stack` on success and demoting via `Responses.STORE` when all methods fail.
* [ ] Subtask: Extend `ResolutionContext` in `src/app/game/logic/modules/cognition/goals/base.py` with `excluded_methods: FrozenSet[str]` and record selected method provenance for rollback tracking.

**3. Task: Implement Online Rollback & Method-Failure Tracking**

*Objective*: Prevent infinite decomposition loops by recording failed methods on `LOST` child Goals and allowing `CognitionMechanics` to fall back to alternate methods before marking a parent Goal dormant.

* [ ] Subtask: Add parent-scoped failed-method tracking (`mark_failed_method`, `failed_methods`, `clear_failed_methods`) and active subgoal provenance to `Perception` in `src/app/game/logic/modules/cognition/perception.py`.
* [ ] Subtask: Update `CognitionMechanics._resolve` and `_sync` in `src/app/game/logic/mechanics/intentional/cognition.py` to pass `excluded_methods` into `GoalResolver.resolve` and record method failures when a pushed child resolves `Outcomes.LOST`.
* [ ] Subtask: Update `UnwindResponse` (or add a retry-aware unwind policy) so unwound parent Goals remain eligible for immediate `Recall` if untried methods exist, and become `dormant = True` once all methods are exhausted.
* [ ] Subtask: Expose $O(1)$ domain predicates (e.g., `has_materials`) in `app.services.automaton.environ.Environ.functions` so `PREREQUISITE` conditions evaluate in ISL without Board scans.

**4. Task: Upgrade `TransitionMechanics` for Multi-Candidate Tactical Selection**

*Objective*: Evaluate all satisfied transitions, filter by equipment admissibility, and select among competing same-Goal loops using `Psyche.motivation` with minimal per-tick allocation overhead.

* [ ] Subtask: Implement `TacticalSelector` to select the highest-scoring admissible `Transition` using `sprite.state.psyche.motivation` with declaration-order tie-breaking.
* [ ] Subtask: Refactor `TransitionMechanics.update` in `src/app/game/logic/mechanics/intentional/transition.py` to query `self.executor.candidates(...)`, filter candidates through `AnimationMap.action(..., intention=t.next)`, skip `candidates()` on goal-less `IDLE` ticks, reuse the `locals` dict and per-layer `board.states(layer)` reference across the loop, and bypass `TacticalSelector` when at most one admissible transition exists.
* [ ] Subtask: Ensure rejecting an inadmissible high-priority transition falls through to remaining admissible candidates instead of stalling the Sprite in its current Intention.

**5. Task: Refactor Declarative Automata Configurations (`goals/main.yaml` & `intentions/main.yaml`)**

*Objective*: Align YAML matrices with strict single-Goal intention loops, exhaustive-evaluation safety, and multi-method prerequisite decomposition.

* [ ] Subtask: Remove cross-Goal category transitions (`mine` to `build`, `barter` to `threaten`) from `src/data/configurations/automata/intentions/main.yaml`.
* [ ] Subtask: Audit and remove short-circuit-dependent self-loops (`attack -> attack`, `escape -> escape`, `mine -> mine`) in `src/data/configurations/automata/intentions/main.yaml`, verifying every `-> idle` exit condition is strictly disjoint from active loop continuation.
* [ ] Subtask: Add `idle` entrypoints for `mine` (`Goals.RESOURCE`) and `build` (`Goals.PROPERTY`), and add Motivation-weighted competing loops for `Goals.TARGET` (`idle` to `{hunt, threaten, mock}`).
* [ ] Subtask: Add `prerequisite` multi-method decomposition blocks (starting with `property` $\to$ `resource` / `subject`) to `src/data/configurations/automata/goals/main.yaml`.

**6. Task: End-to-End Verification, Profiling Regression Check & Documentation**

*Objective*: Validate multi-method decomposition, online backtracking, Motivation-weighted transition selection, and multi-sprite CPU impact using real dependency-tree `pytest` fixtures and `cProfile`.

* [ ] Subtask: Add unit and integration tests using shared `conftest.py` Board/Orchestrator fixtures covering: (a) `PROPERTY` pushing `RESOURCE` onto `memory.stack`, mining to `COMPLETE`, popping `PROPERTY`, and entering `build`; (b) stalling on method 1, unwinding, excluding method 1, and succeeding via method 2; (c) exhausting all methods and demoting the parent cleanly without oscillation.
* [ ] Subtask: Add tests verifying that two identical Sprites with different `Psyche.motivation` values (`CONQUEST` vs. `REBELLION`) select distinct admissible Intention loops from `idle` for the same `Goals.TARGET`, that missing weapon admissibility falls through to non-weapon candidates, and that removing self-loops produces no spurious `-> idle` exits.
* [ ] Subtask: Re-run `cProfile` / `gprof2dot` on `world-01` (and a multi-sprite stress fixture with $N \ge 10$ Sprites) to verify `TransitionMechanics.update` and `CognitionMechanics.update` remain well below frame-budget thresholds under exhaustive outer candidate evaluation.
* [ ] Subtask: Update `docs/04-intentions.md` and `docs/05-mechanics.md` to document `Outcomes.PREREQUISITE`, multi-method decomposition, failed-method rollback, and Motivation-weighted multi-transition selection.