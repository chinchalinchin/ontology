# Ontology: Assets

This document serves to specify the asset hierarchy and provide key definition for game terminology.

**IDs**

IDs are used to map assets to images loaded into the [repository](./overview.md#repository), to ensure each asset is only loaded into the memory once, no matter how many times it is rendered in a single frame. In other words, IDs uniquely identify a physical asset, but not in-game objects.

## Menu

## Objects

*Objects* are static frames.

### Chests

*Chests* are *Objects* whose static frame can be changed by the player entering into an `INTERACT` state.

**Properties**

- ID
- Dimensions `(w, h)`
- Hitboxes: `[ (x, y, w, h), ... ]`

**State**

- Position: `(x, y)`
- Open: `true | false`
- Content

### Crates

*Crates* are *Objects* who static frame can be moved by in-game physics. When a *Spriute* collides with one, a *Crate* moves in the direction of the *Sprite*.

**Properties**

- ID
- Dimensions: `(w, h)`
- Hitboxes: `[ (x, y, w, h), ... ]`

**State**

- Position: `(x, y)`

### Doors

*Doors* are *Objects* that alter the player's `LAYER`. When a player enters the hitbox of a door, the `LAYER` is shifted.

**Properties**

- ID
- Dimensions: `(w, h)`
- Hitboxes: `[ (x, y, w, h), ... ]`

**State**

- Position: `(x, y)`
- Layer

### Gates

*Gates* are *Objects* who state is connected to *Plates*. When opened, they do not have hitboxes and the player can pass freely through them. When closed, their hitboxes prevent approach.

**Properties**

- ID
- Dimensions: `(w, h)`
- Hitboxes: `[ (x, y, w, h), ... ]`

**State**

- Key
- Position: `(x, y)`
- Open: `true | false`

### Plates

*Plates* are *Objects* who static frame can be changed by collision, i.e. whose hitbox flips its state. When activated, *Plates* flip the state of the keyed *Gate*.

**Properties**

- ID
- Dimensions: `(w, h)`
- Hitboxes: `[ (x, y, w, h), ... ]`

**State**

- Position: `(x, y)`
- Open: `true | false`
- Key

### Tiles

*Tiles* are the most basic type of *Object*. They have no hitboxes and are simply rendered, without affecting the game otherwise.

**Properties**

- ID
- Dimensions: `(w, h)`

**State**

- Position: `(x, y)`

## Sheets

*Sheets* are animations arranged in rows of grames.

### Pixies

*Pixies* are *Sheets* over a single row of frames.

**Properties**

- ID
- Dimensions `(w, h)`
- Hitboxes: `[ (x, y, w, h), ... ]`

**State**

- Position: `(x, y)`
- Frame

**Calculated State**

- FrameKey(ID, Frame)

### Nymph

*Nymphs* are *Sheets* over four rows of frames. Nymphs always have the same number of frames in each row.

**Properties**

- ID
- Dimensions `(w, h)`
- Hitboxes: `[ (x, y, w, h), ...]`
- MaxFrame: 6

**State**

- Position: `(x, y)`
- Direction: `UP | LEFT | DOWN | RIGHT`
- Frame

**Calculated State**

- FrameKey(ID, Direction, Action, Frame)

### Sprites

*Sprites* are *Sheets*  over twenty-one rows of frames. *Sprites* have a variable number of frames per row.

**Properties**

- ID
- Dimension: `(w, h)`
- Hitboxes: `[ (x, y, w, h), ...]`
- MaxFrame:
    - `CAST`: 7 Frames
    - `THRUST`: 8 Frames
    - `WALK`: 9 Frames
    - `SLASH`: 6 Frames
    - `SHOOT`: 13 Frames
    - `DIE`: 6 Frames

**State**

- Position: `(x, y)`
- Direction: `UP | LEFT | DOWN | RIGHT`
- Action: `CAST | THRUST | WALK | SLASH | SHOOT | DIE`
- Frame

**Calculated State**

- FrameKey(ID, Direction, Action, Frame)
