#### Ontology Specification: Dialogue Loop

This specification governs the exchange of dialogue between Sprites, and between Sprites and the Player.

!!! note
    All information in this section assumes the default values for the [Intention Configuration](../appendices/01-schemas.md#configuration-intentions).

!!! note
    This specification excludes the [Player](../02-sprites.md#player), whose Intentions are handled through input polling and device mapping.

##### Prologue

**Ideation**

When a Sprite is in `idle` without an active goal, `CognitionMechanics._ideate` evaluates psychological states. If a Sprite has a non-null `state.psyche.dialogue`, it scans `board.characters()` for a valid target within `state.mutators.parameters.vision.radius`. If found on the same layer, a new `Goal(category=Goals.SUBJECT.value)` is assigned, and `sprite.state.memory.sprites` caches the target's current coordinates.

**Motivation**

TODO

##### Step: Entrypoint

**idle:find**

- `sprite.goal`
- `sprite.goal.category == constants.Goals.SUBJECT.value`
- `sprite.layer == sprite.goal.layer`
- `sprites.get(sprite.goal.name)`
- `not functions.is_near(sprite.position, sprites.get(sprite.goal.name).position, sprite.mutators.parameters.action.radius)`

##### Step: Interpoints

**find:speak**

- `sprite.goal`
- `sprite.psyche.dialogue`
- `sprite.goal.category == constants.Goals.SUBJECT.value`
- `sprite.layer == sprite.goal.layer`
- `sprites.get(sprite.goal.name)`
- `sprite.memory.relationships.get(sprite.goal.name)`
- `sprite.memory.relationships[sprite.goal.name] in [ constants.Relationships.FRIEND.value, constants.Relationships.FAMILY.value ]`
- `functions.is_near(sprite.position, sprites.get(sprite.goal.name).position, sprite.mutators.parameters.action.radius)`

**speak:follow**

- `sprite.goal.category == constants.Goals.SUBJECT.value`
- `not functions.is_near(sprite.position, sprite.goal.position, sprite.mutators.parameters.action.radius)`

**follow:speak**

- `sprite.goal.category == constants.Goals.SUBJECT.value`
- `functions.is_near(sprite.position, sprite.goal.position, sprite.mutators.parameters.action.radius)`

##### Step: Divergence (Target Lost to Search)

If a target moves outside `state.mutators.parameters.vision.radius` while the Sprite is traversing toward it, the Dialogue Loop diverts into the [Wander Loop](./02-wander.md):

1. **Abandonment (`CognitionMechanics._resolve`)**: The Sprite reaches the last known coordinates without visual contact (`nearby and not vision`). `_resolve()` shelves the `SUBJECT` goal back into `sprite.state.memory.goals`, triggers a `CONFUSION` expression, and clears `sprite.state.goal = None`.
2. **Divergence (`TransitionMechanics`)**: With `not sprite.goal`, the Sprite transitions `find -> idle -> wander`.
3. **Reacquisition (`TransitionMechanics`)**: While in `wander`, if `functions.any_memories_visible` detects the remembered `SUBJECT` within `vision.radius`, the automaton triggers `wander -> find`.
4. **Resumption (`CognitionMechanics._remember`)**: `_remember()` restores the `SUBJECT` goal from `memory.goals`, resuming direct tracking.

##### Step: Exitpoint

**speak:idle**

- `not sprite.psyche.expression`

!!! note "Sprite-to-Sprite Branch"
    Applies when communicating with NPC Sprites. Control returns to `idle` after the dialogue expression TTL expires.

**speak:idle**

- `sprite.goal.name == constants.RequiredAssets.PLAYER.value`

!!! note "Player-to-Sprite Branch"
    Applies when communicating with the Player. The intention releases immediately to `idle` upon interaction.

##### Workflow: Speak Intention

A Sprite processing a `speak` Intention executes across distributed Engine Mechanics:

1. **Execution (`SocialMechanics`)**: Upon entering `speak`, the mechanic transfers the source Sprite's `state.psyche.dialogue` key into the `state.memory.rumors` list of the target Sprite.
2. **Anchoring (`SocialMechanics`)**: An `AttachmentState` is injected into `state.psyche.expression` configured with a Time-To-Live (TTL). `MotionMechanics` drops impulse, allowing friction to bring the Sprite to a halt.
3. **Decay (`SocialMechanics`)**: Every engine tick decrements the TTL. `state.psyche.dialogue` and `state.psyche.expression` are nulled only when the TTL reaches zero.
4. **Resolution (`CognitionMechanics`)**: On the tick following TTL expiration, `_resolve()` evaluates the goal. Because `goal.category == Goals.SUBJECT` and `not sprite.psyche.dialogue` evaluates to `True`, the goal is cleared (`sprite.state.goal = None`).
5. **Transition (`TransitionMechanics`)**: With `not sprite.goal`, the Sprite transitions back to `idle`.