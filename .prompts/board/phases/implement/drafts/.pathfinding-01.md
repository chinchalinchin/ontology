#### Refactor: Phase 07.03 - Pathfinding & Waypoints

**Goals** CognitionMechanics is becoming very complex. Find ways to abstract and modularize the complexity to make it more manageable.

**Overview**

Decouple spatial navigation from logical intent by introducing a Pathfinding system. The `memory.goals` call stack is retained for hierarchical goal management. `CognitionMechanics` manages the `Goal` state, while a new `PathfindingMechanics` translates the active `Goal` into an immediate spatial `Waypoint`. The ISL and `MotionMechanics` operate exclusively against this `Waypoint`.

**Critiques** This Phase as written is far too ambiguous and ill-defined. Flesh out what Pathfinding needs to do.

##### Goal: Data Model Update

Introduce a `Waypoint` data model to `SpriteState` to separate the physical pathing target from the logical intent. `memory.goals` is untouched.

```python
@dataclass(slots=True)
class Waypoint:
    position: Position
    layer: str
    interaction: Optional[str] = None # Name of the target Asset (e.g., 'door-shadow')

```

##### Goal: Pathfinder System

Introduce `PathfindingMechanics` running after `CognitionMechanics` and before `TransitionMechanics`. It resolves `sprite.state.goal` into a `sprite.state.waypoint`.

```python
# Pseudo-code for PathfindingMechanics.update
if sprite.state.goal:
    # If the goal is a Door/Chest, mark it as the interaction target
    interaction_target = sprite.state.goal.name if sprite.state.goal.category == constants.Goals.OBJECT.value else None
    
    sprite.state.waypoint = Waypoint(
        position=sprite.state.goal.position, 
        layer=sprite.state.layer,
        interaction=interaction_target
    )
else:
    sprite.state.waypoint = None

```

##### Goal: ISL and Motion Updates

`MotionMechanics` and the ISL Transition Matrix are updated to target `waypoint` instead of `goal`. The `find` $\to$ `interact` transition triggers when a `Waypoint` has an `interaction` target and the Sprite overlaps it.

##### Tasks

**1. Task: State Model Updates**

*Objective*: Restructure `SpriteState` to support decoupled waypoints without altering existing memory structures.

* [ ] Subtask: Define `Waypoint` dataclass in `app.models.state.sprites`.
* [ ] Subtask: Add `waypoint: Optional[Waypoint] = None` to `SpriteState`.

**2. Task: PathfindingMechanics Implementation**

*Objective*: Create the dedicated navigation layer to bridge Cognition and Motion.

* [ ] Subtask: Create `PathfindingMechanics` in `app.game.logic.mechanics.spatial`.
* [ ] Subtask: Implement `update` to map `sprite.state.goal` to `sprite.state.waypoint`, setting `waypoint.interaction` if the goal category dictates an interaction.
* [ ] Subtask: Register `PathfindingMechanics` in `/src/data/config/mechanics/main.yaml` directly after `cognition`.

**3. Task: Motion and Transition Pipeline Updates**

*Objective*: Align physics and ISL conditions with the new `Waypoint` model.

* [ ] Subtask: Update `MotionMechanics` (specifically `motive.py`) to calculate impulse vectors towards `sprite.state.waypoint.position` rather than `sprite.state.goal.position`.
* [ ] Subtask: Rewrite `src/data/config/intentions/main.yaml` ISL conditions. Replace `functions.is_near(sprite.position, sprite.goal.position)` with `functions.is_near(sprite.position, sprite.waypoint.position)`.
* [ ] Subtask: Update ISL `find -> interact` transition condition to evaluate `- sprite.waypoint.interaction` and `- functions.is_near(...)` relative to the waypoint.