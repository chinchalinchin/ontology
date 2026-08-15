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

All Assets have an *Id*, *Properties* and *State*. 

In addition, Assets are divided into non-overlapping categories, known as the [Asset Hierarchy](./01-assets.md#asset-hierarchy). Different categories of Assets expand the Properties and States in various ways. In brief, the Asset categories are,

- [Crafts](./01-assets.md#crafts)
- [Cursors](./01-assets.md#cursors)
- [Effects](./01-assets.md#effects)
- Environ
- [Objects](./01-assets.md#objects)
- [Sheets](./01-assets.md#sheets)
- [Sounds](./07-sounds.md)
- [Tiles](./01-assets.md#tiles)
- [Widgets](./06-widgets.md)

Assets are placed in the `/src/assets/<category>/` directory and then added and configured to the Asset category index `/src/assets/<category>/main.yaml`. See [Asset Schema](./01-assets.md#schemas) for more information on each Asset category index schema.

The YAML index schema for each Asset configures its *properties*, i.e. its static attributes that are constant and do not change as a result of gameplay.

## Data

Runtime information is stored in the `/src/data/**` directory, otherwise known as the *data directory*. This information is divided into *state* and *configuration* across the `/src/data/state/*` and the `/src/data/config/*` directories respectively, otherwise known as the *state directory* and the *configuration directory*.

### State

An Asset is deployed onto a *Board*, where it acquires its *state*, i.e. its dynamic attributes that are variable and change as a result of gameplay. The application ingests state data stored in the `/src/data/state/*` directory. 

An Asset Category has a single schema for properties, but each individual Asset Instance has a unique State, particular to particular deployment. For example, a treasure Chest is configured once by its Properties (its width, length, etc.), but each instance of a treasure Chest on a Board has a unique state (its position, content, etc.).

### Configuration

Mechanics and other components of the game engine (e.g. Menus, Orchestrator, etc.) utilize configuration stored in the `/src/data/config/*` directory. The following engine components are configured by the files in this directory.

- Scripts
- [Intentions](./04-intentions.md)
- [Mappings](./03-player.md#mapping)
- [Mechanics](./05-mechanics.md)
- [Menus](./06-widgets.md#menus)
- [Recipes](./01-assets.md#recipes)

## Application 

### Factory

The Factory builds Asset components based on Recipes and other game components.

### Orchestrator

The Orchestrator is responsible for reading in the configuration files for properties and state, converting them into application data models and then instantiating the corresponding classes.

### Engine

The Engine handles the core gameplay loop and framerate calculations.

### Screen

The Screen acts as a high-level container for a Cythonized SDL rendering interface.

### Board

The Board is the Game's "database". It holds all ingame Assets during the course of the game loop and exposes them to the engine through queryable interfaces.

The state files for each Board are maintained in `/src/data/state/<board-key>/**`.

### Registry

The Registry loads in all of the Asset files when the application bootstraps. The frames are indexed and stored in the memory. 

## Concepts

### Hitboxes

Many Assets have Hitboxes. Hitboxes are *properties*, i.e., they are static and do not change. Hitboxes have positions and dimensions. Hitbox positions are always given relative to the Asset, i.e. treating the upper-left corner of the Asset frame as the origin. 

### Layers

All deployed Assets have a Layer. Layers represent a "view" where the Asset is located. When the Screen renders an entire frame, it is rendering a Layer.  

Layers on a board can be traversed through Doors. The coordinate plane of each Layer is independent of every other. For example, a Sprite may enter a Door on Layer 1 at `(x_1, y_1)` and get released on Layer 3 at `(x_2, y_2)`. For this reason, each Layer may have different dimensions.

Sprite interactions are constrained by their Layers. Because Layers are superimposed coordinates, all interaction calculations should be separated by Layer, to avoid inter-Layer collisions

### Sprites

NPC and Enemy Sprites are undifferentiated. Conflict is driven entirely by internal Sprite data structures and the gameplay loop. The Player Sprite is the only unique Sprite in terms of the gameplay loop, insofar the Player's state is determined by polling from the Player's input device, as opposed to the [Intention Transition Matrix](./04-intentions.md#transition-matrix). However, all state changes of Sprites and the Player are communicated through the medium of [Goals and Intentions](./04-intentions.md).
