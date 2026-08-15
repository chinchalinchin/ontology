# Ontology: Sprites

Everything that is rendered in Ontology is an Asset. Therefore, Sprites are Assets. Sprites, however, unique in their deployment, are the most important Asset to the gameplay loop and thus have many unique attributes and methods, as the gameplay loop can be understood mainly as a medium for the Sprite states to interact and react to one another, the Player included. 

**Player, NPCs and Enemies**

NPC and Enemy Sprites are undifferentiated. The Player Sprite is the only unique Sprite in terms of the gameplay loop, insofar the Player's state is determined by polling from the Player's input device, as opposed to the [Intention Transition Matrix](./04-intentions.md#transition-matrix). However, all state changes of Sprites and the Player are communicated through the medium of Intentions.

**Layers**

Sprite interactions are constrained by their Layers. Because Layers are superimposed coordinates, all interaction calculations should be separated by Layer, to avoid inter-Layer collisions.

## Overview 

**Taxonomy**

* `category: sheets`
* `instance: sprites`

**Properties: SheetProperties**

* `actions:` 
    * `count: int`
    * `directions:`
        * `row: int` 
* `dimensions: Dimensions`
* `hitboxes: List[Hitbox]` 
* `stack: List[str]`

**State: SpriteState**

* `position: Position`
* `layer: str`
* `meters: List[Meter]`
    * `health: Meter` 
        * `current: int`
        - `maximum: int`
    - `magic: Meter`
        - `current: int`
        - `maximum: int`
- `character: Character`
    - `strength: int`
    - `defense: int`
    - `speed: int`
- `animation: AnimationState`
    - `action: str`
    - `direction: str`
    - `frame: int`
- `intention: str` 
- `inventory:`
    - `loot: Dict[str, int]`
    - `equipment:`
        `armor: str`
        `weapon: str`
        `tool: str`
        `utility: str`
    - `wallet: int`
- `mutators:`
    - `triggers: Dict[str, bool]`
    - `parameters: Dict[str, Dict[str, Union[int, double]]]`
- `memory:` 
    - `goal: Goal`
    - `communication: List[str]` 
    - `prices: Dict[str, double]`
    - `relationships: Dict[str, str]`
    - `property: List[str]`
- `goal:` 
    - `name: str`
    - `category: Enum[sprite | object | loot]`
    - `position: Position`

**Animation: StateAnimation**

- `state.animation.frame += 1`
- `if state.animation.frame >= properties.actions[state.animation.action].count: state.animation.frame = 0`

**Frame: SpriteFrame**

* `keys(id, animation): returns [ "{id}-{animation.action}-{animation.direction}-{animation.frame}" ] + [ <equipment-frames>]`
* `index(self, id, properties): returns { "{id}-{properties.actions.*}-{properties.actions.*.directions.*}-{properties.actions.*.count}": (0, 0, properties.dimension.w, properties.dimensions.l) }`

### Intentions

*Intentions* are an internal State data structure that governs a Sprite's core logic. 

See [Intentions](./04-intentions.md) for more information.

### Goal

*Goals* are the current focus of the Sprite's path-finding and Direction resolution.

See [Goals documentation](04-intentions.md) for more information.

### Meters

TODO

**Health**

TODO

**Magic**

TODO

### Character

**Strength**

TODO

**Defense**

TODO

**Speed**

TODO

### Mutators

*Mutators* are attributes that alter Sprite behavior. They are functions of the Sprite's state, i.e. they are calculated from state attributes, not *primitive* state attributes themselves.

**Triggers**

- `trigger.animated`: Triggered if a Sprite is currently able to animate, i.e. increment its Frame. When this Mutator trigger is false, the Sprite does not receive animation updates from the game loop, e.g. if the user releases the right arrow button on the keyboard, leaving the Player in a `(walk, right)` state, then this mutator prevents the animation from progressing until the Player resumes pressing the right arrow button.
- `triggers.dead`: Triggered if a Sprite dies. This can only occur if the Sprite's `character.health.current = 0`
- `triggers.struck`: Triggered if a Sprite collides with a hitbox.
- `triggers.frightened`: Triggered for the logical disjunction of the following conditions:
    - Triggered if Sprite's health dips below `frightened.limit`
    - Triggered if Sprite is surrounded by more than `frightened.enemy` enemies with the pixel distance of `frightened.radius`.
- `triggers.vision`: Trigger if a Sprite is within visible distance of its Goal.

**Parameters**

- `parameters.frightened.radius`: Radius of separation within which the Sprite triggers the `triggers.frightened` mutator. Measured in pixels.
- `parameters.frightened.limit`: Percentage of health below which Sprite triggers the `triggers.frightened` mutator.
- `parameters.frightened.enemy`: Number of enemies within the `parameters.frightened.radius` that must be present to trigger the `triggers.frightened` mutator.
- `parameters.vision.radius`: Radius of separation within which the Sprite triggers the `triggers.vision` mutator. Measured in pixels.

### Animation

**Action, Direction**

Action and Direction were previously defined in the [Assets documentation](./01-assets.md), since these two state attributes determine the animation frame currently being rendered in the gameloop. 

As a reminder, the default Actions and Directions for the game engine (and LPC specification) are given below,

- Actions: `cast, thrust, walk, slash, shoot, die`
- Directions: `up, down, left, right`

### Psyche

The *Psyche* is an internal State data structure that governs a Sprite's ancillary Animation logic. All Sprite Assets besides the Player are given a Psyche state when deployed onto the Board. Psyche coordinates encode alterations to be applied to the Sprite Sheet's frame. The complete Psyche state for a Sprite is given by the tuple,

    (Communcation, Expression, Motivation)

**Communication**

The Communication dimension of a Psyche can be thought of as the short-term memory or a buffer for Dialogue the Sprite is about to display. It holds the Communication key for the current Plot state that will be rendered if the Sprite enters into the `speak` Intention.

**Expression**

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

**Motivation**

Motivations are long-term state variables that are used to modulate the [Intention Transition matrix](./04-intentions.md).

The default Motivations are enumerated below,

- `conquest`
- `profit`
- `survival`
- `love`
- `revenge`
- `rebellion`
- `safety`

### Memory

*Memory* is a data structure that stores long-term state while the current Intention and Goal states are focused elsewhere. 

- `memory.goal`: Remember Goal. A Sprite can store its overarching goal in its Memory while pursuing a sub Goal dictated by its Intention and Motivation.
- `memory.communications`: List of saved dialogue.
- `memory.prices`:
- `memory.relationship`:
- `memory.property`:

**Communications**

Under certain conditions based on the Sprite's Intention, the Sprite may emit a Communication through the `speak` Intention. For example, a Sprite in the `mock` Intention might receive a Communication key `insult`. This key gets stored at the *beginning* (0 index) of the `memory.communications` list. 

When a Sprite with a non-empty `memory.communications` enters into the `speak` Intention, the gameplay loop will then take the first entry out of this Sprites `memory.communications` list, delete it from this list and place it in the `psyche.communication` cell. 

!!! important
    The last entry in `memory.communications` is *never* deleted. The entry is termed *unforgettable*.

When a Sprite with a non-null `psyche.communication` enters into the `speak` Intention, the gameplay loop will then take this entry and submit it to a Dialogue widget to be displayed. The entry thus displayed will be deleted from the `intention.communication` cell.

**Prices**

Sprites keep a dictionary keyed by inventory loot for the loot's associated value, known as its Prices. This distionary represents the Sprite's "belief" regarding the fair value of its inventory when engaging in the `barter` Intention. This dictionary only has new keys appended to when the Sprite acquires a new item in its Inventory, e.g. the Sprite doesn't have "initial" Prices.

When two Sprites enter the `speak` Intention within a certain radius of each other, the `SpeechMechanic` does the following:

1. It averages the intersection of Prices. For example, if one Sprite has a price of 1 for Loot A and another has a price of 5 for Loot A, then the new price of Loot A for both Sprites will be (1 + 5)/2 = 3. It performs this calculation for every such Loot Key the Sprites have in common.
2. For each Sprite A and Sprite B, the prices of A subtracted (in the set-theoretic sense) from the prices of B is added to 
A and visa versa. In other words, if a Sprite converses with another Sprite that has Price information it does not possess, the `SpeechMechanic` will populate the Sprite's Prices.

**Relationships**

TODO

**Property**

TODO

### Inventory

TODO

Equipment, while part of the Inventory, affects the rendering of the Sprite, and thus is covered in its own section, [Equipment](#equipment).

**Loot**

TODO

**Wallet**

TODO

## Equipment

- Equipment Sheets: `/src/assets/sheets/equipment/<instance-key>/<equipment-id>.png`

Equipment sheets are superimposed onto the Sprite Sheets based on the active Equipment keys in `sprite.state.inventory.equipment`, e.g.

```yaml
# /src/data/state/<board-key>/sprite.state.inventory: 
equipment:
    armor: plate
    tool: shovel
    utility: lantern
    weapon: dagger
```

Each piece of Equipment is associated with an (Action, Direction) grouping. When a piece of Equipment is active, the Sheet Asset corresponding to the Equipment will be stacked on top of the Sprite's Asset stack. The Animation state associated with a piece of Equipment is configured by [the Equpiment Matrix](#equipment-matrix) file.

Equipment is divided in four *Categories*: Armor, Tools, Utilities and Weapons. Each Kind modifies the gameplay in different ways. 

When a piece of Equipment is active, it affects what Animation Action state results when the Sprite enters into the `attack` Intention. The translation between Intention and Equipment into Animation is achieved through an [AnimationMap](./04-intentions.md#animationmap)

```python
sprite.state.animation.action = AnimationMap.action(
    sprite.state,
    board.equipment
)
```

!!! note
    Equipment properties are stored in the [Board](./00-overview.md#board) database.

### Equipment Animation Sheets

It assumed Equipment sheets conform to the same LPC-derived (Action, Direction) grouping described in previous sections (e.g. [Sheets](#action-direction)). In other words, the frames in an Equipment sheet correspond exactly to frames in a Sprite Sheet. However, Equipment frames may not be present in every frame.

The catchall quantifier `all` implies the Equipment sheet has frames associated with all (Action, Direction) row groups in a sheet. For example `lantern` has a frame for each (Action, Direction) frame (i.e. the `lantern` equipment is present in all (Action, Direction) rows when activated), whereas `shortsword` only has frames in the `(slash, *)` grouping (i.e. the `shortsword` equipment is present in *only* the rows with `action == slash`.).

Equipment rendering adheres to the **Registry Miss** pattern. It is dictated by the `SheetProperties.actions` configured in the Asset directory. If an equipment does not possess a specific action, its omission from the rendering pipeline is handled implicitly by the `Registry` returning `None`. This allows for robust and sparse equipment sheets that only render when they possess the relevant animation rows without additional filtering logic.

**Equipment Stacks**

Equipment Sheets may be stacked like Sprite Sheet [Personas](#personas) to form a piece of Equipment. The `stack` for a piece of Equipment is given in the Equipment configuration file.