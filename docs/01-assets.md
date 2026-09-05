# Ontology: Assets

This document serves to specify the Asset architecture and provide key definition for game terminology.

!!! note "Definition"
    An Asset is an image file.

!!! note "Liberated Pixel Cup"
    [LPC](https://lpc.opengameart.org/) Assets are bundled with the application by default.

## Overview 

The Asset directory (and all subdirectories) contains Asset Image Files (`*.png`) and Asset Property indices (`*.yaml`). The [initialization](./10-architecture.md#initialization) will read in all of these files recursively and then use the property indices to index each Asset file. Each image file that appears in the Asset directories must be configured in a YAML file to get indexed and injected into the game. The property configuration in the `*.yaml` files must conform to the [Asset property schema](./appendices/01-schemas.md#model-properties) of the respective Asset Category they are configuring. 

!!! important
    All `*.yaml` files in the Asset directories are merged into a single schema, so every key must be unique. If two image files have the same name, one of them will be overwritten during [Registry indexing](./00-overview.md#registry).

### Asset Concepts

**IDs & Names**

IDs are used to map Assets to images loaded into the [Registry](./00-overview.md#registry), to ensure each Asset is only loaded into the memory once, no matter how many times it is rendered in a single frame. In other words, IDs uniquely identify a physical Asset, but not in-game entities.

Names are used to uniquely identify an ingame entity. A single Asset ID may have multiple Names. A Name corresponds to a particular deployment of an Asset onto a Board. 

In short, a Name identifies an Asset's deployment. A ID is what binds a deployed state to Asset file.

**Mutability & Animability**

!!! note
    These terms are useful for refering to the state, but do not play a formal role in the application's implementation. They are included to make precise what is meant when they are employed.

Assets are divided along an axis of mutability, into *mutable* and *immutable* groups. *Immutable* Assets never have their state altered by the game loop. *Mutable* Assets change their state based on the game loop.

Assets are also divided along axis of animability, into *animate* and *inanimate* groups. *Inanimate* Assets possess a single frame. *Animate* objects possess rows of frames for different animation states.

These terms form a partition of the Asset "*space*". An inanimate Asset is not necessarily immutable; Crates, for example, do not have animation, but do have mutable states. An animate Asset is not necessarily mutable; Effects, such as water ripples, have an animation, but do not have a mutable state.

In other words, an Asset's *mutability* refers to the capacity of its state (not including its animation) to change.

**Direction & Action**

The frame rows of Sheet Assets are categorized by the axes of *Direction* and *Action*. See [Sheets section](#sheets) below for more information on the division of *Direction* and *Action*.

**Properties & State**

*Properties* are static and never changed by game Mechanics. Properties determine the immutable characteristics of an ingame Asset, e.g. dimensions and hitboxes. They are loaded side-by-side with the Asset files in the `/src/assets/**` directory. All Assets have, at bare minumum, a Dimension property, specifying their respective width and length. Dimensions are Cartesian coordinate tuples.

*State* is dynamic and can be changed by game Mechanics. State determines the mutable characteristics of an ingame Asset, e.g. the current Position of an ingame Asset, the current Animation, etc.. All Assets have a *Position* mutable state; most (except for Widgets) have a *Layer*. Position is given as a Cartesian coordinate (tuple), whereas Layer is a categorical variable.

!!! note "Layers"
    The concept of a Layer is defined more explicitly in [Overview documentation](./00-overview.md#layers). It suffices to think of Layers as floors in a house, i.e. where each floor has the same area and similar topology, but occupies a different height. In-game, Layers are traversed by the Player interacting with Doors.

State files are maintained in `/src/data/state/<board-key>/**` directory, where `<board-key>` is a unique identifer for a [Board](./00-overview.md#board).

Of particular importance is the *AnimationState*, described directly below,

- AnimationState
    - action: Action key of Animation.
    - direction: Directiony key of Animation.
    - frame: Frame index of Animation.
    - tick: Engine tick accumulator. Used in conjunction with Action `delay` to control the speed of the Animation.

**Mass**

Some Asset Categories have a Mass property. Only Assets with Mass can participate in the physics engine. An Asset's mass determines how collisions behave.
 
- $m > 0$: **Dynamic Body**. Participates in momentum calculations.
- $m = 0$: **Static Body**. Treated as having infinite mass ($m \to \infty$) in physics equations. Its Velocity is unaffected by collisions, but it forces dynamic bodies to resolve overlap.
- $m = -1$: **Sensor**. The engine detects the spatial intersection for game logic (like SwitchMechanics or DoorMechanics), but CollisionMechanics bypasses it completely during the overlap resolution phase.

See [Mechanics](./05-mechanics.md#spatial) for more information.

**Depth & Height**

All Assets have a `depth` state attribute. This attribute controls the Z-ordering of the Asset being rendered. Most of the time, it can be ignored, since it defaults to `0`. `depth` is important in the context of [Compositions](./03-compositions.md), where multiple Assets need to be superimposed and rendered on top of one another.

All Assets have an optional `height` state attribute. This attribute also modulates the Z-ordering, but the relationship is more complex than `depth`, relating to the application of the Painter's Algorithm. `height` is only a factor when dealing with [Compositions](./03-compositions.md). 

See [Rendering documentation](./10-architecture.md#rendering) for a complete overview of `depth` and `height`.

### Asset Hierarchy

While Assets are instantiated by injecting a common root class with component behaviors (see [next section](#asset-architecture)), the Assets which result from the Entity-Component-System (ECS) injection still conform to a strict hierarchy of Categories and Instances. The property and state [schemas](./appendices/01-schemas.md) encode Asset Categories and Instances into the top-level keys.

```mermaid
--8<-- "static/mmd/asset-hierarchy.mmd"
```

!!! note
    The Asset Hierarchy can be thought of as a data abstraction governing the schemas, which in turn drive the ECS instantiation. 

**Categories**

Asset *Categories* form the top layer of the hierarchy. Each Asset Category is defined by its static properties; an Asset's Category determines what type of properties it will parse from the property files and inject into its deployment. 

| Asset Category | Properties |
| - | - |
| Tiles | Dimensions, Friction |
| Cursors | Dimensions |
| Effects | Dimensions, Count |
| Objects | Dimensions, Hitboxes, Mass |
| Crafts | Dimensions, Hitboxes, Mass, Cost |
| Sheets | Dimensions, Hitboxes, Mass, Stack, Actions |
| Widgets | Dimensions, Frames |

**Instances**

Each Category has Instances. Asset *Instances* form the bottom layer of the hierarchy. Each Asset Instance is defined by its dynamic state; an Asset's Instance determines what type of state it will parse from the state files and inject into its deployment. 

| Asset Category | Asset Instance | State |
| - | - | - | 
| Tile | Back | Position, Layer, Depth, Height |
| Tile | Fore | Position, Layer, Depth, Height |
| Object | Crate | Position, Layer, Depth, Height |
| Object | Sign | Position, Layer, Depth, Height, Persona, Lexicon |
| Object | Door | Position, Layer, Depth, Height, OutLayer |
| Object | Chest | Position, Layer, Depth, Height, Animation, Switch, Content |
| Object | Gate | Position, Layer, Depth, Height, Aniamtion, Switch, Link |
| Object | Plate | Position, Layer, Depth, Height, Animation, Switch, Link |
| Craft | Strut | Position, Layer, Depth, Height, Owner |
| Craft | Crop | Position, Layer, Depth, Height, Season |
| Craft | Ore | Position, Layer, Depth, Height, Vein |
| Cursor | Expression | Position, Layer, Depth, Height |
| Cursor | Projectile | Position, Layer, Depth, Height, Initial |
| Effect | Temporary | Position, Layer, Depth, Height, Animation |
| Effect | Persistent | Position, Layer, Depth, Height, Animation |
| Sheet | Pixie | Position, Layer. Depth, Height, Animation |
| Sheet | Sprite | Position, Layer, Depth, Height, Animation, Intention, Inventory, Meters, Memory, Mutators, Goal |
| Widget | Icon | Position, Frame |
| Widget | Pane | Position, Layout, Alignment, Gap, Margins |
| Widget | Button  | Position, Status, Icons, Animation |
| Widget | Meter | Position, Reading, Unit |
| Widget | Page | Position, Content, Page Index, Page Size, Canvas |

!!! note
    [Equipment](./02-sprites.md#equipment) and [Player](./02-sprites.md#player) Assets are excluded from this table, due to the special nature of these particular Assets. Equipment is a stateless Sheet, whereas the Player is a special type of [Sprite](./02-sprites.md).

### Asset Architecture

Every physical entity in the game is an instance of the unified Asset class. The distinction between a Tile, a Gate, or a Sprite is determined entirely by the data models and components injected into them. Behaviors are decoupled from Assets and managed entirely by *Mechanic* classes that iterate over the Board Assets. See [Mechanics documentation](./05-mechanics.md) for more information.

The Recipe for an Asset, i.e. the list of components which go into a particular Asset Instance, is specified in the [Recipe](./appendices/01-schemas.md#configuration-recipes) configuration file. The components of each Assets are enumerated below,

1. **Model: Properties:** A model defining immutable data (e.g., `TileProperties`, `ObjectProperties`, etc.).
2. **Model: State:** A model defining mutable data (e.g., `ContainerState`, `PositionalState`, etc.).
3. **Behavior: Animation** Stateless strategies (e.g. `BinaryAnimation`, `StateAnimation`, etc.) injected into the Asset. These contain the specific logic for updating Animation frames.
    - `animate(state, properties)`: Interface for applying animation logic to Asset state.
4. **Behavior: Frame:** A static schema calculation used by the renderer to determine the correct texture string keys. An Asset can be a single logical entity composed of multiple superimposed rendered textures, therefore a Frame component returns a `List[str]` rather than a single `str`. In addition, Frames provide the indexing schema for textures used by the [Registry](./00-overview.md#registry) to store Assets in memory.
    - `keys(id, state)`: Interface for retrieving Asset's current Frame key.
    - `index(id, properties)`: Interface for indexing Asset frames in Registry.

!!! note
    The state model can be calculated from (Category, Instance), but (Animation, Frame) is independent of the state assigned to an Asset through the Asset Hierarchy. It must be specified through a Recipe.

### Asset Taxonomy

An Asset's position in the Asset Hierarchy is encoded into its Taxonomy. These attributes exist on every Asset instantiated within the game. A Taxonomy is neither state, configuration or properties.

- `id: str`
- `category: str`
- `instance: str`
- `name: str`

`id` uniquely identifies the Asset file. It must match a file found in the `src/assets/**` directory.

`category` determines what property model is employed by the Asset. The category must be configured by a `src/assets/<category>/main.yaml` property index file.

`instance` determines what state model is employed by the Asset. An Asset's state is hydrated from the `data/state/<board>/*` directory.

`name` is the physical deployment of the Asset. Every Asset Instance deployed onto a Board has a unique `name`.

`(category, instance)` collectively determine the components `(frame, animation, properties, state)` injected into an Asset class during the [Initialization](./10-architecture.md#initialization). More specifically, category determines properties (`category -> properties`), and instance determines everything else (`instance -> (frame, animation, state)`).

## Tiles

* Property File: `/src/assets/tiles/main.yaml`

Tiles are inanimate, immutable Assets. Tiles are the most basic type of Asset. They have a single frame, have no hitboxes and are simply rendered, without affecting the game otherwise. Tiles are meant to encapsulate backgrounds and foregrounds by breaking each rendered image into a grid of Tiles. 

Tiles Instances have their dimensions fixed by their properties. These dimensions are configurable in the property file, but they apply to all Tiles of a particular instance universally. When a Tile is drawn, it is rendered as a `multiple` of the unit Tile configured in the Asset directory.

Tiles have coefficients of friction. These coefficient are used by [MotionMechanics](./05-mechanics.md#spatial) to determine the rate of velocity decay for Frictive Assets traversing their area.

**Properties: TileProperties**

* `dimensions: Dimensions`
* `friction: float`

### Back

A Back Tile is the first Asset rendered on screen. It has the lowest Z coordinate of all Assets; Back Tiles will *always* be rendered *under* all of the other Assets, regardless of their `depth` or `height`.

**Animation: None**

N/A

**Frame: SingleFrame**

* `keys(id, None): returns [ id ] "`
* `index(self, id, properties): returns { id: (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: MultiplerState**

* `layer: str`
* `depth: int`
* `height: int`
* `position: Position`
* `multiple: Multiple`

### Fore

A Fore Tile is the last Asset rendered on screen. It has the highest Z coordinate of all Assets. Fore Tiles will always be rendered on top of all of other Assets, regardless of their `depth` or `height`. The *one* exception to this rule is Widgets. Fore Tiles are an "in-world" Asset, and thus their Z-ordering is superseded by Widgets.

**Animation: None**

N/A

**Frame: SingleFrame**

* `keys(id, None): returns [ id ] "`
* `index(self, id, properties): returns { id: (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: MultiplerState**

* `layer: str`
* `depth: int`
* `height: int`
* `position: Position`
* `multiple: Multiple`

## Objects

* Property File: `/src/assets/objects/main.yaml`

Objects are mutable Assets made of a single frame or pair of frames. They are meant to encapsulate interactions and objects.

**Binary Frames**

An Object with two frames is considered to have an *on* and *off* state, i.e. a binary trigger. *Binary Objects* are Objects whose frame is dependent on their internal state switch.

Binary Objects frames are always organized in horizontal rows. The off frame will always start at `(0,0)` and the on frame will always start at `(w,0)`. Because of this relation, the dimensions of a Chest image file will always be `(2w, h)`. 

Binary Objects have a `count` of 2, where as all other Objects are initialized with `count = 1` by default.

**Properties: ObjectProperties**

* `dim: Dimensions`
* `hitboxes: List[Hitbox]` 
* `count: int = 1`
* `mass: int`

### Chests

*Chests* are *Binary Objects* whose frame can be changed by the player entering into an `interact` [Intention](./04-intentions.md) while intersecting the hitboxes of the Chest. When `switch == true`, the Chest is *on* (open). When `switch == false`, the Chest is *off* (closed).

A Chest is *reusable* through the `interact` [Intention](./04-intentions.md), meaning [Inventory Loot](./02-sprites.md#inventory) can be taken out of and also placed into a Chest. The `content` state field manages the current contents of the Chest through a list of Inventory Loot keys.

When *interacting* with a Chest, the [Player](./03-player.md) is shown the [Chest menu](./06-widgets.md#menus), allowing them to exchange the contents of their Inventory Loot with the contents of the Chest. A Sprite may also enter into an `interact` Intention with a Chest through its [Intention Transition Matrix](./04-intentions.md#transition-matrix). This interaction is managed through a dedicated Sprite [Mechanic](05-mechanics.md)

**Animation: BinaryAnimation**

- `if switch == true: animation.frame = 1`
- `if switch != true: animation.frame = 0`

**Frame: IterableFrame**

* `keys(id, animation): returns [ "{id}-{animation.frame}" ]`
* `index(self, id, properties): returns { "{id}-{properties.count}": (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: ContainerState**

* `layer: str`
* `depth: int`
* `height: int`
* `position: Position`
* `switch: bool`
* `content: List[str]`

### Crates

Crates are Objects who state can be altered by in-game physics. For example, when a Sprite collides with a Crate, momentum is transferred from the Sprite to the Crate. See [CollisionMechanics](./05-mechanics.md#spatial) for more information on the physics of game collisions.

**State: PositionalState**

* `layer: str`
* `depth: int`
* `height: int`
* `position: Position`
* `velocity: Velocity`

**Frame: SingleFrame**

* `keys(id, None): returns [ id ] "`
* `index(self, id, properties): returns { id: (0, 0, properties.dimension.w, properties.dimensions.l) }`

### Doors

Doors are Objects that alter a Sprite's `<layer>`. When a Sprite enters the hitbox of a door, the `<layer>` is changed to the `<outlayer>` at the `<out>` Position.

**State: DoorState**

* `layer: str`
* `depth: int`
* `height: int`
* `outlayer: str`
* `position: Position`
* `out: Position`

**Frame: SingleFrame**

* `keys(id, animation): returns [ id ]`
* `index(self, id, properties): returns { id: (0, 0, properties.dimension.w, properties.dimensions.l) }`

### Gates

Gates are Binary Objects whose state is connected to Plates. When a Gate is on (open), it does not have hitboxes and the player can pass freely through it. When a Gate is off (closed), its hitboxes prevent the player from passing through its area.

**Animation: BinaryAnimation**

- `if switch == true: animation.frame = 1`
- `if switch != true: animation.frame = 0`

**Frame: IterableFrame**

* `keys(id, animation): returns [ "{id}-{animation.frame}" ]`
* `index(self, id, properties): returns { "{id}-{properties.count}": (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: SwitchState**

* `layer: str`
* `depth: int`
* `height: int`
* `link: str`
* `position: Position`
* `switch: bool`

### Plates

Plates are Binary Objects whose state can be changed by intersection, e.g. when a Sprite enters its hitbox a Plate will flip its `switch`. When activated, a Plate in turn notifies the state of its `link`-keyed Gate to change.

!!! note
    Plates must have their `mass` property configured to be `-1`, to exclude them from the collision resolution while keeping the collision detection active, i.e. Plates do not move due to collisions, but register when other Assets are intersecting them. Plates are considered *Sensors*. See [CollisionMechanics](./05-mechanics.md#spatial) for more information.

**Animation: BinaryAnimation**

- `if switch == true: animation.frame = 1`
- `if switch != true: animation.frame = 0`

**Frame: IterableFrame**

* `keys(id, animation): returns [ "{id}-{animation.frame}" ]`
* `index(self, id, properties): returns { "{id}-{properties.count}": (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: SwitchState**

* `layer: str`
* `depth: int`
* `height: int`
* `link: str`
* `position: Position`
* `switch: bool`

### Signs

Signs are immutable, inanimate Objects whose `content` is transmitted into a [Text Menu](./06-widgets.md#menus) when a Player enters into the `interact` [Intention](./04-intentions.md).

Signs utilize `persona` and `lexicon` keys to grab the appropriate content from the [Library](./08-plots.md#library)

**Animation: None**

N/A

**Frame: SingleFrame**

* `keys(id, animation): returns [ id ]`
* `index(self, id, properties): returns { id: (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: DialogueState**

* `position: Position`
* `persona: str`
* `lexicon: str`

!!! todo "SeasonMechanics"
    Add linkage between Sign lexicon key and Resource SeasonMechanics.

## Cursors

* Property File: `/src/assets/cursors/main.yaml`

Cursors are inanimate, mutable Assets. Cursors track positions and trajectories. They are divided into Expressions and Projectiles.

**Properties: ObjectProperties**

* `dimensions: Dimensions`

### Expressions

Expressions are "Phantom States" used as visual decorators. Unlike most Assets, Expressions are not instantiated as physical entities on the Board. Instead, their spatial offsets and frame keys are calculated dynamically by the [Cradle](./00-overview.md#board) and embedded directly into a Sprite's `Psyche` state as pure data. When the Sprite is rendered, the `SpriteFrame` reads this embedded data and superimposes the Expression into the rendering pipeline.

!!! important
    Due to the nature of Expressions as representations of the Sprite's internal state, there exists a hard dependency between Expression image files and their properties and the possible Expression frame enumerations. Each file name must exist and the following frames must be indexed by the Expression property index,

    - bubbles: `agreement`, `anger`, `confusion`, `disagreement`, `loquacity`, `surprise`, `tired`
    - buffs: TODO

**Animation: None**

N/A

**Frame: MappedFrame**

* `keys(id, state): returns [ (id, 0, 0) ]` *(Note: Bypassed during active rendering; `SpriteFrame` handles the dynamic offset injection).*
* `index(self, id, properties): returns { "{id}-{properties.frames[i]}": (i * properties.dimension.w, 0, properties.dimension.w, properties.dimensions.l) }`

**"Phantom" State: AttachmentState**

* `icon: str`
* `offset: Position`
* `ttl: int`: Number of game ticks for which the Expression is present.

### Projectiles

Projectiles are spawned via the `shoot` Action (entered through the `attack` [Intention](./04-intentions.md) when the `longbow` [Equipment](./02-sprites.md#equipment) is slotted, for instance) with a certain direction and velocity and then follow a fixed trajectory based on the spawn conditions. Projectiles will either impact a hitbox or trigger garbage-collection and be removed from the [Board](./00-overview.md#board).

**Animation: None**

N/A

**Frame: SingleFrame**

* `keys(id, animation): returns [ id ]`
* `index(self, id, properties): returns { id: (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: MotorState**

* `layer: str`
* `depth: int`
* `height: int`
* `position: Position`
* `initial: Position`
* `velocity: Velocity`
* `speed: int`

## Effects

* Property File: `/src/assets/effects/main.yaml`

Effects are animate, immutable Objects. Effects iterate over a single row of frames. They are meant to encapsulate special effect and animation logic. For example, a projectile may produce a cloud of dust when impacting a surface or body of water may ripple when a Sprite moves through it. The dust cloud and ripples are Effects.

**Properties**

* `dim: Dimensions`
* `count: int`

!!! todo
    Further Refinement of Effects. After examining Asset files, the groupings that seem to logically classify this Asset through its "differentia" are: Permanent-Continuous, Permanent-Periodic, Permanent-Hazard, Temporary-Collectables, Temporary-Hazard. Needs more thought.
    
### Temporary

Temporary Effects are brief, short-lived effects, such as explosions or magic. After their animation is concluded, they are garbage-collected and removed from the Board.

**Animation: TemporaryAnimation**

- `if animation.frame =< properties.count: animation.frame += 1`

**Frame: IterableFrame**

* `keys(id, animation): returns [ "{id}-{animation.frame}" ]`
* `index(self, id, properties): returns { "{id}-{properties.count}": (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: AnimatorState**

* `layer: str`
* `depth: int`
* `height: int`
* `position: Position`
* `animation: Animation`

### Persistent

Persistent Effects are long-term, continuous effects, such as water ripples or windmills, whose animation continuously cycles when the frame count is reached.

**Animation: PersistentAnimation**

- `if animation.frame >= properties.count: animation.frame = 0`

**Frame: IterableFrame**

* `keys(id, animation) : [ "{id}-{animation.frame}" ]`
* `index(self, id, properties): returns { "{id}-{properties.count}": (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: AnimatorState**

* `layer: str`
* `depth: int`
* `height: int`
* `position: Position`
* `animation: Animation`

## Crafts

* Property File: `/src/assets/crafts/main.yaml`

Crafts are Assets that can be instantiated through game [Mechanics](./05-mechanics.md), such as `CommerceMechanics` or `ChemistryMechanics`. All Crafts have a `cost` associated with them. 

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
* `mass: int`

### Struts 

*Struts* are inanimate, immutable Assets. *Struts* are meant to encapsulate the concept of property in the game, e.g. houses, fences, etc. In other words, they possess an `owner`. 

Struts may be placed on the Board through the state files manually, but are instantiated ingame through the `build` [Intention](./04-intentions.md). This is an oversimplification, as Struts are closely related to [Asset Compositions](./03-compositions.md), but generally true.

**Animation: None**

N/A

**Frame: SingleFrame**

* `keys(id, None) returns [ id ]`
* `index(self, id, properties): returns { id: (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: PropertyState**

* `layer: str`
* `depth: int`
* `height: int`
* `position: Position`
* `owner: str`

## Resources

TODO

## Sheets

* Property File: `/src/assets/sheets/main.yaml`

*Sheets* are animate, mutable Assets whose files are arranged in rows of Frames. Sheet form the core Asset of the gameplay loop; they are used to encapsulate character entities, such as the Player and NPC Sprites. Most of the application is scaffolding for the complex interactions and calculations that occur when Sheet Assets interact.

**Sheet Specification**

The rows of a Sheet are identified by *Direction*, *Action* and *Frame*. Each row is identified by a tuple (Direction, Action), and then divided horizontally into contiguous horizontal Frames. 

!!! important
    For Sheets, it is assumed coordinates of an image in the Asset file are *completely determined* by Action, Direction and Frame. It is assumed Actions form contiguous rows partitioned by Direction, and frames are organized in horizontal cells of equal length. This specification is enforced on the application level.

**LPC Specification**

While an Action set an be defined in `/src/data/config/actions/main.yaml`, the documentation will often assume the LPC (Liberated Pixel Cup) specification when discussing Action, Direction and Frame, without loss of generality. The values for these fields in the LPC Spec are enumerated below,

* Direction: `up, left, down, right`
* Action: `cast, thrust, walk, slash, shoot, die`
* Frame: `0, 1, 2 , ... , n(Action)`

Where `n(Action)` is the number of frames per Action. The frames per Action for the LPC Spec are given below,

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
    In the LPC specification, the `thrust` Action plays double-duty for spears and shovels. The spear is a Weapon, whereas the shovel is a Tool. With LPC assets, the animations of these pieces of Equipment are governed by the `thrust` state. In other words, different types of Equipment do not necessarily map to different Action states. The engine accounts for this by treating the Equipment Group of Assets as "stateless" and inherently bound to the state of a Sprite Sheet Asset. See [Equipment documentation](./02-sprites.md#equipment) for more information.

**Action**

Actions are part of the Animation state. An Action implicitly contains Directions, i.e. an Action cannot be specified without accompanying Direction(s). The "space" of the (Action, Direction) space is configured by Sheet Properties. 

This snippet from the [Schemas](./appendices/01-schemas.md#configuration-actions) shows the general structure of an Action,

```yaml
<action-key>:
    count: <count>
    delay: <delay>
    directions:
        <direction-key>:
            row: <row>
```

* `<action-key>: str` - Ranges over `cast, thrust, walk, slash, shoot, die` (LPC)
* `<direction-key> : str` -  Ranges over  `up, left, down, right` (LPC)
* `count: int` - is the number of frames in the Action row grouping. 
- `delay`: (*Optional*) Number of Engine ticks to accumulate before a frame update. Used to control the speed of the animation. Defaults to 1. 

**Action Sets**

Many Sheet Assets reuse the same Action specification. Common Asset Action specifications are configured and indexed in the Action Configuration file. These configurations are referred to as Action Sets. Each Sheet specifics an Action Set in its property index file. See [Action Configuration Schema](#action-configuration) below for more details. 

**Stacks**

A Stack is a list of Sheets keys to superimpose over one another to form the resultant Sheet used in the game. The Sheet stacks are drawn in the order they are specified, i.e. the first entry has the lowest Z coordinate, with each subsequent entry being stacked on top.

For example, the `src/assets/sheets/<sheet-category>/features/hair-blonde-bangs.png` might be stacked on top of `src/assets/sheets/<sheet-category>/skins/male-dark-human.png` to create a new Sheet asset used in the game. This Sprite stack is assembled in the [Registry](./00-overview.md#registry) using the `stack` property during the [application bootstrap](./10-architecture.md#initialization). The assembled `stack` is saved as a Sheet Asset, using the `<sheet-id>` as the Asset key. In other words, once assembled, Stacks are effectively new "virtualized" Assets.

!!! note
    It is assumed all Sheets in a Stack conform to the same (Action, Direction) row mapping.

**Properties: SheetProperties**

* `dimensions: Dimensions`
* `stack: List[str]`
* `hitboxes: List[Hitbox]`
* `actions: Actions`
* `mass: int`

### Pixies

Pixies are Sheets that have simple game mechanics, e.g. are excluded from the complex calculations of the [Intention Mechanic](./04-intentions.md). *Pixies* encapsulate simple Characters, such as animals or bugs.

**Animation: StateAnimation**

- `state.animation.frame += 1`
- `if state.animation.frame >= properties.actions[state.animation.action].count: state.animation.frame = 0`

**Frame: StateFrame**

* `keys(id, animation): returns [ "{id}-{animation.action}-{animation.direction}-{animation.frame}" ]`
* `index(self, id, properties): returns { "{id}-{properties.actions.*}-{properties.actions.*.directions.*}-{properties.actions.*.count}": (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: AnimatorState**

* `layer: str`
* `depth: int`
* `height: int`
* `position: Position`
* `animation: Animation`

### Sprites

Sprites are Sheets over multiple rows of frames, where each row may have a variable number of frames. Sprite have a diverse palette of Animation Actions. They are meant to encapsulate the core game entities, e.g. the player, NPCs, and enemies.

**Animation: StateAnimation**

- `state.animation.frame += 1`
- `if state.animation.frame >= properties.actions[state.animation.action].count: state.animation.frame = 0`

**Frame: SpriteFrame**

* `keys(id, animation): returns [ "{id}-{animation.action}-{animation.direction}-{animation.frame}" ] + [ <equipment-frames>]`
* `index(self, id, properties): returns { "{id}-{properties.actions.*}-{properties.actions.*.directions.*}-{properties.actions.*.count}": (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: SpriteState**

* `layer: str`
* `depth: int`
* `height: int`
* `position: Position`
* `velocity: Velocity`
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

Widgets are used to constructs Menus. They are not a part of the core gameplay loop and have special Mechanics for their interaction. 

Widgets are covered in their own section, [Widgets](./06-widgets.md).

## Fonts

Fonts are stateless Assets initialized at [runtime](./10-architecture.md#initialization), i.e. they are not deployed onto the Board; instead Fonts are utilized by the [Screen](./00-overview.md#screen) to render text whenever the game loop calls for text. 

A Font is a wrapper `.ttf` file and a data structure used to configure the Font styling. Each styled Font is stored in the [Registy](./00-overview.md#registry) using its file name. The [Screen](./00-overview.md#screen) retrieves these Fonts from the Registry and passes them to the rendering engine when it needs to write text to screen.

In other words, a Font Asset encapsulates both the script and the styling applied to the script. 

See [SDL Architecture documentation](./10-architecture.md#sdl) for more information on Fonts.

**Properties: FontProperties**

* `alignment: str`
* `bold: bool`
* `italics: bool`
* `margins: int`
* `color:`
    * `r: int`
    * `g: int`
    * `b: int`
    * `a: float`