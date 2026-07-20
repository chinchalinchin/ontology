# Ontology: Assets

This document serves to specify the asset hierarchy and provide key definition for game terminology.

**IDs**

IDs are used to map assets to images loaded into the [registry](./00-overview.md#registry), to ensure each asset is only loaded into the memory once, no matter how many times it is rendered in a single frame. In other words, IDs uniquely identify a physical asset, but not in-game objects.

**Properties vs. State**

*Properties* are static and never changed by ingame mechanics. Properties determine the immutable characteristics of an ingame asset, e.g. dimensions and hitboxes.

*State* is dynamic and is changed by ingame mechanics. State determines the mutable characteristics of an ingame asset, e.g. the current position of an ingame asset. All assets have a *position*, *dimension* and a *layer*. Position and dimension are given as a Cartesian coordinates, whereas Layer is a categorical variable ranging from 1 to 10. 

!!! note
    The concept of a Layer is defined more explicitly in [World documentation](./00-overview.md#world). It suffices to think of Layers as floors in a house, i.e. where each floor has the same area and similar topology, but occupies a different height. In-game, Layers are traversed by the Player interacting Doors.

**Asset Hierarchy**

Assets are divided along two axes.

First, assets are divided into *mutable* and *immutable* categories. *Immutable* assets are never altered by the game loop and always have the same state. *Mutable* objects change their state based on ingame events.

Second, assets are divided in *animate* and *inanimate* categories. *Inanimate* assets either have a single frame or a pair of frames (switches). *Animate* objects possess rows of frames for different animations.

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

## Tiles

*Tiles* are the most basic type of asset. They have a single frame. They have no hitboxes and are simply rendered, without affecting the game otherwise. 

In terms of configuration, Tiles are divided into two categories, *regular* and *irregular*. *Regular Tiles* are always sized 32x32 pixels. *Irregular Tiles* are variable size. 

- Key: `str`

**Properties**

- Dimensions: `tuple[w, h]`

All Tiles properties are statically configured by `src/assets/tiles/main.yaml`

**State**

- Layer: `int`
- Position: `tuple[x, y]`

!!! note
    Tiles have an *immutable state*, but do not participate in the game loop. Their state is never altered by game actions.

## Objects

*Objects* are static assets made of a single frame or pair of frames. An Object with two frames is considered to have an `ON` and `OFF` state, i.e. a binary trigger. *Binary Objects* are Objects whose static frame is dependent on their internal state.

### Chests

*Chests* are *Objects* whose static frame can be changed by the player entering into an `INTERACT` state.

- Key: `str`

**Properties**

- Dimensions `tuple[w, h]`
- Hitboxes: `[ tuple[x, y, w, h], ... ]`

**State**

- Position: `tuple[x, y]`
- Layer: `int`
- Switch: `bool`
- Content: `str`

### Crates

*Crates* are *Objects* who state can be altered by in-game physics. For example, when a *Spriute* collides with a *Crate*, the *Crate* moves in the direction of the *Sprite*, with the same speed as the *Sprite*.

- Key: `str`

**Properties**

- Dimensions `tuple[w, h]`
- Hitboxes: `[ tuple[x, y, w, h], ... ]`

**State**

- Position: `tuple[x, y]`
- Layer: `int`

### Doors

*Doors* are *Objects* that alter the player's `LAYER`. When a player enters the hitbox of a door, the `LAYER` is shifted.

- Key: `str`

**Properties**

- Dimensions `tuple[w, h]`
- Hitboxes: `[ tuple[x, y, w, h], ... ]`

**State**

- Position: `tuple[x, y]`
- Layer: `int`
- OutLayer: `int`

### Gates

*Gates* are *Objects* whose state is connected to *Plates*. When a *Gate* is opened (`ON`), they do not have hitboxes and the player can pass freely through them. When a Gate is closed (`OFF`), its hitboxes prevent the player from approaching.

- Key: `str`

**Properties**

- Dimensions `tuple[w, h]`
- Hitboxes: `[ tuple[x, y, w, h], ... ]`

**State**

- Position: `tuple[x, y]`
- Layer: `int`
- Open: `bool`
- Key: `str`

### Plates

*Plates* are *Objects* whose state can be changed by collision, i.e. when a player enters its hitbox and flips its state. When activated, a *Plate* in turn flips the state of its keyed *Gate*.

- Key: `str`

**Properties**

- Dimensions `tuple[w, h]`
- Hitboxes: `[ tuple[x, y, w, h], ... ]`

**State**

- Position: `tuple[x, y]`
- Layer: `int`
- Switch: `bool`
- Key: `str`

## Sheets

*Sheets* are animated assets arranged in rows of frames. They possess a *Frame* state that iterates over a row of frames as the game loop progresses. 

### Pixies

*Pixies* are *Sheets* defined over a single row of frames.

- Key: `str`

**Properties**

- Dimensions `tuple[w, h]`
- Hitboxes: `[ tuple[x, y, w, h], ... ]`

**State**

- Position: `tuple[x, y]`
- Layer: `int`
- Frame: `int`

**Calculated State**

- FrameKey(ID, Frame)

### Nymphs

*Nymphs* are *Sheets* over four rows of frames. Nymphs always have the same number of frames in each row. 

- Key: `str`

**Properties**

- Dimensions `tuple[w, h]`
- Hitboxes: `[ tuple[x, y, w, h], ...]`
- MaxFrame: `int`

**State**

- Position: `tuple[x, y]`
- Direction: `UP | LEFT | DOWN | RIGHT`
- Frame: `int`

**Calculated State**

- FrameKey(ID, Direction, Action, Frame)

### Sprites

*Sprites* are *Sheets*  over twenty-one rows of frames. *Sprites* have a variable number of frames per row.

- Key: `str`

**Properties**

- Dimension: `tuple[w, h]`
- Hitboxes: `list[ tuple[x, y, w, h] ]`
- MaxFrame: `dict[str, int]`
    - `CAST`: 7 Frames
    - `THRUST`: 8 Frames
    - `WALK`: 9 Frames
    - `SLASH`: 6 Frames
    - `SHOOT`: 13 Frames
    - `DIE`: 6 Frames

**State**

- Position: `tuple[x, y]`
- Direction: `enum[UP | LEFT | DOWN | RIGHT]`
- Action: `enum[CAST | THRUST | WALK | SLASH | SHOOT | DIE]`
- Frame: `int`

**Calculated State**

- FrameKey(ID, Direction, Action, Frame)

## Menu

TODO