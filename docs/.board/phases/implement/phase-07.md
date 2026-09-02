#### Implement: Phase 07 - Intentions

##### Goals

**1. Interfaces (`app.services.translators.base`)**

* **`Executor` (ABC):** Defines the execution contract.

```python
class Executor(ABC):
    @abstractmethod
    def evaluate(self, sprite: SpriteState, sprites: Dict[str, Any]) -> Optional[Intentions]:
        pass
```


* **`Translator` (ABC):** Defines the compilation contract.

```python
class Translator(ABC):
    @abstractmethod
    def compile(self, raw_intentions: Dict[Intentions, List[IntentionConfiguration]]) -> Executor:
        pass
```

**2. Concrete Implementations**

* **`LambdaTranslator` & `LambdaExecutor`:** Evaluates string conditions by generating a Python function via `eval(f"lambda sprite, sprites: {condition_str}")`. Relies on `LOAD_FAST` bytecode optimization.
* **`CompilerTranslator` & `CompilerExecutor`:** Evaluates string conditions by compiling raw expressions via `compile(expr, '<string>', 'eval')` and executing them via `eval(code_obj, globals, locals)`. Relies on `LOAD_NAME` dictionary lookups.

**3. Integration Point**

The `Orchestrator` or `Builder` inspects `settings.TRANSLATOR`, instantiates the appropriate `Translator`, compiles the raw YAML intention configurations into an `Executor`, and injects that `Executor` into `TransitionMechanics`.

**4. Benchmarking Methodology**

To empirically determine whether AST compilation's elegance is "worth the squeeze" in a CPython 2D game loop, the benchmarking harness must measure **inner-loop execution time** under realistic load (e.g., evaluating transitions for $N$ active sprites across thousands of frames).

1. **Metric:** Average execution time per sprite tick (measured in nanoseconds/microseconds using `time.perf_counter_ns()`).
2. **Test Harness:** A dedicated benchmark script (`scripts/benchmark_isl.py`) or an integrated telemetry flag that runs a headless simulation for 1,000 game ticks with 100 active sprites constantly evaluating intention transitions.
3. **Data Collection:** Capture total CPU time spent inside `TransitionMechanics.update()` across both strategies under identical board states.
4. **Evaluation Criteria:** If the `CompilerTranslator` introduces more than a marginal percentage increase in frame-time overhead due to dictionary allocation and `LOAD_NAME` resolution, `LambdaTranslator` remains the default.

**5. The Core Paradigm: Separation of "Brain" and "Instinct"**


* **`CognitionMechanics` (The Brain):** Manages the **Goal Lifecycle**. It evaluates the environment, consults `Motivations` and `Meters`, sets the `Goal`, determines if the `Goal` has been achieved (or invalidated), and manages the Memory stack.
* **`TransitionMechanics` (The Instinct):** Manages the **Intention Transitions**. It looks at the current `Goal` set by Cognition and evaluates the ISL matrix to figure out *how* to achieve it (e.g., "I have a target Sprite, so I transition from `IDLE` to `FIND`").
* **Spatial Mechanics (The Muscle):** `CombatMechanics`, `InteractionMechanics`, etc., alter the physical world state (e.g., killing the target, opening the chest). This physical change is what signals `CognitionMechanics` on the *next* frame that the goal is achieved.

**6. The Goal Lifecycle (Implementation in `CognitionMechanics`)**

`CognitionMechanics.update()` should execute the following four phases in strict order every game tick:

*Phase A: Resolution (Is the goal finished?)*

Before doing anything, the Sprite evaluates its current `goal`. Has the world state changed such that the goal is complete or no longer valid?

* *If `goal.category == SPRITE`:* Is the target dead? If yes, `sprite.state.goal = None`.
* *If `goal.category == LOOT`:* Does `sprite.inventory` now contain the item? If yes, `sprite.state.goal = None`.
* *If `goal.category == POSITION`:* Is `sprite.position` within an epsilon radius of the target? If yes, `sprite.state.goal = None`.

*Phase B: Memory Management (The Stack)*

If `sprite.state.goal` is `None` (either because it was just resolved or never existed), the Sprite checks its memory.

* If `memory.goals` has items, pop the top item and set it as `sprite.state.goal`.

*Phase C: Ideation (Goal Selection)*

If `sprite.state.goal` is *still* `None` (memory is empty), the Sprite must ideate a new Goal based on internal needs and external stimuli. This operates on a hierarchy of priorities:

1. **Immediate Needs (Meters):** If `health` is critically low, generate a `Goal(POSITION, nearest_safe_zone)` or `Goal(LOOT, health_potion)`.
2. **Motivations (Psyche):**
    * `PROFIT`: Scan environment for `CHESTS` or `MINEABLE` resources. Generate `Goal(LOOT, ore)`.
    * `CONQUEST`: Scan for `PLAYERS` or rival faction `SPRITES`. Generate `Goal(SPRITE, player_name)`.
    * `SURVIVAL`: Scan for food or shelter.
* *Fallback:* If no motivational targets are in the `vision.radius`, generate a generic `Wander` coordinate.

*Phase D: Interruptions & Tracking*

Even if a Sprite has a Goal, the environment can interrupt them.

* If the Sprite is struck by an enemy (triggering `mutators.triggers.struck`), survival overrides profit. The Sprite pushes its current `Goal(LOOT, chest)` onto the `memory.goals` stack, and generates an immediate `Goal(SPRITE, attacker)`.
* Finally, `CognitionMechanics` updates `goal.position` for moving targets (what the mechanic currently does).

##### Example Scenario Flow

**Frame 1 (Ideation):**

1. `CognitionMechanics`: Sprite has no Goal. Motivation is `PROFIT`. Scans environment, finds a Chest. Sets `Goal(category=ASSET, name="chest-01")`.
2. `TransitionMechanics`: ISL rule triggers: `not sprite.intention and sprite.goal -> intention = FIND`.
3. `MotionMechanics`: Accelerates Sprite toward `goal.position`.

**Frame X (Arrival):**

1. `MotionMechanics`: Sprite physically collides with the Chest.
2. `TransitionMechanics`: ISL rule triggers: `intersects(sprite, goal) -> intention = INTERACT`.

**Frame X+1 (Interaction):**

1. `InteractionMechanics`: Sees Sprite is in `INTERACT`. Flips chest `switch` to `ON`. Puts chest contents into Sprite's `inventory`.

**Frame X+2 (Resolution):**

1. `CognitionMechanics`: Evaluates Phase A. Target was a Chest, and the Chest is now `ON` (empty). Goal achieved. Sets `goal = None`. Memory is empty. Phase C (Ideation) generates a new goal (e.g., `Wander`).
2. `TransitionMechanics`: ISL rule triggers: `not sprite.goal -> intention = IDLE`.

##### Tasks


**0. Animation & Cognition Map Bug Fixes**

- BUG: *Null Reference in CognitionMechanics:* In `CognitionMechanics._acquire_target` and `_track_target`, you call `sprite.state.mutators.parameters.vision.radius`. However, in `models.state.py`, `Mutators.parameters` defaults to `None`. If a basic Sprite (like a Pixie or simple NPC) lacks parameterized mutators, this will throw an `AttributeError`.
- BUG: *Transition vs. Animation Sync:* Currently, `TransitionMechanics` maps the Animation Action *before* evaluating the Intention conditions. This means the sprite visually reacts one frame *after* its internal state transitions. (Your backlog successfully identified this, but it must be explicitly fixed).

*   [x] Update `AnimationMap.action()` to properly resolve spatial/interactive Intentions (`MINE`, `BUILD`, `INTERACT`) against slotted Tools, Utilities, or default actions.
*   [x] Patch `CognitionMechanics` to check `if sprite.state.mutators.parameters is not None` before accessing `vision.radius` or `fear` radii. 

**1. Data Model Preparation**

*   [x] Create `IntentionTransition` in `app/models/config.py` to include the compiled `conditions: List[Callable] = field(default_factory=list)`.
*   [x] Define an `ISLEnvironment` dictionary in `app/config/settings.py` containing required Enums (e.g., `Goals`), and system targets so they can be injected into the `eval()` context safely.


**2. Settings & Interface Foundations**

* [x] Add `ISL_TRANSLATOR: str = "lambda"` (options: `"lambda"`, `"compiler"`) to `app/config/settings.py`.
* [x] Create `app/services/translators/base.py` defining the `Translator` and `Executor` abstract base classes.

**3. Concrete Translators and Executors**

* [x] Implement `LambdaTranslator` and `LambdaExecutor` in `app/services/translators/lambda_translator.py`, utilizing string-templated `eval(f"lambda sprite, sprites: {cond}")`.
* [x] Implement `CompilerTranslator` and `CompilerExecutor` in `app/services/translators/compiler_translator.py`, utilizing Python's native `compile(cond, '<string>', 'eval')`.

**4. Chronological Refactoring (`TransitionMechanics`)**

* [x] Update `Builder` to compile the YAML intention rules during `build_board()` and inject the `Executor` directly into `TransitionMechanics`.
* [x] In `TransitionMechanics.update()`, generate `sprites_dict = {s.name: s for s in board.instances(AssetInstances.SPRITES) + board.instances(AssetInstances.PLAYERS)}` once at the start of the loop to satisfy the ISL target lookups.
* [x] Refactor `TransitionMechanics.update()` to evaluate the Intention Transition Matrix *first* using the `Executor` and the $O(1)$ `board._cached_characters` dictionary.
* [x] Break the transition loop upon the first successful condition match to prevent multi-node jumps in a single frame.
* [x] *Then* calculate `AnimationMap.action` and `direction` using the newly resolved Intention.

**5. Pipeline Integration & Board Caching**

* [x] Refactor `Board` (`app/game/board.py`) to maintain a cross-layer dictionary: `self._cached_characters: Dict[str, AssetState]` for $O(1)$ sprite reference resolution.
    * [x] Update `Board._cache()`, `add()`, and `remove()` to keep `_cached_characters` perfectly synchronized with all active Sprites and Players.
* [x] Update `Builder` (`app/services/constructors.py`) to select the translator based on `settings.ISL_TRANSLATOR`, compile the intention rules during `build_board()`, and inject the resulting `Executor` into `TransitionMechanics`.
* [x] Refactor `TransitionMechanics` (`app/game/logic/mechanics/intentional/transition.py`) to delegate rule evaluation entirely to the injected `Executor`.

**6. Benchmarking Suite & Empirical Analysis**

* [!] Create a benchmarking utility in `scripts/benchmark.py` that instantiates a test headless board state, runs 1,000 ticks of `TransitionMechanics` under both strategies, and logs precise execution time deltas.
* [!] Execute the benchmark under both settings, record the nanosecond overhead of AST compilation versus lambdas, and document the empirical findings in `docs/appendices/`.

**7. Complete the Finite Automaton**

* [ ] Review `/src/data/config/intentions/main.yaml` and resolve all dead ends. Create new Tasks to achieve this, if necessary.