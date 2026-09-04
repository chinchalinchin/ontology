#### Ontology Specification: Dialogue Loop

This specification governs the exchange of dialogue.

!!! note
    All information in this section assumes the default values for the [Intention Configuration](../appendices/01-schemas.md#configuration-intentions).

!!! note
    This specification excludes the [Player](../02-sprites.md#player), whose Intentions are handled through input polling and device mapping.

##### Step: Prologue

When a Sprite is in the `idle` Intention, `CognitionMechanics._ideate` evaluates immediate psychological overrides. If a Sprite has a non-null `state.psyche.dialogue`, it queries `board.characters()` for a valid target within `state.mutators.parameters.vision.radius`. If found, a new `GoalCategories.SUBJECT` goal is assigned. In addition, the `sprite.memory.sprites` dictionary is updated with the location of Sprite.

##### Step: Entrypoint

**Idle -> Find**

- `sprite.goal`
- `sprite.goal.category == constants.Goal.SUBJECT.value`
- `sprite.psyche.dialogue`

##### Step: Interpoints

**Find -> Speak**

- `functions.is_near(sprites.get(sprite.goal.name).position, sprite.position, sprite.mutators.parameters.vision.radius)`

##### Step: Exitpoint

**Speak -> Idle**

- `not sprite.psyche.dialogue`
- `not sprite.psyche.expression`

**Speak -> Idle**

- `sprite.goal.name == constants.Player.value`

##### Workflow: Speak Intention

A Sprite processing a `speak` Intention undergoes a strict lifecycle distributed across the Engine's Mechanics to ensure data integrity and visual consistency:

1. **Execution (`SocialMechanics`)**: Upon entering `speak`, the mechanic transfers the source Sprite's `state.psyche.dialogue` key into the `state.memory.rumors` list of the target Sprite. 
2. **Anchoring (`SocialMechanics`)**: It immediately injects an `AttachmentState` into `state.psyche.expression` configured with a Time-To-Live (TTL). The Sprite's `state.velocity` stops receiving updates from `character.impulse`, allowing friction to bring it to a halt.
3. **Decay (`SocialMechanics`)**: For each subsequent game tick, the TTL is decremented. The `state.psyche.dialogue` and `state.psyche.expression` variables are *only* nulled once the TTL reaches zero. 
4. **Resolution (`CognitionMechanics`)**: On the tick following the TTL expiration, `CognitionMechanics` evaluates the Goal. Because `goal.category == Goals.SUBJECT` and `not sprite.psyche.dialogue` evaluates to `True`, the interaction is marked satisfied. `CognitionMechanics` sets `sprite.state.goal = None` and pops the original overarching goal from `memory.goals` back into `sprite.state.goal`.
5. **Transition (`TransitionMechanics`)**: With `psyche.dialogue` empty, the ISL conditions for `speak` fail. The Sprite natively transits out of `speak` directly back into the `idle` hub. On the next tick, `idle` will evaluate the restored goal and dispatch the Sprite accordingly.