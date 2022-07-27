# State

The state of the game defines what is actually is rendered on the game canvas. The state is broken into two mutually exclusive components: the _static_ state and the _dynamic_ state.

## Static

- **Location**: _data/state/static.yaml_

Elements defined in the static state _do not_ change over the course of the game. Their values are loaded into the game world and fixed when the engine initializes. The major difference between the static state and configuration properties is that the static state determines the in-game presence of an object; an object with configuration but no static state will not appear on screen. 

The exception to this rule is _Sprite_s, but this is only because their states are completely defined in the dynamic state. A more careful formulation of the preceding statement might read: an object with configuration but no static or dynamic state will not appear on screen.

Or even more generally: an object with configuration but no state will not appear on screen.

```yaml
world:
    tiles:
        w:
        h:
    size:
        units:
        w:
        h:
    tolerance:
    hour:

layers:
    <layer_name>:
        tiles:
            <tileset_name>:
                sets:
                    -   start:
                            units:
                            x:
                            y:
                        cover:
        struts:
            <strutset_name>:
                order:
                sets:
                    -   start:
                            units:
                            x:
                            y:
                        cover:
        plates:
            <plateset_name>:
                order:
                sets:
                    -   start:
                            units:
                            x:
                            y:
                        cover:
                        content:
        compositions:
            <composeset_name>:
                order:
                sets:
                    -   start:
                            units:
                            x:
                            y:
```

### World

This block of the static state file defines general information about the game world static state, including its dimensions.

### Tilesets

###  Strutsets

A strutset is group of _Strut_s created from the same _Strut_ frame. Each _Strut_ is defined in a set that specifies it's starting position and various strut properties (these are properties dependent on the _Strut_'s "physical" instance in the game, as opposed to the properties defined in the _Strut_'s configuration file, which defines metadata and properties common to all instances of a _Strut_ group)

.. warning:
    The rendering order index of _Strut_s is inherently tied to the number of strut sets in a layer, i.e. `max(order) == len(sets)`. In addition, each set _must_ have an order. 

### Platesets

### Compositions

## Dynamic

- **Location**: _data/state/dynamic.yaml_

Elements defined in the dynamic state _do_ change over the course of the game. As a result, the dynamic state needs persisted to the file system anytime the user saves.

This is perhaps the most important file in terms of the in-game state trajectories. This file defines the initial state of any in-game entity that has its own state, and is thus interactable and animated. 

```yaml
```

See [Sprites](./SPRITES.md) for an in-depth discussion of _Sprite_\s