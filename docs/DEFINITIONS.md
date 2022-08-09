# Definitions

The following definitions form the core concepts of the _onta_ engine. Each definition will be explained in greater detail in other sections, but this page can be used a quick reference.

## Core Terminology

The following defintions regard game engine and rendering concepts.

1. **World**: Game object that contains all the state and configuration information about the game world. It possesses internal methods for updating the world state that are called from the public interface method `iterate()`.

    - _Layer_: A world is made up of layers. Each layer is independently rendered. In-game actions trigger the transition from one layer to another layer, e.g. the player interacts with a _Door_.

2. **View**: The GUI widget on which the game screen gets painted. The game world gets cropped to the widget based on the position of the player and the view dimensions.

3. **Repo**: A game object that acts behind the scenes to load in image assets and store them in memory.  

4. **Ontology**: The bundle of configuration, asset files and state definitions taken together is called an _ontology_. It completely determines how the game engine behaves on every iteration of the loop (i.e., poll, update and render).

## Form Terminology

1. **Tile**: An in-game asset whose frame is constructed from a tilesheet. _Tiles_ are not interactable in-game elements; they are simply the background on which other in-game elements interact. They are the first element rendered on the **View**. They can only be painted in multiples of a predefined width and height. The default value for a tile dimension is **32px** by **32px**.

2. **Strut**: An in-game asset whose frame is constructed from a strutsheet. _Struts_ have "physical" presence in the game world, so to speak; in other words, the player can collide with a _Strut_. As such, a strut can have a hitbox defined in its properties. Alternatively, the hitbox can be set to null to create a "degenerate" _Strut_ that is essentially a _Tile_, but cannot be rendered in multiples of a pre-defined dimension. In this case, it is useful for background imagery and covers.

3. **Plates**: An in-game asset whoe frame is construct from a platesheet. _Plates_ also have "phsyical presence in the game world; however, in addition to allowing player collisions, player can interact with plates, e.g. treasure chests, pressure plates, switches, etc. 

    - _Door_: A _Door_ is a special type of _Plate_ that when interacted with allows the player to change the _World_ _Layer_.
    - _Container_: A _Plate_ with an on/off state that delivers `content` to a _Sprite_'s inventor.y
    - _Mass_: A movable _Plate_ that responds to _Sprite_ collisions.
    - _Gate_: A _Gate_ is essentially a locked _Door_ that is connected to a _Pressure_.
    - _Pressure_: A _Pressure_ is triggered when a _Mass_ is placed atop it.

## Entity Terminology

1. **Pixies**:

2. **Nymphs**:

3. **Sprite**: An in-game animation element whose frames are constructed from panels in a sprite sheet. Sprites represent characters in-game, both the player and non-playable characters (NPCs). The only difference between a player sprite and a NPC sprite is how its _Intents_ are mapped. See [Sprites](./SPRITES.md) for more information.

    - _Base_: A _Sprite Base_ is its central character spritesheet.
    - _Accent_: _Sprite Accent_\s are secondary spritesheets overlaid atop its _Base_.
    - _Stature_: A _Sprite_ has a list of _stature_\s in which it can exist. The _World_'s `iterate` method operates on a _Sprite stature_, either persisting it or updating it based on the current state of the _World_.
    - _Property_: A _Sprite_ has a list of properties that determine how it behaves in-game. These properties influence the _Sprite_'s behavior in the _World_'s `iterate()` method, but do not directly affect how the _Sprite_ is rendered.
    - _Frame_: A _Sprite_ has a frame index that denotes its position in the spritesheet, i.e. what frame is currently being animated.
    - _Intent_: A piece of state information held in a sprite that describes its current goals.
    - _Path_: A piece of state information that determines where a sprite is heading.

## Sense Terminology

1. **Apparel**:

2. **Avatars**:

3. **Expressions**:

4. **Slots**:

5. **Mirrors**: 

6. **Packs**:

7. **Baubles**

## Dialectics Terminology

1. **Alchemy**:

2. **Economy**:

3. **Plots**:


### Notes

- Each in-game object builds up complexity in sequence by introducing another dimension of operation.
- A _Tile_ has an image frame; it is painted to screen. The user cannot interact with a _Tile_ in anyway. 
- A _Strut_ has properties in addition to an image frame. Properties determine how the in-game element interacts with other in-game elements. 
- A _Plate_ is interactable in addition to having properties. An interactable element can receive user input.
- A _Pixie_
- A _Nymph_
- A _Sprite_ has properties, reacts to user input _and_ has states. States determine how a given element is animated. In other words, a _Sprite_ has multiple frames and the currently displayed frame depends on the _Sprite_ state.