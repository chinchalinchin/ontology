# Ontology: Compositions

A Composition is collection of multiple Assets organized into a common configuration to allow their "*virtualization*" and reuse. A Composition Configuration defines a Composition `id` that can be referenced like any other Asset in the [state file](./00-overview.md#state). 

## Overview

From the perspective of the state directory, Compositions are another type of Asset that can be deployed onto a Board. Similar to the [Player](./02-sprites.md#player), they are a "*virtual*" Asset composed of other Assets. Unlike the Player, which is a special type of Sprite, Compositions are collections of multiple Assets.

Compositions are organized around [Struts](./01-assets.md#struts).

### Root Struts

Every Composition has atleast one root [Strut](./01-assets.md#struts). A Composition also contains other Assets in predefined configurations, known as the Composition components. For example, a `brick` Composition might contain a `frame-brick` Strut as its root Strut and then a `mansion` Door as a component Asset. The Composition specifies the relative position of the `mansion` Door with respect to the origin of the `frame-brick` Strut. In other words, all component Assets in a Composition have their positions unpacked relative to the root Strut's deployed position. 

### State Hydration

The state files specify Compositions to deploy. The game converts these Compositions into ingame Assets that belong to the [Asset Hierarchy](./01-assets.md#asset-hierarchy). When Compositions are unpacked by the [Orchestrator](./00-overview.md#orchestrator) during the [bootstrapping](./09-architecture.md#initialization), each Asset in a Composition is appended to the [Board](./00-overview.md#board) state dynamically. In other words, the Assets in Compositions, once unpacked, are treated separately by the Engine, as if they had been specified in the state directory.

Components of Compositions have a PseudoState. During the [application bootstrap](./09-architecture.md#initialization), each component's PseudoState is hydrated into an actual Asset State and injected into the Board.

For example, consider the following Composition configuration (defined in `/src/data/config/compositions/main.yml`, i.e., the *composition directory*.),

```yaml
compositions:
    brick-house:
        -   strut: 
                id: frame-brick
                name: house-exterior
            components:
                -   id: mansion
                    name: house-door
                    category: objects
                    instance: doors
                    outlayer: 'compose-layer'
                    position:
                        x: 10
                        y: 10
                    out:
                        x: 10
                        y: 10
        -   strut: 
                id: wall-blue
                name: house-interior
                owner: bind(root.owner)
                layer: 'compose-layer'
                position:
                    x: 25
                    y: 25
            components:
                -   id: door-shadow
                    name: door-frame
                    category: objects
                    instance: doors
                    layer: 'compose-layer'
                    outlayer: bind(root.layer)
                    position:
                        x: 10
                        y: 10
                    out:
                        x: 10
                        y: 10
```

This is a formula for a `brick-house` composed of two Struts on different [Layers](./00-overview.md#layers), each of which have their own Door, each Door being linked to one another through a circuit (`'compose-layer' <-> bind(root.layer)`). In this way, the "inside" of Assets can be traversed. In other words, each Composition may be composed of separate, independent Layers. 

!!! note
    The PseudoState of the Composition overrides or modifies the deployed State. In this example, the `state.layer` of `door-frame` would be `compose-layer`, as opposed `root.layer`. 

The root Strut (first entry of the Composition list) does not have a Position, where as the next Strut does; this is what is meant by Composition PseudoState. The Composition configuration leaves the root Strut Position state "empty", so that it can be injected by the state file for deployment; however the configuration for component Assets contain information for constructing their states from the root Strut state. When the above Composition is deployed into the Board state, e.g.,

```yaml
compositions:
    - id: brick-house
      name: player-home
      layer: '0'
      owner: player
      position:
        x: 100
        y: 100
```

The root Position, `(100, 100)`, is added to the component Assets' PseudoState, so that `house-door` is located at `(110, 110)`, whereas the `house-interior` is located at `(125, 125)`. 

Likewise, in this example, the state `layer` is passed down as a reference to component Asset PseudoStates that use `bind(root.layer)`

All component Assets can `bind(state)` to a root Strut state attribute injected into the Composition from the state directory files. When component Asset reference `bind(root.layer)` this is a reference to the root Strut's layer. Only state attribute defined on the root Strut can be bound.

In addition, unique names are generated for each Composition Asset according to the schema: `<instance.name>-<strut.name>-<component.name>-<increment>`, where `<increment>` is an index to track the number of unique Compositions deployed on the Board to ensure each has a correspondingly unique name.