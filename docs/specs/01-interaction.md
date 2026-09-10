#### Ontology Specification: Interaction Loop

This specification governs the exchange of dialogue.

!!! note
    All information in this section assumes the default values for the [Intention Configuration](../appendices/01-schemas.md#configuration-intentions).

!!! note
    This specification excludes the [Player](../02-sprites.md#player), whose Intentions are handled through input polling and device mapping.

##### Prologue

TODO

##### Step: Entrypoints

**idle:find**

- `sprite.goal`
- `sprite.goal.category == constants.Goals.OBJECT.value`
- `sprite.layer == sprite.goal.layer`
- `not functions.is_near(sprite.position, sprite.goal.position, sprite.mutators.parameters.action.radius)`

##### Step: Interpoints

**find:interact**

- `functions.is_near(sprite.position, sprite.goal.position, sprite.mutators.parameters.action.radius)`

##### Step: Exitpoints

**interact:idle**

- `not sprite.goal`

##### Workflow: Interact Intention

TODO