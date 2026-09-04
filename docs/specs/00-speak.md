#### Ontology Specification: Speak Intention

The `speak` Intention governs the exchange of Dialogue. 

!!! note
    All information in this section assumes the default values for the [Intention Configuration](../appendices/01-schemas.md#configuration-intentions).

!!! note
    This specification excludes the [Player](../02-sprites.md#player), whose Intentions are handled through input polling and device mapping.

##### Entrypoints

The entrypoints into the `speak` Intention are enumerated below.

**Find**

- `sprite.goal`
- `sprite.goal.category == GoalCategories.SPRITE.value`
- `functions.is_near(sprites.get(sprite.goal.name).position, sprite.position, sprite.mutators.parameters.vision.radius)`
- `sprite.psyche.dialogue`
- `sprite.memory.relationships[sprite.goal.name] in [Relationships.FRIEND.value, Relationships.FAMILY.value]`

##### Exitpoints

**Idle**

- `sprite.psyche.expression`
- `sprite.goal.name == AssetInstances.PLAYERS.name`

**Return**

- `not sprite.psyche.dialogue`
- `not sprite.psyche.expression`

##### Workflow

A source Sprite that has entered the `speak` Intention undergoes the following transformation,

1. It immediately changes it `state.psyche.expression` to `LOQUACITY`. This triggers an [Expression Cursor](../01-assets.md#expressions) to be appended to the right corner of the Sprite frame. The Expression `state.frame` is set equal to `state.psyche.expression` from the source Spirte.
2. Its `state.velocity` stops receiving updates from its `state.character.impulse`, allowing friction to bring it to a halt. 

At this point, a decision tree is applied to determine if the Sprite will transit into another Intention. If `state.goal.name == 'player'`, the Sprite will transit into the `idle` Intention when the [TransitionMechanics](../05-mechanics.md#intentional) are applied the next game tick.

Otherwise, the Sprite stays in the `speak` Intention for the next game tick. When this tick is applied, the following two events occur:

1. The `state.psyche.dialogue` key of the source Sprite is transferred into the `state.memory.rumors` list of its target Sprite. 
2. The `state.psyche.dialogue` key and the `state.psyche.expression` key of the source Sprite are set to null.
3. The Sprite's `goal` is replaced by `memory.goal`.

At this point, the conditions for the `return` Intention Transition are satisfied and the Sprite transits into `return`.