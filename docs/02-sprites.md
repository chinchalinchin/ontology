# Ontology: Sprites

Everything that is rendered in Ontology is an Asset. Therefore, Sprites are Assets. Sprites, however, unique in their deployment, are the most important Asset to the game and thus have many unique attributes and methods; the gameplay loop can be understood mainly as a medium for the Sprite states to interact and react to one another, the Player included. 

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
* `velocity: Velocity`
* `layer: str`
* `intention: str` 
* `character: Character`
    * `strength: int`
    * `defense: int`
    * `speed: int` (Maximum magnitude of Velocity vector)
    * `impulse: int`: (Amount of acceleration applied to Velocity per game-tick)
* `animation: AnimationState`
    * `action: str`
    * `direction: str`
    * `frame: int`
* `inventory:`
    * `loot: Dict[str, int]`
    * `equipment:`
        * `armor: str`
        * `weapon: str`
        * `tool: str`
        * `utility: str`
        * `shield: str`
    * `wallet: int`
* `meters: List[Meter]`
    * `health: Meter` 
        * `current: int`
        * `maximum: int`
    * `magic: Meter`
        * `current: int`
        * `maximum: int`
* `mutators:`
    * `triggers: Dict[str, bool]`
    * `parameters: Dict[str, Dict[str, Union[int, double]]]`
* `memory:` 
    * `goal: Goal`
    * `prices: Dict[str, double]`
    * `relationships: Dict[str, str]`
    * `property: List[str]`
* `psyche`:
    * `expression: str`
    * `motivation: str`
    * `persona: str`: (Persona ley for Library Communication retrieval)
* `goal:`
    * `name: str`
    * `category: Enum[sprite, loot, wealth, property, position]`
    * `position: Position`

**Animation: StateAnimation**

- `state.animation.frame += 1`
- `if state.animation.frame >= properties.actions[state.animation.action].count: state.animation.frame = 0`

**Frame: SpriteFrame**

* `keys(id, animation): returns [ "{id}-{animation.action}-{animation.direction}-{animation.frame}" ] + [ <equipment-frames>]`
* `index(self, id, properties): returns { "{id}-{properties.actions.*}-{properties.actions.*.directions.*}-{properties.actions.*.count}": (0, 0, properties.dimension.w, properties.dimensions.l) }`

### Intentions

Intentions are an internal State data structure that governs a Sprite's core logic. 

See [Intentions documentation](./04-intentions.md) for more information.

### Goal

Goals are the current focus of the Sprite's path-finding and Direction resolution.

See [Goals documentation](./04-intentions.md) for more information.

### Meters

A Meter has a `current` value and a `maximum` value.

**Health**

TODO

**Magic**

TODO

### Character

- **Strength**: TODO
- **Defense**: TODO
- **Speed**: Speed determines the maximum magnitude of a Sprite's Velocity vector.
- **Impulse**: Impulse determines the rate of change of a Sprite's Velocity vector.

### Mutators

Mutators are attributes that alter Sprite behavior. They are functions of the Sprite's state, i.e. they are calculated from state attributes, not *primitive* state attributes themselves.

Mutators are *condition-driven*. They may also be *parameterized*; In other words, all Mutators are *conditional* but not all Mutators are parameterized. Parameters modulate the conditions underlying the Mutator calculation. Both Sprites and the [Player](#player) have Mutator fields, but only Sprites have parameterized Mutators; the Player Mutators are all purely driven by game logic. In other words, the Player Mutator triggers serve to flag the game-loop to apply trigger-specific procedures to the Player Asset, whereas Sprite Mutator triggers depend on the specific parameters unique to the Sprite's deployment. 

- Parameterized Mutators: `fear`, `vision`
- Conditional Mutators: `animated`, `dead`, `struck`

**Triggers**

- `trigger.animated`: Triggered if a Sprite is currently able to animate, i.e. increment its Frame. When this Mutator trigger is false, the Sprite does not receive animation updates from the game loop, e.g. if the user releases the right arrow button on the keyboard, leaving the Player in a `(walk, right)` state, then this mutator prevents the animation from progressing until the Player resumes pressing the right arrow button.
- `triggers.dead`: Triggered if a Sprite dies. This can only occur if the Sprite's `character.health.current = 0`
- `triggers.struck`: Triggered if a Sprite collides with a hitbox.
- `triggers.fear`: Triggered for the logical disjunction of the following conditions:
    - Triggered if Sprite's health dips below `fear.limit`
    - Triggered if Sprite is surrounded by more than `fear.enemy` enemies with the pixel distance of `fear.radius`.
- `triggers.vision`: Trigger if a Sprite is within visible distance of its Goal.

**Parameters**

- `parameters.fear.radius`: Radius of separation within which the Sprite triggers the `triggers.fear` mutator. Measured in pixels.
- `parameters.fear.limit`: Percentage of health below which Sprite triggers the `triggers.fear` mutator.
- `parameters.fear.enemy`: Number of enemies within the `parameters.fear.radius` that must be present to trigger the `triggers.fear` mutator.
- `parameters.vision.radius`: Radius of separation within which the Sprite triggers the `triggers.vision` mutator. Measured in pixels.

### Animation

Animations are tuples of (Action, Direction, Frame). Action and Direction were previously defined in the [Assets documentation](./01-assets.md).

### Psyche

The *Psyche* is an internal State data structure that governs a Sprite's ancillary Animation and Intention logic. All Sprite Assets besides the Player are given a Psyche state when deployed onto the Board. Psyche coordinates encode alterations and modulations of the Sprite state. The complete Psyche state for a Sprite is given by the tuple,

    (Persona, Expression, Motivation)

**Persona**

A Sprite persona is a data structure used to index Dialogue to a Sprite through the [Library](./08-plots.md#library). It can be thought of as the "personality" of the Sprite.

**Expression**

The Expression dimension alter the Sprite's appearnce by appending a Cursor Expression to the upper right corner of the Sprite's boundaries. Expressions can be visualized as speech bubbles containing icons that express the Sprite's internal state. Expressions are enumerated below,

- `agreement`
- `anger`
- `confusion`
- `curiosity`
- `disagreement`
- `loquacity`
- `surprise`
- `tired`

Over and above this modification to the Asset frame, the Expression dimension of a Sprite's Psyche can be thought of as the short-term memory or a buffer for dialogue the Sprite is about to transmit. This field holds the lexicon key that will be exchanged at the [Library](./08-plots.md#library) for content and rendered in a [Dialogue Menu](./06-widgets.md#menus) if the Player enters into the `speak` Intention. In addition, Sprites may enter into `speak` Intentions with other Sprites, but these events are not routed to [Menus](./06-widgets.md#menus). Instead, Sprite-to-Sprite Dialogue is used by the [RumorMechanics](./05-mechanics.md).

**Motivation**

Motivations are long-term state variables that are used to modulate the [Intention Transition matrix](./04-intentions.md). Motivations are enumerated below,

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
- `memory.rumors`: List of Lexicon keys the Sprite has heard through entering into the `speak` Intention.
- `memory.prices`:
- `memory.relationship`:
- `memory.property`:

**Prices**

Sprites keep a dictionary keyed by inventory loot for the loot's associated value, known as its Prices. This distionary represents the Sprite's "belief" regarding the fair value of its inventory when engaging in the `barter` Intention. This dictionary only has new keys appended to when the Sprite acquires a new item in its Inventory, e.g. the Sprite doesn't have "initial" Prices.

When two Sprites enter the `speak` Intention within a certain radius of each other, the `SpeechMechanic` does the following:

1. It averages the intersection of Prices. For example, if one Sprite has a price of 1 for Loot A and another has a price of 5 for Loot A, then the new price of Loot A for both Sprites will be (1 + 5)/2 = 3. It performs this calculation for every such Loot Key the Sprites have in common.
2. For each Sprite A and Sprite B, the prices of A subtracted (in the set-theoretic sense) from the prices of B is added to A and visa versa. In other words, if a Sprite converses with another Sprite that has Price information it does not possess, the `SpeechMechanic` will populate the Sprite's Prices.

**Property**

TODO

**Relationships**

TODO

**Rumors**

TODO

### Inventory

TODO

Equipment, while part of the Inventory, affects the rendering of the Sprite, and thus is covered in its own section, [Equipment](#equipment).

**Loot**

TODO

**Wallet**

TODO

## Equipment

Equipment is a grouping of several Sheet Asset Instances that share the common feature of having no state. Instead, their rendering is dependent on a Sprite state. Equipment is not an Asset Category in and of itself, but a label applied to particular Instances of Sheets in the Hierarchy. 

- Equipment: Armor, Tools, Utilities, Weapons

!!! important
    It assumed Equipment Sheets conform to the same (Action, Direction) grouping utilized by the [Sprite Sheets](./01-assets.md#sheets) equipping it. In other words, the frames coordinates and dimensions in an Equipment Sheet must correspond exactly to frames in a Sprite Sheet. This means Equipment frames may not be present in every frame. For example, the `longbow` only occupies the `(shoot, *)` rows of a Sheet, while all other rows of the `longbow` Asset file are blank.

### Equipment Frames

Equipment is a stateless Sheet Asset. It is not deployed onto the Board in a fashion like other Assets. Instead, only properties and frames are supplied for Equipment, i.e. Equipment has a Frame Recipe. This allows the Registry to index and load all Equipment Sheets. However, since Equipment does not possess a State Recipe and therefore does not possess State, it is not instantiated by the game engine when the state directory is traversed during the bootstrapping. Instead, Equipment frame keys are generated by SpriteFrames when Sprites have Equipment slotted into their `sprite.state.inventory.equipment`, e.g.

```yaml
# /src/data/state/<board-key>/sprite.state.inventory: 
equipment:
    armor: plate
    tool: shovel
    utility: lantern
    weapon: dagger
```

When this Sprite's Frame `keys()` interface is called, it will return a list of Frame keys that include Equipment Frame keys. The Screen will then retrieve each of these keys from the Registry and render them in the order they were received, thus stacking the Equipment on top of the Sprite who is equipping it.

!!! important
    Equipment must utilize the StateFrame to get indexed by the Registry.
    
### Equipment Animations

When Equipment is configured in the Sheet Property index file, the Equipment `actions` property determines which Actions in a Sprite's state will result in extra Frame Keys being appended to the `keys()` return result. 

Equipment is divided in four kinds: Armor, Tools, Utilities and Weapons. Each Kind modifies the gameplay in different ways. Just as active Equipment affects the Frame Keys returned by a Sheet Asset, it also affects state transitions. When a piece of Equipment is active, it directly determines which Animation Action state are enterable from the `attack` Intention (or the `build` Intention, etc.). The translation between Intention and Equipment into Animation is achieved through an [AnimationMap](./04-intentions.md#animationmap)

```python
sprite.state.animation.action = AnimationMap.action(
    sprite.state,
    board.equipment
)
```

!!! note
    Equipment properties are stored in the [Board](./00-overview.md#board) database.

## Player

A Player is a special type of Sprite Sheet Asset Instance. It may be thought of as a "*pseudo*"-Asset. It has no properties that differentiate it in the Hierarchy; Instead, it utilizes Sprite Sheet properties. It has own state and Intention management Mechanics. 

The Player Sprite Sheet is configured through the `player` Sprite Sheet. 

!!! important
    The `player` Sprite *must* be defined in `/src/assets/sheets/main.yml#sprites`.

**Taxonomy**

* `category: sheets`
* `instance: players`

**State: PlayerState**

* `position: Position`
* `velocity: Velocity`
* `layer: str`
* `meters:`
    * `health:` 
        * `current: int`
        * `maximum: int`
    * `magic: int`
        * `current: int`
        * `maximum: int`
* `character:`
    * `strength: int`
    * `defense: int`
    * `speed: int`
* `animation:`
    * `action: str`
    * `direction: str`
    * `frame: int`
* `goal: Goal`
* `intention: str` 
* `inventory:`
    * `loot: Dict[str, int]`
    * `equipment:`
        * `armor: str`
        * `weapon: str`
        * `tool: str`
        * `utility: str`
    * `wallet: int`

### Goals & Intentions

Players utilize the same information channel (e.g. Goals and Intentions) as Sprites for communicating state changes. 

- Goal: Players use a "pseudo" Goal to project their input into their intended direction of motion. For example, if a user pressed the right arrow, the Player Goal's shifted is shifted to the right. This in turn determines the direction of the Player's Velocity in their [kinematic sliding](./05-mechanics.md#core), i.e. $\text{player.velocity} \parallel \text{player.state.goal.position} - \text{player.state.position}$. 

### Devices

The [Board](./00-overview.md#board) contains a Device, which polls for user input. The PlayerMechanic uses a Mapping to translate the polling data into a [(Intention, Goal, Menu)](./04-intentions.md)-tuple. The [Mapping Configuration](./appendices/01-schemas.md#configuration-mapping) file provides a translation key between input state and game state.

**Keyboard**

The input state of the Keyboard is polled through SDL. Keyboard mappings correspond to SDL scancodes. See [SDL documentation](https://wiki.libsdl.org/SDL2/SDL_Scancode) for more information.

### Contexts

The Device class implements a stateful context flag (`world`, `menu`). Each Device mapping includes a nested mapping for each separate context. 

When the Board Menus (`board.menus`) are populated, Menu Mechanics toggles the device context, causing `poll()` to return Menu commands instead of [Intentions](./04-intentions.md).