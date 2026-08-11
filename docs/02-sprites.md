# Ontology: Sprites

Everything that is rendered in Ontology is an Asset. Therefore, Sprites are Assets. Sprites, however, unique in their deployment, are the most important Asset to the gameplay loop and thus have many unique attributes and methods, as the gameplay loop can be understood mainly as a medium for the Sprite states to interact and react to one another, the Player included. 

**Player, NPCs and Enemies**

NPC and Enemy Sprites are undifferentiated. The Player Sprite is the only unique Sprite in terms of the gameplay loop, insofar the Player's state is determined by polling from the Player's input device, as opposed to the Disposition Transition Matrix. However, all state changes of Sprites and the Player are communicated through the medium of Intentions.

- See [Player](./03-player.md) documentation for more information on the Player.
- See  [Intentions](./04-intentions.md) documentation for more information on the Intention Mechanics. 

**Layers**

Sprite interactions are constrained by their Layers. Because Layers are superimposed coordinates, all interaction calculations should be separated by Layer, to avoid inter-Layer collisions.

## Overview 

**Taxonomy**

- `category: sheet`
- `instance: sprite`

**Properties**

- `actions:` 
    - `count: int`
    - `directions:`
        - `row: int`
        - `attackboxes: List[Attackbox]` 
* `dimensions: Dimensions`
* `hitboxes: List[Hitbox]` 

**State**

- `name: str`
- `position: Position`
- `layer: str`
- `meters:`
    - `health:` 
        - `current: int`
        - `maximum: int`
    - `magic: int`
        - `current: int`
        - `maximum: int`
- `character:`
    - `strength: int`
    - `defense: int`
    - `speed: int`
- `animation:`
    - `action: str`
    - `direction: str`
    - `frame: int`
- `intention:` 
    - `extension: str`
    - `disposition: str`
    - `motivation: str`
    - `expression: str`
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
    - `prices: `Dict[str, double]`
- `goal:` 
    - `name: str`
    - `category: Enum[sprite | object | loot]`
    - `intention:`
        - `action: str`
        - `extension: str`

`state.animation.frame` is an integer that tracks the current animation frame. Its maximum value is dependent on the Action state and its corresponding properties. In other words, if a Sprite is in the `state.animation.action` Action state, then Frame will cycle from 0 to `properties.actions[state.animation.action].count`.

**Frame**

- `key(asset, animation): asset + animation.direction + animation.action + animation.frame`

### Schema

- Location: `/src/data/intentions/main.yaml`

```yaml
--8<-- "docs/.static/yaml/data-intentions.yaml"
```

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

### Parameters

- `parameters.frightened.radius`: Radius of separation within which the Sprite triggers the `triggers.frightened` mutator. Measured in pixels.
- `parameters.frightened.limit`: Percentage of health below which Sprite triggers the `triggers.frightened` mutator.
- `parameters.frightened.enemy`: Number of enemies within the `parameters.frightened.radius` that must be present to trigger the `triggers.frightened` mutator.
- `parameters.vision.radius`: Radius of separation within which the Sprite triggers the `triggers.vision` mutator. Measured in pixels.

## Animation

### Action, Direction

Action and Direction were previously defined in the [Assets documentation](./01-assets.md), since these two state attributes determine the animation frame currently being rendered in the gameloop. 

As a reminder, the default Actions and Directions for the game engine (and LPC specification) are given below,

- Actions: `cast, thrust, walk, slash, shoot, die`
- Directions: `up, down, left, right`

The frames per Action Group are given below,

- `cast`: Count = 7
- `thrust`: Count = 8
- `walk`: Count = 9
- `slash`: Count = 6
- `shoot`: Count = 13
- `die`: Count = 6

!!! note 
    In the LPC specification, the `thrust` Action plays double-duty for spears and shovels. The spear is a Weapon, whereas the shovel is Equipment. With LPC assets, the animations of these pieces of Equipment is governed by the `thrust` state.

## Intentions

!!! important
    The Player state does not observe the Disposition Transition matrix; the Player state is managed by polling the user's input and mapping input to intention. See [Player documentation](./03-player.md) for more information on the Player.

*Intentions* are an internal State data structure that governs a Sprite's core logic. All Sprite Assets, when deployed on a Board, are given, along with an Animation state, an Intention state that is updated by the gameplay loop. Intention coordinates represent a node in the Sprite "finite automaton", the Disposition Transition Matrix.

The complete Intention State for a Sprite is given by the tuple,

    (Disposition, Expression, Extension, Motivation, Communication)

Intentions are configured through the `/src/data/intentions/main.yaml` file.

See [Intentions](./04-intentions.md) for more information.

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

## Memory

*Memory* is a data structure that stores long-term state while the current Intention and Goal states are focused elsewhere. A Sprite can store its overarching goal in its Memory while pursuing a sub Goal dictated by its Disposition and Motivation.

- `memory.goal`: 
    - `name`: Unique Identifer of Asset Goal.
    - `intention`:
        - `extension`: Extension to be applied when Goal achieved. 
        - `action`: Action to be applied when Goal achieved.
- `memory.communications`: List of saved dialogue.

### Communications

Under certain conditions based on the Sprite's Intention, the Sprite may emit a Communication through the `speak` Extension. For example, a Sprite in the `mock` Disposition might receive a Communication key `insult`. This key gets stored at the *beginning* (0 index) of the `memory.communications` list. 

When a Sprite with a non-empty `memory.communications` enters into the `communicate` Disposition, the gameplay loop will then take the first entry out of this Sprites `memory.communications` list, delete it from this list and place it in the `intention.communication` cell. 

!!! important
    The last entry in `memory.communications` is *never* deleted. The entry is termed *unforgettable*.

When a Sprite with a non-null `intention.communication` enters into the `speak` Extension, the gameplay loop will then take this entry and submit it to a Dialogue widget to be displayed. The entry thus displayed will be deleted from the `intention.communication` cell.

### Prices

Sprites keep a dictionary keyed by inventory loot for the loot's associated value, known as its Prices. This distionary represents the Sprite's "belief" regarding the fair value of its inventory when engaging in the `trade` extension. This dictionary only has new keys appended to when the Sprite acquires a new item in its Inventory, e.g. the Sprite doesn't have "initial" Prices.

When two Sprites enter the `speak` Extension within a certain radius of each other, the `SpeechMechanic` does the following:

1. It averages the intersection of Prices. For example, if one Sprite has a price of 1 for Loot A and another has a price of 5 for Loot A, then the new price of Loot A for both Sprites will be (1 + 5)/2 = 3. It performs this calculation for every such Loot Key the Sprites have in common.
2. For each Sprite A and Sprite B, the prices of A subtracted (in the set-theoretic sense) from the prices of B is added to 
A and visa versa. In other words, if a Sprite converses with another Sprite that has Price information it does not possess, the `SpeechMechanic` will populate the Sprite's Prices.

## Inventory

TODO

Equipment, while part of the Inventory, affects the rendering of the Sprite, and thus is covered in its own section, [Equipment](#equipment).

### Loot

TODO

### Wallet

TODO

## Equipment

- Equipment Sheets: `/src/assets/sheets/sprites/equipment/<kind-key>/<equipment-key>.png`

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

Equipment is divided in four *Kinds*: Armor, Tools, Utilities and Weapons. Each Kind modifies the gameplay in different ways. 

When a piece of Equipment is active, it affects what Animation state results when the Sprite enters into the `attack` Disposition. The translation between Disposition and Animation

```python
# pseudocode
if sprite.state.intention.disposition == 'atack':
    sprite.state.animation = DispositionResolver.animation(
        sprite.state.inventory,
        equipment.properties
    )
```

### Equipment Matrix 

- Location: `/src/data/equipment/main.yaml`

**Schema**

```yaml
--8<-- "docs/.static/yaml/data-equipment.yaml"
```

**Default Equipment Matrix**

```yaml
--8<-- "docs/.static/yaml/data-equipment.yaml"
```

## Personas

Personas are stacks of superimposed Sprite Sheets. They are assembled in the [Registry](./00-overview.md#registry) using the `compositions` property in the configuration file during the [application bootstrap](./06-architecture.md). The assembled Persona Sheet is saved as Sprite Sheet, using the Persona key as the Asset key. In this way, Sprites can specify their Persona through the Asset Key property. In other words, once assembled, Personas are effectively new "virtualized" Assets.

Personas are assembled from a Base Sheet and Feature Sheets. The Base Sheet is the background of the resultant Sheet. Feature Sheets are pasted over the Base in the order they are specified.

!!! note
    It is assumed the Base and Feature Sheets conform to the same (Action, Direction) row mapping as the Sprite Sheets themselves. As always, the game engine assumes and implements the LPC specification by default.

- Base Sheets: `/src/assets/sheets/sprites/base/<base-key>.png`
- Feature Sheets: `/src/assets/sheets/sprites/features/<feature-key>.png`
