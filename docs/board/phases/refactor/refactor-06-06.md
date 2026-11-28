#### Phase 06.06: Goal Decomposition

**Overview**

Elevate Ontology's Sprite AI from a single-method reactive policy into a stratified two-layer deliberative architecture grounded in HTN task decomposition and Utility-scored finite-state selection—while strictly preserving epistemic boundedness and Separation of Duties.

At the **Goal layer** (`CognitionMechanics` / `GoalResolver`), generalize `memory.stack` subsumption beyond spatial `LAYERED` door traversal into a declarative, multi-method online decomposition framework (`PREREQUISITE` outcomes, pluggable `Locator` operators, Motivation-weighted method selection, and failed-method rollback exclusion). At the **Intention layer** (`TransitionMechanics` / `TransitionExecutor`), replace first-match transition short-circuiting with candidate-set evaluation and Motivation-driven tactical selection across competing loops that satisfy the *same* active `Goal`, while removing cross-Goal category transitions (`mine` to `build`, `barter` to `threaten`) that violate Separation of Duties.

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

1. **Ontology Is Currently a Teleo-Reactive Policy Over a 1-Method Stack Decomposer:** `TransitionMechanics` senses live `Board` state each tick and selects the first matching edge without lookahead. While `Goal` loops resemble task lists, implicit traversal through `automata/intentions/main.yaml` cannot perform multi-step Goal decomposition because `TransitionMechanics` is prohibited from mutating `sprite.state.goal`.
2. **Cross-Goal Leakage Already Exists in `automata/intentions/main.yaml`:**
  * `mine` transitions to `build` while `sprite.goal.category == RESOURCE`, but `build` immediately aborts to `idle` unless `sprite.goal.category == PROPERTY`.
  * `barter` transitions to `threaten` while `sprite.goal.category == RESOURCE`, but `threaten` immediately aborts to `idle` unless `sprite.goal.category == TARGET`.
  * Because changing from "gather wood" to "build structure" or from "buy resource" to "rob merchant" changes the *target entity and Goal category*, these transitions belong to `GoalResolver` method decomposition rather than `TransitionMechanics`.
3. **1-Step Transition Scoring Alone Is Insufficient:** Returning the set of valid next Intentions from `TransitionExecutor` and applying decision criteria solves *tactical style branching* for a fixed Goal (e.g., choosing among `{hunt, mock, threaten}` for `Goals.TARGET`), but cannot decompose compound Goals into prerequisite subgoals. Splitting the upgrade cleanly across `GoalResolver` (multi-method HTN stack subsumption) and `TransitionExecutor` (multi-candidate Motivation-weighted selection) resolves both limitations without weakening Separation of Duties.

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