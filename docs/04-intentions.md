# Ontology: Intentions & Goals

Intentions and Goals are an internal data structure that governs a Sprite's core logic. All Sprite Assets, when deployed on a Board, are given, along with an Animation state, an Intention state and Goal state that is updated by the gameplay loop. Intentions represent a node in the Sprite's "*finite automaton*", the Intention Transition Matrix. They are used to calculate the (Action, Direction) dimensions of a Sprite Animations state. Goals represent the focus of the Sprite's logic, e.g. a position to move to, a chest to open, etc.

Both Sprites and Players utilize the interface of Intention and Goals to communicate state updates. The key difference is how Intentions and Goals are generated. In the case of the Player, they are mapped from polling the input codes of a Device. For a non-playable Sprite, they are calculated using the [Intention Transition Matrix](#transition-matrix).

Broadly speaking, an Intention is a "verb", e.g. `attack`, `find`, `barter`, etc. A Goal is a "noun" (e.g. `object`, `position`, `property`, etc.). While the exact mapping is more complex, in general terms: Intentions produce Actions, Goals produce Directions.

!!! note
    Each individual intention has a detailed specification in the [Specifications section](./specs/index.md).

## Intention

A Intention is a [Sprite](./02-sprites.md) field that factors into the Asset Animation calculations indirectly; It may be thought of as a "hidden" state. An Animation is a "projection" of a Sprite's Intention into the (Action, Direction)-space. 

For Sprites, Intention is an attribute that controls state transitions and action mappings. For the Player, it controls action mappings.

It may indirectly alter the Sprite state changes or other properties of the Sprites, e.g. entering into the `sprint` state increases the velocity of the `(walk, *)` states, but does not factor into the animation speed or the frame indexing scheme. Similarly, entering into the `interact` state does not alter the Sprite's current animation in any way, but instead allows, for example, the Sprite to open a Chest or Door.

A brief explanation of each Intention state value is given below,

- `attack`: Initiate an Attack Animation.
- `attract`: Attract a Sprite for interaction.
- `barter`: Exchange Inventories.
- `build`: Instantiate a Strut.
- `escape`: Move away from target.
- `find`: Move towards target.
- `follow`: Move towards target.
- `hunt`: Move towards target.
- `idle`: Do nothing. Used for memory buffering, i.e. allowing remembered goals to pop onto the stack.
- `interact`: Interact with Objects.
- `mine`: Convert Resources into Inventory. 
- `return`: Return to remembered locations.
- `scavenge`: Collect loot.
- `speak`: Initiate dialogue.
- `sprint`: Increase movement speed.
- `threaten`: Pre-cursor to Attack.
- `wander`: Move to randomized positions.

!!! note
    `mine` is complicated by the polymorphism that exists in the LPC spec between the Action of Thrust (i.e. attacking) and using a Shovel or Pickaxe, i.e. the Spear Weapon and the Shovel/Pickaxe Tool both use the same underlying animation rows. This is resolved by [Action Sets](./appendices/01-schemas.md#configuration-actions) and [AnimationMaps](./10-architecture.md#maps).

**Intention Loops**

In order to avoid complex automata, `idle` acts as the origin and terminus of all "*Intention Loops*". In other words, `idle` is the "hub" Intention. All autonomous Sprite Animations are modelled as loops back into their `idle` Intention node in their finite automata. For example, the *Dialogue Loop* is given below.

$$
\text{idle} \to \text{find} \to \text{speak} \to \text{idle}
$$

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
| --- | --- | --- |
| 1 | `attack` | `attack`, `hunt` |
| 2 | `barter` | `threaten`, `idle` |
| 3 | `build` | `idle` |
| 4 | `escape` | `escape`, `idle` |
| 5 | `find` | `interact`, `speak`, `follow` |
| 6 | `follow` | `follow`, `find` |
| 7 | `hunt` | `attack`, `return` |
| 8 | `idle` |  `find`, `idle` |
| 9 | `interact` | `idle` |
| 10 | `mine` | `build`, `mine`, `idle` |
| 11 | `mock` | `threaten`, `idle` |
| 12 | `return` | `find` |
| 13 | `speak` | `idle` |
| 14 | `sprint` | `idle` |
| 15 | `threaten` | `attack`, `hunt`, `idle` |
| 16 | `wander` | `idle` |

**Intentional Scripting Language (ISL)**

The `condition` for each Intention transition is given in a simple truth-valued language that admits the logical operations and terms,

Operations:

* `==`: equivalence
* `!=`: non-equivalence
* `not`: negation
* `or`: disjunction
* `and`: conjunction

Terms:

* `None`: null value
* `str`: constants
* `sprite.<attribute>`: self State variable
* `sprites.get(<sprite-name>).<attribute>`: other Sprites state variable
* `constants`: A dictionary of game constants.
* `functions`: A dictionary of helper functions.

For example, in the default Intention Transition matrix given above, the transition from `attack` to `hunt` is conditional on the following,

```yaml
- not sprite.goal
- sprite.memory.goal.category == constants.Goals.SPRITE.value
```

`sprite` is a reference to the Sprite's state which is currently having its Intention processed by the game engine. Thus, the Sprite's Intention state will transition to `hunt` if the Sprite currently does not have a Goal, but remembers having a Goal of Category `sprite`.

!!! note
    The expression `not sprite.goal` is a *truthy* expression, i.e. it is to be interpretted as an existential claim. In other words, this expression evaluates to `true` if `sprite.goal` does not exist. If the expression involves a List, e.g. `sprite.memory.communications`, this expression evaluates to `true` in the event it has more than 0 entries.

In another example, the transition from `attack` to `scavenge` in the default Intention Transition matrix is given by,

```yaml
- sprites.get(sprite.goal.name)
- sprites.get(sprite.goal.name).mutators.triggers.dead
```

`sprites` is a reference to a cross-layer dictionary (`_cached_characters`) of all ingame Sprites states keyed by their identifying and unique `name`, which provides $O(1)$ access to their state attributes.

Notice in the example there is a self-entrant transition. A Sprite with an `attack` Intention can re-enter the `attack` Intention conditional on the Sprite still having a target,

```yaml
- sprite.goal.category == Goals.SPRITE.value
```

!!! important
    The conditions for an Intention transition are evaluated in the order they specified! In the given example, if `sprite.goal.category == constants.Goals.SPRITE.value`, none of the other conditions for Intention transitions are evaluated and the Intention transitions back into `attack`.

Intention transition conditions are compiled by the application during initialization and evaluated at runtime. The engine supports two execution strategies, configured via `ISL_TRANSLATOR` in `settings.py`: `lambda` (which generates inline Python functions) and `compiler` (which generates native Abstract Syntax Trees). The application evaluates ISL conditions sequentially utilizing Python's native short-circuit logic.

To avoid AttributeError exceptions during runtime, existential checks must strictly precede attribute accesses. Consider,

```yaml
# CORRECT CONFIGURATION
- sprite.goal
- sprite.goal.category == constants.Goals.SPRITE.value
```

versus,

```yaml
# INCORRECT CONFIGURATION
- sprite.goal.category == constants.Goals.SPRITE.value
- sprite.goal
```

In the first case, `goal` is guaranteed to exist before the subsequent condition is applied to `goal.category`, while the second will generate a runtime error.

The ISL environment is injected with variables during execution:

* `sprite`: The SpriteState of the entity currently evaluating its transitions.
* `sprites`: The `_cached_characters` dictionary mapping `name: AssetState` for all mutable characters (Sprites and Players) currently on the board.
* `constants`: A dictionary of Enums. Keys are: `AssetInstances`, `AssetCategories`, `Goals`, `Intentions`, `Motivations`.
* `functions`: A dictionary of boolean helper functions. All functions return a truth value.
    - `is_near(p1: Position, p2: Position, radius: int)`

!!! warning
    When referencing `sprites[...]` via a Goal name, authors must use `sprites.get(sprite.goal.name)` to protect the runtime against `KeyErrors` from garbage-collected entities.

## Goal

*Goals* provide the seed (or energy) for transitions through Intentions and the application of Motivations to modulate said transitions. A Goal is a Sprite's *modus operandi*, the abstract thing it pursues over the course of the game loop. A Sprite's transitions through Intention is *in order* to achieve a Goal.

- `name`: Unique Identifier of the Goal.
- `category`: Category of the Goal. 
- `position`: Last-known position of the Goal. When the Goal is within the `mutators.vision.radius`, this position is updated every game loop. Once the Goal exits the Sprites `mutators.vision.radius`, it becomes a static value that freezes on the last known Position of its Goal.

### Goal Category

When a Sprite has Goal, it will seek out (path-find) its way to `name`. The `category` of a Goal affects the type of identifier given in `name`. 

- `category == position`: The Goal is a Position, i.e. the Sprite is trying to find a location on the Board. The `name` will be a placeholder constant.
- `category == object`: The Goal is an Object, i.e. the Sprite is trying to find an Object. The `name` will be the Object `instance` (*not* the ID).
- `category == property`: The goal is Property, i.e. the Sprite is seeking to create property. The `name` will be the *ID* of the Strut the Sprite is seeking to create.
- `category == target`: The goal is a Sprite, with aggressive intent implied. The `name` will be the name of a Sprite.
- `category == subject`: The goal is a Sprite, with passive intent impled. The `name` will be the name of a Sprite.

**TODO: In Design**

- `category == loot`: The Goal is Loot, i.e. the Sprite is seeking to acquire Loot. The `name` will be an Inventory key. 
- `category == money`: The Goal is Money, i.e. the Sprite is seeking to increase its Wallet. The `name` will be an Inventory key. The key will be of the loot with the maximum value in the Sprite's Prices, e.g. the highest priced loot.

### Goal Satisfaction

TODO

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

- `if state.intention == speak and state.psyche.dialogue: dialogue = state.psyche.dialogue`

## Mechanics

The (Intention, Goal) of a Sprite is managed across the application lifecycle by [Mechanics](./05-mechanics.md). 

- CognitionMechanics ("*The Brain*"): Manages the Goal Lifecycle. It evaluates the environment, consults Motivations and Meters, sets the Goal, determines if the Goal has been achieved (or invalidated), and manages the Memory stack.
- TransitionMechanics ("*The Instinct*"): Manages the Intention Transitions. It blindly evaluates the Transitions condition and shunts the Sprite to its next Intention if they are satisfied.
- SpatialMechanics (*The Muscle*): CombatMechanics, InteractionMechanics, etc., alter the physical world state (e.g., killing the target, opening the Chest). This physical change is what signals CognitionMechanics on the next tick that the goal is achieved.

### Cognition

CognitionMechanics manages the life cycle of Sprite Goals.

1. **Phase A: Resolution**: Conditions are evaluated for goal resolution
    - `if goal.category == TARGET`: If `target.mutators.triggers.dead`, `goal = None`.
    - `if goal.category == SUBJECT`: If `not psyche.dialogue`, `goal = None`.
    - `if goal.category == POSITION`: If `position - goal.position < some_radius`.
    - `if goal.category == OBJECT`: TODO
    - `if goal.category == PROPERTY`: If `goal.name in memory.property`, `goal = None`. 
2. **Phase B: Memory**: The Sprite's memory is managed and updated relative to its vision. 
    - If the Sprite has no Goals, Goals in the Memory are popped off the stack and added to the current Goal. 
    - A scan of the `mutator.parameter.vision.radius` is conducted. If a Sprite is found, its location is updated in `memory.sprites`.
3. **Phase C: Ideation**: If the Sprite has no Goals, environmental and proximal Goals are ideated. 
    - `if psyche.dialogue`: If target Sprite is within `mutators.parameters.vision.radius`, then `goal.category = Goals.SUBJECT.value` and `goal.name` is set to target Sprite.
4. **Phase D: Motivation**: If the Sprite has still no Goals, overarching Motivations are used to form new Goals. These goals are pushed onto the `memory.goals` stack.
    - `if psyche.motivation.CONQUEST`: TODO
    - `if psyche.motivation.PROFIT`: TODO
    - `if psyche.motivation.SURVIVAL`: TODO
    - `if psyche.motivation.LOVE`: TODO
    - `if psyche.motivation.REVENGE`: TODO
    - `if psyche.motivation.REBELLION`: TODO
    - `if psyche.motivation.SAFETY`: TODO
5. **Phase E: Tracking**: The Sprite's current Goal is tracked.
    - `if goal.category in [TARGET, SUBJECT]`: 
        - `if goal.memory.locations.get(goal.name): goal.position = goal.memory.locations[goal.name].position`
        - TODO
    - `if goal.category == POSITION`: 
    - `if goal.category == OBJECT`: 
    - `if goal.category == PROERTY`:
6. **Phase F: Projection**
    - `if intention == ESCAPE`:
    - `if intention == FIND`:
    - `if intention == WANDER`: 