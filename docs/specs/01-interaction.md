#### Ontology Specification: Interaction Loop

This specification governs how Sprites traverse the environment and manipulate Objects (such as Doors and Chests).

!!! note
    All information in this section assumes the default values for the [Intention Configuration](../appendices/01-schemas.md#configuration-intentions).

!!! note
    This specification excludes the [Player](../02-sprites.md#player), whose Intentions are handled through input polling and device mapping.

##### Prologue

The `interact` loop serves a dual purpose: interacting with same-layer Objects (like Chests) and serving as the engine's primary traversal mechanism for cross-layer navigation. 

When CognitionMechanics detects that a Sprite's current Goal resides on a different layer, it performs a **Subsumption**. The Sprite pushes its current goal into `state.memory.goals` and spontaneously injects a prerequisite `OBJECT` goal targeting the nearest available Door. The Interaction Loop is then executed to successfully cross the dimension.

##### Step: Entrypoints

**idle:find**

- `sprite.goal`
- `sprite.goal.category == constants.Goals.OBJECT.value`
- `sprite.layer == sprite.goal.layer`
- `not functions.is_near(sprite.position, sprite.goal.position, sprite.mutators.parameters.action.radius)`

##### Step: Interpoints

**find:interact**

- `sprite.goal`
- `sprite.goal.category == constants.Goals.OBJECT.value`
- `sprite.layer == sprite.goal.layer`
- `functions.is_near(sprite.position, sprite.goal.position, sprite.mutators.parameters.action.radius)`

##### Step: Exitpoints

**interact:idle**

- `not sprite.goal`

##### Workflow: Interact Intention (Door Branch)

A Sprite processing an `interact` Intention targeting a Door undergoes a strict sequence distributed across the engine ticks to ensure spatial continuity and goal integrity:

1. **Approach (`CognitionMechanics` & `MotionMechanics`)**: The Sprite, while in the `find` intention, accelerates toward the Door until its origin is within `mutators.parameters.action.radius` of the Door's origin. 
2. **Transition (`TransitionMechanics`)**: The ISL condition `is_near` evaluates to True. The Sprite transitions from `find` to `interact`. Because `interact` is a static intention, the Sprite's velocity drops to `0.0`.
3. **Execution (`InteractionMechanics`)**: The mechanic evaluates the intersection of the Sprite and the target Door using their exact Axis-Aligned Bounding Boxes (AABBs). Upon a successful collision, it records the Door's routing in `sprite.memory.doors`, alters the Sprite's `state.position`, and calls `board.relayer` to shift the Sprite to the destination layer. 
4. **Resolution (`CognitionMechanics`)**: On the subsequent engine tick, `_resolve` evaluates the Sprite's current layer against its `OBJECT` goal's layer. Because the Sprite has successfully teleported, `sprite.state.layer != goal.layer` evaluates to True. The `OBJECT` goal is satisfied and cleared (`sprite.state.goal = None`).
5. **Exit (`TransitionMechanics`)**: With `sprite.goal` safely nulled out, the ISL conditions to exit `interact` are met. The Sprite transitions directly back into the `idle` hub.
6. **Recall (`CognitionMechanics`)**: On the next tick, while the Sprite is safely resting in `idle`, `_remember` runs. It pops the original, overarching goal off the `memory.goals` stack and reinstates it as the active goal, allowing the Sprite to resume its original pursuit on the new layer.