# Definitions

## Terms

1. **Sprite**: An in-game animation element whose frames are constructed from panels in a sprite sheet.

    - _State_:
    - _Property_:
    - _Frame_:

2. **Tile**: An in-game asset whose frame is constructed from a tile sheet. _Tiles_ are not interactable in-game elements; they are simply the background on which other in-game elements interact. They are the first element rendered on the **View**.

    - _TileCover_: A special sub-class of _Tile_ that gets rendered last. In other words, this element gets painted on top of all other in-game elements.

3. **World**: Game object that contains all the state and property information about the game world. It also possesses internal methods for updating the world state that are called when the public interface method `iterate()` is called. 

4. **View**: The GUI widget on which the game screen gets painted. The game world gets cropped to the widget based on the position of the player.