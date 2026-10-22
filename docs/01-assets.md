# Ontology: Assets

This document serves to specify the Asset architecture and provide key definition for game terminology.

!!! note "Definition"
    An Asset is an image file.

!!! note "Liberated Pixel Cup"
    [LPC](https://lpc.opengameart.org/) Assets are bundled with the application by default.

## Overview 

The Asset directory (and all subdirectories) contains Asset Image Files (`*.png`) and Asset Property indices (`*.yaml`). The [initialization](./11-architecture.md#initialization) reads in all of these files recursively and then use the property indices to index each Asset file into the [Registry](./00-overview.md#registry). Each image file that appears in the Asset directories must be configured in a YAML file to get indexed and injected into the game. The property configuration in the `*.yaml` files must conform to the [Asset property schema](./appendices/01-schemas.md#model-properties) of the respective Asset Category it is configuring. 

!!! important
    All `*.yaml` files in the Asset directories are merged into a single schema, so every key must be unique. If two image files have the same name, one of them will be overwritten during [Registry indexing](./00-overview.md#registry).

### Asset: Concepts

#### Concept: Identity

**IDs & Names**

IDs are used to map Asset Files to images loaded into the [Registry](./00-overview.md#registry), to ensure each Asset is only loaded into the memory once, no matter how many times it is rendered in a single frame. In other words, IDs uniquely identify a physical Asset File, but not in-game entities.

Names are used to uniquely identify an ingame entity. A single Asset ID may have multiple Names. A Name corresponds to a particular deployment of an Asset onto a Board. 

In short, a Name identifies an Asset's deployment. A ID is what binds a deployed Asset to its Asset File.

#### Concept: Mutability

**Properties & State**

*Properties* are static and never changed by game Mechanics. Properties determine the immutable characteristics of Assets, e.g. their dimensions and hitboxes. They are loaded side-by-side with the Asset files in the `/src/assets/**` directory. All Assets have, at bare minumum, a Dimension property, specifying their respective width and length, and a Priority property, that specifies the [statically configured sort key](./11-architecture.md#rendering) for their relative rendering order. Dimension is a Cartesian coordinate (tuple), whereas Priority is an integer.

*State* is dynamic and can be changed by [Mechanics](./05-mechanics.md). State determines the mutable characteristics of an Asset, e.g. the current Position of an ingame Asset, the current Animation, etc. All Assets have a *Position* mutable state; most (except for Widgets) have a *Layer*. Position is given as a Cartesian coordinate (tuple), whereas Layer is a categorical variable.

!!! note "Layers"
    The concept of a Layer is defined more explicitly in [Overview documentation](./00-overview.md#layers). It suffices to think of Layers as floors in a house, where each floor is differentiated by its topography but contributes to the same space. In-game, Layers are traversed by the Player interacting with Doors.

State files are maintained in `/src/data/state/<board-key>/**` directory, where `<board-key>` is a unique identifer for a [Board](./00-overview.md#board).

**Base Model: AssetProperties**

- `dimensions`: Asset Frame dimensions.
- `priority`: Static ordinal render sort key. 

All Asset Properties inherit fields from this model.

**Base Model: AssetState**

- `layer`: Board Layer key.
- `elevation`: Elevation render sort key.
- `anchor`: Offset for ground render sort key.
- `substrate`: Intra-elevation render sort key.
- `mutators`: General behavioral flags for rendering and logic.

All Asset States inherit fields from this model.

#### Concept: Animacy

**Frames & Animations**

A *Frame *represents the binding of an Asset to a particular partitioning of its raw image file into a *Frame space*. Frames expose interfaces for *indexing* the Frame space via Asset Properties, and they also expose interfaces for *accessing* Frame space via Asset State.

In other words, Asset Properties determine the metric used by the Engine to measure the Asset's Frame space, whereas Asset State determines where in its Frame space the Asset currently resides. 

This is the reason for distinguishing Asset Categories and Asset Instances in the Hierarchy: Frames in a Sprite Sheet represent Actions, Frames in a Resource represent Lifespan Stages, Frames in an Effect represent Periodicity, etc. These are different stateful dispositions for an Asset to assume that are categorically distinct and manifest in the atlasing strategy used by the image file. This space is described by the particular configuration of an Asset's Properties, and furthermore, to exist on the [Board](./00-overview.md#board), an Asset must have a strategy for associating its State with a particular Frame described by its Properties.

To extend the analogy, an *Animation* represents a strategy for navigating the Frame space over time (hence its interface depends on a time delta). Animations projects the internal state changes in an Asset onto a particular trajectory through its Frame space.

When an Asset implements an Animation, this is accompanied by its State possessing an `animation` field. The purpose of this field is mutate over time and thus describe the trajectory of the Asset through its Frame space.

**Model: AnimationState**

- `action`: Action key of Animation.
- `direction`: Directiony key of Animation.
- `frame`: Frame index of Animation.
- `tick`: Engine tick accumulator. Used in conjunction with Action `delay` to control the speed of the Animation.

#### Concept: Physicality

Many Asset Categories have a Mass Property. Only Assets with Mass can participate in collisions and other kinematic events. An Asset's mass determines its behavior within the physics of the game,
 
- $m > 0$: **Dynamic Body**. Participates in momentum calculations.
- $m = 0$: **Static Body**. Treated as having infinite mass ($m \to \infty$) in physics equations. Its Velocity is unaffected by collisions, but its immobility forces dynamic bodies to resolve overlap.
- $m = -1$: **Sensor**. The engine detects the spatial intersection for game logic (like SwitchMechanics or DoorMechanics), but CollisionMechanics bypasses it completely during the overlap resolution phase.

See [SpatialMechanics](./05-mechanics.md#spatial) for more information.

#### Concept: Appearance

**Rendering**

World rendering evaluates spatial geometry using discrete macro-elevations, intra-elevation substrate planes, ground perspective, and coplanar priority, known respectively as Elevation, Substrates, Perspective and Priority,

$$
\text{sort_key}(x) = \Big(x.\text{elevation},\; x.\text{substrate},\; \text{ground_y}(x),\; x.\text{properties.priority}\Big)
$$

1. **Primary Key (`x.elevation` $\in \mathbb{Z}_{\ge 0}$)**: Discrete topological story or platform tier (`0`, `1`, `2`, ...).
2. **Secondary Key (`x.substrate` $\in \mathbb{Z}_{\le 0}$)**: Intra-elevation rendering plane within macro-elevation $E$.
3. **Tertiary Key (`ground_y` $\in \mathbb{Z}$)**: Continuous geometric perspective: $\text{ground_y} = \text{int}(x.\text{state.position.y} + x.\text{dimensions.l} + x.\text{state.anchor})$.
4. **Quaternary Key (`priority` $\in \mathbb{Z}$)**: Coplanar tie-breaker declared on immutable `AssetProperties`.

See [Rendering documentation](./11-architecture.md#rendering) for more information.

**Substrates**

Certain Assets have a dedicated Substrate to preserve the fidelity of their rendering order. These values hydrated onto `state.substrate` via [MaterialIndex](./appendices/01-schemas.md#configuration-materials).

--8<-- "static/md/asset-substrates.md"

!!! @TODO(07-04)
    This entire procedure needs re-evaluation now that Substrates are not Elevations, i.e. prior to Phase 07.04 Substrates were used to lazily-load Elevations. Now they are a dedicated partition of the sort key `(elevation, substrate, ground, priority)`

During [CollisionMechanics](./05-mechanics.md#collisionmechanics) and Perimeter generation, all negative Substrates are collapsed into `elevation = 0`, i.e. $\text{elevation} \in [-\infty, 0] \to \text{elevation} = 0$, in order that all Assets on these Substrates may participate in collisions at `elevation = 0`.

#### Concept: Materiality

Many Assets have their Frame space defined over a Material partition. Material affects the color palette of an Asset and has other consequences in the [Economy](./10-emergence.md#economy).

The *Material Space* is further subdivded into non-overlapping Genera,

--8<-- "static/md/material-genera.md"

`chromatics`, being a discrete shade of color, requires a `host` material to accept its payload.

If an Asset indexes its Frame space over Material, then its Asset State must have a `material` field to specify which Material it should instantiate when deployed.

See [Material documentation](./03-compositions.md#material) for more information.

**Model: Material**

- `genus: str`: Partition of Material Space.
- `host: str`: Host Material for Chromatic Genera.

### Asset: Hierarchy

While Assets are instantiated by injecting a common root class with component behaviors (see [next section](#asset-architecture)), the Assets which result from the Entity-Component-System (ECS) injection still conform to a strict hierarchy of Categories and Instances. The property and state [schemas](./appendices/01-schemas.md) encode Asset Categories and Instances into their top-level keys.

!!! note
    The Asset Hierarchy can be thought of as a data abstraction governing the schemas, which in turn drive the ECS instantiation. 

!!! note
    An analogy may be drawn from the Asset Hierarchy to Edward Zalta's Metaphysics: properties *encode* an Asset, state *exemplifies* an Asset. 

```mermaid
--8<-- "static/mmd/asset-hierarchy.mmd"
```

#### Hierarchy: Category

Asset *Categories* form the top layer of the hierarchy. Each Asset Category is defined by its static properties; an Asset's Category determines what type of properties it will parse from the property files and inject into its deployment. 

Each Category is differentiated by its purpose and place in the semantics of the Engine.

- Tiles: Environmental. These Assets determine the background and macro-level processes that underlie the Engine.
- Object: Functional. These Assets perform functions and alter their states. 
- Effects: Periodic. These Assets undergo changes in their state according to fundamental frequencies.
- Geography: Procedural. These Assets are generated via physical principles embodied by the Engine.
- Resources: Biological. These Assets undergo lifecycles and have reactive states that change as the result of the environment.
- Crafts: Structural. These Assets provide the foundation and topology of the Board.
- Sheets: Intentional. These Assets perform Actions and engage Intentionally with the Board.
- Widgets: Metalogical. These Assets display metadata about the world to the User.

--8<-- "static/md/asset-categories.md"

#### Hierarchy: Instance

Each Category has Instances. Asset *Instances* form the bottom of the Asset Hierarchy. Each Asset Instance is defined by its dynamic nature; an Asset's Instance determines what type of state it will parse from the state files and inject into its deployment. 

Each Instance is differentiated by its State, Frame and Animation.

--8<-- "static/md/asset-instances.md"

#### Hierarchy: Taxonomy

An Asset's order in the Asset Hierarchy is encoded into its Taxonomy. These attributes exist on every Asset instantiated within the game. A Taxonomy is neither a state, a configuration or a property. Taxonomy represents the full, unambiguous identity of a deployed Asset,

- `id: str`: Uniquely identifies the Asset file. It must match a file found in the `src/assets/**` directory.
- `name: str`: Uniquely identifies the physical deployment of the Asset. Every Asset Instance deployed onto a Board has a unique `name`.
- `category: str`: Determines what Property model is employed by the Asset. The Category must be configured by a `src/assets/<category>/**/*.yaml` property index file.
- `instance: str`: Determines what State model is employed by the Asset. An Asset's state is hydrated from the `data/state/<board>/**/*.yaml` directory.

`(category, instance)` collectively map to the components `(frame, animation, hitbox, properties, state)` injected into an Asset class during the [application initialization](./11-architecture.md#initialization). More specifically, Category maps to properties ($\text{category} \to \text{properties}$), and Instance maps to the remaining components ($\text{instance} \to (\text{frame}, \text{animation}, text{hitbox}, \text{state})$).

The State and Property model of an Asset can be calculated (and is, during [application bootstrapping](./11-architecture.md#initialization) via Pydantic) from its (Category, Instance)-node, but (Animation, Frame, Hitbox) are independent of the node in the Asset Hierarchy. These components must be specified through a [Recipe](./appendices/01-schemas.md#configuration-recipes).

### Asset Architecture

Every physical entity in the game is an instance of the unified Asset class. The distinction between a Tile, a Gate, or a Sprite is determined entirely by the data models and components injected into them. Behaviors are decoupled from Assets and managed entirely by *Mechanic* classes that iterate over the [Board](./00-overview.md#board) Assets. See [Mechanics documentation](./05-mechanics.md) for more information.

The Recipe for an Asset, i.e. the list of components which go into a particular Asset Instance, is specified in the [Recipe](./appendices/01-schemas.md#configuration-recipes) configuration file. The components of each Assets are enumerated below,

1. **Model: Properties** A model defining immutable data.
2. **Model: State** A model defining mutable data.
3. **Behavior: Animation** Stateless strategies injected into the Asset. These contain the specific logic for updating Animation frames.
    - `animate(state, properties)`: Interface for applying animation logic to Asset state.
4. **Behavior: Frame:** A static schema calculation used by the renderer to determine the correct texture string keys. 
    - `index(id: str, properties: AssetProperties) -> Dict[str, Tuple[int, int, int, int]]`: Interface for indexing Asset frames in Registry.
    - `keys(id: str, state: AssetState) -> List[Tuple[str, int, int]]`: Reflexive intrinsic state projection for dynamic 60 Hz draw passes.
    - `eras(id: str, calendar: CalendarState) -> List[Tuple[str, int, int]]`: Macro-temporal epochal projection for static pre-rendered canvas baking.
    - `channels(id: str, state: AssetState, properties: AssetProperties) -> List[Tuple]`: Emits auxiliary shader and texture modulation directives.
5. **Behavior: Hitbox:** Stateless collision boundary resolution strategies injected via Recipes. Resolves active physical obstacles dynamically without mutating cached properties:
    - `elevations(properties: AssetProperties, state: AssetState) -> List[int]`: Emits the discrete elevation tiers the entity participates in.
    - `get(properties: AssetProperties, state: AssetState, elevation: int, frame: Optional[Frame] = None) -> List[Hitbox]`: Emits active physical collision footprints at the requested elevation, accounting for animation frame states (e.g., Attackboxes).

!!! note
    An Asset can be a single logical entity composed of multiple superimposed rendered textures, i.e. [Sheets](#sheets), therefore a Frame component returns a `List[(str, int, int)]` rather than a single `str`. The tuple `(int, int)` controls how much the frame is offset from its origin (mainly used in [Expressions](#expressions) to pin a [Cursor Expressions](#cursors) to the relative Position of a Sprite).

## Category: Tiles

* Property File: `/src/assets/tiles/**/*.yaml`

Tiles are static Assets that form environmental foundation of the game. 

**Behavior: Rendering**

When a Tile is drawn, it is rendered as a `multiple` of the unit Tile, usings the Dimensions configured in the Asset directory to expand the multiplied area.

**Behavior: Friction**

Tiles have coefficients of friction. These coefficient are used by [MotionMechanics](./05-mechanics.md#spatial) to determine the rate of velocity decay for Frictive Assets traversing their area.

**Properties: TileProperties(AssetProperties)**

* `friction: float`

**Animation: None**

N/A

**Hitbox: StaticHitbox**

* `get(properties, state, frame): returns properties.hitboxes`

**State: MultiplerState(AssetState)**

* `multiple: Multiple`

### Tile: Environ

A Environ Tile represents the environment. They participate in climatic events and macro-level state changes in the [Ecology](./09-ecology.md).

**Behavior: Rendering**

Tiles have the lowest terrain Substrate; They are always rendered underneath the other Assets in the Hierarchy, regardless any calculations involving `elevation`, `substrate`, `ground`, or `priority`. 

Moreover, they are not included in the core rendering loop; Instead, they are prerendered once and drawn from cache. See [Rendering documentation](./11-architecture.md#rendering) for more information.

**Behavior: Seasonality**

Environ Tiles undergo Frame changes based on the accumulation of time on the [Board](./00-overview.md#board). In other words, Environ Tiles have the unique property of having their Frame depend on an external State, rather than internal State. All rendering of Environ Tiles occurs through the `Frame.eras()` interface to account for this external dependency.

For this reason, Environ Tiles leverage a SeasonalFrame and event-driven reconstruction triggered as the Board undergoes Seasons. See [Ecology documentation](./09-ecology.md) for more information.

**Atlas: (Row: Season, Column: Period)**

- columns: `^(?:onset|peak|decline)-[0-9]$`
- rows: `^(?:spring|summer|autumn|winter)`

### Tile: Canopy

Canopy Tiles are hardcoded to always render on on top of all of other Assets, regardless of their `elevation` or `priority`. 

!!! important
    The *single* exception to this rule is Widgets. Canopy Tiles are an "in-world" Asset, and thus their render ordering is superseded by Widgets.

**Frame: SingleFrame**

* `keys(id, state): returns [ (id, 0, 0) ]`
* `index(id, properties): returns { id: (0, 0, properties.dimension.w, properties.dimensions.l) }`

### Tile: Grid

A Grid is a special Tile reserved for use in the [Editor Menu](./06-widgets.md#menus). It is used as an overlay in the Editor, to create a spatial grid that can be traversed through focus. 

!!! @TODO(05)
    Reatlasing of Grid Tiles needs to occur.

There must be precisely *two* Grid tiles:

- `focus`: A Grid Tile to represent active selections.
- `cell`: A Grid Tile to represent idle selections.

**Frame: SingleFrame**

* `keys(id, state): returns [ (id, 0, 0) ]`
* `index(id, properties): returns { id: (0, 0, properties.dimension.w, properties.dimensions.l) }`

## Category: Objects

* Property File: `/src/assets/objects/**/*.yaml`

Objects are Assets that encapsulate interaction and reaction. Objects participate in [CollisionMechanics](./05-mechanics.md#collisionmechanics) and may undergo instantaneous changes of their state due to environmental factors. However, Objects do not implement an Animation; All changes of an Object's Frame are handled through the mutation of State attributes. 

**Atlas: (row: Count, column: Material)**

- columns: `^(?:ceramics|chromatics|geologics|metallics|organics)`
- row: `^[0-9]`

**Properties: ObjectProperties(AssetProperties)**

* `hitboxes: List[Hitbox]` 
* `count: int = 1`
* `mass: int`
* `materials: str`

**State: ObjectState(AssetState)**

* `material: str` 

All Objects extend this base class.

**Frame: ObjectFrame**

* `index(id, properties): returns { "{id}-{i}-{j}": (j * properties.dimension.w, i * properties.dimensions.l, properties.dimensions.w, properties.dimension.l )} for i,j in product(properties.count, properties.material)`

**Animation: None**

N/A

### Object: Chests

*Chests* are Objects with a binary state whose Frame can be changed by the Player or Sprite entering the `interact` [Intention](./04-intentions.md) while in the immediate proximity of the Chest. When `switch == true`, the Chest is *on* (open). When `switch == false`, the Chest is *off* (closed).

A Chest is *reusable* through the `interact` [Intention](./04-intentions.md), meaning [Inventory Loot](./02-sprites.md#inventory) can be taken out of and also placed into a Chest. The `content` state field manages the current contents of the Chest through a list of Inventory Loot keys.

When interacting with a Chest, the [Player](./02-sprites.md#player) is shown the [Chest Menu](./06-widgets.md#menus), allowing them to exchange the contents of their Inventory Loot with the contents of the Chest. A Sprite may also enter into an `interact` Intention with a Chest through its [Intention Transition Matrix](./04-intentions.md#transition-matrix). This interaction is managed through a dedicated Sprite [Mechanic](05-mechanics.md)

**State: ContainerState**

* `switch: bool`
* `content: List[str]`

**Hitbox: StaticHitbox**

* `get(properties, state, elevation, frame): returns properties.hitboxes`

### Object: Crates

Crates are Objects who state can be altered by collisions. When acted upon by an external force, momentum is transferred to the Crate and it acquires velocity. See [CollisionMechanics](./05-mechanics.md#collisionmechanics) for more information on game physics.

**State: MotiveState**

* `velocity: Velocity`

**Hitbox: StaticHitbox**

* `get(properties, state, elevation, frame): returns properties.hitboxes`

### Object: Doors

Doors are Objects that alter a Sprite's `layer`. When a Sprite interacts (`state.intention = 'interact'`) with the hitbox of a Door, the `sprite.state.layer` is changed to the `door.state.outlayer` and `sprite.state.position` is changed to the `door.state.out` Position.

**State: DoorState**

* `outlayer: str`
* `out: Position`

**Hitbox: LayeredHitbox**

* `get(properties, state, elevation, frame): returns properties.hitboxes[state.layer] if LayerProjection.IN.value else properties.hitboxes[state.outlayer]`

### Object: Gates

Gates are Objects with a binary state linked to Plates. When a Gate is on (open), it does not have hitboxes and dynamic Assets can pass freely through its area. When a Gate is off (closed), its hitboxes prevent dynamic Assets from passing through its area.

Gates do not switch their states of their own accord. A Plate automatically updates the `state.switched` of its linked Gate, so when the Plate is on, the Gate is on, and when the Plate is off, the Gate is off.

**State: SwitchState**

* `link: str`
* `switch: bool`

**Hitbox: SwitchHitbox**

* `get(properties, state, elevation, frame): returns [] if state.switch else properties.hitboxes`

### Object: Obstacles

!!! @TODO(11)
    Obstacles need moved to Geography and inducted into procedural generation. This entire section is subject to radical change post Phase 11.
    
Obstacles are immutable, inanimate Objects. They are meant to encapsulate natural obstructions such as rocks, outcroppings and other barriers.

**State: Positional**

* `layer: str`
* `elevation: int`
* `position: Position`

**Frame: SingleFrame**

* `keys(id, state): returns [ (id, 0, 0) ]`
* `index(id, properties): returns { id: (0, 0, properties.dimensions.w, properties.dimensions.l) }`

**Hitbox: StaticHitbox**

* `get(properties, state, elevation, frame): returns properties.hitboxes`

### Object: Plates

Plates are Objects with a binary state. Furthermore, that state can be instantaneously altered by collision, e.g. when a Sprite enters its hitbox. When a collision occurs, a Plate will flip its `switch`. When activated, a Plate in turn notifies the state of its `link`-keyed Gate to change.

!!! note
    Plates must have their `mass` property configured to be `-1`, to exclude them from the collision resolution while keeping the collision detection active, i.e. Plates do not move due to collisions, but register when other Assets are intersecting them. Plates are considered *Sensors*. See [CollisionMechanics](./05-mechanics.md#spatial) for more information.

**State: SwitchState**

* `switch: bool`

**Hitbox: SwitchHitbox**

* `get(properties, state, elevation, frame): returns [] if state.switch else properties.hitboxes`

### Object: Rafts

Rafts are kinematics Objects that allow other Assets to traverse [Fluid](#fluids) streams without entering the `submerged` state or being swept away individually. Rafts do not obstruct [Fluid flow](#fluids), meaning they still acquire velocity in the [Fluid stream](#fluids).

* When deployed in a Fluid corridor, a Raft drifts along the Fluid's `source` vector at a speed proportional to `flow`.
* Characters boarding a Raft have their `mutators.triggers.submerged` mutator suppressed.
* While aboard, locomotion is evaluated relative to the Raft's area: $\vec{v}_{\text{world}} = \vec{v}_{\text{locomotion}} + \vec{v}_{\text{raft}}$

**State: MotiveState**

* `velocity: Velocity`

**Hitbox: StaticHitbox**

* `get(properties, state, elevation, frame): returns properties.hitboxes`

### Object: Signs

Signs are linguistic Objects whose `content` is transmitted into a [Text Menu](./06-widgets.md#menus) when a Player enters into the `interact` [Intention](./04-intentions.md) with them.

Signs utilize `persona` and `lexicon` keys to grab the appropriate content from the [Library](./08-plots.md#library)

**State: DialogueState**

* `persona: str`
* `lexicon: str`

!!! @TODO(10-05)
    Add linkage between Sign lexicon key and Resource SeasonMechanics.

**Hitbox: StaticHitbox**

* `get(properties, state, elevation, frame): returns properties.hitboxes`

## Category: Crafts

* Property File: `/src/assets/crafts/**/*.yaml`

Crafts are Assets instantiated through [Game Mechanics](./05-mechanics.md) or utilized in [Compositions](./03-compositions.md). They encapsulate structures and topologies in the game. Crafts are used to establish boundaries, impose perimeters and stamp decals onto the [Screen](./00-overview.md#screen).

Many Crafts are inherently bound to the process of [Composition](./03-compositions.md). Several specifications (Struts, Stairs, Decor) are covered in more detail in the [Composition documentation](./03-compositions.md#asset-specifications)

Craft Asset files are organized into a (Blueprint, Material) atlas, where each row denotes a different structural schematic (Blueprint) and columns denote an aesthetic quantity (Material) used to bind the [crafting, economic and resource Mechanics](./05-mechanics.md#world) into a unified system. 

Just as the Material space is partitioned into Genera, the *Blueprint Space* is furthered subdivded into non-overlapping partitions of Schema.

--8<-- "static/md/blueprint-schema.md"

**Model: Blueprint**

* `schema: str`

**Atlas: (row: Blueprints, column: Materials)**

* columns: `^(?:ceramics|chromatics|geologics|metallics|organics)`
* rows: `^[?:buildings|corridors|columns|directions|enclosures|orientations|inclines]`

**Properties: CraftProperties(AssetProperties)**

* `mass: int = 0`
* `material: Optional[Material] = None`
* `blueprints: Optional[str] = None` 
* `hitboxes: Optional[Dict[str, List[Hitbox]]] = None`

**State: CraftState(AssetState)**

* `material: str`
* `blueprint: str`
* `multiple: str`

All Crafts inherit fields from this State model.

**Frame: MaterialFrame**

* `keys(id, state): returns [ (f"{id}-{state.material}-{state.blueprint}", 0, 0) ]`
* `index(id, properties): returns { f"{id}-{i}-{j}: (i * properties.dimensions.w, j * properties.dimensions.l, properties.dimension.w, properties.dimensions.l) } for i, j in product(properties.blueprints, properties.materials)`

**Hitbox: MaterialHitbox**

* `get(properties, state, elevation, frame): returns properties.hitboxes[state.blueprint]`

### Craft: Bridges

Bridges are Crafts that elevate dynamic Assets over [Fluid](#effect-fluids) corridors, annular pools, and [Shoreline](#category-geography) margins without entering the `submerged` state.

To achieve this functionality, broadly speaking, the following occurs,

* Bridges are registered as Sensors ($m = -1$). Therefore, they do not participate in momentum transfer or collisions.
* Bridges are excluded from the [Boards Physics Queries](./00-overview.md#board), allowing [Mechanics](./05-mechanics.md) to pathfind across river crossings.
* In [MotionMechanics](./05-mechanics.md#motionmechanics), intersecting a Bridge marks the Asset as being on a surface:
  * [Fluid](#effect-fluids) immersion and current velocity drift are suppressed ($\vec{v}_{\text{drift}} = \vec{0}$).
  * [Shoreline](#category-geography) step-down nudges, ledge constraints, and splash particle emissions are bypassed.
  * `mutators.triggers.submerged` is cleared to `False`.

**Behavior: Rendering**

Bridges belong to a dedicated [Substrate](#concept-appearance), `substrate = -1`. This guarantees that Bridge areas render above [Environ Tiles](#tile-environ), [Fluids](#effect-fluids), and [Shorelines](#category-geography), while allowing dynamic Assets crossing their area to render above the Bridge via their baseline footprint ($y + l$) and [the Painter's Algorithm](./11-architecture.md#rendering).

## Category: Cursors

!!! @TODO(06-02)
    Entire system needs re-evaluated following Phase 07-04's simplifcation of the Hierarchy through Material.

* Property File: `/src/assets/cursors/**/*.yaml`

Cursors are Assets that bind to other Asset States.

### Cursor: Expressions

Expressions are "Phantom States" used as visual decorators. Unlike most Assets, Expressions are not instantiated as physical entities on the [Board](./00-overview.md#board). Instead, their spatial offsets and frame keys are calculated dynamically by the [Cradle](./00-overview.md#board) and embedded directly into a [Sprite's State](./02-sprites.md) as pure data. When the [Sprite](./02-sprites.md#psyche) is rendered, the SpriteFrame reads this embedded data and superimposes the Expression onto its Frame.

**Required: Expressions**

Due to the nature of Expressions as representations of a Sprite's internal state, there exists a hard dependency between Expression image files and their properties and the possible Expression frame enumerations. Each file name must exist and the following frames must be indexed by the Expression property index,

- bubbles: `agreement`, `anger`, `confusion`, `disagreement`, `loquacity`, `surprise`, `tired`
- buffs: TODO

**Animation: None**

N/A

**Frame: IndexFrame**

* `keys(id, state): returns [ (id, 0, 0) ]` *(Note: Bypassed during active rendering; `SpriteFrame` handles the dynamic offset injection).*
* `index(id, properties): returns { "{id}-{properties.frames[i]}": (i * properties.dimension.w, 0, properties.dimension.w, properties.dimensions.l) }`

**"Phantom" State: AttachmentState(AssetState)**

* `icon: str`
* `offset: Position`
* `ttl: int`: Number of game ticks for which the Expression is present.

**Hitbox: None**

N/A

### Cursor: Projectiles

Projectiles are spawned via the `shoot` Action (entered through the `attack` [Intention](./04-intentions.md) when the `longbow` [Equipment](./02-sprites.md#equipment) is slotted, for instance) with a certain direction and velocity and then follow a fixed trajectory based on the spawn conditions. Projectiles will either impact a hitbox or trigger garbage-collection and be removed from the [Board](./00-overview.md#board).

**Animation: None**

N/A

**Frame: SingleFrame**

* `keys(id, state): returns [ (id, 0, 0) ]`
* `index(id, properties): returns { id: (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: MotorState(AssetState)**

* `initial: Position`
* `velocity: Velocity`

## Category: Effects

* Property File: `/src/assets/effects/**/*.yaml`

Effects are periodic Assets used to encapsulate environmental factors, hazards, pickups, and interactive mechanisms. 

Most Effects iterate over a single row of frames using IterableFrame and advance via FrequencyAnimation. The only thing that differentiates each instance of an Effect is its State model (excepting [Fluid](#effect-fluids) which plays an instrumental role in [Ecology](./09-ecology.md)).

**Behavior: Periodicity**

Rather than implementing separate Animation classes to handle Effect animations (which would lead to a combinatorial explosion with the composition of Animation and State implementations necessary to span the space of possible Effects instances, e.g. HarzardContinuousAnimation, HazardPeriodicAnimation, HazardTemporaryAnimation would have the same functional purpose of being a Hazard but different logic handling their Animation), Effects have Frequencies that determines how their Animation is handled.

In other words, the State Model determines the function of the Effect, but the Frequency determines the Animation update strategy.

```mermaid
--8<-- "static/mmd/models-effect.mmd"
```

**Model: Frequency**

* `type: str` (`continuous`, `periodic`, `temporary`)
* `delay: int` (tick pacing between frames)
* `amount: int` (tick interval for periodic resets)
* `persist: bool` (whether temporary effects persist on their final frame)
* `cooldown: int`: (ticks before becoming active after animation)

**Atlas: (column: count)**

* columns: `^(?:[0-9])`

**Animation: FrequencyAnimation**

- `if properties.frequency.type == 'temporary': if animation.state.frame < properties.count: animation.state.frame += 1`
- `if properties.frequency.type== 'continuous': if animation.state.frame >= properties.count: animation.state.frame = 0`
- `if properties.frequency.type== 'periodic': if animation.state.frame > properties.frequency.amount: animation.state.frame = 0 `

**Frame: IterableFrame**

* `keys(id, state): returns [ ("{id}-{state.animation.frame}", 0, 0) ]`
* `index(id, properties): returns { "{id}-{i}": (i * w, 0, w, l) for i in range(properties.count) }`

**Properties: EffectProperties(AssetProperties)**

* `dimensions: Dimensions`
* `count: int`
* `mass: int`
* `hitboxes: List[Hitbox]`
* `frequency: Frequency`

**State: EffectState(AssetState)**

* `animation: AnimationState`

All Effect States inherit fields from this State model.

### Effect: Passive

Passive Effects are inanimate, immutable Assets that do not participate in collision resolution or interactions. They serve to encapsulate static Assets that nonetheless undergo animations: torches, water ripples, falling leaves.

**Required: Passive**

Due to dependencies on other Assets and Mechanics, the following Passive Effects are required to exist at runtime,

- `splash`: Animation for "submerged" Assets moving through [Fluid](#effect-fluids) fields.

**State: AnimatorState**

* `animation: Animation`

**Hitbox: None**

N/A

### Effect: Hazards

Hazard Effects deal damage to intersecting Assets (e.g., lava, floor spikes, poison gas clouds).

**Model: Damage**

* `amount: int`
* `duration: int`
* `reaction: bounce | hinder`

**State: HazardState**

* `damage: Damage`

**Hitbox: StaticHibox**

* `get(properties, state, frame): returns properties.hitboxes`

### Effect: Collectables

Collectables are Effects that transfer loot keys into a Sprite's or Player's inventory upon collision (e.g., dropped coins, potions).

**Model: Lot**

* `inventory: Inventories`
* `item: str`
* `quantity: int`

**State: CollectableState**

* `animation: Animation`
* `lot: Lot`

**Hitbox: StaticHibox**

* `get(properties, state, frame): returns properties.hitboxes`

### Effect: Reactables

Reactables Effects react to the [Intentional](./04-intentions.md) states of [Sprites](./02-sprites.md).

**State: ReactableState**

* `intention: str`

**Hitbox: StaticHibox**

* `get(properties, state, frame): returns properties.hitboxes`

### Effect: Fluids

Fluids are directional Effects that project along a `source` Direction until obstructed by an obstruction (which includes, but is not limited to [Obstacles](#obstacles)). Once obstructed, Fluids form Pools around the obstruction and bifuricate into secondary streams.

Fluids play a vital role in Seasons and Ecology. They are covered in more detail in the [Ecology documentation](./09-ecology.md#instance-fluids).

**State: FluidState**

* `source: Directions`
* `flow: int`
* `length: int`
* `pool: Optional[Pool]`
* `branches: List[Branch]`
* `hitboxes: List[Hitbox]`
* `dirty: bool = True`

**Hitbox: DynamicHitbox**

* `get(properties, state, frame): returns state.hitboxes`

## Category: Geographies

* Property File: `/src/assets/geography/**/*.yaml`

Geography Assets represent inanimate, immutable structural and topographical landforms (e.g., shorelines, cliffs, ledges, and terraces).

**Behavior: Rendering**

Shorelines belong to a dedicated Substrate, `substrate = -3`, to guarantee the correct ordering.

**Atlas: (row: Direction, column: Season)**

* columns: `^(?:[spring|summer|autumn|winter])`
* rows: `^(?:[up|left|down|right])`







2. **Keying**: Uses `Seasons` and `Directions`. Keys follow `{id}-{season}-{direction}` with fractional slices keyed as `{id}-{season}-{direction}-{rem}`.
3. **Ordering**: Shorelines below to a dedicated Substrate, `elevation = -3`, to guarantee the correct ordering.
4. **Lifecycle & Caching**: Shorelines are procedural entities generated via the *Cartographer* class. Frame keys are computed  and cached on `state._keys`. When [SeasonMechanics](./05-mechanics.md#world) emits a SeasonEvent, active Shoreline state seasons are synchronized and frame caches invalidated (`state._keys = None`) without triggering geometric regeneration.

**Properties: GeographyProperties(AssetProperties)**

* `mass: int`
* `thickness: int`
* `hitboxes: List[Hitbox]`
* `tile: str` (Primary key)
* `fluid: str` (Secondary key)

Geography is not deployed onto the Board in an analogous fashion to other Asset Categories. Instead, Geography is procedurally generated using applications services (e.g. Actuator, Cartographer). See [Ecology documentation](./09-ecology.md#instance-fluids) for more information.

**Hitbox: DynamicHitbox**

* `get(properties, state, elevation, frame): returns state.hitboxes`

## Resources

* Property File: `/src/assets/resources/**/*.yaml`

Resources are mutable Assets deployed onto the Board that progress through discrete stages, dependent on [Seasonal](./05-mechanics.md#world) parameters. 

**Loot**

A Resource contains a `loot` key. When Resources are mined through the `mine` [Intention](./04-intentions.md), they are converted into [Collectables](#effects). The `loot` key from the Resource is passed to the Collectable via the [Cradle](./00-overview.md#board) when it is instantiated as a byproduct of `mine`.

**Properties: ResourceProperties**

* `dimensions: Dimensions`
* `hitboxes: List[Hitbox]`
* `mass: int = 0`
* `loot: str`: Inventory loot key dropped upon harvest or mining.
* `lifespan: Lifespans`: Biological or geological progression category (`annual`, `perennial`, `centennial`).

**Frame: StageFrame**

* `keys(id, state): returns [ (f"{id}-{state.stage}", 0, 0) ]`
* `index(id, properties): returns { f"{id}-{stage}": (i * properties.dimensions.w, 0, properties.dimensions.w, properties.dimensions.l) for i, stage in enumerate(properties.lifespan) }`

**Hitbox: StageHitbox**

* `get(properties, state, frame): returns properties[state.stage].hitboxes`

**Animation: None**

Resources do not cycle through animations. Their appearance updates when [SeasonMechanics](./05-mechanics.md#seasonmechanics) transitions `state.stage`.

**Ecology**

Resources form the core of [SeasonMechanics](./05-mechanics.md#seasonmechanics) and possess many unique interactions across Asset classes. They are covered in more detail in the [Ecology documentation](./09-ecology.md#category-resources)

## Sheets

* Property File: `/src/assets/sheets/**/*.yaml`

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

Many Sheet Assets reuse the same Action specification. Common Asset Action specifications are configured and indexed in the Action Configuration file. These configurations are referred to as Action Sets. Each Sheet specifics an Action Set in its property index file. See [Action Configuration Schema](./appendices/01-schemas.md#configuration-actions) for more details. 

**Attackboxes**

An Attackbox is a special type of hitbox unique to Sheet Assets. It is mapped to a canonical `<action>-<direction>-<frame>` key (where `setting.SEPARATOR = "-"`) and applied during the animation state identified by this key. Attackboxes are used to augment the Sheet's basic hitbox collision detection during [CombatMechanics](./05-mechanics.md#spatial). While any Sprite can alter its Attackbox properties, this property is utilized mainly by [Equipment](./02-sprites.md#equipment).

**Stacks**

A Stack is a list of Sheets keys to superimpose over one another to form the resultant Sheet used in the game. The Sheet stacks are drawn in the order they are specified, i.e. the first entry has the lowest Z coordinate, with each subsequent entry being stacked on top.

For example, the `src/assets/sheets/<sheet-category>/features/hair-blonde-bangs.png` might be stacked on top of `src/assets/sheets/<sheet-category>/skins/male-dark-human.png` to create a new Sheet asset used in the game. This Sprite stack is assembled in the [Registry](./00-overview.md#registry) using the `stack` property during the [application bootstrap](./11-architecture.md#initialization). The assembled `stack` is saved as a Sheet Asset, using the `<sheet-id>` as the Asset key. In other words, once assembled, Stacks are effectively new "virtualized" Assets.

!!! note
    It is assumed all Sheets in a Stack conform to the same (Action, Direction) row mapping.

**Properties: SheetProperties**

* `dimensions: Dimensions`
* `stack: List[str]`
* `attackboxes: Dict[str, List[Hitbox]]`
* `hitboxes: List[Hitbox]`
* `actions: Actions`
* `mass: int`

**Hitbox: StaticHitbox**

* `get(properties, state, frame): returns properties.hitboxes`

### Pixies

Pixies are Sheets that have simple game mechanics, i.e. they are excluded from the complex calculations of the [Intention Mechanic](./04-intentions.md). *Pixies* encapsulate simple Characters, such as animals or bugs.

**Animation: StateAnimation**

- `state.animation.frame += 1`
- `if state.animation.frame >= properties.actions[state.animation.action].count: state.animation.frame = 0`

**Frame: StateFrame**

* `keys(id, state): returns [ ("{id}-{state.animation.action}-{state,animation.direction}-{state.animation.frame}", 0, 0) ]`
* `index(id, properties): returns { "{id}-{properties.actions.*}-{properties.actions.*.directions.*}-{properties.actions.*.count}": (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: TBD**

TODO

### Sprites

Sprites are Sheets over multiple rows of frames, where each row may have a variable number of frames. Sprite have a diverse palette of Animation Actions. They are meant to encapsulate the core game entities, e.g. the player, NPCs, and enemies.

Sprite States are covered in more detail in the [Sprites documentation](./02-sprites.md).

### Equipment 

- Equipment: Weapons, Utilities, Tools, Armor, Shields

Equipment is a group of Asset Instances within the Category of Sheets (known as the Equipment Instance Group). They are closely tied to Sprites Animations. Equipment Assets are rendered on top of a Sprite when those pieces of Equipment are active in the Sprite's inventory. Because of this relationship between the Assets,  i.e. Equipment rendering is dependent on Sprite state, Equipment does not possess its own state, frame or animation implementation. Equipment only has properties.

Equipment is covered in more detail in the [Sprites documentation](./02-sprites.md#equipment).

## Widgets

Widgets are used to constructs Menus. They are not a part of the core gameplay loop and have special Mechanics that govern their lifecycle. 

Widgets are covered in their own section, [Widgets](./06-widgets.md).

## Fonts

Fonts are stateless Assets initialized at [runtime](./11-architecture.md#initialization). Rather than being deployed onto the Board, Fonts are loaded into the [Registry](./00-overview.md#registry) and utilized by the [Screen](./00-overview.md#screen) to rasterize text canvases for Widgets and dialogue modals.

See [Fonts documentation](./11-architecture.md#fonts) for more information.