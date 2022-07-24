# Overview

_onta_ is a highly configurable game engine written in **Python**. _onta_ operates on an **ontology**. An **ontology** is a collection of configuration, assets and state information bundled together. _onta_ includes a tutorial **ontology** in its default installation, that serves as a tutorial for the game engine _through the game itself_.

To view this tutorial, install `ontology` using the **Python** package manager and then boot up the tutorial game,

```shell
pip install onta
onta
```

If you already have a custom **ontology** ready-to-go, you can load it into the _onta_ engine,

```
onta --ontology <path/to/ontology>
```

If all of this is incredibly confusing, then you are in the right place. This is the official documentation for _onta_. In the following pages, you will find explanations for all the nomenclature and how to configure _onta_ for your own project.

## Introduction

_onta_ derives from the [Greek word]() for _beings_. An _ontology_ is defined (by the [University of Warwick]() anyway) as,

`The science of the what is, the kinds and structures of objects`

This definition, in essense, explains what this library is all about. _onta_ operates on a world state and user input and processes it into a view, or a world frame. These world frames are displayed in succession atop a PySide6 widget to give the appearance of animation. 

The general principle of _onta_ is: configuration is gospel. In other words, _onta_ is written in such as way as to declare as much of the game configuration as possible in external files that get fed into the game engine on start. Learning how to create a game in _onta_ requires understanding the [YAML]() syntax, as all configuration is declared through **YAML** files. 

That said, _onta_ does have scripting capabilities, if the base engine is not sufficient for your project's purposes. These scripts are essentially callbacks that get injected with references to the game state information, allowing you to modify the game state on the fly. 

For more information on configuration, see [Configuration](./CONFIGURATION.md).

For more information on scripting, see [Scripting](./SCRIPTING.md)

## 

While possessing a degree of flexibility, _onta_ is highly opinionated on the type of games it will run. Obviously, only two-dimensional games based on spritesheets can be run in the _onta_ engine, but beyond that, _onta_ produces a very specific type of game. 

What sets _onta_ apart is how it approaches the game loop. The state of the game is described through configuration files that are loaded into the game world once and then saved at the end of a session; everything in between is driven entirely through how the user interacts with the game engine. There are no "scripted" events in the game (not entirely accurate, but spiritually true). What this means is: the game state is always updating. When a NPC dialogue appears, for instance, this was a natural consequence of the previous game state, and when it disappears, that event will subsequently affect the game state's evolution. There are no "cutscenes"; all in-game events are derived through NPC and villain _intents_ and _plots_. A well-written _ontology_ creates a network of relationships between in-game elements

What does this mean? 

It means no invisible walls, beyond the world dimensions. A player can go anywhere, unless the _ontology_ is designed to contain locked doors, pressure plates, puzzles, etc. 

It means there is "time" in the engine. In fact, a key piece of world configuration is the number of iterations equal to an in-game hour. "Plot" states, which affect the presence, dialogue and path options of sprites, can be calculated from a combination of in-game time and player history. 

As a consequence, this means the world state, the collection of NPC, hero, villain state, is always updating, regardless of whether or it that particular element is being rendered. NPCs and villains exist independent of the player, seeking goals defined in their _intents_.