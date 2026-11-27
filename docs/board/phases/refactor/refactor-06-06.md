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
| Tactical Style Selection | `TransitionExecutor` + `TacticalSelector` | Multi-candidate evaluation over competing same-Goal loops weighted by `Psyche.motivation` |

**2. Outcome Precedence & Generalized Decomposition**

Extend `OUTCOME_PRECEDENCE` in `app.services.automaton.executors.resolutions`:

$$\text{COMPLETE} \succ \text{LAYERED} \succ \text{PREREQUISITE} \succ \text{LOST}$$

* `COMPLETE`: Objective satisfied; evicts active Goal (`TerminalOutcome`) so `Recall.remember` pops any suspended parent from `memory.stack`.
* `LAYERED`: Cross-layer mismatch; retains specialized `DoorLocator` BFS routing over `memory.doors`.
* `PREREQUISITE`: Same-layer compound Goal missing material, inventory, or relational preconditions (e.g., `Goals.PROPERTY` lacking build materials in `inventory.pack`). Evaluates candidate `MethodRule` entries, filters out excluded/unlocatable/inadmissible methods, selects the highest-utility method via `Psyche.motivation`, pushes the parent onto `memory.stack`, and installs the located child `Goal`.
* `LOST`: Unreachable or stalled Goal; executes `UNWIND` and records the failed method/asset against the unwound parent so subsequent ticks select an alternate method instead of oscillating.

**3. Multi-Candidate Transition Evaluation**

Replace `TransitionExecutor.evaluate(...) -> Optional[str]` with candidate-set collection:

* `TransitionExecutor.candidates(current_state, locals) -> List[Transition]` evaluates *all* transitions declared for `current_state` (preserving short-circuit conjunction evaluation inside each transition) and returns every satisfied `Transition`.
* `TransitionMechanics` filters the candidate list through `AnimationMap.action(sprite.state, board.equipment, intention=candidate.next)` to drop inadmissible equipment transitions *before* tactical scoring.
* When multiple admissible candidates remain for the same `Goal`, a deterministic/weighted `TacticalSelector` chooses the next `Intention` using `Transition.weights` keyed by `Motivations` (falling back to declaration order when unconfigured or when `psyche.motivation is None`).

**4. Epistemic Constraint (No Offline Lookahead)**

Decomposition remains strictly **online and epistemically bounded**: method preconditions and `Locator` queries read solely from `sprite.state` (`inventory`, `memory`, `slots`) and same-layer `vision.radius` perceptions. Sprites never simulate omniscient `WorkingWS` rollouts over unobserved layers or hidden NPC inventories; reality mismatches trigger physical `LOST` resolution, `UNWIND`, and alternate-method selection.

##### Architectural Analysis I

Comparing Ontology's current cognitive stack against Classical Planning (STRIPS), GOAP, and HTN reveals three structural findings:

1. **Ontology Is Currently a Teleo-Reactive Policy Over a 1-Method Stack Decomposer:** `TransitionMechanics` senses live `Board` state each tick and selects the first matching edge without lookahead. While `Goal` loops resemble task lists, implicit traversal through `automata/intentions/main.yaml` cannot perform multi-step Goal decomposition because `TransitionMechanics` is prohibited from mutating `sprite.state.goal`.
2. **Cross-Goal Leakage Already Exists in `automata/intentions/main.yaml`:**
* `mine` transitions to `build` while `sprite.goal.category == RESOURCE`, but `build` immediately aborts to `idle` unless `sprite.goal.category == PROPERTY`.
* `barter` transitions to `threaten` while `sprite.goal.category == RESOURCE`, but `threaten` immediately aborts to `idle` unless `sprite.goal.category == TARGET`.
* Because changing from "gather wood" to "build structure" or from "buy resource" to "rob merchant" changes the *target entity and Goal category*, these transitions belong to `GoalResolver` method decomposition rather than `TransitionMechanics`.


3. **1-Step Transition Scoring Alone Is Insufficient:** Returning the set of valid next Intentions from `TransitionExecutor` and applying decision criteria solves *tactical style branching* for a fixed Goal (e.g., choosing among `{hunt, mock, threaten}` for `Goals.TARGET`), but cannot decompose compound Goals into prerequisite subgoals. Splitting the upgrade cleanly across `GoalResolver` (multi-method HTN stack subsumption) and `TransitionExecutor` (multi-candidate Motivation-weighted selection) resolves both limitations without weakening Separation of Duties.

##### Goals

###### Goal: Generalized Multi-Method Prerequisite Decomposition (`GoalResolver`)

Extend the declarative Goal schema (`app.models.configurations.automata.goals`) and `GoalEvaluator` so a Goal category can declare multiple named decomposition methods under `Outcomes.PREREQUISITE`, each binding a `Locator`, child `Goals` category, ISL preconditions, and `Motivations` affinity weights.

```yaml
# src/data/configurations/automata/goals/main.yaml (illustrative excerpt)
goals:
  property:
    complete:
      reflexes: []
      responses: [ forget ]
      conditions:
        - sprite.goal.name in sprite.memory.property
    layered:
      reflexes: []
      responses: [ push ]
      conditions:
        - sprite.goal.layer
        - sprite.layer != sprite.goal.layer
    prerequisite:
      reflexes: []
      responses: [ push ]
      conditions:
        - not functions.has_materials(sprite, sprite.goal.name)
      methods:
        - key: harvest_resource
          locator: resource
          category: resource
          weights:
            survival: 1.0
            safety: 0.9
            profit: 0.4
          conditions:
            - sprite.slots.equipment.tool is not None
        - key: trade_merchant
          locator: merchant
          category: subject
          weights:
            profit: 1.0
            love: 0.7
            conquest: 0.1
          conditions:
            - len(sprite.inventory.pouch) > 0
        - key: raid_target
          locator: rival
          category: target
          weights:
            conquest: 1.0
            revenge: 0.9
            rebellion: 0.8
          conditions:
            - sprite.slots.equipment.weapon is not None
    lost:
      reflexes: []
      responses: [ store ]
      conditions:
        - sprite.trajectory.stalled

```

`PrerequisiteOutcome` iterates over compiled `MethodRule` entries, filters out methods whose `key` is in `context.excluded_methods` or whose ISL conditions fail, queries `context.locators.resolve(method.locator, sprite, board, excluded=context.excluded)`, ranks viable `(method, target_asset)` pairs by `MethodSelector` (using `sprite.state.psyche.motivation`, distance, and `AnimationMap` admissibility), pushes the parent `Goal` onto `memory.stack`, and installs the child `Goal`. If no method yields a reachable target, `PrerequisiteOutcome` demotes the parent via `Responses.STORE` (matching `LayeredOutcome` unreachable-portal semantics) so the Sprite does not spin in `Recall → Sync`.

###### Goal: Online Rollback & Failed-Method Exclusion (`Perception` + `UnwindResponse`)

Generalize `Perception._stalled_doors` into parent-scoped method/asset failure tracking so online backtracking cleanly tries alternative decomposition methods before abandoning a compound Goal.

```python
# Conceptual state tracked per sprite in Perception
# Maps (sprite_name, parent_goal_key) -> set of failed method keys
_failed_methods: Dict[Tuple[str, str], Set[str]]

# Active subgoal provenance so CognitionMechanics._resolve knows
# which (parent_key, method_key) produced the failing child Goal
_active_method: Dict[str, Tuple[str, str]]

```

When a child `Goal` pushed by method `M` resolves `LOST`:

1. `UnwindResponse` pops the parent `Goal` from `memory.stack` into `memory.goals` (non-dormant if alternate methods remain; dormant if all methods are exhausted).
2. `Perception` records `M` in `_failed_methods[(sprite.name, parent.name)]` and clears `_active_method[sprite.name]`.
3. On the next `IDLE` acquisition cycle, `Recall` resumes the parent, `PrerequisiteOutcome` excludes `M`, and the Sprite attempts the next highest-ranked method (e.g., falling back from `harvest_resource` to `trade_merchant`).
4. Layer transitions or parent `COMPLETE` / `FORGET` evict the parent's `_failed_methods` entry.

###### Goal: Multi-Candidate Transition Selection (`TransitionExecutor` + `TransitionMechanics`)

Upgrade `IntentionConfiguration`, `Transition`, and `TransitionExecutor` to support competing same-Goal intention loops scored by `Psyche.motivation`.

```python
@dataclass(slots=True, frozen=True)
class IntentionConfiguration(Configuration):
    next: str
    conditions: List[str] = field(default_factory=list)
    weights: Dict[Enumerated[Motivations], float] = field(default_factory=dict)

@dataclass(slots=True, frozen=True)
class Transition:
    next: str
    conditions: Tuple[Any, ...]
    weights: Dict[Motivations, float]

```

* `TransitionExecutor.candidates(current_state, locals)` returns every `Transition` whose compiled conjunction evaluates to `True`.
* `TransitionMechanics` filters candidates through `AnimationMap.action(sprite.state, board.equipment, intention=t.next) is not None`, ensuring inadmissible equipment never blocks a lower-priority admissible transition.
* `TacticalSelector.select(candidates, sprite.state)` selects the candidate maximizing `t.weights.get(motivation, 0.0)` with declaration-order tie-breaking, guaranteeing deterministic behavior and full compatibility with un-weighted transitions.

###### Goal: Clean Single-Goal Intention Topology (`automata/intentions/main.yaml`)

Audit and normalize `src/data/configurations/automata/intentions/main.yaml` so every Intention loop strictly preserves its Goal category invariant and has valid entry/exit edges:

* Remove broken cross-category transitions (`mine → build` on `RESOURCE`, `barter → threaten` on `RESOURCE`).
* Add proper `idle` entrypoints for `mine` (`Goals.RESOURCE`), `build` (`Goals.PROPERTY`), and `barter` (`Goals.SUBJECT` when trade-motivated), plus competing tactical entrypoints for `Goals.TARGET` (`idle → {hunt, threaten, mock}`) differentiated by `weights` over `Motivations`.
* Verify via static graph validation that every non-`idle` Intention has at least one reachable path from `idle` and a guaranteed exit path to `idle` on Goal clearance or category mismatch.

##### Tasks

**1. Task: Extend Automata Configuration & Executor Models**

*Objective*: Add typed `MethodConfiguration` / `MethodRule` support for `Outcomes.PREREQUISITE` and Motivation `weights` on `IntentionConfiguration` / `Transition`.

* [ ] Subtask: Add `Outcomes.PREREQUISITE` and new `Locators` keys (`RESOURCE`, `MERCHANT`, `RIVAL`) to `app.static.semantics`.
* [ ] Subtask: Define frozen `dataclass(slots=True)` `MethodConfiguration` (`key`, `locator`, `category`, `weights`, `conditions`) and add `methods: List[MethodConfiguration]` to `GoalConfiguration` in `src/app/models/configurations/automata/goals.py`.
* [ ] Subtask: Add `weights: Dict[Enumerated[Motivations], float]` to `IntentionConfiguration` in `src/app/models/configurations/automata/transitions.py`.
* [ ] Subtask: Update `OUTCOME_PRECEDENCE`, `GoalRule`, and `GoalTranslator.compile` in `src/app/services/automaton/executors/resolutions.py` to compile `MethodRule` tuples via the active `Backend` (`Compiler` / `Lambda`) with fail-fast validation.
* [ ] Subtask: Add `TransitionExecutor.candidates(current_state, locals) -> List[Transition]` alongside `evaluate` in `src/app/services/automaton/executors/transitions.py`, preserving AST/Lambda backend parity.

**2. Task: Implement Generalized Stack Subsumption & Locators**

*Objective*: Enable `GoalResolver` to decompose compound Goals into prerequisite subgoals via pluggable `Locator` strategies and Motivation-weighted method ranking.

* [ ] Subtask: Implement `ResourceLocator` (nearest visible/remembered matching `AssetCategories.RESOURCES` on the current layer) and register it in `LocatorOperator.defaults()` in `src/app/game/logic/modules/cognition/goals/locators.py`.
* [ ] Subtask: Implement `MethodSelector` in `src/app/game/logic/modules/cognition/goals/` to score viable `(MethodRule, Asset)` candidates using `Psyche.motivation` weights, `AnimationMap` equipment admissibility, and distance tie-breaking.
* [ ] Subtask: Implement `PrerequisiteOutcome` in `src/app/game/logic/modules/cognition/goals/outcomes.py` and register it under `Outcomes.PREREQUISITE` in `OutcomeOperator.defaults()`, pushing the parent onto `memory.stack` on success and demoting via `Responses.STORE` when all methods fail.
* [ ] Subtask: Extend `ResolutionContext` in `src/app/game/logic/modules/cognition/goals/base.py` with `excluded_methods: FrozenSet[str]` and return/record selected method provenance for rollback tracking.

**3. Task: Implement Online Rollback & Method-Failure Tracking**

*Objective*: Prevent infinite decomposition loops by recording failed methods on `LOST` child Goals and allowing `CognitionMechanics` to fall back to alternate methods before marking a parent Goal dormant.

* [ ] Subtask: Add parent-scoped failed-method tracking (`mark_failed_method`, `failed_methods`, `clear_failed_methods`) and active subgoal provenance to `Perception` in `src/app/game/logic/modules/cognition/perception.py`.
* [ ] Subtask: Update `CognitionMechanics._resolve` and `_sync` in `src/app/game/logic/mechanics/intentional/cognition.py` to pass `excluded_methods` into `GoalResolver.resolve` and record method failures when a pushed child resolves `Outcomes.LOST`.
* [ ] Subtask: Update `UnwindResponse` (or add a dedicated retry-aware unwind policy) so unwound parent Goals remain eligible for immediate `Recall` if untried methods exist, and become `dormant = True` once all methods are exhausted.
* [ ] Subtask: Expose required domain predicates (e.g., `has_materials`) in `app.services.automaton.environ.Environ.functions` so `PREREQUISITE` conditions evaluate cleanly in ISL.

**4. Task: Upgrade `TransitionMechanics` for Multi-Candidate Tactical Selection**

*Objective*: Evaluate all satisfied transitions, filter by equipment admissibility, and select among competing same-Goal loops using `Psyche.motivation`.

* [ ] Subtask: Implement `TacticalSelector` in `src/app/game/logic/modules/maps/` (or `cognition/`) to select the highest-scoring admissible `Transition` using `sprite.state.psyche.motivation` with declaration-order tie-breaking.
* [ ] Subtask: Refactor `TransitionMechanics.update` in `src/app/game/logic/mechanics/intentional/transition.py` to query `self.executor.candidates(...)`, filter candidates through `AnimationMap.action(..., intention=t.next)`, and dispatch through `TacticalSelector`.
* [ ] Subtask: Ensure that rejecting an inadmissible high-priority transition falls through to remaining admissible candidates instead of stalling the Sprite in its current Intention.

**5. Task: Refactor Declarative Automata Configurations (`goals/main.yaml` & `intentions/main.yaml`)**

*Objective*: Align YAML matrices with strict single-Goal intention loops and multi-method prerequisite decomposition.

* [ ] Subtask: Remove cross-Goal category transitions (`mine` to `build`, `barter` to `threaten`) from `src/data/configurations/automata/intentions/main.yaml`.
* [ ] Subtask: Add `idle` entrypoints for `mine` (`Goals.RESOURCE`) and `build` (`Goals.PROPERTY`), and add Motivation-weighted competing loops for `Goals.TARGET` (`idle` to `{hunt, threaten, mock}`).
* [ ] Subtask: Add `prerequisite` multi-method decomposition blocks (starting with `property` → `resource` / `subject`) to `src/data/configurations/automata/goals/main.yaml`.

**6. Task: End-to-End Verification & Documentation**

*Objective*: Validate multi-method decomposition, online backtracking, and Motivation-weighted transition selection using real dependency-tree `pytest` fixtures.

* [ ] Subtask: Add unit and integration tests using shared `conftest.py` Board/Orchestrator fixtures covering: (a) `PROPERTY` pushing `RESOURCE` onto `memory.stack`, mining to `COMPLETE`, popping `PROPERTY`, and entering `build`; (b) stalling on method 1, unwinding, excluding method 1, and succeeding via method 2; (c) exhausting all methods and demoting the parent cleanly without oscillation.
* [ ] Subtask: Add tests verifying that two identical Sprites with different `Psyche.motivation` values (`CONQUEST` vs. `REBELLION`) select distinct admissible Intention loops from `idle` for the same `Goals.TARGET`, and that missing weapon admissibility cleanly falls through to non-weapon candidates.
* [ ] Subtask: Update `docs/04-intentions.md` and `docs/05-mechanics.md` to document `Outcomes.PREREQUISITE`, multi-method decomposition, failed-method rollback, and Motivation-weighted multi-transition selection.