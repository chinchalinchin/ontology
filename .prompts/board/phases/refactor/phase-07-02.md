#### Refactor: Phase 07.02 - Interact Intention

**Goals**: Implement the `interact` Intention and its Interaction Loop.

**Focus**: Analyze the theoretical and not-yet-implemented question of Sprite-Door interactions.

**Considerations**

- The `Goal` data model. Currently it only has `category` and `position`, lacking `layer`, i.e. a Sprite goal is agnostic of its layer. 

**Notes**

Suppose a Sprite is pursuing a Goal such that `goal.layer != sprite.state.layer`.

**NOTE**: Sprite needs memory of `door` Positions and their corresponding `layer`. 

If Sprite knows Goal is not on its layer, but does not know which `door` leads to the desired `layer`, it needs a routine for "testing" doors to acquire knowledge of their `layer`. If `sprite.intention == Intentions.FIND.value and sprite.goal.category == GoalCategores.SUBJECT.value and sprite.goal.layer != sprite.state.layer`, but `nearby(door.state.position, sprite.state.position, sprite.state.mutators.parameters.vision.radius) and (sprite.memory.doors[door.name].outlayer = goal.layer or door.name not in sprite.memory.doors.keys()`, Sprite should store its current goal in its `memory.goals` stack, create a new goal `Goal(category=GoalCategories.OBJECT.value)`.

Then, once Sprite intersects with door, it transitions into `interact`, and passes through the door. At this point, the `door.state.outlayer` is saved in the `sprite.memory.doors` dictionary. 

The `interact` goal is satisfied and resolved, the Sprite transitions back into `find` and continues searching for sprite.

**Principles**

- Goal creation and resolution is currently handled entirely by CognitionMechanics. It should be kept this way.
- Intentions are only altered by TransitionMechanics. It should be kept this way.

These are soft constraints and up for debate, should the need arise, but justification for violating them must be substantial.

**Questions**

- How can the Interaction Loop be defined in the Transition Matrix? 
- How can the Interaction Loop be designed in such way to keep Intentions "nestable", i.e. the Interaction Loop must be accessible when traversing the Speak Loop, in case the Sprite needs to speak to a Sprite on another layer.
- What are the general principles and guidelines for Transitions? How can Transitions be kept independent of the logic applied by the Intention? To some extent, this impossible. Intentions modify the state and transitioning to another Intention will alter the state and thus affect the Transition. Transitions can't be indepedent, as they depend on the particular implementation of the Intentional. But there are general principles, I think anyway, that can be adopted (e.g. nothing changes an Intention *except* a Transition, nothing creates a Goal *except* Cognition.) Propose some general rules of Transitions to keep them clean and succinct. Propose some general rules of Mechanics to ensure Transitions and Intentions do not become a logical labyrinth of infinite complexity.

### Goal: Door Interaction Sequence

**Tick 1: The Prerequisite Setup**

* **Cognition (`_ideate`):** Assigns `SUBJECT` goal.
* **Cognition (`_track`):** Detects `active_goal.layer != sprite.layer`. Pushes `SUBJECT` to `memory.goals`. Assigns Door as the new `OBJECT` goal.
* **Transition:** Evaluates `idle`. **[Requires Code Change]** We must add an ISL branch to `idle` that transitions to `find` when `goal.category == OBJECT`.

**Tick 2 - N: Pathfinding**

* **Cognition:** Maintains goal.
* **Transition:** Evaluates `find`. Sprite stays in `find` until `functions.is_near` evaluates to True.
* **Spatial (`MotionMechanics`):** Moves Sprite toward the Door.

**Tick N+1: The Interaction**

* **Transition:** `is_near` evaluates True. Sprite transitions from `find` to `interact`.
* **Spatial (`InteractionMechanics`):** Resolves the interaction. Teleports the Sprite to `door.outlayer`.

**Tick N+2: The Resolution & Memory Trap**

* **Cognition (`_resolve`):** Sees the `OBJECT` goal is met (Sprite layer matches Door `outlayer`). Sets `goal = None`.
* **Cognition (`_remember`):** *Crucial safeguard.* The codebase dictates `_remember` only pops goals if `sprite.state.intention == Intentions.IDLE.value`. Because the Sprite is currently in `interact`, the `SUBJECT` goal remains safely on the stack. `sprite.goal` remains `None`.
* **Transition:** Evaluates `interact`. Because `not sprite.goal` is True, it transitions to `idle`.

**Tick N+3: The Resumption**

* **Cognition (`_remember`):** Sees intention is `idle` and `goal` is `None`. Pops the `SUBJECT` goal back into active memory.
* **Transition:** Evaluates `idle`. Goal is `SUBJECT`. Transitions to `find`. The Sprite resumes the hunt on the new layer.


##### Tasks

**1. Task: ISL Matrix Patch for Prerequisites**

*Objective*: Ensure the finite automaton can route prerequisite `OBJECT` goals from the hub state.

* [x] Subtask: Add `OBJECT` category condition to the `idle -> find` transitions in `src/data/config/intentions/main.yaml`.
* [x] Subtask: Add explicit layer-alignment checks to all `functions.is_near` conditions in the ISL to prevent cross-layer proximity false positives (Bug B005).

**2. Task: CognitionMechanics Goal Swapping**

*Objective*: Implement the layer-mismatch detection and stack management securely within the engine loop.

* [x] Subtask: In `CognitionMechanics._track`, evaluate `if active_goal.layer != sprite.state.layer`. If true, push the goal to `memory.goals` and assign a target Door as a new `OBJECT` goal.
* [x] Subtask: In `CognitionMechanics._resolve`, evaluate if the active `OBJECT` goal is a Door and `sprite.state.layer == door.outlayer`. If true, set `goal = None` to trigger the `interact -> idle` ISL exit.

**3. Task: InteractionMechanics Resolution**

*Objective*: Execute the layer traversal and spatial memory acquisition.

* [x] Subtask: Ensure `InteractionMechanics` successfully updates `sprite.state.layer` when processing an `interact` intention on a Door target.
* [x] Subtask: Inject `source.state.memory.doors[target.name] = target.state.outlayer` before modifying the Sprite's position, allowing the Sprite to learn the door mapping.