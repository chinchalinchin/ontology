# Ontology: Assets

!!! note
    LPC Assets are bundled with the application by default.

This document serves to specify the Asset architecture and provide key definition for game terminology.

!!! note "Definition"
    An asset is an image or sound file.

The Asset directory is organized as follows,

```bash
assets % tree -L 2
.
├── cursors
│   ├── expressions
│   ├── main.yaml
│   └── projectiles
├── effects
│   ├── main.yaml
│   ├── persistent
│   └── temporary
├── menu
│   └── main.yaml
├── objects
│   ├── chests
│   ├── crates
│   ├── doors
│   ├── gates
│   ├── main.yaml
│   └── plates
├── sheets
│   ├── main.yaml
│   ├── pixies
│   └── sprites
├── sounds
│   ├── main.yaml
│   ├── music
│   └── speech
└── tiles
    ├── irregular
    ├── main.yaml
    └── regular

```

The `main.yaml` files in each subdirectory conform to the [Asset property schemas](https://www.google.com/search?q=%23schemas).

**Keys**

Keys are used to map assets to images loaded into the [registry](https://www.google.com/search?q=./00-overview.md%23registry), to ensure each Asset is only loaded into the memory once, no matter how many times it is rendered in a single frame. In other words, keys uniquely identify a physical Asset, but not in-game objects.

**Properties vs. State**

*Properties* are static and never changed by ingame mechanics. Properties determine the immutable characteristics of an ingame Asset, e.g. dimensions and hitboxes. They are loaded side-by-side with the asset files in the `/src/assets/**` directory.

*State* is dynamic and is changed by ingame mechanics. State determines the mutable characteristics of an ingame Asset, e.g. the current position of an ingame Asset. All Assets have a *position*, *dimension* and a *layer* mutable state. Position and dimension are given as Cartesian coordinates, whereas Layer is a categorical variable.

Both Properties and State are explicitly typed using strict **Pydantic Models** (e.g., `SpriteProperties`, `SpriteState`). This separation of data guarantees memory safety and allows the engine to compile smoothly into fast C-structs via Cython.

!!! note "Layers"
The concept of a Layer is defined more explicitly in [World documentation](https://www.google.com/search?q=./00-overview.md%23world). It suffices to think of Layers as floors in a house, i.e. where each floor has the same area and similar topology, but occupies a different height. In-game, Layers are traversed by the Player interacting Doors.

**Names**

Names are used to uniquely identify an ingame entity. A single Asset may have multiple Names. A Name corresponds to a particular deployment of an Asset onto a Board. A Name is part of an Asset's state.

**Asset Architecture**

To ensure high performance and compatibility with Cython (which strictly requires single-inheritance for C-level extensions), Ontology abandons deep object-oriented inheritance trees in favor of **Composition**.

Every physical entity in the game is an instance of the unified `Asset` class (or a lightweight single-inheritance subclass). The distinction between a "Tile", a "Gate", and a "Sprite" is determined entirely by the data models and stateless behaviors injected into them:

1. **Properties:** A Pydantic model defining immutable data (e.g., `TileProperties`, `ObjectProperties`).
2. **State:** A Pydantic model defining mutable data (e.g., `TileState`, `ChestState`).
3. **Shape:** A component constructed from Properties and State that manages `Position`, `Dimensions`, and `Hitboxes` to process inline collision math.
4. **Animation & Frame Behaviors:** Stateless strategies (e.g. `SpriteAnimation`, `SpriteFrame`) injected into the Asset. These contain the specific logic for updating frames and calculating the render key, mutating the Asset's state in-place to avoid data duplication.

## Conceptual Categories

While all Assets share the same underlying architecture, they are conceptually divided into categories based on their data complexity.

### Tiles

*Tiles* are inanimate, immutable configurations. *Tiles* are the most basic type of Asset. They have a single frame. They have no hitboxes and are simply rendered, without affecting the game otherwise. Tiles are meant to encapsulate backgrounds by breaking each rendered image into a grid of tiles.

In terms of configuration, Tiles are divided into two categories, *regular* and *irregular*. *Regular Tiles* are always sized 32x32 pixels (configurable in the `/src/assets/tile/main.yaml` file). *Irregular Tiles* are variable size.

**Properties**

* `key: str`
* `dimensions: Dimensions`

**State**

* `layer: str`
* `position: Position`
* `multiple: Multiple`

**Frame Behavior**

* `key(animation) -> <key>`

### Objects

*Objects* are inanimate, mutable configurations made of a single frame or pair of frames. They are meant to encapsulate interactions and objects.

**Binary Objects**

An Object with two frames is considered to have an *activated* and *idle* state, i.e. a binary trigger. *Binary Objects* are Objects whose frame is dependent on their internal state switch.

**Binary Frames**

Binary objects frames are always organized in horizontal rows. The idle frame will always start at `(0,0)` and the activated frame will always start at `(w,0)`. Because of this relation, the dimensions of a Chest image file will always be `(2w, h)`

#### Chests

*Chests* are *Binary Objects* whose frame can be changed by the player entering into an `INTERACT` state while intersecting the dimensions of the *Chest*. When `switch == true`, the Chest is *activated* (open). When `switch == false`, the Chest is *idle* (closed).

**Properties**

* `key: str`
* `shape: ShapeProperties` (contains Dimensions and Hitboxes)

**State**

* `name: str`
* `layer: str`
* `position: Position`
* `switch: bool`
* `content: List[str]`

**Frame Behavior**

* `key(animation)`
* If `switch == true`, returns `<key>-activated`
* If `switch == false`, returns `<key>-idle`



#### Crates

*Crates* are *Objects* who state can be altered by in-game physics. For example, when a *Sprite* collides with a *Crate*, the *Crate* moves in the direction of the *Sprite*, with the same speed.

**Properties**

* `key: str`
* `shape: ShapeProperties`

**State**

* `name: str`
* `layer: str`
* `position: Position`

**Frame Behavior**

* `key(animation): returns <key>`

#### Doors

*Doors* are *Objects* that alter the player's `<layer>`. When a player enters the hitbox of a door, the `<layer>` is changed to the `<outlayer>`.

**Properties**

* `key: str`
* `shape: ShapeProperties`

**State**

* `name: str`
* `layer: str`
* `outlayer: str`
* `position: Position`
* `out: Position`

**Frame Behavior**

* `key(animation): returns <key>`

#### Gates

*Gates* are *Objects* whose state is connected to *Plates*. When a *Gate* is activated (open), it does not have hitboxes and the player can pass freely through it. When a Gate is idle (closed), its hitboxes prevent the player from passing through its area.

**Properties**

* `key: str`
* `shape: ShapeProperties`

**State**

* `name: str`
* `layer: str`
* `link: str`
* `position: Position`
* `switch: bool`

**Frame Behavior**

* `key(animation)`
* If `switch == true`, returns `<key>-idle`
* If `switch == false`, returns `<key>-activated`

#### Plates

*Plates* are *Binary Objects* whose state can be changed by collision, i.e. when a player enters its hitbox and flips its state. When activated, a *Plate* in turn flips the state of its keyed *Gate*.

**Properties**

* `key: str`
* `shape: ShapeProperties`

**State**

* `name: str`
* `layer: str`
* `link: str`
* `position: Position`
* `switch: bool`

**Frame Behavior**

* `key(animation)`
* If `switch == true`, returns `<key>-idle`
* If `switch == false`, returns `<key>-activated`

### Cursors

*Cursors* are inanimate, mutable Assets made of a single frame. They are divided into *Expressions* and *Projectiles*. Expressions are pinned to other Assets and have their position state updated in tandem with the Asset to which they are linked. Projectiles are spawned with a certain direction and velocity, follow a fixed trajectory based on the spawn conditions, and then either impact a hitbox or are garbage-collected.

*(See schemas for detailed property lists).*

### Effects

*Effects* are animate, immutable configurations. *Effects* are defined over a single row of frames. *Effects* utilize an injected *Animation* behavior that iterates over the row of frames as the game loop progresses.

*Effects* are meant to encapsulate special effect and animation logic. For example, a projectile may produce a cloud of dust when impacting a surface. The dust cloud is an *Effect*.

**Temporary vs. Persistent**

Some Effects are brief (e.g. explosions or magic effects), while others loop through their frames forever (e.g. water ripples or a windmill). Temporary Effects are garbage-collected and removed from the Board after they "die", whereas Persistent Effects are excluded from garbage collection.

**Properties**

* `key: str`
* `shape: ShapeProperties`
* `count: int`

**Frame Behavior**

* `key(animation) -> <key>-<animation.frame>`

### Sheets

*Sheets* are animate, mutable configurations arranged in rows of frames.

**Direction and Action**

For any sheet composed of more than one row (i.e. all types of Sheets except *Pixies*), the rows of that Sheet are identified by *Direction*, *Action* and *Frame*.

The default (*LPC*) categories are enumerated below. The categories can be configured in the `/src/data/intents/main.yaml` file.

* Direction: `Enum[up, left, down, right]`
* Action: `Enum[cast, thrust, walk, slash, shoot, die]`
* Frame: `Interval[0, n(Action)]`

Where `n(Action)` is the number of frames per Action.

**IMPORTANT** For Sheets, it is assumed coordinates of a frame are *completely determined* by Action, Direction and Frame. It is assumed Actions form contiguous rows partitioned by Direction, and frames are organized in horizontal cells of equal length.

#### Pixies

*Pixies* are *Sheets* over four rows of frames. Pixies always have the same number of frames in each row. Pixies only have one Action state: `walk`. The rows of their Sheet Asset file are assumed to be partitioned over Direction only.

*Pixies* encapsulate simple Characters, such as animals or bugs.

**Properties**

* `key: str`
* `shape: ShapeProperties`

**State**

* `layer: str`
* `position: Position`
* `animation: Animation` (includes direction and frame)

**Frame Behavior**

* `key(animation) -> <key>-<animation.direction>-<animation.frame>`

#### Sprites

*Sprites* are *Sheets* over multiple rows of frames with a variable number of frames per row. They are meant to encapsulate the core Characters, e.g. the player, NPCs, and enemies.

**Properties**

* `key: str`
* `shape: ShapeProperties`
* `actions: Dict[str, SpriteActionProperty]`

**State**

* `name: str`
* `layer: str`
* `position: Position`
* `animation: Animation` (Action, Direction, Frame)
* `character: Character`
* `intention: Intention`
* `inventory: Inventory`
* `mutators: Mutator`
* `memory: Memory`
* `goal: Goal`

**Animation Behavior**

The injected `SpriteAnimation` component directly mutates the `animation.frame` property on the `SpriteState` to advance the animation sequence based on its current `animation.action`.

## Menu

TODO

## Sounds

TODO

## Schemas

### Properties: Tile Properties

* Location: `/src/assets/tiles/main.yaml`

```yaml
--8<-- "docs/.static/yaml/asset-property-tiles.yaml"

```

### Properties: Objects

* Location: `/src/assets/objects/main.yaml`

```yaml
--8<-- "docs/.static/yaml/asset-property-objects.yaml"

```

### Properties: Effects

* Location: `/src/assets/effects/main.yaml`

```yaml
--8<-- "docs/.static/yaml/asset-property-effects.yaml"

```

### Properties: Sheets

* Location: `/src/assets/sheets/main.yaml`

```yaml
--8<-- "docs/.static/yaml/asset-property-sheets.yaml"

```

### State: Immutable, Inanimate

* Location: `/src/data/state/<board-key>/immutable/inanimate.yaml`

```yaml
--8<-- "docs/.static/yaml/data-state-immutable-inanimate.yaml"

```

### State: Immutable, Animate

* Location: `/src/data/state/<board-key>/immutable/animate.yaml`

```yaml
--8<-- "docs/.static/yaml/data-state-immutable-animate.yaml"

```

### State: Mutable, Inanimate

* Location: `/src/data/state/<board-key>/mutable/inanimate.yaml`

```yaml
--8<-- "docs/.static/yaml/data-state-mutable-inanimate.yaml"

```

### State: Mutable, Animate

* Location: `/src/data/state/<board-key>/animate.yaml`

```yaml
--8<-- "docs/.static/yaml/data-state-mutable-animate.yaml"

```