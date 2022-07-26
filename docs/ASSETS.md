# Assets

Assets are the backbone of the _onta_ engine. They form the basis for the graphics and the sound. Assets are grouped according to how they are treated by the engine.

## Tiles

Tiles have their dimensions defined in the the static world state, i.e. _data/state/static.yaml_. Because of this, whatever the tile dimensions are defined to be (by default, _(92px, 32px)_), all tiles are rendered in multiples of these dimensions. There is no getting around this. It is hardcoded into the game engine. If you wish to paint a graphic of arbitrary dimensions, you are looking for a _Strut_. 

The benefit of having a pre-defined tile size is it makes the math of rendering large areas of the canvas relatively simple. _Tiles_ are rendered in multiples of the base unit. _Tiles_ are meant to provide a general background to the game, more custom graphics are implemented by higher level in-game objects.

### Notes

- **Collections**: A set of _Tile_\s constructed from the same tileset frame is called a _tileset_.
- **State vs. Property**: A _Tile_ has static state information, but its in-game representation is defined entirely by its image configuration properties. Its representation does not depend in any way on what happens in-game. 

## Struts

### Notes

- **Collections**: A set of _Strut_\s constructed from the same strutsheet frame is called a _strutset_.
- **State vs Property**: A _Strut_ has static state information, but its in-game representation is defined entirely by its image configuration properties and its additional physical property (i.e., its hitbox).  Its representation does not depend in anyway on what happens in-game. 

## Plates


### Door

_Door_s are a special type of _Plate_. When the player character overlaps with the hitbox of a _Door_, he or she has the option of interacting with it. This will trigger the world transitioning to a new layer. The layer is delivered statically through the _Door_'s `content`.

See [Configuration](./CONFIGURATION.md#plates) for more information on _Doors_ and their `content`. See [Definitions](./DEFINITIONS.md#terms) for more information on layers.

### Container

The item in a _Container_ is delivered statically through the _Container_'s `content`.

### Mass

A _Mass_ gets to the heart of why _Plate_\s are fuzzy concepts, in the sense they blur the line between definitions of configuration and state. A _Mass_ is a plate that, when a sprite collides with it, will move in the direction of the collision.
 
Obviously, in order to do this, a _Mass_ must alter its position based on the _Sprite_ interaction. Position is state level information, thus a _Mass_ is inherently tied to the game state. This does not, however, mean _Mass_\es have a dynamic state. See the **Notes** as the end of the section for more discussion on this "fuzziness".

A _Mass_'s weight is statically delivered through its `content`.

### Pressure

_Pressure_\s, while capable of existing independently, are not very interesting without _Gate_\s. _Pressure_\s are "switches" that activate a _Gate_. See next section for more information on _Gate_\s

The _Pressure_'s connection to a _Gate_ when activated is statically delivered through the _Pressure_'s `content`.

See [Configuration](./CONFIGURATION.md#plates) for more information on _Plates_ and their `content`

### Gate

A _Gate_ is most easily understood as a locked door that is opened when its accompanying _Pressure_ is activated, although the notion of a "door" simply means a connection between different world layers in game.

A _Gate_'s connection to a _Pressure_ is statically delivered through the _Gate_'s `content`.


See [Configuration](./CONFIGURATION.md#plates) for more information on _Gates_ and their `content`

### Notes

- **Collections**: A set of _Plate_\s constructed from the same platesheet frame is called a _plateset_.
- **State vs. Property**: The concept of _Plate_ is "fuzzy." They are completely defined by their configuration and static state infromation, but, while they do not have a defined dynamic state, they have, in a sense, a _pseudo_-dynamic state. As is plain from the different types of _Plate_\s described above, they are inherently tied to an in-game interaction at a certain position. In order to accomplish interactions like opening a chest, stepping on a pressure plate or entering a door, the engine requires some way of keeping track of these events so they can be rendered. In order to avoid adding _Plates_ to the list of in-game elements with a dynamic state (and thus excluding them from _Compositions_; see next section), at a high level, this is done through the dynamic state of _Sprite_\s; all of the possible _Plate_ interactions have one thing in common: they are dependent on a _Sprite_ in a particular state initiating the interaction. To put a finer point on it, the dynamic part of the interaction is dependent on the _Sprite_ state, while the _type_ and _content_ of the interaction can be defined statically. Therefore, the _type_ of a _Plate_'s interaction is defined in its configuration file, the _content_ of its interaction defined in the static state and then the actual interaction is manifested in-game dynamically through a _Sprite_'s dynamic state, e.g. a _Sprite_ entering the `interact` state while colliding with a _Plate_.


## Compositions

A _Composition_ can be constructed from a collection of sets of _Strut_\s and a collection of sets of _Plate_\s. To use the terminology defined in the previous sections, a composition is a union of _strutsets_ and _platesets_. 

Think of a _Composition_ as a rendering template for a group of objects. For example, a _Composition_ could be used to easily render a house wall, a house roof, a house porch and a house door through a logical grouping. These objects can have their relative positions defined in a _Composition_ and then this collection itself can be referenced in the game's static state file. A _Composition_ definition can be referenced as many times as desired in the static state files, so that a group of assets can be reused, instead of defining each of its constituents multiple times in the state file. 

## Sprites

A _Sprite_ have frames extracted from spritesheets arranged in rows and columns, so that each state frame can be mapped to an entry in the sheet. This engine was developed around the [Liberated Pixel Cup's]() _Sprite_ specification, where there are 21 states arranged in rows, with a different name of frames for each state. Therefore, each sprite has the following states defined: 
    
- cast_up
- cast_left
- cast_right
- cast_down
- thrust_up
- thrust_left
- thrust_right
- thrust_down
- walk_up
- walk_left
- walk_right
- walk_down
- run_up
- run_left
- run_right
- run_down
- slash_up
- slash_left
- slash_right
- slash_down
- shoot_up
- shoot_left
- shoot_right
- shoot_down
- death

In theory, a sprite could have as many states defined as the user desires; however, it must, at minimum, provide definitions for these states.

Sprites also have states that do map one-to-one with animation frames, such as `interact` interacting with an in-game object or `jump`. These states are called _null states_, because they do not possess an outlet in the game's rendering engine.

_Sprite_\s are complex creatures. They have properties defined in their configuration, but they also have a state defined in the game state. Beyond that, _Sprites_ have `intents`. This state information describes the different goals of a sprite depending on the current _plot_. See [Plotting](./PLOTTING.md) for more information on _plots_ and _intents_.