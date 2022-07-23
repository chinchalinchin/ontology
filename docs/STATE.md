# State

The state of the game defines what is actually is rendered on the game canvas. The state is broken into two mutually exclusive components: the _static_ state and the _dynamic_ state.

## Static

- **Location**: _data/state/static.yaml_

Elements defined in the static state _do not_ change over the course of the game. Their values are loaded into the game world and fixed when the engine initializes.

```yaml
```
### Properties

This block of the static state file defines general information about the game world, including its dimensions.

### Tilesets

###  Strutsets

A strutset is group of _Strut_s created from the same _Strut_ frame. Each _Strut_ is defined in a set that specifies it's starting position and various strut properties (these are properties dependent on the _Strut_'s "physical" instance in the game, as opposed to the properties defined in the _Strut_'s configuration file, which defines metadata and properties common to all instances of a _Strut_ group)
.. warning:
    The rendering order index of _Strut_s is inherently tied to the number of strut sets in a layer, i.e. `max(order) == len(sets)`. In addition, each set _must_ have an order. 

## Dynamic

- **Location**: _data/state/dynamic.yaml_

Elements defined in the dynamic state _do_ change over the course of the game. As a result, the dynamic state needs persisted to the file system anytime the user saves.

```yaml
```
### 