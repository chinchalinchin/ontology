
# Overview

The core game loop is made up of three components: the _World_ object, the _Renderer_ object and the _Controller_ object. This implementation mirrors the common [Model-View-Controller(MVC)]() architecture seen in many modern frameworks. At a high level, the _World_ object contains all of the object state information and methods for updating this state. The _Controller_ object listens for user input, keeping track of which keys have been pressed. The _Renderer_ object paints the game graphics to screen based on the world state.

The objects are orchestrated in the central _main_ module (i.e., _main.py_).

**Note**: This is an over-simplification; technically, there is also another core component: the asset repository, which holds all of the images in memory for quick retrieval. This is used during rendering to optimize the rendering speed. However, for the most part, it should function in background without the developer being aware it is the entity responsible for image processing. 


## View Module

## World Module

## Control Module

## Engine Module

See [Engine](./ENGINE.md) for more information on the different components of this module.

## Load Module

This is the module through which all physical files pass from the filesystem into the game memory. If the game needs access to any asset, configuration or state data, it will make a call to one of the functions in this module.

## Util Module