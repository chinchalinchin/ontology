# Assets

## Tiles

Tiles are defined to be 96px by 32px. There is no getting around this. It is hardcoded into the game engine. If you wish to paint a graphic of arbitrary dimensions, you are looking for a _Strut_. 

The benefit of having a hardcoded tile size is it makes the math of rendering large areas of the canvas relatively simple. _Tiles_ are rendered in multiples of the base unit (96px, 32px). _Tiles_ are meant to provide a general background to the game, more custom graphics are implemented 


## Struts

### Doors

_Doors_ are a special type of _Strut_. When the player character overlaps with the hitbox of a _Door_, he or she has the option of interacting with it. This will trigger the world transitioning to a new layer. See [Definitions](./DEFINITIONS.md) for more information on layers.