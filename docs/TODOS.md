
- add `looper` property to sprite definitions to allow developers to turn off game loop physics and interactions for that sprite. lets scripts completely control the sprite state.

- multiple regression of sprite states against hero state vs. collection of simple linear regression of sprite state against state.

- if sprite aware: train model: if iteration == learning_rate or something, then apply prediction

- Make Conf and State wrapper classes singletons (so conf is not loaded over and over again)

- Every sprite has a sell interaction with whatever is in their bag or belt.

- Special entity type: merchant. Merchant acts as an interface between sprites and "economy". 


UPDATE: REPLACE intents with desires
    
Sprites should have intents to `sell`, `purchase` and these intents should target `bag | belt` and `equipment | armor | inventory` respectively. 

Sprites will need a map to merchants, in order to locate. 

The "economy" outline

If item is sold to merchant
    economy price asymptotically decreases to zero. 

If item is bought from merchant
    price asymptotically increases to some set maximum point

If sprite has `purchase` intent 
    then if sprite has `wallet` contents and within merchant distance
        inititate sprite to merchant transaction
    else if no `wallet` contents,
        then if item in `bag | belt`
            add `sell` intent
        else if no item in `bag | belt
            add `loot` intent.

If sprite has `sell` intent
    then if sprite within other_sprite interaction distance
        then if other_sprite is willing
            initiate sprite to sprite transaction
        else
            seek another_sprite
    else:
        seek other_sprite 

If sprite has `loot` intent
    then if sprite within treasure chest, crop, nymph or loot ..
        initiate loot type interaction
            if treasure chest or crop or loot
                then sprite interact
            if nymph
                then sprite attack

needs some way for price increases/decreases to affect sprite `intent`. also need other `intents` that "motivate economic activity". For example, if sprite has `intent` to purchase, then if purchase_price > some boundary, then `intent` receives less precedence, i.e. "desire". if purchase_price < some_boundary, then `intent` receives greather precedence.

or, another example, if purchase_price > some other boundary, that might induce a sprite to create an intent to `sell`. I.e., perhaps sprites have "desires" to acquire if conditions are met.

or, another example (this might not work or be a good example), suppose we create a sprite `intent` to `enter`, for entering bomb-locked door, this could act on the sprite's `bag`, in that the sprite will "desire" to acquire a shrapnel_bomb, so `intent` to enter creates `intent` to `purchase` shrapnel_bomb, and then once acquired, creates `intent` to `locate` bomb-locked door, and then intent to `open`, which initiates sprite `use` state.



IDEA: make one of the plot predicates an economic indicator, i.e. enter plot state whatever if certain price is greater than or less than some critical points. In other words, a plot state for "economic boom" and "economic recession".

~~~~~~~~~~~~~~~~~~~
THIS NEXT ONE FIRST (after interface stuff)
~~~~~~~~~~~~~~~~~~~

- Nymphs and nymphsets. Nymphs are the answer to the uniqueness of sprites. Sprites are unique state machines. Nymphs are generic state machines. "Nymphsets".

~~~~~~~~~~~~~~~~~~~~
THAT PREVIOUS ONE FIRST
~~~~~~~~~~~~~~~~~~~~

- dialogue should be of the same form as hud, insofar as its used to hold static position information about widgets. in dialogue's case, the widget will be a scrollable display frame, a scrollbar and scroll thumb.

- make a sheet of all the singleton objects in the avatars folder. edit and crop nymph sheets to be same size, i.e. rows and columns, not necessarily dimensions, although dimensions would be nice.


- conf directory is parameterized, parameterize asset directory too. will probably require wrapping in object.

- idea: keep the previous world state in read only variable to be able to compare when filtering intents, so sprites "remember".

- todo: should initialize common calculations in some sort of cache. like the distance from (0,0) to (world_h, world_w), cos(45), sin(45), etc.

- world bounds have problems with new collision detection. will need to treat separately.

- discovery sound when pressure plate is pressed and gate opens somewhere...

- it might be better to add another nest in the asset directory structure, so compositions can be specified in separate files, otherwise composite.yaml is going to be huge. Plus, it promotes "modularity" of the composition.