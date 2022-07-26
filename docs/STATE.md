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

### Sprite State

_Sprite_ states are complex. By far, a _Sprite_ state trajectory is the most complex data structure in the game. Different states means different things, in terms of how they get interpretted by the engine, and thus it's possible for a slightly different initial states to produce radically different outcomes (see [Chaos Theory](). Because of this complexity, we will be as precise as possible in defining what is meant by a _Sprite_ state, in the hopes that everything is clear.

A _Sprite_ state can be grouped into _animate_ and _null_ (or _inanimate_) states. _Animate_ states have a _frameset_ associated them, which the engine uses to animate that _Sprite_. _Null_ states do not affect the content of the _frameset_ animation, although they may alter its rendering options; for instance, when jumping, the sprite has its frame margins shifted and a shadow painted underneath it, without altering which _frameset_ is being iterated.

A _Sprite_ has twenty-one _animate_ state and four _null_ states.

An _animate_ _Sprite_ state is composed of an _action_ and a _direction_. The _direction_ of a state maps one-to-one to the direction keys the player users for input (one-to-one, ignoring the diagonal directions, which produce diagonal movement while using the _left_ and _right_ direction states, so for all intents and purposes, these directions can be ignored in what follows), whereas an _action_ is mapped to the secondary buttons, such as `ASDF`, `SHFT, ALT, CTRL, TAB` or widgets on a touch screen.

A _Sprite_ has four directions: `left`, `right`, `up`, `down`.

A _Sprite_ has five actions: `cast`, `thrust`, `slash`, `shoot`

The cross of these two sets, _(action, direction)_, yields 20 distinct states. In addition to this cross product, there is one more _animate_ state: `death`. `death` has no direction. It is always rendered head-on.

In addition to these 21 _animate_ states, there exists four _null_ states: `interact`, `jump`, `shield`, `use`.

_Sprite_ _action_ states are mapped to equipment _slots_. (See [Configuration](./CONFIGURATION.md#equipment) for more information on _Equipment_). When a _Sprite_ has an _Equipment_ equipped to a _slot_, this appends a spritesheet onto the existing spritesheets for a _Sprite_ and alters the engine calculations for player attack damage in that state. When the player is rendered, the equipmentsheet will be rendered on top of him or her.