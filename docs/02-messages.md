# Ontology: Messages

Sprites consume Messages. Messages represent mutable state changes. Messages are generated and passed to Assets via the game loop. Messages are divided into Instructions and Intents.

The base class for a message is Instruction. Instructions are extended into Intents for more complex operations, i.e. all Intents are Instructions, but not all Instructions are Intents. 

All Assets implement an `update` method that receives as argument an Instruction object. This method is called during the game loop for each Asset. 

## Schema

- Location: `/src/assets/intents/main.yaml`

```yaml
--8<-- "docs/.static/yaml/data-intents.yaml"
```

## Instructions

An Instruction has a Direction and Action. 

Instructions are primarily utilized by the [Player](./04-player.md) interface. Controller mappings are converted into Instructions, which are then passed to the Player Sprite during the game loop. In addition, Instructions are utilized by mutable, inanimate Objects, such as Cursors and Crates, which change their position state within the game loop and do not require complex handling.

### Attributes

!!! info "LPC Default"
    The default Actions created for the LPC Assets is enumerated below,

    - CAST
    - THRUST
    - WALK
    - SLASH
    - SHOOT
    - DIE

!!! info "LPC Default"
    The default Actions created for the LPC Assets is enumerated below,

    - UP
    - LEFT
    - DOWN 
    - RIGHT

!!! important
    *Immutable*, *inanimate* Assets, while implementing an `update` method, receive a null Message. All other Asset categories implement a non-trivial `update` method.

Action and Direction may determine ingame events, such as an Asset moving across the screen or starting an attack animation. In the case of Sheets, Action and Direction jointly determine the coordinates of the Asset frame to use.

## Intents

An Intent has atleast one of the following: *action*, *direction*, *disposition* and *communication*.

### Attributes

**Action**

Possibly null.

**Direction**

Possibly null.

**Disposition**

A Disposition is an internal state attribute of a Sprite. This attribute determines the state progression of non-playable character. For example, Sprites with a Disposition of `idle` cannot enter into the `attack` Disposition without first passing through a `recoil` or `threaten` Disposition, and a Sprite cannot engage in the `slash` or `shoot` Action without first being in the `attack` Disposition. 

As can be seen from this example, Disposition manages the possible states (in particular, Actions) that can be reached from the Sprite's current state, i.e. Dispositions govern the logic of state transitions. The Disposition transition tree is covered more thoroughly in the [Sprites documentation](./03-sprites.md).

**Communication**

Possibly null.

A Communication contains a key to retrieve the content of a specific text file contained in `/src/data/intents/communications/<plot-state>.yaml#<key>`, where `<plot-state>`.