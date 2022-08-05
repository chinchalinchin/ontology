- it would be nice if instead of dictionary state and configuration were kept in native python objects so values could be accessed with dot notation instead of dictionary key lookups. this is potentially a huge ask, since the application is written using dictionary look up notation.

- ups vs fps

- the question arises. should each sprite be unique? or, like with strutsets and platesets, if the configuration should allow sets of them to be declared. The question there is how to differentiate sprite states. Currently, each sprite is keyed to dictionaries in the world object. If the concept of a spriteset is to be introduced, then a stateset must be also be introduced, so each member of the set has its own unique state recorded in the world state.It is either that, or each npc needs its own definition in the configuration, which might get out of hand.

another option would be to introduce a division in the concept of npc. there could be stranger and character npcs, where anonymosu and stranger sets offer less functionality, but allow sets to be declared, where as character and rogues are unique. Perhaps. Perhaps. Will need to think on it.

- exiting a door has a problem with collision engine, since when you exit you will most likely be intersecting with outside object, but facing the wrong way you would approach it in-layer. thus, the character sprite slides over the hitbox.

- when rendering, should check if element intersects with crop box to determine whether or not to proceed with rendering, i.e. only render on screen elements. already inherently does this with layers. need an additional positional check.

- for some reason, the npc walk_left and walk_right are not mapping the same way as the player walk_left and walk_right. i have to switch the rows for npcs, where as the hero is fine. control mapping issue?

- allow sprites to create their own intents if attacked by another sprite, i.e. add intent of attacking_sprite to sprite['intents']

- add `looper` property to sprite definitions to allow developers to turn off game loop physics and interactions for that sprite. lets scripts completely control the sprite state.

- multiple regression of sprite states against hero state vs. collection of simple linear regression of sprite state against state.

- if sprite aware: train model: if iteration == learning_rate or something, then apply prediction

- desires: `safety`, `treasure`, `battle`, `relationship`

- Sprites have paths, intents, desires, expressions.

A path is a point in space a sprite seeks to find. An intent operates on the path by searching for world state conditions. An intent can change the state of sprite.

A desire is a point in plot space a sprite seeks to find. An expression operates on the sprite state directly by searching for the plot state conditions.

in order to achieve a more sensitive feedback loop between desire and state, another channel of communication is opened between desire and intent. Desires should prioritize intents. 

Aha. Desire is the ordering of intent. Expression and intent are the transmittal of desire to state. 

What does plot space looks like?


- Ingest interface styles through yaml instead of hardcoded constants (80% done)

- Menu can alter the world's dynamic state. HUD cannot. HUD is just a vessel for information, while Menu is an interface for altering information (or at least associations)

- The essence of the collision bug is due to the diagonal directions. When only four directions, no bugs. But because recoil is based on direction of sprite, and diagonal movement mixes orthogonal directions with left and right, result in recoil not knowing which direction to send the sprite. Only applies to hero since that is the only sprite that can move diagonally.

- Make Conf and State wrapper classes singletons (so conf is not loaded over and over again)


- Every sprite has a sell interaction with whatever is in their bag or belt.

- Special entity type: merchant. Merchant acts as an interface between sprites and "economy". 


    
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

- more debug output

- dialogue should be of the same form as hud, insofar as its used to hold static position information about widgets. in dialogue's case, the widget will be a scrollable display frame, a scrollbar and scroll thumb.

- make a sheet of all the singleton objects in the avatars folder. edit and crop nymph sheets to be same size, i.e. rows and columns, not necessarily dimensions, although dimensions would be nice.


- conf directory is parameterized, parameterize asset directory too. will probably require wrapping in object.

- what if, instead of the player sprite reacting directly to user input, sprites were written to react to intents? that way, hero could be treated along with npcs. each update method would parse through sprite intents and map them to state changes.

example.

instead of 

    user_input == north

have a layer that processes user_input into hero intents and then update method of,

    sprite.intent == north

in other words, user input operates on sprite intents, sprite intents operate on sprite state.


- REMEMBER. ANYTHING THAT CHANGES OVER THE COURSE OF THE GAME IS DYNAMIC STATE INFORMATION. DISTINCTION BETWEEN STATIC STATE AND CONFIGURATION: STATIC STATE DIRECTLY MAPS TO ON-SCREEN REPRESENTATION. THINGS WITHOUT STATE DO NOT GET RENDERED!!!

- perhaps subsume `radii.aware` into intents?

- idea: keep the previous world state in read only variable to be able to compare when filtering intents, so sprites "remember".