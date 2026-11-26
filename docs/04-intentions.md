# Ontology Docs: Intentions & Goals

Intentions and Goals are an internal data structure that governs a [Sprite](./02-sprites.md)'s core logic. All [Sprites](./02-sprites.md), when deployed on the [Board](./00-overview.md#component-board), are given an Intention and Goal State that is updated by the [Engine Loop](./00-overview.md#component-engine). 

Intentions represent a node in the Sprite's "*finite automaton*", the **Intention Transition Matrix**. Intentions are used to calculate the (Action, Direction) dimensions of a Sprite AnimationState.

Goals represent the focus of the Sprite's Intention, e.g. a Position to move to, a [Chest](./01-assets.md#object-chests) to open, etc.

!!! important "Separation of Duties"
    [CognitionMechanics](./05-mechanics.md#intentional-mechanic-cognitionmechanics) mutates Goals, [TransitionMechanics](./05-mechanics.md#intentional-mechanic-transitionmechanics) mutates Intentions. The [Intention Transition Matrix](#intention-transition-matrix) governs all mutations of Sprite Intentions. This rule **must** be followed at all times.

Both [Sprites and Players](./02-sprites.md) utilize the interface of Intention and Goals to communicate State updates and reactions to the environment. The key difference is how Intentions and Goals are generated. In the case of the [Player](./02-sprites.md#instance-player), they are mapped by polling the [Device](./02-sprites.md#devices). For a non-playable Sprite, the progression of Intentions towards a Goal is calculated using the [Intention Transition Matrix](#intention-transition-matrix) while the resolution of a Goal is calculated by the [Goal Resolution Matrix](#goal-resolution-matrix).

Broadly speaking, an Intention is a "verb", e.g. `attack`, `find`, `barter`, etc. A Goal is a "noun" (e.g. `object`, `position`, `property`, etc.). 

In general terms: Intentions produce Actions, Goals produce Directions.

!!! note "Transition Notation"
    A Transition from the Intention $i_1$ to the Intention $i_2$ is denoted $i_1:i_2$

## Intentions: Concepts

### Concepts: Cognition

A Sprite's cognitive processes are distributed through successive layers of interdependent abstractions, called the *Cognitive Pipeline*.

1. Actions: Animate Events that generate collisions or interactions.
2. Intentions: Predisposition to Action
3. Goals: Objective of Action
4. Instincts: Procedure for generating Goals
5. Motivations: TODO

The Action layer represents the actual physical events that occur on the [Board](./00-overview.md#component-board) and are ultimately rendered on the [Screen](./00-overview.md#component-screen). Everything beyond the Action layer represents abstractions governing the internal data structure of Sprites.

### Concept: Praxeology

At a high-level, the *Cognitive Pipeline* represents the Sprite's *praxeological process* for engaging in Action in the "*world*".

1. The Sprite observes the Board State.
2. The Sprite's Instincts produce Goals. 
3. Goals and their pursuit induce transitions through Intentions.
4. An (Intention, Goal) projects into (Action, Direction).
5. An (Action, Direction) has an effect on the external world. 

## Specification: Intentions

An Intention is a [Sprite](./02-sprites.md) field that factors into the its Animation calculations and State mutations indirectly; It may be thought of as a "hidden" State variable. An Animation is a "*projection*" of a Sprite's Intention into the (Action, Direction)-space. 

Intentions, as hidden State variables, may have no "*visible*" (more precisely, *animate*) effect on the [Board](./00-overview.md#component-screen) or [Screen](./00-overview.md#component-screen), but may indirectly alter the Sprite State rates of changes or modulate calculations involving Sprite Properties, e.g. entering into the `sprint` Intention increases the Velocity of the `walk` Actions, but does not factor into the Animation speed or the Frame indexing scheme. Similarly, entering into the `scavenge` state does not alter the Sprite's current Animation or Frame, but instead allows, for example, the Sprite to open a Chest and increase its Inventory.

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
    `mine` is complicated by the polymorphism that exists in the LPC spec between the Action of `thrust` (i.e. attacking) and using a Shovel, i.e. the Spear Weapon and the Shovel Tool both use the same underlying animation rows. This is resolved by [Action Sets](./appendices/01-schemas.md#configuration-actions) and [AnimationMaps](./12-architecture.md#maps).

**Semantics: Intention Groups**

Intentions form natural groups based on the logic they cluster around during the course of [Engine Loop](./00-overview.md#component-engine).

* BlockingIntentions (`attack`, `mine`): Intentions whose projected Animations must be complete before control is released.
* AnimatedIntentions (`attack`, `mine`): Intentions that produce an Animation.
* StaticIntentions (`idle`, `barter`, `speak`, `interact`, `threaten`, `mock`): Intentions that do not produce an Animation.
* NavigationIntentions (`find`, `follow`, `hunt`, `escape`, `wander`, `return`): Intentions that produce a Velocity.
* StationaryIntentions (`barter`, `build`, `idle`, `interact`, `mine`): Intentions that do not produce a Velocity.

**Concept: Intention Loops**

Each Intention Loop rooted at `idle` forms a closed "*intentional act*", $\langle I, \pi, \beta \rangle$:

1. **Initiation ($I$):** The Entrypoint transition $\text{idle} : i_1$ together with any required equipment admissibility constraint.
2. **Execution ($\pi$):** Interpoint transitions $i_j : i_{j+1}$ ($i_j, i_{j+1} \neq \text{idle}$) paired with spatial and navigational mechanics.
3. **Termination ($\beta$):** Goal resolution (`complete` or `lost`) or a context-invariant violation (the active Goal category no longer matches the active Intention), routing the Sprite back to `idle` via an Exitpoint $i_{n-1} : \text{idle}$.

All autonomous Sprite Animations are modelled as loops back into the `idle` Intention. For example, one variation of the *Dialogue Loop* is given below,

$$
\text{idle} \to \text{find} \to \text{speak} \to \text{idle}
$$

Another route through the *Dialogue Loop* is given by,

$$
\text{idle} \to \text{find} \to \text{speak} \to \text{follow} \to \text{find} \to \text{speak} \text{idle}
$$

For this reason, Intention *Transitions* are classified as *Entrypoints*, *Interpoints* and *Exitpoints*, where the entrance and exit is in reference to the particular loop being traversed. 

A valid Intention Loop with $n$ steps must always satisfy the following constraints,

* $\text{idle}:i_1$ : The Entrypoint must transition from `idle`
* $:i_{n-1}:\text{idle}$ : The Exitpoint must transition into `idle`

If $i_j:i_{j+1}$ where $i_j, i_{j+1} \neq \text{idle}$, then that transition is called an Interpoint.

### Intention: Transition Matrix

* Location: `/src/data/configuration/automata/intentions/main.yaml`

!!! important "Player Exclusion"
    The Player State does not observe the Intention Transition matrix; the Player State is managed by polling the user's input and mapping input to intention. See [Player documentation](./02-sprites.md#instance-player) for more information on the Player.

!!! warning "Intention Silo"
    Nothing in the [Engine](./00-overview.md#component-engine) changes Intentions *except* Transitions. Transitions (and TransitionMechanics) are the only component of the [Application](./00-overview.md#application) that alters Intention State. This is important for consistency. Failure to observe this rule may result in Sprites behaving incorrectly. 

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
* `sprite.<attribute>`: self State reference.
* `sprites.get(<sprite-name>).<attribute>`: other Sprites' State reference.
* `constants`: A dictionary of Application constants.
* `functions`: A dictionary of helper functions.

For example, in the Application's default Intention Transition Matrix, the transition from `attack` to `hunt` is conditional on,

```yaml
- not sprite.goal
- sprite.memory.goal.category == constants.Goals.TARGET
```

`sprite` is a reference to the Sprite's State which is currently having its Intention processed by the Engine. Thus, the Sprite's Intention will transition to `hunt` if the Sprite currently does not have a Goal, but remembers having a Goal of Category `target`.

!!! note
    The expression `not sprite.goal` is a *truthy* expression, i.e. it is to be interpretted as an existential claim. In other words, this expression evaluates to `true` if `sprite.goal` does not exist. If the expression involves a List, e.g. `sprite.memory.communications`, this expression evaluates to `true` in the event it has more than 0 entries.

In another example, the transition from `attack` to `scavenge` in the default Intention Transition Matrix is given by,

```yaml
- sprites.get(sprite.goal.name)
- sprites.get(sprite.goal.name).mutators.triggers.dead
```

`sprites` is a reference to a cross-Layer dictionary of all Sprites States on the [Board](./00-overview.md#component-board) keyed by their unique `name`.

!!! important "Intention Order"
    The conditions for an Intention transition are evaluated in the order they specified. In the example, if `not sprite.goal`, none of the other conditions for Intention transitions are evaluated and the Intention remains into `attack`.

Intention transition conditions are compile during [Application Initialization](./12-architecture.md#specification-initialization) and evaluated at runtime. 

**Behavior: Translation**

The engine supports two execution strategies, configured via `TRANSLATOR_IMPLEMENTATION` in `settings.py`: `lambda` (which generates inline Python functions) and `compiler` (which generates native Abstract Syntax Trees). The application evaluates conditions sequentially utilizing Python's native short-circuit logic.

**Example: Configuration Syntax**

Consider

```yaml
# CORRECT CONFIGURATION
- sprite.goal
- sprite.goal.category == constants.Goals.TARGET
```

versus,

```yaml
# INCORRECT CONFIGURATION
- sprite.goal.category == constants.Goals.TARGET
- sprite.goal
```

In the first case, `goal` is guaranteed to exist before the subsequent condition is applied to `goal.category`, while the second will generate a runtime error.

**Environment: Variables**

The Transition execution environment is injected with variables during execution.

* `sprite`: The Sprite State of the Asset evaluating its conditions.
* `sprites`: Map of deployed Character `name` to Character State across the Board.
* `assets`: Map of deployed Asset `name` to Asset State on the Sprite's current Layer.
* `constants`: Map of Application semantics. 
    * `AssetInstances`, `AssetCategories`, `Goals`, `Intentions`, `Motivations`, `Relationship`
* `functions`: A dictionary of boolean helper functions. All functions return a truth value.
    * `is_near(p1: Position, p2: Position, radius: int)`: Determine if positions are close.
    * `any_goals(goals: Dict[str, Goal], category: Optional[str])`: Determines whether any remembered Goal matches the requested Category (or whether Memory contains any Goals when `category` is omitted).
    * `any_memories_visible(sprite: SpriteState, sprites: Dict[str, SpriteState], categories: List[GoalCategories])`

!!! warning "KeyErrors"
    When referencing `sprites[...]` via a Goal name, authors must use `sprites.get(sprite.goal.name)` to protect the runtime against `KeyErrors` from garbage-collected entities.

## Specification: Goal

*Goals* provide the seed (or energy) for transitions through Intentions Loops. A Goal is a Sprite's *modus operandi*, the abstract thing it pursues over the course of the [Engine Loop](./00-overview.md#component-engine). A Sprite's transition through Intentions is *in order* to achieve a Goal.

* `name`: Unique Identifier of the Goal.
* `category`: Category of the Goal. 
* `layer`: Layer of the Goal.
* `position`: Last-known position of the Goal. 

### Goal: Position 

When the Goal is within the `mutators.vision.radius`, the Sprite's Mmeory of this Position is updated every [Engine Loop](./00-overview.md#component-engine). Once the Goal exits the Sprites `mutators.vision.radius`, its Position becomes a static value that freezes on the last known Position of its Goal.

### Goal: Category

Goal Categories identify the class of outcomes a Sprite is pursuing:

* `position`: A spatial coordinate on a Layer. `name` is a synthetic label (e.g., `wander`).
* `door`: A portal used to transition between Layers. 
* `object`: A non-portal interactive Object (such as a Chest, Plate, or Sign). 
* `resource`: A biological or geological Resource targeted for harvesting.
* `property`: A structure targeted for construction or ownership.
* `target`: A Character pursued with hostile intent.
* `subject`: A Character pursued with passive or social intent.

### Goal: Satisfaction

* Location: `/src/data/configurations/automata/goals/main.yaml`

Goal lifecycle resolution is governed declaratively by the *Goal Resolution Matrix*, compiled and evaluated using the same propositional condition language as the [Intention Transition Matrix](#intention-transition-matrix).  The *Goal Resolution Matrix* classifies the active Goal by its Category, using three possible Outcomes in descending precedence.

**Semantics: Outcomes**

$$
\text{complete} \succ \text{layered} \succ \text{lost}
$$

1. `complete`: The Goal's objective has been achieved. Clears the active Goal.
2. `layered`: The Goal resides on a different Layer than the Sprite. Attempts to assign a prerequisite `door` Goal on the Sprite's current Layer, or clears the active Goal if no reachable portal exists.
3. `lost`: The Goal has failed, been invalidated, or been superseded by an Intention transition. Clears the active Goal.

Each Outcome dispatches across modular cognitive operators: Responses, Reflexes, Locators.

**Semantics: Responses**

Responses mutate [Sprite Memory](./02-sprites.md#model-memory).

* `forget`: Removes the Goal from episodic Memory.
* `store`: Marks the Goal dormant and stores it in episodic Memory.
* `push`: Pushes the Goal onto the Commitment Stack.
* `unwind`: Pops a suspended parent Goal from the Commitment Stack into dormant episodic Memory.

**Semantics: Reflexes**

Reflexes mutate [Sprite Psyche](./02-sprites.md#model-psyche).

* `confusion`: Attaches a `confusion` Expression to the Sprite's Psyche.

**Semantics: Locators**

Locators search the Sprite's active Layer for candidate Assets needed to satisfy an Outcome.

* `door`: Sensory recall of Doors.

## Module: AnimationMap

A Sprite's State is mapped onto an (Action, Direction) through an AnimationMap. AnimationMap statically ingests a Sprite State, applies mapping formulae and returns the mapped tuple.

See [Map Modules](./05-mechanics.md#modules-maps) for more information.

**Behavior: Player Preprocessing**

[Device Mappings](./02-sprites.md#device-contexts) are applied to convert Device Payloads to Intention and Goals, prior to the mapping of an Intention onto Sprite's (Action, Direction) Animation space.

### Mapping: Actions

The Action of a Sprite's AnimationState is a function of the Sprite's Intention and Equipment,

$$
f(\text{Intention}, \text{Equipment}) \to \text{Action}
$$

### Mapping: Directions

The Direction of a Sprite's AnimationState is a function of the Sprite's Position and Goal,

$$
f(\text{Position}, \text{Goal}) \to \text{Direction}
$$

## Mechanics: Intention Workflow

The (Intention, Goal, Trajectory) triad of a Sprite is managed across the application lifecycle by [Mechanics](./05-mechanics.md).

* [CognitionMechanics](./05-mechanics.md#intentional-mechanic-cognitionmechanics): Manages the Goal lifecycle. Evaluates environmental perceptions, consults Motivations and Psyche, sets and completes Goals, and manages Memory.
* [TransitionMechanics](./05-mechanics.md#intentional-mechanic-transitionmechanics): Manages Intention Transitions. Evaluates Transition conditions sequentially and shunts the Sprite to its next Intention state when criteria are satisfied.
    * [AnimationMaps](./05-mechanics.md#map-animation) are applied after each Transition to project the new Intention into its accompanying (Action, Direction).
* [NavigationMechanics](./05-mechanics.md#intentional-mechanic-navigationmechanics): Manages Trajectories. Queries the environment, evaluates obstacle geometry, and raycasts to maintain Trajectory.
* [MotionMechanics](./05-mechanics.md#core-mechanic-motionmechanics): Induces movement. Accelerates velocity vectors toward the Trajectory target.
* [SpatialMechanics](./05-mechanics.md#mechanics-spatial): Resolves collisions, combat, and interactions (e.g., passing through [Doors](./01-assets.md#object-doors) or opening a [Chest](./01-assets.md#object-chests)).

### Workflow Component: Cognition

[CognitionMechanics](./05-mechanics.md#intentional-mechanic-cognitionmechanics) manages the lifecycle of Sprite Goals across four stages each tick:

1.  **Sensory Processing**:
    * **Perception**: Updates same-Layer Memory coordinates within vision radius, wakes dormant Goals upon observing their target or an accessible Door, and evaluates the `frightened` trigger. Unseen Assets freeze at their last observed Layer and coordinates until re-observed.
2.  **Resolution**:
    * If the Sprite becomes `frightened` while pursuing another Goal, shelves the active Goal in Memory and clears it so the Sprite returns to `idle`.
    * Otherwise classifies the active Goal against the Goal Resolution Matrix and runs the configured Responses, Reflexes, and Goal lifecycle update for the matched Outcome.
3.  **Acquisition (`idle` Only)**: When the Sprite is in the `idle` Intention with no active Goal, Cognition selects the first Goal produced across ordered tiers:
    * **Survival Instincts**: Generates an `escape` Position Goal when `frightened`, taking precedence over Memory.
    * **Commitment Stack**: Pops the top suspended parent Goal from the LIFO Commitment Stack when non-empty.
    * **Episodic Memory**: Selects a non-dormant remembered Goal from episodic Memory.
    * **Drive Instincts**: Runs low-level Goal procedures (such as engaging a visible foe or speaking to a visible ally when dialogue is present).
    * **Exploratory Instinct**: Generates a bounded `wander` Position Goal when no higher tier produces a Goal.
4.  **Synchronization**:
    Updates visibility and checks cross-Layer Door subsumption for any Goal acquired during the current tick before TransitionMechanics runs.