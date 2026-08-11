# Ontology: Intentions & Goals

* Location: `/src/data/intentions/main.yaml`

*Intentions* and *Goals* are an internal data structure that governs a Sprite's core logic. All Sprite Assets, when deployed on a Board, are given, along with an Animation state, an Intention state and Goal state that is updated by the gameplay loop. Intentions represent a node in the Sprite "finite automaton", the Intention Transition Matrix. They are used to calculate the (Action, Direction) dimensions of a Sprite Animations state. Goals represent the focus of the Sprite's logic, e.g. a position to move to, a chest to open, etc.

Both Sprites and Players utilize the interface of Intention and Goals to communicate state updates. The key difference is how Intentions and Goals are generated. In the case of the Player, they are mapped from polling the input codes of a Device. For a non-playable Sprite, they are calculated using the [Intention Transition Matrix]().

## AnimationMap

A Sprite's State is mapped onto an (Action, Direction) through an AnimationMap. This component of the Application statically ingests a Sprite State, applies formulas and returns the mapped tupel.

**Player Device**

Player Device mappings are applied to convert Device input to Intention and Goals, prior to the mapping of an Intention onto Animation (Action, Direction)-tuple. 

### Actions

Sprite Animation Actions is as a function of Sprite Intention state and Equipment state

    f(Intention, Equipment) = Action

**Formulae**

- `if intention == attack: action = equipment.animation.action`

### Directions

Sprite Animation Direction is a function of Sprite Position state and Goal state,

    f(Position, Goal) = Direction

**Player Mappings**

- `if input.scancode == rightarrow: goal.position.x += speed`
- `if input.scancode == leftarrow: goal.position.x -= speed`
- `if input.scancode == uparrow: goal.position.y -= speed`
- `if input.scancode == downarrow: goal.position.y += speed`

**Formulae**

Let `dx = position.x - goal.position.x, dy = position.y - goal.position.y`.

- `if dy > dx, delta_y > -dx: direction = down`
- `if dy < dx, delta_y > -dx: direction = right`
- `if dy < dx, delta_y < -dx: direction = up`
- `if dy > dx, delta_y > -dx: direction = left`

### Dialoge Resolution

**Formulae**

- `if intention.disposition == communicate and psyche.communication: popup = psyche.communcation`


## Dimensions

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

| Start State | Reachable Sprite States | Player State| 
| - | - | - |
| `attack` | `attack`, `hunt`, `loot` |
| `attract` | `barter`, `speak` |
| `build` |  - |
| `escape` | - | 
| `find` | - |
| `sprint` | - | 
| `follow` | - |  

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


## Goal

*Goals* are provide the seed (or energy) for transitions through Dispositions and the application of Motivations to modulate said transitions. A Goal is a Sprite's *modus operandi*, the abstract thing it pursues over the course of the game loop. A Sprite's transitions through Dispositions is *in order* to achieve a Goal.

- `name`: Unique Identifier of the Goal.
- `category`: Category of the Goal. (`sprite`, `asset`, `position`, `loot`, `wealth`)
- `intention`:
    - `extension`: Extension to be applied when Goal achieved .
    - `action`: Action to be applied when Goal achieved.

When a Sprite has Goal, it will seek out (path-find) its way to the AssetName, provided the AssetName is within `mutators.parameters.vision.radius`.

The `category` of a Goal affects the type of identifier given in `name`. 

- `category == sprite`: The Goal is a Sprite Asset, i.e. the Sprite is trying to find another Sprite. The `name` will be a Sprite `name`.
- `category == asset`: The Goal is a non-Sprite Asset, i.e. the Sprite is trying to find an ingame Object. The `name` will be the Asset `name`.
- `category == loot`: The Goal is Loot, i.e. the Sprite is seeking to acquire Loot. The `name` will be an Inventory key. 
- `category == wealth`: The Goal is Money, i.e. the Sprite is seeking to increase its Wallet. The `name` will be an Inventory key. The key will be of the value with the maximum value in the Sprite's Prices, e.g. the loot with the highest Price.
- `category == position`: The Goal is Position, i.e. the Sprite is trying to find a Position on the Board. The `name` will be ... (TODO: PROPERTY MECHANICS).
