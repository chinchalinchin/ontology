# Ontology: Sprites

Everything that is rendered in Ontology is an Asset. Therefore, Sprites are Assets. Sprites, however, unique in their deployment, are the most important Asset to the gameplay loop and thus have many unique attributes and methods, as the gameplay loop can be understood mainly as a medium for the Sprite states to interact and react to one another, the Player included. 

**LPC Frames**

The LPC specification defines the following frames per Sprite Action,

- `cast`: Count = 7
- `thrust`: Count = 8
- `walk`: Count = 9
- `slash`: Count = 6
- `shoot`: Count = 13
- `die`: Count = 6

The game engine use the LPC as its default setting.

**Player, NPCs and Enemies**

NPC and Enemy Sprites are undifferentiated. The Player Sprite is the only unique Sprite in terms of the gameplay loop, insofar the Player's Intent is determined by polling from the Player's input device. See [Intents documentation](./02-messages.md#intents) for more information on Intents. See [Player documentation](./04-player.md) for more information on the Player.

## Overview 

**Properties**

- AssetKey: `str`

**State**

- Name: `str`
- Position: `Tuple[int, int]`
- Layer: `str`
- Meters
    - Health: 
        - Current: `int`
        - Maximum: `int`
    - Magic: `int`
        - Current: `int`
        - Maxium: `int`
- Character
    - Strength: `int`
    - Defense: `int`
    - Speed: `int`
- Intention: 
    - Action: `str`
    - Direction: `str`
    - Extension: `str`
    - Disposition: `str`
    - Motvation: `str`
    - Expression: `str`
- Inventory:
    - Loot: `Dict[str, int]`
    - Equipment: `Dict[str, bool]`
    - Wallet: `int`
- Mutators:
    - Triggers: `Dict[str, bool]`
    - Parameters: `Dict[str, Dict[str, Union[int, double]]]`
- Memory: 
    - Goal:
        - AssetName: `str`
        - Intention:
            - Action: `str`
            - Extension: `str`
    - Communication: `List[str]` 
- Goal: 
    - AssetName: `str`
    - Intension:
        - Action: `str`
        - Extension: `str`
- Frame: `int`

Frame is an integer that tracks the current animation frame. It's maximum value is dependent on the Action state. For example, if a Sprite is in the `walk` Action state, then Frame will cycle from 0 to `walk.MaxFrames`.

**Calculated State**

- FrameKey: `AssetKey + Intention.Direction + Intention.Action + Frame`

**Methods**

- `animate() -> None`: Increments Frame, if `triggers.animated == true`.
- `poll() -> Intent`: Returns the Sprite's current Intent.
- `update(intent: Intent) -> None`: Updates the Sprite's current Intent.
- `achieved(goal_asset: Asset) -> Union[Intent, None]`: Returns Goal Intention if Goal achieved, None otherwise.

## Meters

TODO

### Health

TODO

### Magic

TODO

## Character

### Strength

TODO

### Defense

TODO

### Speed

TODO

## Mutators

*Mutators* are attributes that alter Sprite behavior. They are functions of the Sprite's state, i.e. they are calculated from state attributes, not *primitive* state attributes themselves.

### Triggers

- `trigger.animated`: Triggered if a Sprite is currently able to animate, i.e. increment its Frame. When this Mutator trigger is false, the Sprite does not receive animation updates from the game loop, e.g. if the user releases the right arrow button on the keyboard, leaving the Player in a `(walk, right)` state, then this mutator prevents the animation from progressing until the Player resumes pressing the right arrow button.
- `triggers.dead`: Triggered if a Sprite dies. This can only occur if the Sprite's `character.health.current = 0`
- `triggers.struck`: Triggered if a Sprite collides with a hitbox.
- `triggers.frightened`: Triggered for the logical disjunction of the following conditions:
    - Triggered if Sprite's health dips below `frightened.limit`
    - Triggered if Sprite is surrounded by more than `frightened.enemy` enemies with the pixel distance of `frightened.radius`.
- `triggers.vision`: Trigger if a Sprite is within visible distance of its Goal.

### Paramaeters

- `parameters.frightened.radius`: Radius of separation within which the Sprite triggers the `triggers.frightened` mutator. Measured in pixels.
- `parameters.frightened.limit`: Percentage of health below which Sprite triggers the `triggers.frightened` mutator.
- `parameters.frightened.enemy`: Number of enemies within the `parameters.frightened.radius` that must be present to trigger the `triggers.frightened` mutator.
- `parameters.vision.radius`: Radius of separation within which the Sprite triggers the `triggers.vision` mutator. Measured in pixels.

## Intentions

*Intentions* are an internal State data structure that governs a Sprite's core logic. The two most basic Intentions, Direction and Action, determine the current animation of the Sprite. All Sheet Assets, when deployed on a Board, are given an Intention state with a Direction and Action that is updated by the gameplay loop. Sprites, however, have a more complex internal state, represented by the other attributes of Intentions, which in turn provides a greater variety of behavior and enhanced possibility of emergent gameplay.

## Action, Directions

Action and Direction were previously defined in the [Assets documentation](./01-assets.md), since these two Intention states determine the animation frame currently being rendered in the gameloop. 

As a reminder, the default Actions and Directions for the game engine (and LPC specification) are,

- Actions: `cast, thrust, walk, slash, shoot, die`
- Directions: `up, down, left, right`

!!! note 
    In the LPC specification, the `thrust` Action plays double-duty for spears and shovels. The spear is a Weapon, whereas the shovel is Equipment. With LPC assets, the animations of these pieces of Equipment is governed by the `thrust` state.

!!! note
    Any Actions defined in the `/src/assets/sheets/**.png` file rows must have its Action key entered in `/src/data/intents/main.yaml#actions` file to register as an Action enterable from a Disposition.

The complete Intention State for a Sprite is given by the tuple,

    (Action, Direction, Extension, Disposition, Motivation, Expression)

The attributes of Intention are discussed in more detail below.

### Extension

A Extension is a pseudo-state that does not factor into the Asset frame key calculation directly. It may indirectly alter the Sprite state changes or other properties of the Sprites, e.g. entering into the `sprint` Extension state increases the velocity of the `(walk, *)` states, but does not factor into the animation speed or the frame indexing scheme. Similarly, entering into the `interact` Extension state does not alter the Sprite's current animation in any way, but instead allows, for example, the Sprite to open a Chest or Door.

The default Extension states are enumerated below,

- `interact`
- `speak`
- `sprint`

### Disposition

!!! importatnt
    The Player state does not observe the Disposition Transition matrix; the Player state is entirely managed by polling the user's input and mapping input to Instructions (a subset of Intents). See [Player documentation](./04-player.md) for more information on the Player. See [Instructions documentation](./02-messages.md#instructions) for more information on Instructions.
    
A Disposition determines which Actions are currently reachable for a Sprite. In other words, a Sprite's *Disposition* determines its Disposition Transition matrix, covered below. Dispositions are configurable, but since they are an essential piece of gameplay data, a default Disposition configuration has been provided. The default Dispositions are enumerated below.

1. `attack`
    - Reachable Actions: `cast, thrust, slash, shoot`
    - Reachable Dispostions: `attack, hunt, loot`
    - Reachable Extensions: None
2. `attract`
    - Reachable Actions: `walk`
    - Reachable Dispostions: `barter, communicate`
    - Reachable Extensions: `interact`
3. `barter`
    - Reachable Actions: None
    - Reachable Dispostions: None
    - Reachable Extensions: None
4. `communicate`
    - Reachable Actions: None
    - Reachable Dispostions: None
    - Reachable Extensions: None
5. `escape`
    - Reachable Actions: `walk`
    - Reachable Dispostions: None
    - Reachable Extensions: None
6. `find`
    - Reachable Actions: `walk, thrust`
    - Reachable Dispostions: None
    - Reachable Extensions: None
7. `follow`
    - Reachable Actions: `walk`
    - Reachable Dispostions: None
    - Reachable Extensions: None
8. `idle`
    - Reachable Actions: `walk`
    - Reachable Dispostions: None
    - Reachable Extensions: None
9. `interact`
    - Reachable Actions: None
    - Reachable Dispostions: None
    - Reachable Extensions: None
10. `loot` 
    - Reachable Actions: None
    - Reachable Dispostions: None
    - Reachable Extensions: None
11. `mock`
    - Reachable Actions: None
    - Reachable Dispostions: None
    - Reachable Extensions: None
12. `recoil`
    - Reachable Actions: `die`
    - Reachable Dispostions: None
    - Reachable Extensions: None
13. `return`
    - Reachable Actions: `walk`
    - Reachable Dispostions: `find`
    - Reachable Extensions: None
14. `threaten`
    - Reachable Actions: None
    - Reachable Dispostions: `attack`
    - Reachable Extensions: None
15. `wander`
    - Reachable Actions: `walk`
    - Reachable Dispostions: None
    - Reachable Extensions: None

**Default Disposition Transition Matrix**

Provided below is the Disposition Transition Matrix bundled with the application by default,

```yaml
--8<-- "docs/.static/yaml/examples/default-disposition-matrix.yaml"
```

**Transition Scripting**

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
- `sprite.<state>`: self variable
- `sprites[<sprite-name>].<state>`: Sprites variable

In the default Disposition Transition matrix given above, the transition from `attack` to `hunt` is conditional on the following,

```yaml
- not sprite.goal.target
- sprite.memory.goal.target.category == 'sprite'
```

`sprite` is a reference to the Sprite which is currently processing the given Disposition. Thus, the Sprite's Disposition state will transition to `hunt` if the Sprite currently does not have a target, but remembers having a target of category `sprite`.

!!! note
    The expression `not sprite.intention.goal.target` is a *truthy* expression, i.e. it is to be interpretted as existential claim. In other words, this expression evaluates to `true` if `sprite.intention.goal.target` does not exist. If the expression involves a List, e.g. `sprite.memory.communications`, this expression evaluates to `true` in the event it has more than 0 entries.

In another example, the transition from `attack` to `loot` in the default Disposition Transition matrix is given by,

```yaml
- sprites[sprite.target.name].mutators.triggers.dead
```

`sprites` is a reference to a dictionary of all ingame Sprites keyed by their identifying and unique `name`, which provides access to their state attributes.

Notice in the example there is a self-entrant transition. A Sprite with an `attack` Disposition can re-enter the `attack` Disposition conditional on the Sprite still having a target,

```yaml 
- sprite.goal.target.category == 'sprite'
```

!!! important
    The conditions for a Disposition transition are evaluated in the order they specified! In the given example, if `sprite.goal.target.category == 'sprite'`, none of the other conditions for Disposition transitions are evaluated and the Disposition transitions back into `attack`.

### Motivation

Motivations are long-term variables that modulate the Disposition Transition matrix.

The default Motivations are enumerated below,

- `conquest`
- `profit`
- `survival`
- `love`
- `revenge`
- `rebellion`

### Communication

The Communication dimension of an Intention can be thought of as the short-term memory or a buffer for Dialogue the Sprite is about to display. It holds the Communication key for the current Plot state that will be rendered if the Sprite enters into the `speak` Extension.

### Expression

The Expression dimension alter the Sprite's apperance by appending a Cursor Expression to the upper right corner of the Sprite's boundaries. Expressions can be visualized as speech bubbles containing icons that express the Sprite's internal state. 

The default Expressions are enumerated below,

- `agreement`
- `anger`
- `confusion`
- `curiosity`
- `disagreement`
- `loquacity`
- `surprise`
- `tired`

## Goal

*Goals* are provide the seed (or energy) for transitions through Dispositions and the application of Motivations to modulate said transitions. A Goal is a Sprite's *modus operandi*, the abstract thing it pursues over the course of the game loop. A Sprite's transitions through Dispositions is *in order* to achieve a Goal.

- `name`: Unique Identifier of Asset Goal.
- `intention`:
    - `extension`: Extension to be applied when Goal achieved .
    - `action`: Action to be applied when Goal achieved.

When a Sprite has Goal, it will seek out (path-find) its way to the AssetName, provided the AssetName is within `mutators.parameters.vision.radius`.

## Memory

*Memory* is a data structure that stores long-term state while the current Intention and Goal states are focused elsewhere. A Sprite can store its overarching goal in its Memory while pursuing a sub Goal dictated by its Disposition and Motivation.

- `memory.goal`: 
    - `name`: Unique Identifer of Asset Goal.
    - `intention`:
        - `extension`: Extension to be applied when Goal achieved. 
        - `action`: Action to be applied when Goal achieved.
- `memory.communications`: List of saved dialogue.

### Communications

Under certain conditions based on the Sprite's Disposition, the gameplay loop delivers to the Sprite an Intent containing a Communication key. For example, a Sprite in the `mock` Disposition might receive a Communication key `insult`. This key gets stored at the *beginning* (0 index) of the `memory.communications` list. 

When a Sprite with a non-empty `memory.communications` enters into the `communicate` Disposition, the gameplay loop will then take the first entry out of this Sprites `memory.communications` list, delete it from this list and place it in the `intention.communication` cell. 

!!! important
    The last entry in `memory.communications` is *never* deleted. The entry is termed *unforgettable*.

When a Sprite with a non-null `intention.communication` enters into the `speak` Extension, the gameplay loop will then take this entry and submit it to a Dialogue widget to be displayed. The entry thus displayed will be deleted from the `intention.communication` cell.

## Inventory

TODO