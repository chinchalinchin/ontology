# Ontology: Intentions & Goals

Intentions and Goals are an internal data structure that governs a Sprite's core logic. All Sprite Assets, when deployed on a Board, are given, along with an Animation state, an Intention state and Goal state that is updated by the gameplay loop. Intentions represent a node in the Sprite "finite automaton", the Intention Transition Matrix. They are used to calculate the (Action, Direction) dimensions of a Sprite Animations state. Goals represent the focus of the Sprite's logic, e.g. a position to move to, a chest to open, etc.

Both Sprites and Players utilize the interface of Intention and Goals to communicate state updates. The key difference is how Intentions and Goals are generated. In the case of the Player, they are mapped from polling the input codes of a Device. For a non-playable Sprite, they are calculated using the [Intention Transition Matrix](#transition-matrix).

## Intention

A Intention is a "pseudo-state" that factors into the Asset Animation calculations indirectly; It may be thought of as a "hidden" state. An Animation is a "projection" of a Sprite's Intention into the (Action, Direction)-space. 

For Sprites, Intention is an attribute that controls state transitions and action mappings. For the Player, it controls action mappings.

It may indirectly alter the Sprite state changes or other properties of the Sprites, e.g. entering into the `sprint` state increases the velocity of the `(walk, *)` states, but does not factor into the animation speed or the frame indexing scheme. Similarly, entering into the `interact` state does not alter the Sprite's current animation in any way, but instead allows, for example, the Sprite to open a Chest or Door.

### Transition Matrix
    
* Location: `/src/data/config/intentions/main.yaml`

!!! important
    The Player state does not observe the Intention Transition matrix; the Player state is managed by polling the user's input and mapping input to intention. See [Player documentation](./03-player.md) for more information on the Player.

The Intention Transition Matrix determines which Intention states are currently reachable for a Sprite from its current Intention. A brief explanation of each Intention state value is given below,

- `attack`: Apply CombatMechanics, conditional on Equipment constraint.
- `attract`: 
- `barter`: Apply CommerceMechanics for Sprites; Open a TradeWindow for Player.
- `build`: Apply IndustryMechanics for Sprites; Open a BuildWindow for Player. 
- `escape`: 
- `find`: 
- `follow`: 
- `hunt`: 
- `idle`: 
- `interact`: Used to interact with Objects.
- `mine`: Convert Resources into Inventory. 
- `return`:
- `scavenge`: 
- `speak`: Draw their Communication on a Dialogue window.
- `sprint`: Increase movement speed.
- `threaten`: 
- `wander`: 

!!! note
    `mine` is complicated by the polymorphism that exists in the LPC spec between the Action of Thrust (i.e. attacking) and using a Shovel or Pickaxe, i.e. the Spear Weapon and the Shovel/Pickaxe Tool both use the same underlying animation rows.

**Default Intention Transition Matrix**

Provided below is the Intention Transition Matrix bundled with the application by default,

| # | Starting Intention | Reachable Intentions |
| - | - | - |
| 1 | `attack` | `attack`, `hunt`, `scavenge` |
| 2 | `attract` | `attract`, `barter`, `speak` |
| 3 | `barter` | `speak`, `find`, `threaten` |
| 4 | `build` |  `barter`, `find`, `mine` |
| 5 | `escape` | `return`, `find`, `sprint` | 
| 6 | `find` | `interact`, `speak`, `barter` |
| 7 | `follow` | `find`, `sprint` |
| 8 | `hunt` | `sprint` | 
| 9 | `idle`| `return`, `wander` |
| 10 | `interact` | `barter`, `speak`, `attract` | 
| 11 | `mine` | `barter`, `scavenge` |
| 11 | `mock` | `threaten`, `escape` |
| 12 | `return` | `find`, `wander` |
| 13 | `scavenge` | `find` |
| 14 | `speak` | `barter`, `mock`, `threaten` |
| 15 | `sprint` | `escape`, `hunt` |
| 16 | `threaten` | `attack`, `mock` |
| 17 | `wander` | `idle`, `return` |

```yaml
--8<-- "docs/.static/yaml/examples/default-intention-matrix.yaml"
```

**Intentional Scripting Language (ISL)**

The `condition` for each Intention transition is given in a simple truth-valued language that admits the logical operations and terms,

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

For example, in the default Intention Transition matrix given above, the transition from `attack` to `hunt` is conditional on the following,

```yaml
- not sprite.goal
- sprite.memory.goal.category == 'sprite'
```

`sprite` is a reference to the Sprite's state which is currently having its Intention processed by the game engine. Thus, the Sprite's Intention state will transition to `hunt` if the Sprite currently does not have a Goal, but remembers having a Goal of Category `sprite`.

!!! note
    The expression `not sprite.goal` is a *truthy* expression, i.e. it is to be interpretted as an existential claim. In other words, this expression evaluates to `true` if `sprite.goal` does not exist. If the expression involves a List, e.g. `sprite.memory.communications`, this expression evaluates to `true` in the event it has more than 0 entries.

In another example, the transition from `attack` to `scavenge` in the default Intention Transition matrix is given by,

```yaml
- sprites[sprite.name].mutators.triggers.dead
```

`sprites` is a reference to a dictionary of all ingame Sprites states keyed by their identifying and unique `name`, which provides access to their state attributes.

Notice in the example there is a self-entrant transition. A Sprite with an `attack` Intention can re-enter the `attack` Intention conditional on the Sprite still having a target,

```yaml 
- sprite.goal.category == 'sprite'
```

!!! important
    The conditions for an Intention transition are evaluated in the order they specified! In the given example, if `sprite.goal.category == 'sprite'`, none of the other conditions for Intention transitions are evaluated and the Intention transitions back into `attack`.

Intention transition conditions are converted into lambda functions by the application and then evaluated at runtime.

## Goal

*Goals* provide the seed (or energy) for transitions through Intentions and the application of Motivations to modulate said transitions. A Goal is a Sprite's *modus operandi*, the abstract thing it pursues over the course of the game loop. A Sprite's transitions through Intention is *in order* to achieve a Goal.

- `name`: Unique Identifier of the Goal.
- `category`: Category of the Goal. (`sprite`, `loot`, `wealth`, `property`)
- `position`: Last-known position of the Goal. When the Goal is within the `mutators.vision.radius`, this position is updated every game loop. Once the Goal exits the Sprites `mutators.vision.radius`, it becomes a static value that freezes on the last known Position of its Goal.

### Goal Category

When a Sprite has Goal, it will seek out (path-find) its way to `name`. The `category` of a Goal affects the type of identifier given in `name`. 

- `category == asset`: The Goal is a Sprite Asset, i.e. the Sprite is trying to find another Sprite. The `name` will be the Asset `name`.
- `category == loot`: The Goal is Loot, i.e. the Sprite is seeking to acquire Loot. The `name` will be an Inventory key. 
- `category == wealth`: The Goal is Money, i.e. the Sprite is seeking to increase its Wallet. The `name` will be an Inventory key. The key will be of the value with the maximum value in the Sprite's Prices, e.g. the loot with the highest Price.
- `category == property`: The goal is Property, i.e. the Sprite is seeking the location of Property. The `name` will be an Asset name of an Asset that implements a `PropertyState`.

## AnimationMap

A Sprite's State is mapped onto an (Action, Direction) through an AnimationMap. This component of the Application statically ingests a Sprite State, applies formulas and returns the mapped tupel.

**Player Device**

Player Device mappings are applied to convert Device input to Intention and Goals, prior to the mapping of an Intention onto Animation (Action, Direction)-tuple. 

### Actions

Sprite Animation Actions is as a function of Sprite Intention state and Equipment state

    f(Intention, Equipment) = Action

**Formulae**

- `if state.intention == attack: state.animation.action = board.equipment[weapons][state.inventory.weapon].action`

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

- `if dy > dx, dy > -dx: direction = down`
- `if dy < dx, dy > -dx: direction = right`
- `if dy < dx, dy < -dx: direction = up`
- `if dy > dx, dy > -dx: direction = left`

## DialogueMap

TODO

**Formulae**

- `if state.intention == speak and state.psyche.communication: dialogue = state.psyche.communcation`

