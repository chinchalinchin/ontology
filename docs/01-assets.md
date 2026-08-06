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

The `main.yaml` files in each subdirectory conform to the [Asset property schemas](#schemas).

**Keys**

Keys are used to map assets to images loaded into the [Registry](./00-overview.md#registry), to ensure each Asset is only loaded into the memory once, no matter how many times it is rendered in a single frame. In other words, keys uniquely identify a physical Asset, but not in-game objects.

**Properties vs. State**

*Properties* are static and never changed by ingame mechanics. Properties determine the immutable characteristics of an ingame Asset, e.g. dimensions and hitboxes. They are loaded side-by-side with the asset files in the `/src/assets/**` directory.

*State* is dynamic and is changed by ingame mechanics. State determines the mutable characteristics of an ingame Asset, e.g. the current position of an ingame Asset. All Assets have a *position*, *dimension* and a *layer* mutable state. Position and dimension are given as Cartesian coordinates, whereas Layer is a categorical variable.

!!! note "Layers"
    The concept of a Layer is defined more explicitly in [World documentation](./00-overview.md#world). It suffices to think of Layers as floors in a house, i.e. where each floor has the same area and similar topology, but occupies a different height. In-game, Layers are traversed by the Player interacting with Doors.

State files are maintained in `/src/data/boards/*`.

**Names**

Names are used to uniquely identify an ingame entity. A single Asset may have multiple Names. A Name corresponds to a particular deployment of an Asset onto a Board. A Name is part of an Asset's state.

**Asset Hierarchy**

Assets are divided along two axes.

First, Assets are divided into *mutable* and *immutable* categories. *Immutable* Assets never have their state altered by the game loop. *Mutable* objects change their state based on the game loop.

Second, Assets are divided in *animate* and *inanimate* categories. *Inanimate* Assets either have a single frame or a pair of frames (*Binary Objects*). *Animate* objects possess rows of frames for different animation states.

The rows of *animate* Assets are further categorized by the axes of *Direction* and *Action*. See [Sheets section](#sheets) below for more information on the division of *Direction* and *Action*.

In order of ascending complexity, where complexity is defined as the number of dimensions in the state, the game asset hierarchy is given below,

- *Immutable*, *Inanimate* Assets
    - Tile: State: Position, Layer
    - Strut: State: Position, Layer, Owner
- *Mutable*, *Inanimate* Assets
    - Object: Crate, State: Position, Layer
    - Object: Door, State: Position, Layer, OutLayer
    - Object: Chest, State: Position, Layer, Switch, Content
    - Object: Gate, State: Position, Layer, Switch, Link
    - Object: Plate, State: Position, Layer, Switch, Link
- *Mutable*, *Inanimate* Assets
    - Cursor: Expression, State: TODO 
    - Cursor: Projectile, State: TODO
- *Immutable*, *Animate* Assets
    - Effect: Temporary, State: Position, Layer, Frame
    - Effect: Persistent, State: Position, Layer, Frame
- *Mutable*, *Animate* Assets
    - Sheet: Pixie, State: Postion, Layer, Frame
    - Sheet: Sprite, State: Position, Layer, Frame, Direction, Action, Intention, ...

**Asset Architecture**

Every physical entity in the game is an instance of the unified `Asset` class. The distinction between a Tile, a Gate, or a Sprite is determined entirely by the data models and stateless behaviors injected into them:

1. **Properties:** A model defining immutable data (e.g., `TileProperties`, `ObjectProperties`).
2. **State:** A model defining mutable data (e.g., `TileState`, `ChestState`).
3. **Shape:** A component constructed from Properties and State that manages `Position`, `Dimensions`, and `Hitboxes` to process inline collision math.
4. **Animation** Stateless strategies (e.g. `SpriteAnimation`, `PixieAnimation`) injected into the Asset. These contain the specific logic for updating frames.
5. **Frame:** A static schema calculation used by the renderer to determine the correct texture string key.

*Behaviors* are decoupled from Assets and managed entirely by *Mechanics* classes that iterate over the Board Assets. See [Mechanics documentation](./06-architecture.md#mechanics) for more information.

The "*recipe*" for an Asset is specified in the `/src/assets/main.yaml` configuration file. A recipe includes the Frame implementation, the Animation implementation, the State model and the Properties model. See [Schemas](#schemas) for an example of the Asset recipe schema. The recipe configuration file defines each of the Asset categories in the following headings.

## Tiles

*Tiles* are inanimate, immutable Assets. *Tiles* are the most basic type of Asset. They have a single frame. They have no hitboxes and are simply rendered, without affecting the game otherwise. Tiles are meant to encapsulate backgrounds by breaking each rendered image into a grid of tiles.

*Tiles* are always assumed to be sized 32x32 pixels. These dimensions configurable in the `/src/assets/tile/main.yaml` file, but they apply to all Tiles universally.

**Properties**

* `key: str`
* `dimensions: Dimensions`

**State**

* `layer: str`
* `position: Position`
* `multiple: Multiple`

**Frame**

* `key(asset, None) -> <asset>`

## Struts

*Struts* are inanimate, immutable Assets. They are similar to tiles, except they have variable dimensions and possess an *owner*. *Struts* are meant to encapsulate the concept of property in the game, e.g. houses, fences, roads.

**Properties**

* `key: str`
* `dimensions: Dimensions`

**State**

* `layer: str`
* `position: Position`
* `multiple: Multiple`

**Frame**

* `key(asset, None) -> <asset>`

## Objects

*Objects* are inanimate, mutable Assets made of a single frame or pair of frames. They are meant to encapsulate interactions and objects.

**Binary Objects**

An Object with two frames is considered to have an *activated* and *idle* state, i.e. a binary trigger. *Binary Objects* are Objects whose frame is dependent on their internal state switch.

**Binary Frames**

Binary objects frames are always organized in horizontal rows. The idle frame will always start at `(0,0)` and the activated frame will always start at `(w,0)`. Because of this relation, the dimensions of a Chest image file will always be `(2w, h)`

### Chests

*Chests* are *Binary Objects* whose frame can be changed by the player entering into an `interact` Extension (see [Extensions](./02-sprites.md#extension) for more details on the distinction between Extension and Action) while intersecting the hitboxes of the *Chest*. When `switch == true`, the Chest is *activated* (open). When `switch == false`, the Chest is *idle* (closed).

**Properties**

* `key: str`
* `shape: ShapeProperties` 

**State**

* `name: str`
* `layer: str`
* `position: Position`
* `switch: bool`
* `content: List[str]`

**Frame**

* `key(asset, animation)`
    * If `switch == true`, returns `<asset>-activated`
    * If `switch == false`, returns `<asset>-idle`

### Crates

*Crates* are *Objects* who state can be altered by in-game physics. For example, when a *Sprite* collides with a *Crate*, the *Crate* moves in the direction of the *Sprite*, with the same speed.

**Properties**

* `key: str`
* `shape: ShapeProperties`

**State**

* `name: str`
* `layer: str`
* `position: Position`

**Frame**

* `key(asset, animation): returns <asset>`

### Doors

*Doors* are *Objects* that alter a Sprite's `<layer>`. When a Sprite enters the hitbox of a door, the `<layer>` is changed to the `<outlayer>`.

**Properties**

* `key: str`
* `shape: ShapeProperties`

**State**

* `name: str`
* `layer: str`
* `outlayer: str`
* `position: Position`
* `out: Position`

**Frame**

* `key(asset, animation): returns <asset>`

### Gates

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

**Frame**

* `key(asset, animation)`
    * If `switch == true`, returns `<asset>-idle`
    * If `switch == false`, returns `<asset>-activated`

### Plates

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

**Frame**

* `key(asset, animation)`
    * If `switch == true`, returns `<asset>-idle`
    * If `switch == false`, returns `<asset>-activated`

### Cursors

*Cursors* are inanimate, mutable Assets made of a single frame. They are divided into *Expressions* and *Projectiles*. Expressions are pinned to other Assets and have their position state updated in tandem with the Asset to which they are linked. Projectiles are spawned with a certain direction and velocity, follow a fixed trajectory based on the spawn conditions, and then either impact a hitbox or are garbage-collected.

TODO

### Effects

*Effects* are animate, immutable configurations. *Effects* are defined over a single row of frames. *Effects* utilize an injected *Animation* behavior that iterates over the row of frames as the game loop progresses.

*Effects* are meant to encapsulate special effect and animation logic. For example, a projectile may produce a cloud of dust when impacting a surface. The dust cloud is an *Effect*.

**Temporary vs. Persistent**

Some Effects are brief (e.g. explosions or magic effects), while others loop through their frames forever (e.g. water ripples or a windmill). Temporary Effects are garbage-collected and removed from the Board after they "die", whereas Persistent Effects are excluded from garbage collection.

**Properties**

* `key: str`
* `shape: ShapeProperties`
* `count: int`

**Frame**

* `key(asset, animation) -> <asset>-<animation.frame>`

### Sheets

*Sheets* are animate, mutable configurations arranged in rows of frames.

**Direction and Action**

The rows of a Sheet are identified by *Direction*, *Action* and *Frame*.

The default (*LPC*) categories are enumerated below. The categories can be configured in the `/src/data/intents/main.yaml` file.

* Direction: `Enum[up, left, down, right]`
* Action: `Enum[cast, thrust, walk, slash, shoot, die]`
* Frame: `Interval[0, n(Action)]`

Where `n(Action)` is the number of frames per Action.

**IMPORTANT** For Sheets, it is assumed coordinates of a frame are *completely determined* by Action, Direction and Frame. It is assumed Actions form contiguous rows partitioned by Direction, and frames are organized in horizontal cells of equal length.

- ROW #: `(Action, Direction)`
- row 0: `(cast, up)`
- row 1: `(cast, left)`
- row 2: `(cast, down)`
- row 3: `(cast, right)`
- row 4: `(thrust, up)`
- row 5: `(thrust, left)`
- row 6: `(thrust, down)`
- row 7: `(thrust, right)`
- row 8: `(walk, up)`
- row 9: `(walk, left)`
- row 10: `(walk, down)`
- row 11: `(walk, right)`
- row 12: `(slash, up)`
- row 13: `(slash, left)`
- row 14: `(slash, down)`
- row 15: `(slash, right)`
- row 16: `(shoot, up)`
- row 17: `(shoot, left)`
- row 18: `(shoot, down)`
- row 19: `(shoot, right)`
- row 20: `(die, down)`

!!! note
    `die` is only associated with a single row in the LPC specification.

!!! note
    The row indexing starts at 0.

### Pixies

*Pixies* are *Sheets* over four rows of frames. Pixies always have the same number of frames in each row. Pixies only have one Action state: `walk`. The rows of their Sheet Asset file are assumed to be partitioned over Direction only.

*Pixies* encapsulate simple Characters, such as animals or bugs.

**Properties**

* `key: str`
* `shape: ShapeProperties`

**State**

* `layer: str`
* `position: Position`
* `animation: Animation` (includes direction and frame)

**Frame**

* `key(asset, animation) -> <asset>-<animation.direction>-<animation.frame>`

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

**Animation**

The injected `SpriteAnimation` component directly mutates the `animation.frame` property on the `SpriteState` to advance the animation sequence based on its current `animation.action`.

**Frame**

* `key(asset, animation) -> <asset>-<animation.action>-<animation.direction>-<animation.frame>`

## Menu

TODO

## Sounds

TODO

## Schemas

### Recipes

* Location: `/src/assets/main.yaml`

### Properties

* Location: `/src/assets/<category>/main.yaml`

```yaml
--8<-- "docs/.static/yaml/asset-properties.yaml"
```

### State

* Location: `/src/data/state/<board-key>/*.yaml`

```yaml
--8<-- "docs/.static/yaml/asset-state.yaml"
```

