- it would be nice if instead of dictionary state and configuration were kept in native python objects so values could be accessed with dot notation instead of dictionary key lookups.

- ups vs fps

- the question arises. should each sprite be unique? or, like with strutsets and platesets, if the configuration should allow sets of them to be declared. The question there is how to differentiate sprite states. Currently, each sprite is keyed to dictionaries in the world object. If the concept of a spriteset is to be introduced, then a stateset must be also be introduced, so each member of the set has its own unique state recorded in the world state.It is either that, or each npc and villain needs its own definition in the configuration, which might get out of hand.

another option would be to introduce a division in the concept of npc and villain. there could be anoynmous and character npcs, and stranger and rogue villains, where anonymosu and stranger sets offer less functionality, but allow sets to be declared, where as character and rogues are unique. Perhaps. Perhaps. Will need to think on it.