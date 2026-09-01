# Ontology: Intentions & Goals

Intentions and Goals are an internal data structure that governs a Sprite's core logic. All Sprite Assets, when deployed on a Board, are given, along with an Animation state, an Intention state and Goal state that is updated by the gameplay loop. Intentions represent a node in the Sprite's "*finite automaton*", the Intention Transition Matrix. They are used to calculate the (Action, Direction) dimensions of a Sprite Animations state. Goals represent the focus of the Sprite's logic, e.g. a position to move to, a chest to open, etc.

Both Sprites and Players utilize the interface of Intention and Goals to communicate state updates. The key difference is how Intentions and Goals are generated. In the case of the Player, they are mapped from polling the input codes of a Device. For a non-playable Sprite, they are calculated using the [Intention Transition Matrix](#transition-matrix).

## Intention

A Intention is a [Sprite](./02-sprites.md) field that factors into the Asset Animation calculations indirectly; It may be thought of as a "hidden" state. An Animation is a "projection" of a Sprite's Intention into the (Action, Direction)-space. 

For Sprites, Intention is an attribute that controls state transitions and action mappings. For the Player, it controls action mappings.

It may indirectly alter the Sprite state changes or other properties of the Sprites, e.g. entering into the `sprint` state increases the velocity of the `(walk, *)` states, but does not factor into the animation speed or the frame indexing scheme. Similarly, entering into the `interact` state does not alter the Sprite's current animation in any way, but instead allows, for example, the Sprite to open a Chest or Door.

A brief explanation of each Intention state value is given below,

- `attack`: Initiate an Attack Animation..
    - *Sprite*: Apply CombatMechanics, conditional on Equipment constraint.
    - *Player*: Apply CombatMechanics, conditional on Equipment constraint.
- `attract`: Attract a Sprite for interaction.
    - *Sprite*:
    - *Player*: N/A
- `barter`: Exhcange Inventories.
    - *Sprite*: Apply CommerceMechanics.
    - *Player*: Open a TradeWindow with Target.
- `build`: Instantiate a Strut
    - *Sprite*: Apply IndustryMechanics for Sprites
    - *Player*: Open a BuildWindow. 
- `escape`: Move away from target.
    - *Sprite*:
    - *Player*: N/A
- `find`: Move towards target.
    - *Sprite*:
    - *Player*: N/A
- `follow`: Move towards target. (Redundant? Functionally, but separate node in tree leading to different outcomes)
    - *Sprite*: 
    - *Player*: N/A
- `hunt`: Move towards target (Redundant? Functionally, but separate node in tree leading to different outcomes and interactions.)
    - *Sprite*: 
    - *Player*: N/A
- `idle`: Do nothing.
    - *Sprite*:
    - *Player*: N/A
- `interact`: Interact with Objects.
    - *Sprite*: 
    - *Player*: 
- `mine`: Convert Resources into Inventory. 
    - *Sprite*: Apply MineMechanics, conditional on Equpiment constraints.
    - *Player*: Apply MineMechanics, conditional on Equipment constraints.
- `return`: Return to remembered locations.
    - *Sprite*: Move `sprite.state.memory.goal` to `sprite.state.goal`
    - *Player*: N/A
- `scavenge`: Collect loot.
    - *Sprite*: 
    - *Player*: 
- `speak`: Initiate dialogue.
    - *Sprite*: Apply CommerceMechanics (exchanges `prices`). Apply RumorMechanics (exchange `rumors`) 
    - *Player*: Draw the target Sprite's `state.psyche.dialogue` on a Dialogue window.
- `sprint`: Increase movement speed.
    - *Sprite*:
    - *Player*: 
- `threaten`: Pre-cursor to Attack (wiggle-room).
    - *Sprite*:
    - *Player*: N/A
- `wander`: 
    - *Sprite*:
    - *Player*: N/A

!!! note
    `mine` is complicated by the polymorphism that exists in the LPC spec between the Action of Thrust (i.e. attacking) and using a Shovel or Pickaxe, i.e. the Spear Weapon and the Shovel/Pickaxe Tool both use the same underlying animation rows. This is resolved by [Action Sets](./appendices/01-schemas.md#configuration-actions) and [AnimationMaps](./10-architecture.md#maps).

### Transition Matrix
    
* Location: `/src/data/config/intentions/main.yaml`

!!! important
    The Player state does not observe the Intention Transition matrix; the Player state is managed by polling the user's input and mapping input to intention. See [Player documentation](./02-sprites.md#player) for more information on the Player.

The Intention Transition Matrix determines which Intention states are currently reachable for a Sprite from its current Intention. The general schema for the Intention Transition Matrix is given below,

```yaml
intentions:
    <intention-key>:
        - next: <intention-key>
          conditions: 
            - <condition>
```

**Default Intention Transition Matrix**

Provided below is the Intention Transition Matrix bundled with the application by default,

```mermaid
--8<-- "static/mmd/intention-transitions.mmd"
```

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
- `sprite.<attribute>`: self State variable
- `sprites[<sprite-name>].<attribute>`: other Sprites state variable

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

Intention transition conditions are converted into lambda functions by the application and then evaluated at runtime.The application evaluates ISL conditions sequentially utilizing Python's native short-circuit logic.

To avoid AttributeError exceptions during runtime, existential checks must strictly precede attribute accesses. Consider,

```yaml
# CORRECT CONFIGURATION
- sprite.goal
- sprite.goal.category == 'sprite
```

versus,

```yaml
# INCORRECT CONFIGURATION
- sprite.goal.category == 'sprite'
- sprite.goal
```

In the first case, `goal` is guaranteed to exist before the subsequent condition is applied to `goal.category`, while the second will generate a runtime error.

The ISL environment is injected with variables during execution:

- `sprite`: The SpriteState of the entity currently evaluating its transitions.
- `sprites`: A dictionary mapping `name: AssetState` for all mutable characters (Sprites and Players) currently on the board.
- `constants`: A dictionary of enums for accessing categorical constants.

!!! warning
    When referencing `sprites[...]` via a Goal name, authors must use `sprites.get(sprite.goal.name)` to protect the runtime against `KeyErrors` from garbage-collected entities.
    
## Goal

*Goals* provide the seed (or energy) for transitions through Intentions and the application of Motivations to modulate said transitions. A Goal is a Sprite's *modus operandi*, the abstract thing it pursues over the course of the game loop. A Sprite's transitions through Intention is *in order* to achieve a Goal.

- `name`: Unique Identifier of the Goal.
- `category`: Category of the Goal. (`asset`, `sprite`, `loot`, `wealth`, `property`, `position`)
- `position`: Last-known position of the Goal. When the Goal is within the `mutators.vision.radius`, this position is updated every game loop. Once the Goal exits the Sprites `mutators.vision.radius`, it becomes a static value that freezes on the last known Position of its Goal.

### Goal Category

When a Sprite has Goal, it will seek out (path-find) its way to `name`. The `category` of a Goal affects the type of identifier given in `name`. 

- `category == position`: The Goal is a Position, i.e. the Sprite is trying to find a location on the Board. The `name` will be the Sprite's name.
- `category == asset`: The Goal is a Sprite Asset, i.e. the Sprite is trying to find an Asset. The `name` will be the Asset `name`.
- `category == loot`: The Goal is Loot, i.e. the Sprite is seeking to acquire Loot. The `name` will be an Inventory key. 
- `category == wealth`: The Goal is Money, i.e. the Sprite is seeking to increase its Wallet. The `name` will be an Inventory key. The key will be of the loot with the maximum value in the Sprite's Prices, e.g. the highest priced loot.
- `category == property`: The goal is Property, i.e. the Sprite is seeking the location of Property. The `name` will be an Asset name of an Asset that implements a `PropertyState`.
- `category == sprite`: The goal is a Sprite. The `name` will be a name of a Sprite.

## AnimationMap

A Sprite's State is mapped onto an (Action, Direction) through an AnimationMap. This component of the Application statically ingests a Sprite State, applies formulas and returns the mapped tuple.

**Player Device**

Player Device mappings are applied to convert Device input to Intention and Goals, prior to the mapping of an Intention onto Animation (Action, Direction)-tuple. 

### Actions

Sprite Animation Actions is as a function of Sprite Intention state and Equipment state

    f(Intention, Equipment) = Action

In order to pass from an `ATTACK` Intention to a phsyically animated Action, an Equipment constraint must be satisfied. Likewise for other animated Intentions.

- `ATTACK`: Uses `equipment.weapon`
- `MINE`: Uses `equipment.tool`

**Formulae**

- `if state.intention == Intentions.ATTACK: state.animation.action = board.equipment.weapons[state.equipment.weapon].action`
- `if state.intention == Intentions.MINE: state.animation.action = board.equipment.tools[state.equipment.tools].action`

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

