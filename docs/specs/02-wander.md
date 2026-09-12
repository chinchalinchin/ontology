#### Ontology Specification: Wander Loop

This specification governs autonomous exploratory navigation and target reacquisition.

!!! note
    All information in this section assumes the default values for the [Intention Configuration](../appendices/01-schemas.md#configuration-intentions).

!!! note
    This specification excludes the [Player](../02-sprites.md#player), whose Intentions are handled through input polling and device mapping.

##### Architectural Note: Loop Taxonomy & Intentional Subsumption

There is an inherent ambiguity in designating an automaton cycle an "Intention Loop":

1. **Terminal Action Loops (e.g., Dialogue, Combat)**: Named after the discrete external emission or physical world mutation they produce (`speak:idle`, `attack:idle`, `interact:idle`). These are closed, finite cycles.
2. **Residence Search Loops (e.g., Wander)**: Named after an extended behavioral residence state. The Wander Loop produces no discrete terminal world event; it functions as an open-ended exploratory engine.

The Wander Loop operates as a **subsumptive secondary loop**. It is traversed to resolve situational gaps in primary loops—specifically when an entity loses direct line of sight to a target or has no immediate ideated objective. Rather than freezing, the entity enters an autonomous spatial walk, preserving suspended primary goals in `memory.goals` until sensory predicates permit a re-entry transition into a terminal action loop.


```
    [Primary Loop Suspended]
             │
             ▼
     ┌───────────────────┐
┌───►│  wander (Random)  │◄───┐
│    └─────────┬─────────┘    │
│              │              │
│ (No Vision)  │ (Target Seen)│ (Waypoint Step)
│              ▼              │
│     [any_memories_visible]  │
│              │              │
│              ▼              │
└───────  find / hunt ────────┘
```

##### Prologue

**Subsumption**

Before entering the Wander Loop from an interrupted action loop (`find` or `hunt`), `CognitionMechanics._resolve` ensures the unresolved overarching goal is saved to `sprite.state.memory.goals`. This guarantees the target identity, category, and last-known coordinate remain queryable throughout exploratory navigation.

**Randomization**

When an entity is in `wander` with no active goal (`not sprite.state.goal`) and no pending waypoints in memory, `CognitionMechanics._project` samples a coordinate within the bounding square \([-\text{radius}_{\text{vision}}, \text{radius}_{\text{vision}}]\) relative to the Sprite's position. This coordinate is clamped against the physical boundaries of the active board layer:

$$x_{\text{dest}} = \max\left(0, \min(x_{\text{pos}} + \Delta x, W_{\text{layer}} - W_{\text{sprite}})\right)$$

$$y_{\text{dest}} = \max\left(0, \min(y_{\text{pos}} + \Delta y, L_{\text{layer}} - L_{\text{sprite}})\right)$$

The resulting destination is committed as `Goal(name="wander", category=Goals.POSITION.value)`.

##### Step: Entrypoint

**idle:wander**

* `not sprite.goal`

!!! note "Autonomous Idle Exit"
    Fires when the Sprite has exhausted all goals and has no immediate ideations.

**idle:wander**

* `sprite.goal`
* `sprite.goal.category == constants.Goals.POSITION.value`
* `sprite.layer == sprite.goal.layer`

!!! note "Waypoint / Position Consumption"
    Fires when an RRT waypoint (`path-*`) or a persistent positional target is loaded as the active goal.

##### Step: Interpoints

**wander:idle**

* `not sprite.goal`

!!! note "Waypoint Step Resolution"
    When an RRT waypoint (`path-*`) is cleared in `_resolve()`, the goal is nulled. The Sprite drops to `idle` for a single tick, permitting `CognitionMechanics._remember()` to pop the next sequential waypoint off `memory.goals`.

##### Step: Exitpoints

**wander:find**

* `sprite.goal`
* `functions.any_memories_visible(sprite, sprites, constants.Goals.SUBJECT.value)`

!!! note "Passive Target Reacquisition"
    Fires when a remembered dialogue partner or interactive entity re-enters the active vision radius on the same layer.

**wander:hunt**

* `sprite.goal`
* `functions.any_memories_visible(sprite, sprites, constants.Goals.TARGET.value)`

!!! note "Hostile Target Reacquisition"
    Fires when a remembered hostile target re-enters the active vision radius on the same layer.

**wander:idle**

* `sprite.goal`
* `sprite.goal.category != constants.Goals.POSITION.value`

!!! note "External Goal Preemption"
Fires if a mechanic, plot trigger, or mutator injects a non-positional goal directly into the active state.

##### Workflow: Wander Intention

Exploratory navigation adheres to the following mechanical lifecycle:

1. **Resolution (`CognitionMechanics._resolve`)**:
    * For an active wander goal (`name == "wander"`), `complete()` evaluates Euclidean proximity against `parameters.action.radius`. If within radius, `_resolve()` logs the resolution and sets `sprite.state.goal = None`.
    * For an RRT waypoint (`name.startswith("path-")`), reaching the coordinate sets `sprite.state.goal = None`, leaving subsequent waypoints intact in `memory.goals`.
2. **Scanning (`CognitionMechanics._scan`)**:
    * Entities visible within `parameters.vision.radius` update `memory.sprites`.
    * Any matching key in `memory.goals` updates its internal `position` and `layer` attributes to match the live entity position.
3. **Recall (`CognitionMechanics._remember`)**:
    * If `sprite.state.goal` is `None` and the Sprite is in `idle`, the next goal is popped from `memory.goals` (FIFO).
    * If a candidate goal in `memory.goals` has already been reached without sight (`nearby and not vision`), it remains dormant in memory until `any_memories_visible` detects it.
4. **Projection (`CognitionMechanics._project`)**:
    * If the Sprite remains in `wander` with `not sprite.state.goal`, no pending `path-*` waypoints, and no actionable memories waiting for recall, `_project()` samples and clamps a new random destination, setting `goal = Goal(name="wander", category=POSITION)`.
5. **Transition (`TransitionMechanics`)**:
    * The ISL evaluator parses `wander`. If `any_memories_visible` evaluates to `True`, the automaton executes `wander -> find` or `wander -> hunt`.
    * If `goal` is `None` (a waypoint finished), it transitions `wander -> idle` so `_remember()` can pop the next step on the subsequent tick.
    * If a new `wander` goal was generated by `_project()`, no transition conditions are met; the Sprite remains in `wander`.
6. **Kinematics (`MotionMechanics`)**:
    * `motive.update()` queries `sprite.state.goal.position` and applies acceleration vectors via `physics.dynamics()`, clamping speed to `character.speed`.
