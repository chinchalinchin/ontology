# Ontology: Messages

Sprites consume Messages. Messages represent mutable state changes. Messages are generated and passed to Assets via the game loop. All Assets implement an `update` method that receives as argument an Instruction object. This method is called during the game loop for each Asset. 

The base class for a message is Instruction. Instructions are extended into Intents for more complex operations, i.e. all Intents are Instructions, but not all Instructions are Intents. 

## Schema

### Intent Schema

- Location: `/src/assets/intents/main.yaml`

```yaml
--8<-- "docs/.static/yaml/data-intents.yaml"
```


## Instructions

An Instruction has a Direction and Action. 

Instructions are primarily utilized by the [Player](./06-player.md) interface. Controller mappings are converted into Instructions, which are then passed to the Player Sprite during the game loop. In addition, Instructions are utilized by mutable, inanimate Objects, such as Cursors and Crates, which change their position state within the game loop and do not require complex handling.

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

## Intents

An Intent has atleast one of the following: *action*, *direction*, *disposition* and *communication*.

### Attributes

**Action**

Possibly null.

**Direction**

Possibly null.

**Disposition**

A Disposition is an internal state attribute of a Sprite. This attribute determines the state progression of non-playable character. For example, Sprites with a Disposition of `IDLE` cannot enter into the `ATTACK` Disposition without first passing through a `SHOCK` or `THREATEN` Disposition, and a Sprite cannot engage in the `SLASH` or `SHOOT` Action without first being in the `ATTACK` Disposition. 

As can be seen from this example, Disposition manages the possible states (in particular, Actions) that can be reached from the Sprite's current state. Disposition is covered more thoroughly in the [Sprites documentation](./05-sprites.md), along with a complete map of Dispositions and Actions.

**Communication**

Possibly null.

A Communication contains a key to retrieve the content of a specific text file contained in `/src/data/intents/communications/<plot-state>.yaml#<key>`, where `<plot-state>`.