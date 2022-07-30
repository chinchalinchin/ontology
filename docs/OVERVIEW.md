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

In a more technical sense, the object of _onta_ is to show how a game can be written entirely in markup, without any additional scripting. Furthermore, games written purely in markup can be fully featured, with complex stories and gameplay mechanics, if the parsing engine is written with this in mind.

That said, _onta_ does have scripting capabilities, if the base engine is not sufficient for your project's purposes. These scripts are essentially callbacks that get injected with references to the game state information, allowing you to modify the game state on the fly. 

While possessing a degree of flexibility, _onta_ is highly opinionated on the type of games it will run. Obviously, being a **Python** library, only two-dimensional games based on spritesheets are viable running in the game engine (and in fact, the _onta_ rendering engine has a hard dependency on the [PIL]() library for image processing; a future TODO may be detaching the rendering altogether from **Python**, and using a lower level language to implement rendering in order to speed everything up; in other words, using _onta_ as a logic engine only, which, in a sense, is the goal of the current endeavor: to devvelop a logic engine that can effectively simulate a world; graphics are secondary to that goal), but beyond that, _onta_ produces a very specific type of game. 

_onta_ is not about cutting edge graphics; it is about simulation. The state of the game is described through configuration files that are loaded into the game world once and then saved at the end of a session; everything in between is driven entirely through how the user interacts with the game engine. There are no "scripted" events in the game (not entirely accurate, but spiritually true). What this means is: the game state is always updating. When a NPC dialogue appears, for instance, this was a natural consequence of the previous game state, and when it disappears, that event will subsequently affect the game state's evolution. There are no "cutscenes"; all in-game events are derived through NPC and villain _intents_ and _plots_. A well-written _ontology_ creates a network of relationships between in-game elements and then allows this network to be manipulated by the user as he or she sees fit.

What does this mean? 

It means no invisible walls, beyond the world dimensions. A player can go anywhere, unless the _ontology_ is designed to contain locked doors, pressure plates, puzzles, etc. 

It means there is "time" in the engine. In fact, a key piece of world configuration is the number of iterations equal to an in-game hour. "Plot" states, which affect the presence, dialogue and path options of sprites, can be calculated from a combination of in-game time and state information. 

As a consequence, this means the world state, the collection of NPC, hero, villain states, is always updating, regardless of whether or not that particular element is being rendered. NPCs and villains exist independent of the player, seeking goals defined in their _intents_. A game _World_ in _onta_ is a "living", "breating" "thing".

With _onta_, I have tried to apply all the mathematical, philosophical and scientific knowledge I have accumulated in my life to develop a world simulator, albeit a virutal one. But, when it comes right down to it, where does the physical end and the virtual start?

For more information on configuration, see [Configuration](./CONFIGURATION.md).

For more information on scripting, see [Scripting](./SCRIPTING.md)

## Liberated Pixel Cup

This engine was designed around the **LPC** specification (see [here](https://lpc.opengameart.org/static/LPC-Style-Guide/build/styleguide.html) and [here](https://bztsrc.gitlab.io/lpc-refined/). In principle, there is nothing special about LPC assets, and _onta_ could be configured to use an entirely different class of assets, assuming that class of sets meets certain requirements. However, since **LPC** assets have well-defined states and animations, and embody the principles of well-designed game assets, they have been used as a starting point. I recommend reading through the guides linked above and understanding at least a general overview of some of the design choices in the **LPC** specification.

This engine meets and exceeds that spec, as I have understood it. In fact, this documentation is intended to serve as a guide for how to take the **LPC** specification and expand it into an entire markup language so that an **LPC**-compliant game can be specified entirely in terms of that markup. 

The default _ontology_ configuration and _asset_ files describe an engine that implements the **LPC** specification (in addition to added functionality, detailed in this documentation). Default state files are also provided to show a proof of concept for an **LPC**-compliant game, but they are meant more as a guide on how to configure your own **LPC** game.