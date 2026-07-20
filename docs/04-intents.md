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

Possibly null.

### Communication

Possibly null.

A Communication contains a key to retrieve the content of a specific text file contained in `/src/data/intents/communications/<key>.txt`.
