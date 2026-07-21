# Ontology: Intents

*Intent* represents a mutable state change for an Asset. Intents are passed to Assets via the game loop. All Assets implement an `update` method that receives as argument an Intent object. This method is called during the game loop for each Asset. 

!!! important
    *Immutable*, *inanimate* Assets, while implementing an `update` method, receive a null Intentn. All other Asset categories implement a non-trivial `update` method.

An Intent has atleast one of the following: *action*, *direction*, *disposition* and *communication*.

## Intent Schema

- Location: `/src/assets/intents/main.yaml`

```yaml
--8<-- "docs/.static/yaml/property-intents.yaml"
```

## Intent Overview

### Action

Possibly null.

!!! info "LPC Default"
    The default Actions created for the LPC Assets is enumerated below,

    - CAST
    - THRUST
    - WALK
    - SLASH
    - SHOOT
    - DIE

### Direction

Possibly null.

!!! info "LPC Default"
    The default Actions created for the LPC Assets is enumerated below,

    - UP
    - LEFT
    - DOWN 
    - RIGHT

### Disposition

A Disposition is an internal state attribute of a Sprite. This attribute determines the state progression of non-playable character. For example, Sprites with a Disposition of `IDLE` cannot enter into the `ATTACK` Disposition without first passing through a `SHOCK` or `THREATEN` Disposition, and a Sprite cannot engage in the `SLASH` or `SHOOT` Action without first being in the `ATTACK` Disposition. 

As can be seen from this example, Disposition manages the possible states (in particular, Actions) that can be reached from the Sprite's current state. Disposition is covered more thoroughly in the [Sprites documentation](./05-sprites.md), along with a complete map of Dispositions and Actions.

### Communication

Possibly null.

A Communication contains a key to retrieve the content of a specific text file contained in `/src/data/intents/communications/<plot-state>.yaml#<key>`, where `<plot-state>` .
