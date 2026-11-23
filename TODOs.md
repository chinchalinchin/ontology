

##### Draft: Three-Tier Sheet State & Component Hierarchy

- **Page**: `docs/01-assets.md` & `docs/02-sprites.md`
- **Heading**: `###### Sheet: Pixies` (`01-assets.md`), `###### Sheet: Sprite` & `###### Sheet: Player` (`02-sprites.md`)

###### Drift

`docs/01-assets.md` leaves Pixie State as `TBD`, while `docs/02-sprites.md` describes `PlayerState` as an informal truncation of `SpriteState` without specifying the strict three-tier inheritance across States, Frames, and Animations. This ambiguity caused `Player`, `Sprite`, and `Pixie` deployments to share incompatible state and component strategies.

###### Update

```markdown
##### Sheet Hierarchy: States, Frames & Animations

Stateful Sheet Instances partition along a three-tier specialization hierarchy so each Instance carries strictly the data and rendering strategies required by its domain:

1. **Base Tier (`Pixies`)**:
   * **State (`SheetState`)**: Spatial and animation primitives (`position`, `velocity`, `animation`).
   * **Frame (`StateFrame`)**: Projects `(action, direction, frame)` onto the Sheet atlas.
   * **Animation (`StateAnimation`)**: Advances `(action, direction, frame)` according to Action count and delay.

2. **Character Tier (`Players`)**:
   * **State (`CharacterState` extends `SheetState`)**: Adds intentionality and physical agency (`intention`, `goal`, `character`, `slots`, `inventory`, `meters`).
   * **Frame (`CharacterFrame` extends `StateFrame`)**: Superimposes active Equipment frames in Z-order (`armor`, `utility`, `tool`, `weapon`, `shield`) over the base Sheet.
   * **Animation (`CharacterAnimation` extends `StateAnimation`)**: Gates body-frame advancement on `mutators.triggers.animated`, resetting idle animations to frame `0`.

3. **Autonomous Tier (`Sprites`)**:
   * **State (`SpriteState` extends `CharacterState`)**: Adds autonomous cognition and navigation (`psyche`, `memory`, `trajectory`).
   * **Frame (`SpriteFrame` extends `CharacterFrame`)**: Appends active Psyche Expression overlays at their configured spatial offset.
   * **Animation (`SpriteAnimation` extends `CharacterAnimation`)**: Advances body animations while decaying `psyche.expression.ttl` unconditionally on every tick, independent of body movement or `triggers.animated`.
```

---

##### Draft: Intention Transition Matrix Examples & Function Signature Drift

- **Page**: `docs/04-intentions.md`
- **Heading**: `###### Intention: Transition Matrix`

###### Drift

The prose example references `sprite.memory.goal.category == constants.Goals.TARGET.value` (whereas `memory.goals` is a mapping of Goal entries) and documents `any_goals(m: List[Goal], category: str)` when `memory.goals` is `Dict[str, Goal]`.

###### Update

```markdown
* `any_goals(goals: Dict[str, Goal], category: Optional[str])`: Determines whether any remembered Goal matches the requested Category (or whether Memory contains any Goals when `category` is omitted).
```

---

##### Draft: Three-Tier Sheet State Hierarchy & Mutator Parameters

* **Page**: `docs/01-assets.md`
* **Heading**: `Concept: Mutability` & `Sheet: Pixies`

###### Drift

`Model: Mutators` declares `parameters.action` and `parameters.vision` as booleans instead of spatial radii. `Sheet: Pixies` lists its State as `TBD`, diverging from the three-tier Sheet hierarchy (`Sheet` $\to$ `Character` $\to$ `Sprite`).

###### Update

**Model: Mutators**

* `parameters`: Numeric and categorical bounds modulating conditional calculations.
* `action: int`: Spatial radius of interaction.
* `vision: int`: Spatial radius of perception.


* `triggers`: Boolean flags.
* `animated: bool`: Flag governing animation progression.
* `dead: bool`: Flag indicating terminal state.
* `submerged: bool`: Flag governing aquatic frame modulation.

**Sheet: Pixies**

Pixies are kinematic Sheets excluded from equipment slotting, inventory management, and intentional goal loops. Their State inherits the minimal kinematic base (`Position`, `Velocity`, `AnimationState`) shared by all Sheets, while Characters extend this base with equipment, inventory, meters, intention, and goal, and Sprites further extend Characters with episodic memory, psyche, and trajectory.

---

##### Draft: Direction Mapping Sign Convention & Intentional Propositions

* **Page**: `docs/04-intentions.md`
* **Heading**: `Intention: Transition Matrix` & `Mapping: Directions`

###### Drift

1. Under `Direction Mapping: Sprite`, displacement is defined as $\text{position} - \text{target}$ while mapping $\Delta y > 0$ to `down`. Under the top-left origin coordinate system ($+y$ downward), a target below the Sprite satisfies $\text{target}.y > \text{position}.y$, so $\text{position}.y - \text{target}.y < 0$; the sign convention is inverted (and the formula contains malformed math delimiters).
2. Under `Concept: Intentional Propositions`, examples reference nonexistent singular `sprite.memory.goal.category` and `sprite.memory.communications`.

###### Update

**Direction Mapping: Sprite**

Let $\mathbf{p} = (p_x, p_y)$ be the Sprite position and $\mathbf{t} = (t_x, t_y)$ be the active target coordinate (the next trajectory waypoint if present, otherwise the goal position). Define displacement toward the target as:

$$\Delta x = t_x - p_x, \qquad \Delta y = t_y - p_y$$

Partitioning the plane along the diagonals $|\Delta y| = |\Delta x|$ maps displacement onto cardinal headings:

$$\begin{aligned}
(\Delta y > \Delta x \;\land\; \Delta y > -\Delta x) &\implies \text{down} \\
(\Delta y < \Delta x \;\land\; \Delta y > -\Delta x) &\implies \text{right} \\
(\Delta y < \Delta x \;\land\; \Delta y < -\Delta x) &\implies \text{up} \\
(\Delta y > \Delta x \;\land\; \Delta y < -\Delta x) &\implies \text{left}
\end{aligned}$$

---

##### Draft: Formal Intention Loops, Commitment Stack & Epistemic Perception

* **Page**: `docs/04-intentions.md`
* **Heading**: `Concept: Intention Loops` & `Workflow Component: Cognition`

###### Drift

The current documentation conflates unordered episodic goal memory with suspended subgoal commitments (such as cross-layer portal traversal) and does not state the epistemic boundary of perception or the invariant-monitoring contract between Goal resolution and Intention transitions.

###### Update

**Concept: Intention Loops**

Each Intention Loop rooted at `idle` forms a temporally extended option $\langle I, \pi, \beta \rangle$:

1. **Initiation ($I$):** The Entrypoint transition $\text{idle} : i_1$ together with any required equipment admissibility constraint.
2. **Execution ($\pi$):** Interpoint transitions $i_j : i_{j+1}$ ($i_j, i_{j+1} \neq \text{idle}$) paired with spatial and navigational mechanics.
3. **Termination ($\beta$):** Goal resolution (`complete` or `lost`) or a context-invariant violation (the active Goal category no longer matches the active Intention), routing the Sprite back to `idle` via an Exitpoint $i_{n-1} : \text{idle}$.

**Workflow Component: Cognition**

Cognition distinguishes three cognitive stores:

* **Perception (Beliefs):** Same-Layer sensory updates bounded by vision radius. Unseen entities freeze at their last observed Layer and coordinates until re-observed.
* **Commitment Stack (Intentions):** An ordered LIFO stack of parent Goals suspended by prerequisite subgoals (such as a Layer-transit Door). Completing a prerequisite immediately resumes the top suspended parent Goal.
* **Episodic Memory (Desires):** An unordered store of abandoned or remembered Goals evaluated only when the Commitment Stack is empty, filtered by Intention compatibility and live-visibility dormancy.

##### Draft: Three-Tier Sheet State Hierarchy & Mutator Parameters

* **Page**: `docs/01-assets.md`
* **Heading**: `Concept: Mutability` & `Sheet: Pixies`

###### Drift

`Model: Mutators` declares `parameters.action` and `parameters.vision` as booleans instead of spatial radii. `Sheet: Pixies` lists its State as `TBD`, diverging from the three-tier Sheet hierarchy (`Sheet` $\to$ `Character` $\to$ `Sprite`).

###### Update

**Model: Mutators**

* `parameters`: Numeric and categorical bounds modulating conditional calculations.
* `action: int`: Spatial radius of interaction.
* `vision: int`: Spatial radius of perception.


* `triggers`: Boolean flags.
* `animated: bool`: Flag governing animation progression.
* `dead: bool`: Flag indicating terminal state.
* `submerged: bool`: Flag governing aquatic frame modulation.



**Sheet: Pixies**

Pixies are kinematic Sheets excluded from equipment slotting, inventory management, and intentional goal loops. Their State inherits the minimal kinematic base (`Position`, `Velocity`, `AnimationState`) shared by all Sheets, while Characters extend this base with equipment, inventory, meters, intention, and goal, and Sprites further extend Characters with episodic memory, psyche, and trajectory.

---

##### Draft: Direction Mapping Sign Convention & Intentional Propositions

* **Page**: `docs/04-intentions.md`
* **Heading**: `Intention: Transition Matrix` & `Mapping: Directions`

###### Drift

1. Under `Direction Mapping: Sprite`, displacement is defined as $\text{position} - \text{target}$ while mapping $\Delta y > 0$ to `down`. Under the top-left origin coordinate system ($+y$ downward), a target below the Sprite satisfies $\text{target}.y > \text{position}.y$, so $\text{position}.y - \text{target}.y < 0$; the sign convention is inverted (and the formula contains malformed math delimiters).
2. Under `Concept: Intentional Propositions`, examples reference nonexistent singular `sprite.memory.goal.category` and `sprite.memory.communications`.

###### Update

**Direction Mapping: Sprite**

Let $\mathbf{p} = (p_x, p_y)$ be the Sprite position and $\mathbf{t} = (t_x, t_y)$ be the active target coordinate (the next trajectory waypoint if present, otherwise the goal position). Define displacement toward the target as:

$$\Delta x = t_x - p_x, \qquad \Delta y = t_y - p_y$$

Partitioning the plane along the diagonals $|\Delta y| = |\Delta x|$ maps displacement onto cardinal headings:

$$\begin{aligned}
(\Delta y > \Delta x \;\land\; \Delta y > -\Delta x) &\implies \text{down} \\
(\Delta y < \Delta x \;\land\; \Delta y > -\Delta x) &\implies \text{right} \\
(\Delta y < \Delta x \;\land\; \Delta y < -\Delta x) &\implies \text{up} \\
(\Delta y > \Delta x \;\land\; \Delta y < -\Delta x) &\implies \text{left}
\end{aligned}$$

---

##### Draft: Formal Intention Loops, Commitment Stack & Epistemic Perception

* **Page**: `docs/04-intentions.md`
* **Heading**: `Concept: Intention Loops` & `Workflow Component: Cognition`

###### Drift

The current documentation conflates unordered episodic goal memory with suspended subgoal commitments (such as cross-layer portal traversal) and does not state the epistemic boundary of perception or the invariant-monitoring contract between Goal resolution and Intention transitions.

###### Update

**Concept: Intention Loops**

Each Intention Loop rooted at `idle` forms a temporally extended option $\langle I, \pi, \beta \rangle$:

1. **Initiation ($I$):** The Entrypoint transition $\text{idle} : i_1$ together with any required equipment admissibility constraint.
2. **Execution ($\pi$):** Interpoint transitions $i_j : i_{j+1}$ ($i_j, i_{j+1} \neq \text{idle}$) paired with spatial and navigational mechanics.
3. **Termination ($\beta$):** Goal resolution (`complete` or `lost`) or a context-invariant violation (the active Goal category no longer matches the active Intention), routing the Sprite back to `idle` via an Exitpoint $i_{n-1} : \text{idle}$.

**Workflow Component: Cognition**

Cognition distinguishes three cognitive stores:

* **Perception (Beliefs):** Same-Layer sensory updates bounded by vision radius. Unseen entities freeze at their last observed Layer and coordinates until re-observed.
* **Commitment Stack (Intentions):** An ordered LIFO stack of parent Goals suspended by prerequisite subgoals (such as a Layer-transit Door). Completing a prerequisite immediately resumes the top suspended parent Goal.
* **Episodic Memory (Desires):** An unordered store of abandoned or remembered Goals evaluated only when the Commitment Stack is empty, filtered by Intention compatibility and live-visibility dormancy.

##### Bug 0602-01: `find -> interact` Radius Stops Sprites Outside `InteractionMechanics` Hitbox Overlap

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

`intentions/main.yaml` transitions `find -> interact` when `functions.is_near(sprite.position, sprite.goal.position, sprite.mutators.parameters.action.radius)` holds (default `30` px). Because `interact` belongs to `StationaryIntentions`, `NavigationMechanics` immediately clears the trajectory and halts locomotion. However, `InteractionMechanics` executes Door/Chest interactions on physical hitbox overlap (`self.intersections(assets)`). With Sprite hitboxes inset at `(x=23, y=34, w=18, l=15)` inside a `64x64` frame, the Sprite stops up to 30 px away without overlapping the target hitbox, deadlocking permanently in `interact`.

**Steps to Replicate**

1. Assign an autonomous Sprite a same-layer `Goals.OBJECT` (or `Goals.DOOR`) Goal with default `action.radius = 30`.
2. Advance ticks until the Sprite enters `action.radius` of the target's origin.
3. Observe `TransitionMechanics` switch `find -> interact` while `hitboxes` do not intersect; `InteractionMechanics` never fires and `interact -> idle` (`not sprite.goal`) is never satisfied.

**Proposed Remediation**

Align the initiation predicate and interaction geometry: either have `InteractionMechanics` evaluate `self.proximities` for Sprite-initiated `interact` transitions (matching `action.radius`), or tighten `find -> interact` / `NavigationMechanics` arrival so the Sprite overlaps the target's physical hitbox before halting.

---

##### Bug 0602-02: Cross-Layer Door Subsumption Deadlocks Sprites in `hunt`

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

When a Sprite in `Intentions.HUNT` pursues a `Goals.TARGET` residing on a different Layer, cross-layer door subsumption replaces `sprite.state.goal` with a `Goals.DOOR` (or `Goals.OBJECT`). In `src/data/config/intentions/main.yaml`, `hunt` only transitions to `attack` (requiring `goal.category == TARGET`) or `idle` (requiring `not sprite.goal`). The Sprite walks to the door in `hunt`, never enters `interact`, and stalls indefinitely.

**Steps to Replicate**

1. Place a Sprite in `hunt` on `layer_1` with a `Goals.TARGET` on `layer_2` and a mapped Door on `layer_1`.
2. Let `CognitionMechanics` substitute the prerequisite Door Goal.
3. Advance ticks; the Sprite arrives at the Door while remaining stuck in `hunt`.

**Proposed Remediation**

Add a category-mismatch Exitpoint to `hunt` (`sprite.goal` and `sprite.goal.category != constants.Goals.TARGET` $\to$ `idle`) and analogous mismatch Exitpoints to `attack` and `follow` so substituted `Goals.DOOR` goals route through `idle` $\to$ `find` $\to$ `interact`.

---

##### Bug 0602-03: Silent Conjunct Dropping on ISL Compilation Failure

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/services/translators/compiler.py` (`CompilerTranslator.compile`) and `src/app/services/translators/lamb.py` (`LambdaTranslator.compile`), syntax errors in an individual condition string are caught and logged, but compilation continues and appends the remaining conditions into the resulting `Transition`. This silently weakens a conjunction (`A and INVALID` compiles into `A`), causing transitions to fire under unintended states.

**Steps to Replicate**

1. Introduce a syntax error into one condition of a multi-condition rule in `src/data/config/intentions/main.yaml`.
2. Bootstrap the application and evaluate the transition when the remaining conditions hold.
3. Observe the transition firing despite the malformed condition.

**Proposed Remediation**

Fail fast during bootstrap by raising a configuration compilation error when any ISL condition fails to parse/compile in either `CompilerTranslator` or `LambdaTranslator`.

---

##### Bug 0602-04: `any_memories_visible` Matches Dead Targets

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/services/translators/environ.py`, `any_memories_visible` checks whether a remembered goal's `name` is in `sprites` on the same layer within `vision.radius`, without checking `not target.mutators.triggers.dead`. A wandering Sprite passing near a remembered target that died while dormant triggers `wander -> hunt` repeatedly until the target is garbage-collected.

**Steps to Replicate**

1. Place a `Goals.TARGET` into `sprite.memory.goals` and set `target.mutators.triggers.dead = True` while retaining the entity on the board.
2. Move the Sprite in `Intentions.WANDER` within `vision.radius` of the dead target.
3. Observe `any_memories_visible` returning `True` and triggering `wander -> hunt`.

**Proposed Remediation**

Guard `any_memories_visible` with `if target.mutators.triggers.dead: continue` for `Goals.TARGET` / `Goals.SUBJECT` candidates.

---

##### Bug 0602-05: `CognitionMechanics.update` Dereferences `board.player()` Without `None` Guard

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/game/logic/mechanics/intentional/cognition.py`, `CognitionMechanics.update` evaluates `if sprite.name == board.player().name:` on every sprite iteration without checking whether `board.player()` is `None` (unlike `TransitionMechanics` and `NavigationMechanics`), causing an `AttributeError` on boards without a deployed Player (such as headless or unit-test simulations).

**Steps to Replicate**

1. Instantiate a `Board` containing at least one `Sprite` and zero `Player` assets.
2. Invoke `CognitionMechanics().update(board, delta, bus, payload)`.
3. Observe `AttributeError: 'NoneType' object has no attribute 'name'`.

**Proposed Remediation**

Hoist `player = board.player()` outside the sprite loop and guard with `if player and sprite.name == player.name: continue`.

---

##### Bug 0602-06: Per-Tick `logger.info` Logging in `PlayerMechanics` and Dead Statement in `StateFrame`

**STATUS**: OPEN
**SEVERITY**: LOW

**Description**

1. `src/app/game/logic/mechanics/intentional/player.py` emits two `logger.info` statements on every simulation tick while `player.state.intention == Intentions.ATTACK`, causing hot-loop log I/O overhead analogous to `SpriteFrame`.
2. `src/app/assets/frames/sheets.py` contains a stray no-op expression `properties.actions` in `StateFrame.index`.

**Steps to Replicate**

1. Hold or trigger `Intentions.ATTACK` on the Player with logging at `INFO` level.
2. Observe two `SheetState(...)` / `Equipment(...)` log entries emitted every tick for the full duration of the attack animation.

**Proposed Remediation**

Downgrade the per-tick `logger.info` calls in `PlayerMechanics` (and `SpriteFrame`) to `logger.debug`, and remove the dead `properties.actions` statement in `StateFrame.index`.