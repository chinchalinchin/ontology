# Ontology: Overview

!!! note "Capitalization"
    Terminology is capitalized to distinguish it from its colloquial connotations.

!!! note "Angular Brackets"
    Angular brackets denote parameters.

!!! note "Orientation"
    (0,0) corresponds to the upper-left corner, with down being the positive y-direction.

## Assets

All Assets have an *ID*, *Properties* and *State*. 

1. Key: `str`
2. Properties:
    - Dimensions: `tuple[w, h]`
3. State:
    - Layer: `int`
    - Position: `tuple[x, y]`

In addition, Assets are divided into several categories. See [Assets](./01-assets.md) for more information on each category. Different categories of Assets expand the Properties and States in various ways. In brief, the Asset categories are,

- Menu
- Object
- Sheet
- Tile

Assets are placed in the `/src/assets/<category>/` directory and then added and configured to the Asset category index `/src/assets/<category>/main.yaml`. See [Schema](./03-schema.md) for more information on each Asset category index schema.

The index schema for each Asset configures its *Properties*, i.e. its static attributes that are constant and do not change as a result of gameplay.

An Asset is deployed onto a *Board*, where it acquires its *State*, i.e. its dynamic attributes that are variable and change as a result of gameplay. 

A group of Assets of the same category have a single set of Properties, but each individual Asset may have a unique State, unique to its particular deployment. For example, a treasure chest is configured once by its Properties (its height, weight, etc.), but each instance of a treasure chest on a Board has a unique State (its position, content, etc.).

### Hitboxes

Many Assets have Hitboxes. Hitboxes are *Properties*, i.e., they are static and do not change. Hitboxes have positions and dimensions. Hitbox positions are always given relative to the Asset, i.e. treating the upper-left corner of the Asset frame as the origin. 

## Intents

TODO

## Engine

TODO

### View

TODO 

### Board

TODO

The Board state is maintained in `/src/data/boards/`.

The Board state is divided into *immutable* Assets, *mutable inanimate* Assets and *mutable animate* Assets. 

## Registry

