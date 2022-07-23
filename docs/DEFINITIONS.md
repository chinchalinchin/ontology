# Definitions

## Terms

1. **World**: Game object that contains all the state and property information about the game world. It also possesses internal methods for updating the world state that are called when the public interface method `iterate()` is called. 

    - _Layer_: A world is made up of layers. Each layer is independently rendered. In-game actions trigger the transition from one layer to another layer, e.g. the player interacts with a _Door_.

2. **Sprite**: An in-game animation element whose frames are constructed from panels in a sprite sheet.

    - _State_: A _Sprite_ has a list of states in which it can exist. The _World_'s `iterate` method operates on the sprite state, either persisting it or updating it based on the current state of the _World_.
    - _Property_: A _Sprite_ has a list of properties that determine how it behaves in-game. These properties influence the _Sprite_'s behavior in the _World_'s `iterate()` method.
    - _Frame_:
    - _Hero_: A special instance of a _Sprite_. This _Sprite_ represents the player's in-game character. It responds to user input via the _World_ `iterate()` method.

3. **Tile**: An in-game asset whose frame is constructed from a tile sheet. _Tiles_ are not interactable in-game elements; they are simply the background on which other in-game elements interact. They are the first element rendered on the **View**.

4. **Strut**: An in-game asset whose frame is constructed from a strut sheet. _Struts_ have "physical" presence in the game world, so to speak; in other words, the player can collide with _Struts_. They must have a hitbox defined in their properties

5. **View**: The GUI widget on which the game screen gets painted. The game world gets cropped to the widget based on the position of the player.

### Notes

- Each in-game object builds up complexity in sequence by introducing another dimension of operation.
- A _Tile_ has an image frame; it is painted to screen. The user cannot interact with a _Tile_ in anyway. 
- A _Strut_ has properties in addition to an image frame. Properties determine how the in-game element interacts with other in-game elements. 
- A _Sprite_ has properties _and_ states. States determine how a given element is animated. In other words, a _Sprite_ has multiple frames and the currently displayed frame depends on the _Sprite_ state.