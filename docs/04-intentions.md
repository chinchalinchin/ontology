# Ontology Docs: Intentions & Goals

Intentions and Goals are an internal data structure that governs a [Sprite](./02-sprites.md)'s core logic. All [Sprites](./02-sprites.md), when deployed on the [Board](./00-overview.md#component-board), are given, along with an AnimationState, an Intentionand Goal state that is updated by the gameplay loop. Intentions represent a node in the Sprite's "*finite automaton*", the **Intention Transition Matrix**. Intentions are used to calculate the (Action, Direction) dimensions of a Sprite AnimationState. Goals represent the spatial focus of the Sprite's Intention, e.g. a Position to move to, a [Chest](./01-assets.md#object-chests) to open, etc.

!!! important "Separation of Duties"
    [CognitionMechanics](./05-mechanics.md#intentional-mechanic-cognitionmechanics) mutates Goals, [TransitionMechanics](./05-mechanics.md#intentional-mechanic-transitionmechanics) mutates Intentions. The [Intention Transition Matrix](#transition-matrix) governs all mutations of Sprite Intentions. This rule **must** be followed at all times.

Both [Sprites and Players](./02-sprites.md) utilize the interface of Intention and Goals to communicate State updates and reactions to the environment. The key difference is how Intentions and Goals are generated. In the case of the [Player](./02-sprites.md#instance-player), they are mapped by polling the input codes of a [Device](./02-sprites.md#devices). For a non-playable Sprite, they are calculated using the [Intention Transition Matrix](#transition-matrix).

Broadly speaking, an Intention is a "verb", e.g. `attack`, `find`, `barter`, etc. A Goal is a "noun" (e.g. `object`, `position`, `property`, etc.). While the exact mapping is more complex and interdependent, in general terms: Intentions produce Actions, Goals produce Directions.

!!! note "Specifications"
    Each "*Intention Loop*" has a detailed specification in the [Specifications section](./specs/index.md).

!!! note "Transition Notation"
    A Transition from the Intention $i_1$ to the Intention $i_2$ is denoted $i_1:i_2$

## Specification: Intention

An Intention is a [Sprite](./02-sprites.md) field that factors into the its Animation calculations indirectly; It may be thought of as a "hidden" State. An Animation is a "projection" of a Sprite's Intention into the (Action, Direction)-space. 

For Sprites, Intention is an attribute that controls State transitions and Action mappings. For the Player, it controls action mappings.

It may indirectly alter the Sprite state changes or other properties of the Sprites, e.g. entering into the `sprint` state increases the velocity of the `(walk, *)` states, but does not factor into the animation speed or the frame indexing scheme. Similarly, entering into the `interact` state does not alter the Sprite's current animation in any way, but instead allows, for example, the Sprite to open a Chest or Door.

**Semantics: Intentions**

* `attack`: Initiate an Attack Animation.
* `attract`: Attract a Sprite for interaction.
* `barter`: Exchange Inventories.
* `build`: Instantiate a Strut.
* `escape`: Move away from target.
* `find`: Move towards target.
* `follow`: Move towards target.
* `hunt`: Move towards target.
* `idle`: Do nothing. Used for memory buffering, i.e. allowing remembered goals to pop onto the stack.
* `interact`: Interact with Objects.
* `mine`: Convert Resources into Inventory. 
* `return`: Return to remembered locations.
* `scavenge`: Collect loot.
* `speak`: Initiate dialogue.
* `sprint`: Increase movement speed.
* `threaten`: Pre-cursor to Attack.
* `wander`: Move to randomized positions.

!!! note "Thrust Polymorphism"
    `mine` is complicated by the polymorphism that exists in the LPC spec between the Action of Thrust (i.e. attacking) and using a Shovel or Pickaxe, i.e. the Spear Weapon and the Shovel/Pickaxe Tool both use the same underlying animation rows. This is resolved by [Action Sets](./appendices/01-schemas.md#configuration-actions) and [AnimationMaps](./12-architecture.md#maps).

**Semantics: Intention Groups**

Intentions form natural groups based on the gameplay logic they inhabit and produce. Intention Groups are enumerated below,

* BlockingIntentions (`attack`, `mine`): Intentions whose projected animations must be complete before control is released.
* AnimatedIntentions (`attack`, `mine`): Intentions that produce an animation.
* StaticIntentions (`idle`, `barter`, `speak`, `interact`, `threaten`, `mock`): Intentions that do not produce an animation.
* NavigationIntentions (`find`, `follow`, `hunt`, `escape`, `wander`, `return`): Intentions with a velocity.
* StationaryIntentions (`barter`, `build`, `idle`, `interact`, `mine`,): Intentions with no velocity.

**Concept: Intention Loops**

In order to avoid modeling the Sprite as an overly complex automata, `idle` acts as the origin and terminus of all "*Intention Loops*" in the Intention Transition Matrix. In other words, `idle` is the "hub" Intention. All autonomous Sprite Animations are modelled as loops back into the `idle` Intention. For example, one variation of the *Dialogue Loop* is given below,

$$
\text{idle} \to \text{find} \to \text{speak} \to \text{idle}
$$

Another route through the *Dialogue Loop* is given by,

$$
\text{idle} \to \text{find} \to \text{speak} \to \text{follow} \to \text{find} \to \text{speak} \text{idle}
$$

For this reason, Intention *Transitions* are further classified as *Entrypoints*, *Interpoints* and *Exitpoints*, where the entrance and exit is in reference to the particular loop being traversed. 

A valid Intention Loop with $n$ steps must always satisfy the following constraints,

* $\text{idle}:i_1$ : The Entrypoint must transition from `idle`
* $:i_{n-1}:\text{idle}$ : The Exitpoint must transition into `idle`

If $i_j:i_{j+1}$ where $i_j, i_{j+1} \neq \text{idle}$, then that transition is called an Interpoint.

### Intention: Transition Matrix

* Location: `/src/data/config/intentions/main.yaml`

!!! important "Player Exclusion"
    The Player State does not observe the Intention Transition matrix; the Player State is managed by polling the user's input and mapping input to intention. See [Player documentation](./02-sprites.md#instance-player) for more information on the Player.

!!! warning "Intention Silo"
    Nothing in the [Engine](./00-overview.md#component-engine) changes Intentions *except* Transitions. Transitions (and TransitionMechanics) are the only component of the [Application](./00-overview.md#application) that alters Intention State. This is important for consistency. Failure to observe this rule may result in Sprites not behaving correctly. 

The Intention Transition Matrix determines which Intention states are currently reachable for a Sprite from its current Intention. The general schema for the Intention Transition Matrix is given below,

```yaml
intentions:
    <intention-key>:
        - next: <intention-key>
          conditions: 
            - <condition>
```

**Default: Intention Transition Matrix**

Provided below is the Intention Transition Matrix bundled with the application by default,

```mermaid
--8<-- "static/mmd/executor-intention-transitions.mmd"
```

--8<-- "static/md/executor-intention-transitions.md"

**Concept: Intentional Propositions**

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
- sprite.memory.goal.category == constants.Goals.TARGET.value
```

`sprite` is a reference to the Sprite's state which is currently having its Intention processed by the Engine. Thus, the Sprite's Intention will transition to `hunt` if the Sprite currently does not have a Goal, but remembers having a Goal of Category `sprite`.

!!! note
    The expression `not sprite.goal` is a *truthy* expression, i.e. it is to be interpretted as an existential claim. In other words, this expression evaluates to `true` if `sprite.goal` does not exist. If the expression involves a List, e.g. `sprite.memory.communications`, this expression evaluates to `true` in the event it has more than 0 entries.

In another example, the transition from `attack` to `scavenge` in the default Intention Transition matrix is given by,

```yaml
- sprites.get(sprite.goal.name)
- sprites.get(sprite.goal.name).mutators.triggers.dead
```

`sprites` is a reference to a cross-layer dictionary of all Sprites States on the [Board](./00-overview.md#component-board) keyed by their unique `name`.

!!! important "Intention Order"
    The conditions for an Intention transition are evaluated in the order they specified. In the given example, if `sprite.goal.category == constants.Goals.TARGET.value`, none of the other conditions for Intention transitions are evaluated and the Intention transitions back into `attack`.

Intention transition conditions are compiled by the application during initialization and evaluated at runtime. The engine supports two execution strategies, configured via `TRANSLATOR_IMPLEMENTATION` in `settings.py`: `lambda` (which generates inline Python functions) and `compiler` (which generates native Abstract Syntax Trees). The application evaluates conditions sequentially utilizing Python's native short-circuit logic.

To avoid AttributeError exceptions during runtime, existential checks must strictly precede attribute accesses. Consider,

```yaml
# CORRECT CONFIGURATION
- sprite.goal
- sprite.goal.category == constants.Goals.TARGET.value
```

versus,

```yaml
# INCORRECT CONFIGURATION
- sprite.goal.category == constants.Goals.TARGET.value
- sprite.goal
```

In the first case, `goal` is guaranteed to exist before the subsequent condition is applied to `goal.category`, while the second will generate a runtime error.

The Transition execution environment is injected with variables during execution:

* `sprite`: The SpriteState of the entity currently evaluating its transitions.
* `sprites`: The `_cached_characters` dictionary mapping `name: AssetState` for all mutable characters (Sprites and Players) currently on the board.
* `constants`: A dictionary of Enums. Keys are: `AssetInstances`, `AssetCategories`, `Goals`, `Intentions`, `Motivations`.
* `functions`: A dictionary of boolean helper functions. All functions return a truth value.
    * `is_near(p1: Position, p2: Position, radius: int)`: Determine if positions are close.
    * `any_goals(m: List[Goal], category: str)`: Determine if a GoalCategory exists in the Sprite memory.
    * `any_memories_visible(sprite: SpriteState, sprites: Dict[str, SpriteState], categories: List[GoalCategories])`

!!! warning "KeyErrors"
    When referencing `sprites[...]` via a Goal name, authors must use `sprites.get(sprite.goal.name)` to protect the runtime against `KeyErrors` from garbage-collected entities.

## Specification: Goal

*Goals* provide the seed (or energy) for transitions through Intentions and the application of Motivations to modulate said transitions. A Goal is a Sprite's *modus operandi*, the abstract thing it pursues over the course of the game loop. A Sprite's transitions through Intention is *in order* to achieve a Goal.

* `name`: Unique Identifier of the Goal.
* `category`: Category of the Goal. 
* `position`: Last-known position of the Goal. When the Goal is within the `mutators.vision.radius`, this position is updated every game loop. Once the Goal exits the Sprites `mutators.vision.radius`, it becomes a static value that freezes on the last known Position of its Goal.

### Goal: Category

When a Sprite has Goal, it will seek out (path-find) its way to `name`. The `category` of a Goal affects the type of identifier given in `name`. 

* `position`: The Goal is a Position, i.e. the Sprite is trying to find a location on the Board. The `name` will be a placeholder constant.
* `object`: The Goal is an Object, i.e. the Sprite is trying to find an Object. The `name` will be the Object `name`.
* `property`: The goal is Property, i.e. the Sprite is seeking to create property. The `name` will be the *ID* of the Strut the Sprite is seeking to create, unless matched by an ID in its `sprite.memory.property`.
* `target`: The goal is a Sprite, with aggressive intent implied. The `name` will be the name of a Sprite.
* `subject`: The goal is a Sprite, with passive intent impled. The `name` will be the name of a Sprite.

!!! @TODO(06-03)
    `resource` need implementation.

* `resource`: The Goal is Resources, i.e. the Sprite is seeking to acquire Resources. The `name` will be a Material key from the [MaterialIndex](./appendices/01-schemas.md#configuration-materials).

### Goal: Satisfaction

TODO

## Module: AnimationMap

A Sprite's State is mapped onto an (Action, Direction) through an AnimationMap. This component of the Application statically ingests a Sprite State, applies formulas and returns the mapped tuple.

**Player Device**

Player Device mappings are applied to convert Device input to Intention and Goals, prior to the mapping of an Intention onto Animation (Action, Direction)-tuple. 

### Mapping: Actions

The Action of a Sprite's AnimationState is as a function of the Sprite's Intention and Equipment,

$$
f(\text{Intention}, \text{Equipment}) \to \text{Action}
$$

In order to pass from an `attack` Intention to a phsyically animated Action, an Equipment constraint must be satisfied. Likewise for other animated Intentions.

* `attack`: Uses `equipment.weapon`
* `mine`: Uses `equipment.tool`

**Formulae**

* `if state.intention == Intentions.ATTACK.value: state.animation.action = board.equipment.weapons[state.equipment.weapon].action`
* `if state.intention == Intentions.MINE.value: state.animation.action = board.equipment.tools[state.equipment.tools].action`

### Mapping: Directions

The Direction of a Sprite's AnimationState is a function of the Sprite's Position and Trajectory,

$$
f(\text{Position}, \text{Trajectory}) \to \text{Direction}
$$

**Direction Mapping: Player**

* `if input.scancode == rightarrow: goal.position.x += speed`
* `if input.scancode == leftarrow: goal.position.x -= speed`
* `if input.scancode == uparrow: goal.position.y -= speed`
* `if input.scancode == downarrow: goal.position.y += speed`

**Direction Mapping: Sprite**

$$
\text{target} = \text{trajectory.target} \lor \text{goal.position}
$$

$$
dx = \text{position.x} - \text{target.x}$ and $dy = \text{position.y} - \text{target.y}
$$

* $(dy > dx \land dy > -dx) \implies (\text{direction} = \text{down})$
* $(dy < dx \land dy > -dx) \implies (\text{direction} = \text{right})$
* $(dy < dx \land dy < -dx) \implies (\text{direction} = \text{up})$
* $(dy > dx and dy < -dx) \implies \text{direction} = \text{left}$

## Mechanics: Intention Workflow

The (Intention, Goal, Trajectory) triad of a Sprite is managed across the application lifecycle by [Mechanics](./05-mechanics.md):

* [CognitionMechanics](./05-mechanics.md#intentional-mechanic-cognitionmechanics): Manages the Goal lifecycle. Evaluates environmental perceptions, consults Motivations and Psyche, sets and completes Goals, and manages Memory.
* [TransitionMechanics](./05-mechanics.md#intentional-mechanic-transitionmechanics): Manages Intention Transitions. Evaluates Transition conditions sequentially and shunts the Sprite to its next Intention state when criteria are satisfied.
* [NavigationMechanics](./05-mechanics.md#intentional-mechanic-navigationmechanics): Manages Trajectories. Queries the environment, evaluates obstacle geometry, and raycasts to maintain Trajectory.
* [MotionMechanics](./05-mechanics.md#core-mechanic-motionmechanics): Induces movement. Accelerates velocity vectors toward the Trajectory target.
* [SpatialMechanics](./05-mechanics.md#mechanics-spatial): Resolves collisions, combat, and interactions (e.g., passing through [Doors](./01-assets.md#object-doors) or opening a [Chest](./01-assets.md#object-chests)).

### Workflow Compoentn: Cognition

CognitionMechanics manages the lifecycle of strategic Sprite Goals across seven deterministic phases:

!!! @TODO(06-03)
    `doors` should be a semantically distinct Goal from Object. Goal semantics need to correspond to "accomplishable feats" in the Sprite's repeteroire, e.g. opening a door, opening a chest, attacking, speaking, crafting, etc. This would seem related to the differentia of `modality` recently introduced in Phase 07.04.

1. **Phase A: Resolution**: Evaluates whether active strategic goals are complete or abandoned:
    * `category == 'target'`: 
        * If Target is dead, Goal is resolved. 
        * If within the Sprite's [Action radius](./02-sprites.md#field-mutators) without line of sight, shelves goal into [Memory](./02-sprites.md#field-memory) and abandons active tracking.
    * `category == 'subject'`: 
        * If the Sprite has no [Dialogue in its Psyche](./02-sprites.md#field-psyche), resolves goal. 
        * If within the Sprite's [Action radius](./02-sprites.md#field-mutators) without line of sight, and spawns a `confusion` [Expression](./01-assets.md#cursor-expressions).
    * `category == 'position''`: If the Sprite is near the Position, the Goal is resolved.
    * `category == 'object'`: 
        * If `sprite.layer != goal.layer`, the transition door was traversed; resolves goal (`goal = None`). 
    * `category == 'property'`: If `goal.name in memory.property`, resolves goal.
2. **Phase B: Scan**: Scans [Vision radius](./02-sprites.md#field-mutators) on the same [Layer](./00-overview.md#concept-layers). Caches discovered entities into [Memory](./02-sprites.md#field-memory) and updates coordinates of corresponding entries in its remembered Goals.
3. **Phase C: Memory**: Pops suspended Goals off [Memory](./02-sprites.md#field-memory) into its active Goal when in `idle`, `find`, or `hunt`. Dormant targets whose last known positions were empty are skipped until sighted again.
4. **Phase D: Ideation**: Spontaneously generates new strategic goals from internal psychological state:
    * `if psyche.dialogue`: Scans Sprites on the same layer within Vision Radius. Assigns `subject` Goal.
5. **Phase E: Motivation**: If the Sprite has still no Goals, overarching Motivations are used to form new Goals. These goals are pushed onto the [Memory](./02-sprites.md#field-memory) stack.
    * `if psyche.motivation.CONQUEST`: TODO
    * `if psyche.motivation.PROFIT`: TODO
    * `if psyche.motivation.SURVIVAL`: TODO
    * `if psyche.motivation.LOVE`: TODO
    * `if psyche.motivation.REVENGE`: TODO
    * `if psyche.motivation.REBELLION`: TODO
    * `if psyche.motivation.SAFETY`: TODO
6. **Phase F: Tracking**: Updates coordinates of active strategic goals:
    * `category in ['target', 'subject']`: Updates Goals when within its Vision radius. Freezes coordinates when sight is lost.
    * **Cross-Layer Door Subsumption**: If Goal Layer does not equal Sprite layer, subsumes active goal into Memory and assigns a prerequisite `object` goal for the nearest connecting Door.
7. **Phase G: Projection**:
    * `intention == 'escape'`: Extrapolates a destination coordinate in the opposite vector direction of the threat.
    * `intention == 'wander'`: Samples a random destination within $[-\text{radius}_{\text{vision}}, \text{radius}_{\text{vision}}]$, clamps to layer dimensions, and commits `Goal(name="wander", category=POSITION)`.