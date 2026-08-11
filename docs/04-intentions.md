# Ontology: Intentions

* Location: `/src/data/intentions/main.yaml`

*Intentions* are an internal State data structure that governs a Sprite's core logic. All Sprite Assets, when deployed on a Board, are given, along with an Animation state, an Intention state that is updated by the gameplay loop. Intention coordinates represent a node in the Sprite "finite automaton", the Disposition Transition Matrix.

The complete Intention State for a Sprite is given by the tuple,

    (Disposition, Expression, Extension, Motivation, Communication)

The dimensions of Intention are discussed in [more detail below](#dimensions).

## Animation Resolution

Each component of a Sprite's Animation is resolved through a different relation.

### Action Resolution

Sprite Animation Actions can be viewed as a function of Sprite Intention state and Equipment state

    f(Intention, Equipment) = Action

**Formulas**

- `if intention.disposition == attack: action = equipment.animation.action`

### Direction Resolution

TODO

### Frame Resolution

Frame resolution is covered in more detail in the [Asset documentation](./01-assets.md). Frame resolution is handled entirely by the Frame component schema injected into the Asset during initialization. The schema is dependent on Asset Instance type and current Asset Action.

    f(Instance, Action) = Frame

## Dimensions

!!! note
    Player Intentions do not contain the Motivation or Communication fields.

### Extension

A Extension is a pseudo-state that does not factor into the Asset frame key calculation directly. It may indirectly alter the Sprite state changes or other properties of the Sprites, e.g. entering into the `sprint` Extension state increases the velocity of the `(walk, *)` states, but does not factor into the animation speed or the frame indexing scheme. Similarly, entering into the `interact` Extension state does not alter the Sprite's current animation in any way, but instead allows, for example, the Sprite to open a Chest or Door.

The default Extension states are enumerated below,

- `interact`: Sprites enter into this Extension to interact with Objects.
- `speak`: Sprites enter into this Extension to draw their Communication on a Dialogue window.
- `sprint`: Sprites enter into this Extension to increase their velocity.
- `trade`: Sprites enter into this Extension to exchange Money for Inventory with another Sprite.
- `build`: Sprites enter into this Extension to place Crafts on the Board.
- `mine`: Sprites enter into this Extension to convert Resources into Inventory. **NOTE**: This Extension is complicated by the polymorphism that exists in the LPC spec between the Action of Thrust (i.e. attacking) and using a Shovel or Pickaxe, i.e. the Spear Weapon and the Shovel/Pickaxe Tool both use the same underlying animation rows.

### Disposition
    
!!! important
    The Player state does not observe the Disposition Transition matrix; the Player state is managed by polling the user's input and mapping input to intention. See [Player documentation](./03-player.md) for more information on the Player.

A Disposition determines which Intention states are currently reachable for a Sprite. In other words, a Sprite's *Disposition* is an element in its Disposition Transition matrix, covered below. Dispositions are enumerated below, along with their reachable states.

1. `attack`
    - Reachable Dispostions: `attack, hunt, loot`
    - Reachable Extensions:
2. `attract`
    - Reachable Dispostions: `barter, communicate`
    - Reachable Extensions: `interact`
3. `barter`
    - Reachable Dispostions:
    - Reachable Extensions: `trade`
4. `communicate`
    - Reachable Dispostions:
    - Reachable Extensions: `trade`, `speak`
5. `construct`
    - Reachable Dispositions: 
    - Reachable Extension: `build`, `mine`
6. `engage`
    - Reachable Dispostions: 
    - Reachable Extensions: `interact`
7. `escape`
    - Reachable Dispostions: 
    - Reachable Extensions: `sprint`
8. `find`
    - Reachable Dispostions: 
    - Reachable Extensions: `sprint`
9. `follow`
    - Reachable Dispostions: 
    - Reachable Extensions: `sprint`
10. `hunt`:
    - Reachable Dispositions:
    - Reachable Extensions:
11. `idle`
    - Reachable Dispostions: 
    - Reachable Extensions:
12. `mock`
    - Reachable Dispostions: `threaten`
    - Reachable Extensions: `speak`
13. `recoil`
    - Reachable Dispostions: 
    - Reachable Extensions: 
14. `return`
    - Reachable Dispostions: `find`
    - Reachable Extensions:
15. `scavenge` 
    - Reachable Dispostions:
    - Reachable Extensions:
16. `threaten`
    - Reachable Dispostions: `attack`
    - Reachable Extensions: 
17. `wander`
    - Reachable Dispostions: `find`, `return`, `idle`
    - Reachable Extensions:

**Default Disposition Transition Matrix**

Provided below is the Disposition Transition Matrix bundled with the application by default,

```yaml
--8<-- "docs/.static/yaml/examples/default-disposition-matrix.yaml"
```

**Disposition Scripting Language (DSL)**

The `condition` for each Disposition transition is given in a simple truth-valued language that admits the logical operations and terms,

Operations:

- `==`: equivalence
- `!=`: non-equivalence
- `not`: negation
- `or`: disjunction
- `and`: conjunction

Terms:

- `None`: null value
- `str`: constants
- `sprite.<state>`: self State variable
- `sprites[<sprite-name>].<state>`: other Sprites state variable

For example, in the default Disposition Transition matrix given above, the transition from `attack` to `hunt` is conditional on the following,

```yaml
- not sprite.goal
- sprite.memory.goal.category == 'sprite'
```

`sprite` is a reference to the Sprite's state which is currently processing the given Disposition. Thus, the Sprite's Disposition state will transition to `hunt` if the Sprite currently does not have a target, but remembers having a target of category `sprite`.

!!! note
    The expression `not sprite.goal` is a *truthy* expression, i.e. it is to be interpretted as an existential claim. In other words, this expression evaluates to `true` if `sprite.goal` does not exist. If the expression involves a List, e.g. `sprite.memory.communications`, this expression evaluates to `true` in the event it has more than 0 entries.

In another example, the transition from `attack` to `loot` in the default Disposition Transition matrix is given by,

```yaml
- sprites[sprite.target.name].mutators.triggers.dead
```

`sprites` is a reference to a dictionary of all ingame Sprites states keyed by their identifying and unique `name`, which provides access to their state attributes.

Notice in the example there is a self-entrant transition. A Sprite with an `attack` Disposition can re-enter the `attack` Disposition conditional on the Sprite still having a target,

```yaml 
- sprite.goal.target.category == 'sprite'
```

!!! important
    The conditions for a Disposition transition are evaluated in the order they specified! In the given example, if `sprite.goal.category == 'sprite'`, none of the other conditions for Disposition transitions are evaluated and the Disposition transitions back into `attack`.

Disposition conditions are converted into lambda functions by the application and then evaluated at runtime.

### Motivation

Motivations are long-term variables that modulate the Disposition Transition matrix.

The default Motivations are enumerated below,

- `conquest`
- `profit`
- `survival`
- `love`
- `revenge`
- `rebellion`
- `safety`

### Communication

The Communication dimension of an Intention can be thought of as the short-term memory or a buffer for Dialogue the Sprite is about to display. It holds the Communication key for the current Plot state that will be rendered if the Sprite enters into the `speak` Extension.

### Expression

The Expression dimension alter the Sprite's appearnce by appending a Cursor Expression to the upper right corner of the Sprite's boundaries. Expressions can be visualized as speech bubbles containing icons that express the Sprite's internal state. 

The default Expressions are enumerated below,

- `agreement`
- `anger`
- `confusion`
- `curiosity`
- `disagreement`
- `loquacity`
- `surprise`
- `tired`
