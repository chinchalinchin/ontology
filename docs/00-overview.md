# Ontology: Overview

!!! note "Capitalization"
    Terminology is capitalized to distinguish it from its colloquial connotations.

!!! note "Angular Brackets"
    Angular brackets denote parameters.

!!! note "Orientation"
    (0,0) corresponds to the upper-left corner, with down being the positive y-direction.

!!! note "Width, Length"
    Width is a horizontal displacement, length is a vertical displacement.
    
## Assets

All Assets have an *Key*, *Properties* and *State*. 

In addition, Assets are divided into several categories. See [Assets](./01-assets.md) for more information on each category. Different categories of Assets expand the Properties and States in various ways. In brief, the Asset categories are,

- Menu
- Object
- Effect
- Cursor
- Sheet
- Tile

Assets are placed in the `/src/assets/<category>/` directory and then added and configured to the Asset category index `/src/assets/<category>/main.yaml`. See [Asset Schema](./01-assets.md#schemas) for more information on each Asset category index schema.

The index schema for each Asset configures its *Properties*, i.e. its static attributes that are constant and do not change as a result of gameplay.

An Asset is deployed onto a *Board*, where it acquires its *State*, i.e. its dynamic attributes that are variable and change as a result of gameplay. 

A group of Assets of the same category have a single set of Properties, but each individual Asset may have a unique State, unique to its particular deployment. For example, a treasure chest is configured once by its Properties (its height, weight, etc.), but each instance of a treasure chest on a Board has a unique State (its position, content, etc.).

### Hitboxes

Many Assets have Hitboxes. Hitboxes are *Properties*, i.e., they are static and do not change. Hitboxes have positions and dimensions. Hitbox positions are always given relative to the Asset, i.e. treating the upper-left corner of the Asset frame as the origin. 

## Application 

### Factory

The Factory builds Asset components based on Recipes.

TODO

### Orchestrator

The Orchestrator is responsible for reading in the configuration files for properties and state, converting them into application data models and then instantiating the corresponding classes.

The Orchestrator handles the core gameplay loop and framerate calculations.

TODO

### Screen

The Screen acts as a high-level container for a Cythonized SDL rendering interface.

TODO

### Board

The Board is the Game's "database". It holds all ingame Assets during the course of the game loop and exposes them to the engine through queryable interfaces.

The state files for each Board is maintained in `/src/data/state/<board-key>/**`.

TODO

### Registry

The Registry loads in all of the Asset files when the application bootstraps. The frames are indexed and stored in the memory. 

TODO

## Concepts

### Layers

All deployed Assets have a Layer. Layers represent a "view" where the Asset is located. When the Screen renders an entire frame, it is rendering a Layer.  

Layers on a board can be traversed through Doors. The coordinate plane of each Layer is independent of every other. For example, a Sprite may enter a Door on Layer 1 at `(x_1, y_1)` and get released on Layer 3 at `(x_2, y_2)`. For this reason, each Layer may have different dimensions.