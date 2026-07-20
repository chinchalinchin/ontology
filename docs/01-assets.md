# Ontology: Assets

This document serves to specify the Asset hierarchy and provide key definition for game terminology.

!!! note "Definition"
    An asset is an image file.

The Asset directory is organized as follows,

```bash
assets % tree -L 2
.
├── menu
│   └── main.yaml
├── objects
│   ├── chests
│   ├── crates
│   ├── doors
│   ├── gates
│   ├── plates
│   └── main.yaml
├── sheets
│   ├── nymphs
│   ├── pixies
│   ├── sprites
│   └── main.yaml
└── tiles
    ├── irregular
    ├── regular
    └── main.yaml
```

The `main.yaml` files in each subdirectory conform to the [Asset property schema](./02-schema.md#asset-property-schemas).

**Keys**

Keys are used to map assets to images loaded into the [registry](./00-overview.md#registry), to ensure each Asset is only loaded into the memory once, no matter how many times it is rendered in a single frame. In other words, keys uniquely identify a physical Asset, but not in-game objects.

**Properties vs. State**

*Properties* are static and never changed by ingame mechanics. Properties determine the immutable characteristics of an ingame Asset, e.g. dimensions and hitboxes. They are loaded side-by-side with the asset files in the `/src/assets/**` directory.

*State* is dynamic and is changed by ingame mechanics. State determines the mutable characteristics of an ingame Asset, e.g. the current position of an ingame Asset. All Assets have a *position*, *dimension* and a *layer* mutable state. Position and dimension are given as a Cartesian coordinates, whereas Layer is a categorical variable. 

!!! note "Layers"
    The concept of a Layer is defined more explicitly in [World documentation](./00-overview.md#world). It suffices to think of Layers as floors in a house, i.e. where each floor has the same area and similar topology, but occupies a different height. In-game, Layers are traversed by the Player interacting Doors.

**Asset Hierarchy**

Assets are divided along two axes.

First, Assets are divided into *mutable* and *immutable* categories. *Immutable* Assets are never altered by the game loop and always have the same state. *Mutable* objects change their state based on ingame events.

Second, Assets are divided in *animate* and *inanimate* categories. *Inanimate* Assets either have a single frame or a pair of frames (*Binary Objects*). *Animate* objects possess rows of frames for different animations. The rows of *inanimate* Assets are further categorized by the axes of *direction* and *action*. See [Sheets section](#sheets) below for more information on the division of *direction* and *action*.

All *immutable* objects are *inanimate*, but not all *mutable* objects are *animate*. 

In order of ascending complexity, where complexity is defined as the number of dimensions in the state, the game asset hierarchy is given below,

- (*Immutable*, *Inanimate*) Tile: 
    - Regular: State = Position, Layer
    - Irregular: State = Position, Layer
- (*Mutable*, *Inanimate*) Objects:
    - Crate: State = Position, Layer
    - Door: State = Position, Layer, OutLayer
    - Chest: State = Position, Layer, Switch, Content
    - Gate: State = Position, Layer, Switch, Key
    - Plate: State = Position, Layer, Switch, Key
- (*Mutable*, *Animate*) Sheets:
    - Pixie: State = Postion, Layer, Frame
    - Nymph: State = Position, Layer, Frame, Direction
    - Sprite: State = Position, Layer, Frame, Direction, Action

**Intent**

Intent represents a mutable state change. All Assets implement an `update` method that receives as argument an `Intent` object.

## Tiles

*Tiles* are inanimate, immutable Assets. *Tiles* are the most basic type of Asset. They have a single frame. They have no hitboxes and are simply rendered, without affecting the game otherwise. 

In terms of configuration, Tiles are divided into two categories, *regular* and *irregular*. *Regular Tiles* are always sized 32x32 pixels. *Irregular Tiles* are variable size. 

- AssetKey: `str`

**Properties**

- Dimensions: `tuple[w, h]`

All Tiles properties are statically configured by `src/assets/tiles/main.yaml`

**State**

- LayerKey: `str`
- Position: `tuple[x, y]`

!!! note "Immutable"
    Tiles have an *immutable state* and do not participate in the game loop. Their state is never altered by ingame actions.

## Objects

*Objects* are inanimate Assets made of a single frame or pair of frames. 

**Binary Objects**

An Object with two frames is considered to have an *activated* and *idle* state, i.e. a binary trigger. *Binary Objects* are Objects whose frame is dependent on their internal state. They are composed of two frames.

**Binary Frames**

Binary objects frames are always organized in horizontal rows. The idle frame will always start at `(0,0)` and the activated frame will always start at `(w,0)`. Because of this relation, the dimensions of a Chest image file will always be `(2w, h)`

### Chests

*Chests* are *Binary Objects* whose frame can be changed by the player entering into an `INTERACT` state while intersecting the dimensions of the *Chest*. When `switch == true`, the Chest is *activated* (open). When `switch == false`, the Chest is *idle* (closed).

- AssetKey: `str`

**Properties**

- Dimensions `Tuple[w, h]`
- Hitboxes: `List[Tuple[x, y, w, h], ... ]`

**State**

- Position: `Tuple[x, y]`
- LayerKey: `str`
- Switch: `bool`
- Content: `str`

**CalculatedState**

- FrameKey(Switch)
    - If `switch == true`, returns `<key>-idle`
    - If `switch == false`, returns `<key>-activated`

### Crates

*Crates* are *Objects* who state can be altered by in-game physics. For example, when a *Spriute* collides with a *Crate*, the *Crate* moves in the direction of the *Sprite*, with the same speed as the *Sprite*.

- AssetKey: `str`

**Properties**

- Dimensions `Tuple[w, h]`
- Hitboxes: `List[Tuple[relX, relY, w, h]]`

**State**

- Position: `Tuple[x, y]`
- LayerKey: `str`

**Calculated State**

- FrameKey(Key): returns `<key>`

### Doors

*Doors* are *Objects* that alter the player's `<layer>`. When a player enters the hitbox of a door, the `<layer>` is changed to the `<outlayer>`.

- AssetKey: `str`

**Properties**

- Dimensions `Tuple[w, h]`
- Hitboxes: `List[Tuple[x, y, w, h], ... ]`

**State**

- Position: `Tuple[x, y]`
- LayerKey: `str`
- OutLayerKey: `str`

**Calculated State**

- FrameKey(): returns `<key>`

### Gates

*Gates* are *Objects* whose state is connected to *Plates*. When a *Gate* is activated (open), it does not have hitboxes and the player can pass freely through it. When a Gate is idle (closed), its hitboxes prevent the player from passing through its area.

- AssetKey: `str`

**Properties**

- Dimensions `Tuple[w, h]`
- Hitboxes: `List[Tuple[relX, relY, w, h]]`

**State**

- Position: `Tuple[x, y]`
- LayerKey: `str`
- LinkKey: `str`
- Switch: `bool`

**Calculated State**

- FrameKey(Switch)
    - If `switch == true`, returns `<key>-idle`
    - If `switch == false`, returns `<key>-activated`

### Plates

*Plates* are *Binary Objects* whose state can be changed by collision, i.e. when a player enters its hitbox and flips its state. When activated, a *Plate* in turn flips the state of its keyed *Gate*.

- AssetKey: `str`

**Properties**

- Dimensions `Tuple[w, h]`
- Hitboxes: `List[Tuple[x, y, w, h], ... ]`

**State**

- Position: `Tuple[x, y]`
- LayerKey: `str`
- LinkKey: `str`
- Switch: `bool`

**CalculatedState**

- FrameKey(Switch)
    - If `switch == true`, returns `<key>-idle`
    - If `switch == false`, returns `<key>-activated`
    
## Sheets

*Sheets* are animate Assets arranged in rows of frames. They possess a *Frame* state that iterates over a row of frames as the game loop progresses. 

**Direction and Action**

For any sheet composed of more than one row (i.e. all types of Sheets except *Pixies*), the rows of that Sheet are identified by *direction* and *action*. These categories are enumerated below. 

- Direction: `enum[UP | LEFT | DOWN | RIGHT]`
- Action: `enum[CAST | THRUST | WALK | SLASH | SHOOT | DIE]`

### Pixies

*Pixies* are *Sheets* defined over a single row of frames. They are meant to encapsulate special effect and animation logic. For example, a projectile may produce a cloud of dust when impacting a surface. The dust cloud is a *Pixie*.

Some Pixies are brief (e.g. explosions or magic effects), while others loop through their frames forever (e.g. water ripples or a windmill). The *Persistent* property determines whether a Pixie is short-lived or long-lived.

- Key: `str`

**Properties**

- Dimensions `Tuple[w, h]`
- Hitboxes: `List[Tuple[x, y, w, h], ... ]`
- Persistent: `bool`

**State**

- Position: `Tuple[x, y]`
- Layer: `str`
- Frame: `int`

**Calculated State**

- FrameKey(Key, Frame) -> `<key>-<frame>`

### Nymphs

*Nymphs* are *Sheets* over four rows of frames. Nymphs always have the same number of frames in each row, determine by the *MaxFrame* property. They are meant to encapsulate simple ingame characters, such as animals, bugs, or other creatures.

- Key: `str`

**Properties**

- Dimensions `Tuple[w, h]`
- Hitboxes: `List[Tuple[relX, relY, w, h]]`
- MaxFrame: `int`

**State**

- Position: `tuple[x, y]`
- Direction: `Direction`
- Frame: `int`

**Calculated State**

- FrameKey(Key, Direction, Frame) -> `<key>-<direction>-<frame>`

### Sprites

*Sprites* are *Sheets*  over twenty-one rows of frames. *Sprites* have a variable number of frames per row. They are meant to encapsulate the core ingame characters, e.g. the player, non-playable characters and enemies.

**Player, NPCs and Enemies**

NPC and Enemy Sprites are undifferentiated. The Player Sprite is the only unique Sprite in terms of the gameplay loop, insofar the Player's Intent is determined by polling from the Player's input device. 

- Key: `str`

**Properties**

- Dimension: `tuple[w, h]`
- Hitboxes: `List[Tuple[relX, relY, w, h]]`
- MaxFrame: `Dict[str, int]`
    - `CAST`: 7 Frames
    - `THRUST`: 8 Frames
    - `WALK`: 9 Frames
    - `SLASH`: 6 Frames
    - `SHOOT`: 13 Frames
    - `DIE`: 6 Frames

**State**

- Position: `Tuple[x, y]`
- Direction: `Direction`
- Action: `Action`
- Frame: `int`

**Calculated State**

- FrameKey(Key, Direction, Action, Frame) -> `<key>-<direction>-<action>-<frame>`

**Methods**

## Menu

TODO