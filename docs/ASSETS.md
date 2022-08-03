# Assets

Assets are the backbone of the _onta_ engine. They form the basis for the graphics and the sound. Assets are grouped according to how they are treated by the engine.

Assets are logically grouped into types: _Forms_, _Entities_ and _Self_. These asset types are purely organizational and do not have any direct effect, although the names were carefully chosen as they do reflect how the assets are treated by the engine when being rendered and acted upon in-game. 

Forms
-----

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

Entities
--------

## Effects

_Effects_ can be transitory or persistent.

_Effects_ have one state animation that cycles through itself or expires after a set number of iterations, depending on its configuration and state information. The state is wired into the _World_ insofar the _World_ is aware the _Effect_ has been placed, but the _World_ will not update the state of an _Effect_ throughout the course of its loop; it will only monitor its life cycle and delete it if end-life conditions are met, i.e. number of iterations has been reached.

## Nymphs

_Nymphs_ are persistent.

_Nymphs_ have four state animations: `walk_up`, `walk_down`, `walk_left`, `walk_right`. These states and animations are wired into the _World_ iteration loop. They change based on world state information. 

**NOTE**: A _Nymph_ is essentially a "degenerate" _Sprite_, i.e. one with substantially less functionality. 

## Sprites

A _Sprite_ have frames extracted from spritesheets arranged in rows and columns, so that each state frame can be mapped to an entry in the sheet. This engine was developed around the [Liberated Pixel Cup's]() _Sprite_ specification, where there are 21 states arranged in rows, with a different number of frames for each state. Therefore, each sprite has the following states defined: 
    
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

In theory, a sprite could have as many states defined as the user desires; however, it must, at minimum, provide definitions for these states; furthermore, these are the only states that will be animated by the game engine by default. Any other state definitions will be to be taken care of with scripts. See [Scripting](./SCRIPTING.md) for more information on scripting.

Sprites also have states that do map one-to-one with animation frames, such as `interact` interacting with an in-game object or `jump`. These states are called _null states_, because they do not possess an outlet in the game's rendering engine.

_Sprite_\s are complex creatures. They have properties defined in their configuration, but they also have a state defined in the game state. Beyond that, _Sprites_ have `intents`. This state information describes the different goals of a sprite depending on the current _plot_. See [Plotting](./PLOTTING.md) for more information on _plots_ and _intents_. See [State: Sprites](./STATE#sprite-state) for more information on _Sprite_ state information.

## Effects

Self
----

The various components in this category are used to construct both the headsup display (HUD) and the menu. 


**Note**: Styles are applied to most UI elements to organize their layout on screen; these styles are applied are the asset is extract from the element sheet and put into the application's memory.

**Note**: Some of the eccentrities of the following definitions are due to the format of the assets used to construct the user interface. All of the assets are open-source and have no unifying standard. The following is an attempt to provide a framework that can interpret and parse arbtirary UI sheets into a user interface, provided certain elements are present in the sheet. Furthermore, the elements must be able to be broken down into the definition's constituent components.


## Slots

A _Slot_ is used to display the current mapping between _Equipment_ and the hero's equipment state on the heads up display. A player has four _equipment_ states, i.e. a state that gets binded and modified by _Equipment_, `thrust`, `slash`, `cast` and `shoot` (technically, these are actions; an _animate_ state is the combination of an _action_ and a _direction_; See [Sprites](./SPRITES.md) for more information on _Sprite_ _actions_ and _directions_).

When a player enters into one of these four states, the slotted equipment will be added to the animation and the equipment properties will modify the player properties.

A _Slot_ container has five graphical components. The three main frames are: an `enabled` frame, an `disabled` frame and an `active` frame. Decoration frames are: a `cap` frame and a `buffer` frame. In order to be ingested into the _onta_ engine, a _Slot_ **must** have these five components.

_Slot_\s are rendered, in conjunction with the applied styles, so that the first frame is a `cap` and then alternating frames of `buffer` and `disabled | enabled | active` (depending on the hero equipment state) and finally another `cap`.

## Mirrors

A _Mirror_ measures and displays player state information, such as a life or magic, on the heads up display.

### Life
 
A _Life Mirror_ is a collection of _Unit_ frames, where the number of _Unit_\s displayed is directly proportional the player health state. The difference between the maximum player health and the current player health is rendered using _Empty_ frames.

As such, a _Life Mirror_ container has two graphical components: an `empty` frame and a `unit` frame. In order to be ingested into the _onta_ engine and displayed on-screen, a _Life Mirror_ **must** have these two components.

### Magic

A _Magic Mirror_ are slightly different than a _Life Mirror_, because instead of measuring life units, it measures a "discrete continuum", embodied in a meter or gauge. A _Magic Mirror_ must have a _Container_ frame and _Unit_ frames that provide the meter with tiny units of "fill".

**TODO**: Elaborate more once implemented.

## Packs

A _Pack_ is similar to a _Slot_, in that it displays specific player state information related to controller mappings on the heads up display. To understand what a _Pack_ is, take a look at its subtypes.

### Bag

The _Bag_ is used to display the current item binded to the player's `use` state.

A _Bag_ is made up of `left` and `right` pieces. These pieces are rendered adjoined to one another, to form a single whole. (See second note in section introduction). Take note that a _Bag_ can only be defined in the horizontal direction in a pack sheet, not the vertical.

### Belt

The _Belt_ is used to display hero state information regarding the quantity of ammo in the player's inventory. 

A _Belt_ is made up of an `enabled` and a `disabled` frame. 

The `enabled` frame is used when the contents of the _Belt_ are non-zero, according to the player belt state. The `disabled` frame is used otherwise.

### Wallet

A _Wallet_ is made up of a single `display` frame.

A _Wallet_ `display` frame is used to contain an the _Wallet_'s avatar and an accumulator representing the player's current wallet state.


## Avatars

### Equipment
### Inventory
### Quantity

## Equipment



