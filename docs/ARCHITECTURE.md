
# Overview

The core game loop is made up of three components: the _World_ object, the _Renderer_ object and the _Controller_ object. This implementation mirrors the common [Model-View-Controller(MVC)]() architecture seen in many modern frameworks. At a high level, the _World_ object contains all of the object state information and methods for updating this state. The _Controller_ object listens for user input, keeping track of which keys have been pressed. The _Renderer_ object paints the game graphics to screen based on the world state.

The objects are orchestrated in the central _main_ module (i.e., _main.py_).

**Note**: This is an over-simplification; technically, there are also two other core component: the asset repository, which holds all of the images in memory for quick retrieval, and the HUD, which displays game state information to the user. The asset repository is used during rendering to optimize the rendering speed while the HUD is stateless and doesn't affect the engine in anyway, serving simply as an outlet. For the most part, these two components should function in background, although on occassion the developer may need to be aware of their existence. 

## onta Package

Below is a general overview of the _onta_package structure. See the [Package API documentation]() for more details on the methods and objects in the _onta_ package.

**TODO**: finish doc strings and generate package api

### Main Module

### Settings Module

### View Module


### World Module

By their nature, the _View_ and _World_ module are tightly coupled. The _View_ renders what is displayed on the world. It accesses properties on the _World_ object and uses their values to calculate rendering coordinates. The _View_, however, does **not** modify the _World_ state in _any way_.

### Control Module

### HUD Module

Much like the _View_ and the _World_ modules, the _HUD_ and the _World_ modules are tightly coupled. This is inescapable, as the _HUD_ is nothing more than an outlet for displaying _World_ state information.

## onta.engine Package 

See [Engine](./ENGINE.md) for more information on the different components of this module.

### onta.
## onta.load Package

This is the package through which all physical files pass from the filesystem into the game memory. If the game needs access to any asset, configuration or state data, it will make a call to one of the functions in this module.

## onta.util Package
