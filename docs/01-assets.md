# Ontology: Assets

This document serves to specify the Asset architecture and provide key definition for game terminology.

!!! note "Definition"
    An Asset is an image file.

!!! note
    LPC Assets are bundled with the application by default.

## Overview 

The Asset directory is organized as follows,

```bash
assets % tree -L 2
.
├── crafts
│   └── struts
│   └── main.yaml
├── cursors
│   ├── expressions
│   ├── projectiles
│   └── main.yaml
├── effects
│   ├── persistent
│   ├── temporary
│   └── main.yaml
├── environ
│   └── main.yaml
├── main.yaml
├── menu
│   ├── icons
│   ├── symbols
│   ├── windows
│   └── main.yaml
├── objects
│   ├── chests
│   ├── crates
│   ├── doors
│   ├── gates
│   ├── plates
│   ├── struts
│   └── main.yaml
├── sheets
│   ├── pixies
│   ├── sprites
│   └── main.yaml
├── sounds
│   ├── music
│   ├── speech
│   └── main.yaml
└── tiles
│   ├── back
│   ├── fore
│   └── main.yaml
└── main.yaml
```

The root `main.yaml` configures [Asset Recipes](#recipes). The `main.yaml` files in each subdirectory conform to the [Asset property schema](#schemas) of their respective Asset Category. 

### Asset Concepts

**IDs & Names**

IDs are used to map Assets to images loaded into the [Registry](./00-overview.md#registry), to ensure each Asset is only loaded into the memory once, no matter how many times it is rendered in a single frame. In other words, IDs uniquely identify a physical Asset, but not in-game entities.

Names are used to uniquely identify an ingame entity. A single Asset ID may have multiple Names. A Name corresponds to a particular deployment of an Asset onto a Board. 

A Name identifies an Asset's deployment. A ID is what binds an Asset deployed state to its deployed properties.

**Mutability & Animability**

!!! note
    These terms are useful for refering to the state and properties, but do not play a formal role in the application's implementation. They are included to make precise what is meant when they are employed.

Assets are divided along *mutable* and *immutable* axes. *Immutable* Assets never have their state altered by the game loop. *Mutable* Assets change their state based on the game loop.

Assets are also divided along *animate* and *inanimate* axes. *Inanimate* Assets possess a single frame. *Animate* objects possess rows of frames for different animation states.

These terms form a partition of the Asset "*space*". An inanimate Asset is not necessarily immutable; Crates, for example, do not have animation, but do have mutable states. An animate Asset is not necessarily mutable; Effects, such as water ripples, has an animation, but does not have a mutable state.

In other words, an Asset's *mutability* refers to the capacity of its state (not including its animation) to change.

**Direction & Action**

The frame rows of *animate* Assets are further categorized by the axes of *Direction* and *Action*. See [Sheets section](#sheets) below for more information on the division of *Direction* and *Action*.

**Properties & State**

*Properties* are static and never changed by game Mechanics. Properties determine the immutable characteristics of an ingame Asset, e.g. dimensions and hitboxes. They are loaded side-by-side with the asset files in the `/src/assets/**` directory. All Assets have, at bare minumum, a Dimension property, specifying their respective length and width. Dimensions are Cartesian coordinate tuples.

*State* is dynamic and is changed by game Mechanics. State determines the mutable characteristics of an ingame Asset, e.g. the current position of an ingame Asset, the current animation, etc.. All Assets have a *position* and a *layer* mutable state. Position are given as Cartesian coordinates, whereas Layer is a categorical variable.

!!! note "Layers"
    The concept of a Layer is defined more explicitly in [World documentation](./00-overview.md#world). It suffices to think of Layers as floors in a house, i.e. where each floor has the same area and similar topology, but occupies a different height. In-game, Layers are traversed by the Player interacting with Doors.

State files are maintained in `/src/data/state/<board-key>/**`, where `<board-key>` is a unique identifer for a [Board](./00-overview.md#board).

### Asset Hierarchy

While Assets are instantiated by injecting a common root class with component behaviors (see [next section](#asset-architecture)), the Assets which result from the Entity-Component-System (ECS) injection still conform to  a strict Object hierarchy. The property and state [schemas](#schemas) encode Asset Categories and Instances into the top-level keys.

!!! note
    The Asset Hierarchy can be thought of as a data abstraction governing the schemas which drive the ECS instantiation. 

**Categories & Instances**

Asset *Categories* form the top layer of the hierarchy. Each Asset Category is defined by its static properties; an Asset's Category determines what type of properties it will parse from the property files and inject into its deployment. 

- Tiles: Properties = Dimensions 
- Cursor: Properties = Dimensions
- Objects: Properties = Dimensions, Hitboxes
- Craft: Properties = Dimensions, Hitboxes, Cost
- Effects: Properties = Dimensions, Hitboxes, Count
- Sheets: Properties = Dimensions, Hitboxes, Actions, Personas

Each Category has Instances. Asset *Instances* form the bottom layer of the hierarchy. Each Asset Instance is defined by its dynamic state; an Assets Instance determine what type of state it will parse from the property and state files and inject into its deployment. 

- Tile - BackTile: State = Position, Layer
- Tile - ForeTile: State = Position, Layer
- Object - Crate: State = Position, Layer
- Object - Door: State = Position, Layer, OutLayer
- Object - Chest: State = Position, Layer, Switch, Content
- Object - Gate: State = Position, Layer, Switch, Link
- Object - Plate: State = Position, Layer, Switch, Link
- Craft - Strut: State = Position, Layer, Owner
- Craft - Tract: State = Position, Layer, Owner, Stage
- Cursor - Expression: State = Position, Layer
- Cursor - Projectile: State = Position, Layer, Initial
- Effect - Temporary: State = Position, Layer
- Effect - Persistent: State = Position, Layer
- Sheet - Pixie, State: Postion = Position, Layer
- Sheet - Sprite, State: Position = Position, Layer, Intention, Inventory, Meters, Memory, Mutators, Goal

!!! note
    Animation and Frame states are not shown in the above table to save space, but belong in the Instance as well. See [Asset Recipes](#recipes) for more details.

### Asset Architecture

Every physical entity in the game is an instance of the unified `Asset` class. The distinction between a Tile, a Gate, or a Sprite is determined entirely by the data models and stateless behaviors injected into them:

1. **Properties:** A model defining immutable data (e.g., `TileProperties`, `ObjectProperties`, etc.).
2. **State:** A model defining mutable data (e.g., `ContainerState`, `PositionalState`, etc.).
3. **Animation** Stateless strategies (e.g. `BinaryAnimation`, `StateAnimation`, etc.) injected into the Asset. These contain the specific logic for updating frames.
4. **Frame:** A static schema calculation used by the renderer to determine the correct texture string keys. A `Frame` component returns a `List[str]` rather than a single `str`. An `Asset` can be a single logical entity composed of multiple superimposed rendered textures

*Behaviors* are decoupled from Assets and managed entirely by *Mechanics* classes that iterate over the Board Assets. See [Mechanics documentation](./06-architecture.md#mechanics) for more information.

The Recipe for an Asset is specified in the [Recipe](#recipes) configuration file. A recipe includes the Frame implementation, the Animation implementation, the State model and the Properties model. The recipe configuration file defines each of the Asset categories in the following headings.

### Asset Taxonomy

An Asset's position in the Asset Hierarchy is encoded into its Taxonomy is encoded into each Asset's attributes. These attributes exist on every Asset instantiated within the game,

- `id: str`
- `category: str`
- `instance: str`
- `name: str`

`id` uniquely identifies the Asset file. It must match a file found in the `src/assets/**` directory.

`category` determines what property model is employed by the Asset. The category must be configured by a `src/assets/<category>/main.yaml` property file.

`instance` determines what state model is employed by the Asset. An Asset's state is hydrated from the `data/state/<board>/*` directory.

`name` is the physical deployment of the Asset. Every Asset Instance deployed onto a Board has a unique `name`.

`(category, instance)` collectively determine the components `(frame, animation, properties, state)` injected into an Asset class during the [Initialization](./07-architecture.md#initialization). More specifically, category determines properties (`category -> properties`), and instance determines everything else (`instance -> (frame, animation, state)`).

## Tiles

* Property File: `/src/assets/tiles/main.yaml`

*Tiles* are inanimate, immutable Assets. *Tiles* are the most basic type of Asset. They have a single frame. They have no hitboxes and are simply rendered, without affecting the game otherwise. Tiles are meant to encapsulate backgrounds and foregrounds by breaking each rendered image into a grid of tiles.

*Tiles* are always assumed to be sized 32x32 pixels. These dimensions configurable in the property file, but they apply to all Tiles universally.

**Properties: TileProperties**

* `dimensions: Dimensions`

### Back

A Back Tile is the first Asset rendered on screen. It has the lowest Z coordinate of all Assets. Back Tiles will always be rendered *under* all of the other Assets.

**Animation: None**

N/A

**Frame: SingleFrame**

* `keys(id, None): returns [ id ] "`
* `index(self, id, properties): returns { id: (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: MultiplerState**

* `layer: str`
* `position: Position`
* `multiple: Multiple`

### Fore

A Fore Tile is the last Asset rendered on screen. It has the highest Z coordinate of all Assets. Fore Tiles will always be render on top of all of other Assets.

**Animation: None**

N/A

**Frame: SingleFrame**

* `keys(id, None): returns [ id ] "`
* `index(self, id, properties): returns { id: (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: MultiplerState**

* `layer: str`
* `position: Position`
* `multiple: Multiple`

## Objects

* Property File: `/src/assets/objects/main.yaml`

*Objects* are inanimate, mutable Assets made of a single frame or pair of frames. They are meant to encapsulate interactions and objects.

**Binary Frames**

An Object with two frames is considered to have an *On* and *off* state, i.e. a binary trigger. *Binary Objects* are Objects whose frame is dependent on their internal state switch.

Binary Objects frames are always organized in horizontal rows. The off frame will always start at `(0,0)` and the on frame will always start at `(w,0)`. Because of this relation, the dimensions of a Chest image file will always be `(2w, h)`. 

Binary Objects have a `count` of 2, where as all other Objects are initialized with `count = 1` by default.

**Properties: ObjectProperties**

* `dim: Dimensions`
* `hitboxes: List[Hitbox]` 
* `count: int = 1`

### Chests

*Chests* are *Binary Objects* whose frame can be changed by the player entering into an `interact` [Intention](./04-intentions.md) while intersecting the hitboxes of the *Chest*. When `switch == true`, the Chest is *on* (open). When `switch == false`, the Chest is *off* (closed).

A Chest is *reusable* through the `interact` [Intention](./04-intentions.md), meaning [Inventory Loot](./02-sprites.md#inventory) can be taken out of and also placed into a Chest. The `content` state field manages the current contents of the Chest through a list of Inventory Loot keys.

When *interacting* with a Chest, the [Player](./03-player.md) is shown a two windowed menu, allowing them to exchange the contents of their Inventory Loot with the contents of the Chest. A Sprite may also enter into an `interact` Intention through its [Intention Transition Matrix](./04-intentions.md#transition-matrix). This interaction is managed through a [Mechanic](./06-architecture.md#mechanics)s

**Animation: BinaryAnimation**

- `if switch == true: animation.frame = 1`
- `if switch != true: animation.frame = 0`

**Frame: IterableFrame**

* `keys(id, animation): returns [ "{id}-{animation.frame}"`
* `index(self, id, properties): returns { "{id}-{properties.count}": (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: ContainerState**

* `layer: str`
* `position: Position`
* `switch: bool`
* `content: List[str]`

### Crates

*Crates* are *Objects* who state can be altered by in-game physics. For example, when a *Sprite* collides with a *Crate*, the *Crate* moves in the direction of the *Sprite*, with the same speed.

**State: PositionalState**

* `layer: str`
* `position: Position`

**Frame: SingleFrame**

* `keys(id, None): returns [ id ] "`
* `index(self, id, properties): returns { id: (0, 0, properties.dimension.w, properties.dimensions.l) }`

### Doors

*Doors* are *Objects* that alter a Sprite's `<layer>`. When a Sprite enters the hitbox of a door, the `<layer>` is changed to the `<outlayer>` at the `<out>` Position.

**State: DoorState**

* `layer: str`
* `outlayer: str`
* `position: Position`
* `out: Position`

**Frame: SingleFrame**

* `keys(id, animation): returns id`
* `index(self, id, properties): returns { id: (0, 0, properties.dimension.w, properties.dimensions.l) }`

### Gates

*Gates* are *Binary Objects* whose state is connected to *Plates*. When a *Gate* is on (open), it does not have hitboxes and the player can pass freely through it. When a Gate is off (closed), its hitboxes prevent the player from passing through its area.

**Animation: BinaryAnimation**

- `if switch == true: animation.frame = 1`
- `if switch != true: animation.frame = 0`

**Frame: IterableFrame**

* `keys(id, animation): returns [ "{id}-{animation.frame}"`
* `index(self, id, properties): returns { "{id}-{properties.count}": (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: SwitchState**

* `layer: str`
* `link: str`
* `position: Position`
* `switch: bool`

### Plates

*Plates* are *Binary Objects* whose state can be changed by collision, i.e. when a player enters its hitbox and flips its state. When activated, a *Plate* in turn flips the state of its keyed *Gate*.

**Animation: BinaryAnimation**

- `if switch == true: animation.frame = 1`
- `if switch != true: animation.frame = 0`

**Frame: IterableFrame**

* `keys(id, animation): returns [ "{id}-{animation.frame}"`
* `index(self, id, properties): returns { "{id}-{properties.count}": (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: SwitchState**

* `layer: str`
* `link: str`
* `position: Position`
* `switch: bool`

## Cursors

* Property File: `/src/assets/cursors/main.yaml`

*Cursors* are inanimate, mutable Assets made of a single frame. They are divided into *Expressions* and *Projectiles*.

**Properties: ObjectProperties**

* `dim: Dimensions`

### Expressions

Expressions are pinned to other Assets and have their position state updated in tandem with the Asset to which they are linked. 

**Animation: None**

N/A

**Frame: SingleFrame**

* `key(asset, id): returns [ id ]`
* `index(self, id, properties): returns { id: (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: PositionalState**

* `layer: str`
* `position: Position`

### Projectiles

Projectiles are spawned via the `shoot` Action with a certain direction and velocity and then follow a fixed trajectory based on the spawn conditions. They will either impact a hitbox or get garbage-collected.

**Animation: None**

N/A

**Frame: SingleFrame**

* `keys(id), animation): returns [ id ]`
* `index(self, id, properties): returns { id: (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: MetricState**

* `layer: str`
* `position: Position`
* `initial: Position`

## Effects

* Property File: `/src/assets/effects/main.yaml`

*Effects* are animate, immutable Objects. *Effects* are defined over a single row of frames. *Effects* utilize an injected *Animation* behavior that iterates over the row of frames as the game loop progresses.

*Effects* are meant to encapsulate special effect and animation logic. For example, a projectile may produce a cloud of dust when impacting a surface. The dust cloud is an *Effect*.

**Properties**

* `dim: Dimensions`
* `hitboxes: List[Hitbox]` 
* `count: int`

### Temporary

Temporary Effects are brief, short-lived effects, such as explosions or magic effects. After their animation is concluded, they are garbage-collected and removed from the Board after they "die"

**Animation: TemporaryAnimation**

- `if animation.frame < properties.count: animation.frame += 1`

**Frame: IterableFrame**

* `keys(id, animation): returns [ "{id}-{animation.frame}" ]`
* `index(self, id, properties): returns { "{id}-{properties.count}": (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: AnimatorState**

* `layer: str`
* `position: Position`
* `animation: Animation`

### Persistant

Persistent Effects are long-term, continuous effects, such as water ripples or windmills, whose animation continually cycles through its loop.

**Animation: PersistantAnimation**

- `if animation.frame > properties.count: animation.frame = 0`

**Frame: IterableFrame**

* `keys(id, animation) : [ "{id}-{animation.frame}" ]`
* `index(self, id, properties): returns { "{id}-{properties.count}": (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: AnimatorState**

* `layer: str`
* `position: Position`
* `animation: Animation`

## Crafts

* Property File: `/src/assets/crafts/main.yaml`

Crafts are Assets that can be instantiated through game [Mechanics](./06-architecture.md#mechanics), such as `CommerceMechanics` or `ChemistryMechanics`. All Crafts have a `cost` associated with them. 

**Cost**

Cost is a set of quantities that must be satisfied before the Craft can be instantiated. It is a "formula" for the Craft's creation. 

```yaml
cost:
    - key:
      quantity:
```

The `key` referenced in the `cost` depends on the Instance type of the Craft. For example, a Strut costs Inventory Loot. The `cost` of a Strut is deducted from a Sprite's Inventory Loot when being instantiated.

**Properties: CraftProperties**

* `dimensions: Dimensions`
* `hitboxes: List[Hitbox]`
* `cost: Cost`

### Struts 

*Struts* are inanimate, immutable Assets. *Struts* are meant to encapsulate the concept of property in the game, e.g. houses, fences, etc. In other words, they possess an `owner`. 

Struts may be placed on the Board through the state files manually, but are instantiated ingame through the `build` Sprite [Intention](./04-intentions.md)

**Animation: None**

N/A

**Frame: SingleFrame**

* `keys(id, None) returns [ id ]`
* `index(self, id, properties): returns { id: (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: PropertyState**

* `layer: str`
* `position: Position`
* `owner: str`

## Sheets

* Property File: `/src/assets/sheets/main.yaml`

*Sheets* are animate, mutable configurations arranged in rows of frames.

**Sheet Specification**

The rows of a Sheet are identified by *Direction*, *Action* and *Frame*. Each row is identified by a tuple (Direction, Action), and then divided horizontally into contiguous horizontal Frames. 

!!! important
    For Sheets, it is assumed coordinates of an image in the Asset file are *completely determined* by Action, Direction and Frame. It is assumed Actions form contiguous rows partitioned by Direction, and frames are organized in horizontal cells of equal length. This specification is enforced on the application level.

**LPC Specification**

While an Action set an be defined in `/src/data/config/actions/main.yaml`, the documentation will often assume the LPC (Liberated Pixel Cup) specification when discussing Action, Direction and Frame. The values for these fields in the LPC Spec are enumerated below,

* Direction: `up, left, down, right`
* Action: `cast, thrust, walk, slash, shoot, die`
* Frame: `0, 1, 2 , ... , n(Action)`

Where `n(Action)` is the number of frames per Action. The frames per Action are given below,

- `cast`: Count = 7
- `thrust`: Count = 8
- `walk`: Count = 9
- `slash`: Count = 6
- `shoot`: Count = 13
- `die`: Count = 6

!!! note
    `die` is only associated with a single row in the LPC specification.

!!! note
    The row indexing starts at 0.

!!! note 
    In the LPC specification, the `thrust` Action plays double-duty for spears and shovels. The spear is a Weapon, whereas the shovel is Equipment. With LPC assets, the animations of these pieces of Equipment is governed by the `thrust` state.

**Action**

Actions are part of the Animation state. An Action implicitly contains Directions, i.e. an Action cannot be specified without an accompanying Direction. The "space" of the (Action, Direction) space is configured by Sheet Properties. 

This snippet from the [Schemas](#schemas) shows the general structure of an Action,

```yaml
<action-key>:
    count:
    directions:
        <direction-key>:
            row:
```

* `<action-key>: str` - Ranges over `cast, thrust, walk, slash, shoot, die` (LPC)
* `<direction-key> : str` -  Ranges over  `up, left, down, right` (LPC)
* `count: int` - is the number of frames in the Action row grouping. 

**Action Sets**

Many Sheet Assets reuse the same Action specification. Common Asset Action specifications are configured and indexed in the Action Configuration file. These configurations are referred to as Action Sets. Each Sheet specifics an Action Set in its property file. See [Action Configuration Schema](#action-configuration) below for more details. 

**Stacks**

A Stack is a list of Sheets keys to superimpose over one another to form the resultant Sheet used in the game. The Sheet stacks are drawn in the order they are specified, i.e. the first entry has the lowest Z coordinate, with each subsequent entry being stacked on top.

For example, the `src/assets/sheets/<sheet-category>/features/hair-blonde-bangs.png` might be stacked on top of `src/assets/sheets/<sheet-category>/skins/male-dark-human.png` to create a new Sheet asset used in the game. These "stack" of Sheets is keyed in the [Registry](./00-overview.md#registry) using the `<sheet-id>`. 

Stacks are assembled in the [Registry](./00-overview.md#registry) using the `stack` property in the Asset property file during the [application bootstrap](./06-architecture.md). The assembled `stack` is saved as a Sheet Asset, using the `<sheet-id>` as the Asset key. In other words, once assembled, Stacks are effectively new "virtualized" Assets.

!!! note
    It is assumed all Sheets in a Stack conform to the same (Action, Direction) row mapping.

**Properties: SheetProperties**

* `dimensions: Dimensions`
* `stack: List[str]`
* `hitboxes: List[Hitbox]`
* `actions: Actions`

### Pixies

*Pixies* are *Sheets* that have simple game mechanics, e.g. are excluded from the complex calculations of the [Intention Mechanic](./04-intentions.md). *Pixies* encapsulate simple Characters, such as animals or bugs.

**Animation: StateAnimation**

- `state.animation.frame += 1`
- `if state.animation.frame >= properties.actions[state.animation.action].count: state.animation.frame = 0`

**Frame: StateFrame**

* `keys(id, animation): returns [ "{id}-{animation.action}-{animation.direction}-{animation.frame}" ]`
* `index(self, id, properties): returns { "{id}-{properties.actions.*}-{properties.actions.*.directions.*}-{properties.actions.*.count}": (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: AnimatorState**

* `layer: str`
* `position: Position`
* `animation: Animation`

### Sprites

*Sprites* are *Sheets* over multiple rows of frames with a variable number of frames per row. They have a diverse palette of Actions. They are meant to encapsulate the core Characters, e.g. the player, NPCs, and enemies.

**Animation: StateAnimation**

- `state.animation.frame += 1`
- `if state.animation.frame >= properties.actions[state.animation.action].count: state.animation.frame = 0`

**Frame: SpriteFrame**

* `keys(id, animation): returns [ "{id}-{animation.action}-{animation.direction}-{animation.frame}" ] + [ <equipment-frames>]`
* `index(self, id, properties): returns { "{id}-{properties.actions.*}-{properties.actions.*.directions.*}-{properties.actions.*.count}": (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: SpriteState**

* `layer: str`
* `position: Position`
* `animation: Animation`
* `character: Character`
* `intention: Intention`
* `inventory: Inventory`
* `meters: Dict[str, Meter]`
* `mutators: Mutators`
* `memory: Memory`
* `goal: Goal`

Sprite States are covered in more detail in the [Sprites documentation](./02-sprites.md).

### Equipment (Weapons, Utilities, Tools, Armor, Shields)

Equipment is a group of Asset Instances within the Category of Sheets (known as the Equipment Instance Group). They are closely tied to Sprites Animations. Equipment Assets are rendered on top of a Sprite when those pieces of Equipment are active in the Sprite's inventory. Because of this relationship between the Assets,  i.e. Equipment rendering is dependent on Sprite state, Equipment does not possess its own state, frame or animation implementation. Equipment only has properties.

Equipment is covered in more detail in the [Sprites documentation](./02-sprites.md#equipment).

## Widgets

Widgets are used to constructs Menus. They are not a part of the core gameplay loopjku and have special Mechanics for their interaction. 

Widgets are covered in their own section, [Widgets](./06-widgets.md).

## Schemas

### Recipe Configuration

Asset Recipe files determine the specific (State, Animation, Frame) components injected into an Asset Category Instance. The Category and Instance key are encoded into the top-level fields of each Recipe.

* Location: `/src/data/config/recipes/main.yaml`

```yaml
--8<-- "docs/.static/yaml/data-recipes.yaml"
```

**Default Recipe Configuration**

```yaml
--8<-- "docs/.static/yaml/examples/default-recipes.yaml"
```

### Action Configuration

Action Configurations determine the (Action, Direction) partitions employed by a Sheet Asset.

* Location: `/src/data/config/actions/main.yaml`

```yaml
--8<-- "docs/.static/yaml/data-actions.yaml"
```

**Default Action Configuration**

```yaml
--8<-- "docs/.static/yaml/examples/default-actions.yaml
```

### Properties

Asset Property files hydrate the application models.

* Location: `/src/assets/<category>/main.yaml`

```yaml
--8<-- "docs/.static/yaml/asset-properties.yaml"
```

### State

Asset State files populate the [Board](./00-overview.md#board).

* Location: `/src/data/state/<board-key>/*.yaml`

```yaml
--8<-- "docs/.static/yaml/asset-state.yaml"
```

