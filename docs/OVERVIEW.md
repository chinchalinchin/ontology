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

The general principle of _onta_ is: configuration is gospel. In other words, _onta_ is written in such as way as to declare as much of the game configuration as possible in external files that get fed into the game engine on start. Learning how to create a game in _onta_ requires understanding the [YAML]() syntax, as all configuration is declared through **YAML** files. 

That said, _onta_ does have scripting capabilities, if the base engine is not sufficient for your project's purposes. These scripts are essentially callbacks that get injected with references to the game state information, allowing you to modify the game state on the fly. 

For more information on configuration, see [Configuration](./CONFIGURATION.md).

For more information on scripting, see [Scripting](./SCRIPTING.md)

## 

While possessing a degree of flexibility, _onta_ is highly opinionated on the type of games it will run. Obviously, only two-dimensional games based on spritesheets can be run in the _onta_ engine, but beyond that, _onta_ produces a very specific type of game. 

What sets _onta_ apart is how it approaches the game loop. The state of the game is described through configuration files that are loaded into the game world once and then saved at the end of a session; everything in between is driven entirely through how the user interacts with the game engine. There are no "scripted" events in the game (not entirely accurate, but spiritually true). What this means is: the game state is always updating. When a NPC dialogue appears, this was a natural consequence of the previous game state, and when it disappears, that event will subsequently affect the game state's evolution. A well-written _ontology_ 