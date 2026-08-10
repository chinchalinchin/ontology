Here is a problem that might not be worth solving yet, but it will be a hurdle to overcome. Not so much a problem, as a specification that needs to be implemented with careful consideration. It relates to Sprites and the Player. 

Sprites are governed by the Intentions and Dispositions, i.e. their state transitions are a finite automata defined by the Disposition Transition Matrix. The Player's state transitions come from polling the device, i.e. the user. 

The animation states `thrust`, `slash` and `shoot` are the "attack" frames. 

For Sprites, these will states will be reachable from the `attack` Disposition. 

`thrust` requires `equipment.tool == shovel` or `equipment.weapon == spear`. Only the latter corresponds to the `attack` Disposition. The other `thrust` state can be reached through Dispositions such as `find`, `wander`, etc. 

`slash` requires `equipment.weapon in [sword, knife, axe]` and is only reachable through the `attack` Disposition.

`shoot` requires `equipment.weapon in [crossbow, bow]` and is only reachable through the `attack` Disposition.

The Player also has the same conditions on its state entry, i.e. `equipment == x` must be true. So, there appears to be a isomorphism between how Sprites and Players will transition states. 

How can Player State transitions and Sprite Disposition transitions systems be setup in a way that makes sense, is simple, reuses components intelligently (not just for the sake of it) and is not overly verbose? I.e., what is the most Pythonic and elegant way to do this?