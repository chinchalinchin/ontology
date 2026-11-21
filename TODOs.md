

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

## Bug Reports

##### Bug 06-02-01: `NavigationMechanics._target` Overrides `ESCAPE` Goal Projection, Steering Fleeing Sprites Toward Their Attacker

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

When a Sprite enters `Intentions.ESCAPE`, `CognitionMechanics._project` (`src/app/game/logic/mechanics/intentional/cognition.py`, lines 512–518) extrapolates `sprite.state.goal.position` away from the threat while leaving `sprite.state.goal.name` set to the attacker's name. Immediately afterward, `NavigationMechanics._target` (`src/app/game/logic/mechanics/intentional/navigation.py`, lines 152–157) resolves `board.asset(goal.name, sprite.state.layer)` whenever `goal.name` matches a same-layer asset—completely ignoring `goal.position` and returning `self.anchor(attacker)`. As a result, fleeing Sprites path directly into their attacker. Additionally, `_project` dereferences `sprite.state.goal.position` without a `None` check and fails to clamp the extrapolated point to layer bounds.

**Steps to Replicate**

1. Deploy a Sprite at `(100, 100)` with `intention = Intentions.ESCAPE`, `triggers.vision = True`, and `goal = Goal(name=attacker.name, category=Goals.TARGET, layer=layer, position=Position(120, 100))`.
2. Run `CognitionMechanics.update()` followed by `NavigationMechanics.update()`.
3. Observe `sprite.state.goal.position.x == -100` (unclamped off-map), while `sprite.state.trajectory.target` is set to the attacker's position at `(120, 100)` instead of fleeing left.

**Proposed Remediation**

Respect `goal.position` in `NavigationMechanics._target()` when `sprite.state.intention == Intentions.ESCAPE` (or when `goal.category == Goals.POSITION`), guard `sprite.state.goal` for `None` in `Projector`, and clamp extrapolated escape coordinates to `[0, max_w - sprite_w] x [0, max_l - sprite_l]` matching `WANDER`.

---

##### Bug 06-02-02: `SpriteAnimation.animate` Freezes Expression TTL Decay When `triggers.animated` Is `False`

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

`TransitionMechanics` (`src/app/game/logic/mechanics/intentional/transition.py`, lines 128–135) sets `sprite.state.mutators.triggers.animated = False` whenever a Sprite is stationary (`vx == 0, vy == 0`) in any `StaticIntention` (including `speak` and `idle`). `SpriteAnimation.animate` (`src/app/assets/animations/sheets.py`, lines 22–34) returns early when `not state.mutators.triggers.animated` before decrementing `state.psyche.expression.ttl`. Because `intentions/main.yaml` exits `speak -> idle` only when `not sprite.psyche.expression`, a stationary Sprite speaking to another Sprite (or displaying a `confusion` bubble while stationary in `idle`) never clears its Expression and permanently softlocks in `speak`.

**Steps to Replicate**

1. Place two non-player Sprites adjacent to each other with `velocity = (0, 0)`, `intention = Intentions.SPEAK`, and a `psyche.expression` with `ttl = 30`.
2. Tick `TransitionMechanics` followed by `AnimationMechanics` for 60 ticks.
3. Observe `triggers.animated == False`, `expression.ttl` remains `30`, and the Sprite never transitions back to `idle`.

**Proposed Remediation**

In the refactored `SpriteAnimation(CharacterAnimation)`, execute `super().animate(state, properties)` for body frames and decrement `state.psyche.expression.ttl` unconditionally afterward regardless of `mutators.triggers.animated`.

---

##### Bug 06-02-03: `CognitionMechanics._remember` Uses Stale `triggers.vision` for Dormancy & Ignores Intention Affinity

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

In `src/app/game/logic/mechanics/intentional/cognition.py` (lines 352–363), `_remember` evaluates dormancy for memorized goals using `not sprite.state.mutators.triggers.vision` — a flag belonging to the Sprite's *previously active* Goal rather than the memorized candidate.
1. If a Sprite abandons a `TARGET` at `(100, 100)` (`triggers.vision = False`), and the `TARGET` later returns to `(105, 100)` (within `action.radius`), `_scan` updates `memory.goals[target].position` without setting `triggers.vision = True`. `_remember` then skips the `TARGET` as dormant even though it is standing directly next to the Sprite.
2. Conversely, after dropping a `WANDER` goal (`_track` sets `triggers.vision = True` for `POSITION`), a genuinely absent dormant `TARGET` is immediately popped back into `sprite.state.goal`.
3. `_remember` selects the first matching dict entry without considering `sprite.state.intention`, allowing a Sprite in `Intentions.HUNT` to pop a `SUBJECT` goal and deadlock in `hunt`.

**Steps to Replicate**

1. Place a Sprite at `(100, 100)` with `goal = None`, `triggers.vision = False`, and `memory.goals["target"] = Goal(name="target", category=Goals.TARGET, layer=L, position=Position(100, 100))`.
2. Move `"target"` to `(105, 100)` (within `action.radius`) on layer `L`.
3. Execute `CognitionMechanics._scan` and `CognitionMechanics._remember`.
4. Observe `sprite.state.goal` remains `None` despite `"target"` being visible and adjacent.

**Proposed Remediation**

Evaluate dormancy in `Recall` by checking live visibility against `board.character(candidate.name)` (same layer and within `vision.radius`), skipping only when the entity is currently *unseen* and the Sprite is already within `action.radius` of `candidate.position` on `candidate.layer`. Filter/prioritize candidates by intention affinity (`HUNT` $\to$ `TARGET`; `FIND` $\to$ `SUBJECT`, `OBJECT`, `DOOR`; `IDLE` $\to$ any eligible category).

---

##### Bug 06-02-04: `attack` Intention Softlock, Unreachable `attack -> scavenge`, and Unsafe Attribute Dereference

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

In `src/data/config/intentions/main.yaml` (lines 3–22):
1. `CognitionMechanics` runs before `TransitionMechanics` and clears `sprite.state.goal = None` as soon as `target.mutators.triggers.dead` becomes `True`. Consequently, `attack -> scavenge` (which requires `sprite.goal` and `target.dead`) is unreachable.
2. `attack` has no exitpoint to `idle` when `not sprite.goal` and no other `TARGET` exists in `memory.goals`, violating the Intention Loop hub invariant and leaving the Sprite permanently stuck in `attack`.
3. `attack -> attack` accesses `sprites.get(sprite.goal.name).mutators.triggers.dead` without an existential `sprites.get(sprite.goal.name)` check, and does not check `is_near(..., action.radius)` to transition back to `hunt` when a Target retreats out of attack range.

**Steps to Replicate**

1. Put an autonomous Sprite in `Intentions.ATTACK` targeting an enemy with `memory.goals = {}`.
2. Set the target's `mutators.triggers.dead = True`.
3. Run `CognitionMechanics.update()` then `TransitionMechanics.update()`.
4. Observe `sprite.state.goal` becomes `None`, `attack -> scavenge` does not trigger, and `sprite.state.intention` stays `Intentions.ATTACK` indefinitely.

**Proposed Remediation**

Add a terminal `- next: idle` rule (`conditions: [not sprite.goal]`) to `attack`, guard `sprites.get(sprite.goal.name)` before dereferencing `.mutators`, add a range-loss transition back to `hunt` when the live Target leaves `action.radius`, and decouple `scavenge` acquisition cleanly via `idle` rather than relying on a cleared `TARGET` goal.

---

##### Bug 06-02-05: `CognitionMechanics._scan` Aliases Mutable `Position` Reference in `memory.sprites`

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/game/logic/mechanics/intentional/cognition.py` (line 325), `sprite.state.memory.sprites[other_name] = other_state.position` stores a direct reference to the live Cython `Position` object of `other_state`. Once another character enters vision radius a single time, `memory.sprites[other_name]` mutates in lockstep with that character's true coordinates even after they leave vision radius or move to another Layer.

**Steps to Replicate**

1. Allow Sprite A to scan Sprite B at `(100, 100)`.
2. Move Sprite B to `(900, 900)` outside Sprite A's vision radius.
3. Inspect `sprite_a.state.memory.sprites[sprite_b.name]` and observe it reads `(900, 900)` instead of the last-observed `(100, 100)`.

**Proposed Remediation**

Store an independent snapshot `Position(x=other_state.position.x, y=other_state.position.y)` (or update an existing owned `Position` instance in place) in `Perception.scan`.

---

##### Bug 06-02-06: `CognitionMechanics.update` Dereferences `board.player().name` Without `None` Guard

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

`CognitionMechanics.update` (`src/app/game/logic/mechanics/intentional/cognition.py`, line 168) executes `if sprite.name == board.player().name:` on every Sprite iteration without verifying `board.player()` is not `None`. On any Board lacking a Player entity (such as headless NPC tests or simulations), this raises `AttributeError: 'NoneType' object has no attribute 'name'`.

**Steps to Replicate**

1. Instantiate a `Board` containing at least one `AssetInstances.SPRITES` entity and zero `AssetInstances.PLAYERS` entities.
2. Call `CognitionMechanics().update(board, delta, bus, payload)`.
3. Observe `AttributeError`.

**Proposed Remediation**

Hoist `player = board.player()` outside the Sprite loop and guard with `if player and sprite.name == player.name: continue` (matching `NavigationMechanics` and `TransitionMechanics`).

---

##### Bug 06-02-07: `CognitionMechanics.door` Can Target Non-Interactive `LayerProjections.OUT` Shadow Doors

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

`CognitionMechanics.door` (`src/app/game/logic/mechanics/intentional/cognition.py`, lines 139–151) scans `board.instances(AssetInstances.DOORS, sprite.state.layer)` without filtering by `DoorState.projection`. Because Board hydration deploys reciprocal `LayerProjections.OUT` shadow doors onto destination layers (with empty `LayeredHitbox.elevations()`), a Sprite exploring unmapped doors can select an `OUT` projection that it can never physically intersect or traverse.

**Steps to Replicate**

1. Deploy a Door on `layer-1` projecting an `OUT` shadow footprint onto `layer-2`.
2. Give a Sprite on `layer-2` (within vision radius of the `OUT` shadow, with empty `memory.doors`) a Goal located on `layer-1`.
3. Call `CognitionMechanics.door(sprite, board)`.
4. Observe the `OUT` shadow door may be returned as `target_door`.

**Proposed Remediation**

Filter candidate doors in `GoalResolver.door()` to strictly require `d.state.projection == LayerProjections.IN`.

---

##### Bug 06-02-08: `CognitionMechanics._track` Blocks Cross-Layer Door Subsumption for Static Goals

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/game/logic/mechanics/intentional/cognition.py` (lines 454–465), `_track` returns early for `Goals.POSITION`, `Goals.OBJECT`, and `Goals.PROPERTY` prior to reaching the cross-layer door subsumption block (lines 470–492). If a Sprite holds a static Goal located on another Layer, it never subsumes the Goal into a Door while `NavigationMechanics` (`navigation.py`, line 210) clears its trajectory whenever `goal.layer != sprite.layer`, freezing the Sprite indefinitely.

**Steps to Replicate**

1. Assign a Sprite on `layer-1` a Goal with `category=Goals.OBJECT` (or `POSITION`) and `layer="layer-2"`.
2. Run `CognitionMechanics.update()` and `NavigationMechanics.update()`.
3. Observe no Door goal is assigned and `sprite.state.trajectory.target` remains `None`.

**Proposed Remediation**

Move cross-layer subsumption out of `_track` into `GoalResolver`'s declarative `layered` outcome, enabling uniform Door routing across all non-`DOOR` Goal categories (`TARGET`, `SUBJECT`, `OBJECT`, `POSITION`, `PROPERTY`, `RESOURCE`).

---

##### Bug 06-02-09: Invalid Attribute/Enum References & Proximity Stalls in `intentions/main.yaml`

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

Multiple rules in `src/data/config/intentions/main.yaml` diverge from current State models or create deadlocks:
1. `barter -> threaten` (line 27) evaluates `sprite.inventory.wallet`, an attribute that does not exist on `Inventory` (`src/app/models/state/assets/sheets.py`).
2. `barter` and `mine` (lines 26, 147, 151) reference `constants.Goals.LOOT`, whereas Goal semantics specify `RESOURCE`.
3. `idle -> find` for `SUBJECT` and `OBJECT` (lines 95–116) requires `not functions.is_near(..., action.radius)`, yet `idle` defines no transition to `speak` or `interact` when already within `action.radius`—stalling idle Sprites positioned next to their target.
4. `CognitionMechanics._ideate` (lines 380–404) creates `Goals.SUBJECT` for any nearby character regardless of `memory.relationships`, while `find -> speak` (lines 58–62) requires `FRIEND` or `FAMILY`, causing a Sprite with dialogue near a stranger to pursue them and stall indefinitely in `find`.

**Steps to Replicate**

1. Place an `idle` Sprite with `psyche.dialogue = "hello"` directly adjacent (within `action.radius`) to a `FRIEND` character.
2. Run `CognitionMechanics` and `TransitionMechanics`.
3. Observe `_ideate` sets a `SUBJECT` Goal, `idle -> find` evaluates to `False` (already near), and the Sprite never transitions to `speak`.

**Proposed Remediation**

Align `barter`/`mine` with actual `Inventory` fields and `Goals.RESOURCE`; add proximity-ready transitions from `idle` (or remove the negated `is_near` guard on `idle -> find` so `find` immediately transitions to `speak`/`interact` on the following tick); and validate relationship admissibility inside `Ideation` before committing a `SUBJECT` Goal.

---

##### Bug 06-02-10: `SheetState.goal` Default Factory Instantiates a Truthy Empty `Goal()`

**STATUS**: OPEN
**SEVERITY**: LOW

**Description**

`SheetState` (`src/app/models/state/assets/sheets.py`, line 143) declares `goal: Optional[Goal] = field(default_factory=Goal)`. Any Sprite hydrated without an explicit `goal: null` receives a non-`None`, truthy `Goal(name=None, category=None, layer=None, position=Position(0, 0))`, causing `not sprite.goal` guards across `CognitionMechanics` and `TransitionMechanics` (`idle -> wander`, `_remember`, `_motivate`) to evaluate to `False`.

**Steps to Replicate**

1. Instantiate `SpriteState(id="archaxes", name="npc-1", layer="layer-1")` without specifying `goal`.
2. Evaluate `bool(state.goal)` and observe `True` with `state.goal.category is None`.

**Proposed Remediation**

Default `CharacterState.goal` to `Optional[Goal] = None` (and validate `Goal.category` as `Optional[Enumerated[Goals]]`), auditing `MotionMechanics` and `PlayerMechanics` to confirm `None` safety.




---

# Documentation Updates

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

---

# Bug Reports

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