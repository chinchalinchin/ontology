# Assets

## Tiles

Tiles are defined to be 96px by 32px. There is no getting around this. It is hardcoded into the game engine. If you wish to paint a graphic of arbitrary dimensions, you are looking for a _Strut_. 

The benefit of having a hardcoded tile size is it makes the math of rendering large areas of the canvas relatively simple. _Tiles_ are rendered in multiples of the base unit (96px, 32px). _Tiles_ are meant to provide a general background to the game, more custom graphics are implemented 

A set of _Tile_\s construccted from the same tileset frame is called a _tileset_.

## Struts

A set of _Strut_\s constructed from the same strutsheet frame is called a _strutset_.

## Plates


A set of _Plate_\s constructed from the same platesheet frame is a called a _plateset_.

### Doors

_Doors_ are a special type of _Plate_. When the player character overlaps with the hitbox of a _Door_, he or she has the option of interacting with it. This will trigger the world transitioning to a new layer. See [Definitions](./DEFINITIONS.md) for more information on layers.


## Compositions

A _Composition_ can be constructed from a collection of sets of _Strut_\s and a collection of set of _Plate_\s. To use the terminology defined in the previous sections, a composition is a union of strutsets and platesets. 

A composition definition can be referenced as many times as desired in the game state files, so that a group of assets can be reused, instead of defining each of its constituents multiple times in the state files.

## Sprites

The player sprite has actions defined in the game engine for the following states: 
    
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