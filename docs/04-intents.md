# Ontology: Intents

*Intent* represents a mutable state change for an Asset. Intents are passed to Assets via the game loop. All Assets implement an `update` method that receives as argument an Intent object. This method is called during the game loop for each Asset. 

!!! important
    *Immutable*, *inanimate* Assets, while implementing an `update` method, do not operate on the received Intent. All other Asset categories implement a non-trivial `update` method.

An Intent has atleast one of the following: *action*, *direction*, *disposition* and *communication*.

## Intent Overview

**Action**

TODO

**Direction**

TODO

**Disposition**

TODO

**Communication**

## Intent Schema

- Location: `/src/assets/intents/main.yaml`

```yaml
--8<-- "docs/.static/yaml/property-intents.yaml"
```