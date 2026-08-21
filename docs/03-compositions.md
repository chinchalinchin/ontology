# Ontology: Compositions

A Composition is collection of multiple Assets organized into a common configuration to allow their "*virtualization*" and reuse. A Composition Configuration defines a Composition `id` that can be referenced like any other Asset in the [state file](./00-overview.md#state). 

## Overview

From the perspective of the state directory, Compositions are another type of Asset that can be deployed onto a Board. Similar to the [Player](./02-sprites.md#player), they are a "*virtual*" Asset composed of other Assets. Unlike the Player, which is a special type of Sprite, Compositions are collections of multiple Assets.

A Composition is a way to reuse common Asset configurations in the state without have to specify their individual components each time they are deployed. Functionally, Compositions serve no purpose from the Board's perspective. They only serve to simplify the amount of state specification that is required to fully declare a complex, high-level game Board.

Compositions are organized around [Struts](./01-assets.md#struts).

### Root Struts

Every Composition has atleast one [Strut](./01-assets.md#struts), known as the root Strut. If it has more than one, the other Struts are known as branch Struts. 

A Composition contains other Assets in predefined configurations, known as the Composition components. Each Strut in a Composition has components.

For example, a `brick-house` Composition might contain a `frame-brick` Strut as its root Strut and then a `mansion` Door as a component Asset. The Composition specifies the relative position of the `mansion` Door with respect to the origin of the `frame-brick` Strut, i.e. all component Assets in a Composition have their positions unpacked relative to the root Strut's deployed position. 

### State Hydration

The state files specify Compositions to deploy. The game converts these Compositions into ingame Assets that belong to the [Asset Hierarchy](./01-assets.md#asset-hierarchy). When Compositions are unpacked by the [Orchestrator](./00-overview.md#orchestrator) during the [bootstrapping](./09-architecture.md#initialization), each Asset in a Composition is appended to the [Board](./00-overview.md#board) state dynamically. In other words, the Assets in Compositions, once unpacked, are treated separately by the Engine, as if they had been specified in the state directory individually.

Components of Compositions have a PseudoState. During the [application bootstrap](./09-architecture.md#initialization), each component's PseudoState is hydrated into an actual Asset State and injected into the Board.

For example, consider the following Composition configuration (defined in `/src/data/config/compositions/main.yml`, i.e., the *composition directory*.),

```yaml
compositions:
    brick-house:
        root:
            strut: 
                id: frame-brick
                name: house-exterior
            components:
                objects:
                    doors:
                        -   id: mansion
                            name: house-door
                            outlayer: 'compose-layer'
                            position:
                                x: 20
                                y: 20
                            out:
                                x: 10
                                y: 10
        branches:
            -   strut: 
                    id: wall-blue
                    name: house-interior
                    owner: bind(root.owner)
                    layer: 'compose-layer'
                    position:
                        x: 10
                        y: 10
                components:
                    objects:
                        doors:
                            -   id: door-shadow
                                name: door-frame
                                layer: 'compose-layer'
                                outlayer: bind(root.layer)
                                position:
                                    x: 20
                                    y: 20
                                out:
                                    x: 10
                                    y: 10
```

!!! note
    `components` is an [Asset State](./00-overview.md#state) schema, identical to a state file.

This is a formula for a `brick-house` composed of two Struts on different [Layers](./00-overview.md#layers), each of which have their own [Door](./01-assets.md#doors), each Door being linked to one another through a circuit (`'compose-layer' <-> bind(root.layer)`). In this way, the "inside" of Assets can be traversed. In other words, each Composition may be composed of separate, independent Layers. 

!!! note
    Except for Position (see immediately below), the PseudoState of the components of a Composition overrides the deployed state of the root Strut. In this example, the `state.layer` of `door-frame` would be `compose-layer`, regardless of the `layer` passed to the root Strut when deployed. 

The root Strut (`brick-house.root`) does not have a Position, where as the `brick-house.branches` Strut(s) does
(do); this is what is meant by Composition PseudoState. The Composition configuration leaves the root Strut Position state and layer "empty", so that it can be injected by the state file during deployment; however the configuration for component Assets contain information for constructing their states from the root Strut state. When the above Composition is deployed into the Board state, e.g.,

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

The root Position, `(100, 100)`, is added to the component Assets' PseudoState, so that `house-door` is located at `(120, 120)`, whereas the `house-interior` is located at `(110, 110)`. Any state attribute *not* specified in a component Asset PseudoState automatically inherits the root Strut State, if those attributes exist on the root Strut. 

The PseudoState attribute of component Assets (and branching Struts) can be bound to the root Strut as well, to allow for parameterization of relationships. In this example, the state `layer` is passed down as a reference to the component `door-frame` Asset, which then uses it to specify its (PseudoState) attribute for `outlayer` through the use of `bind(root.layer)`; This is how the interior door leads back to the deployed layer, allowing the Player to return from whence they came. In other words, a binding is a formal constraints between Asset states that makes component Asset states dependent on the root Strut state. This constraint is realized during the Composition unpacking and PseudoState hydration.

All component Assets can `bind(state)` to a root Strut state attribute injected into the Composition from the state directory files. When component Asset reference `bind(root.layer)` this is a reference to the root Strut's layer. Only state attributes defined on the root Strut can be bound.

In addition, unique names are generated for each component Asset of a Composition according to the schema: `<instance.name>-<strut.name>-<component.name>-<increment>`, where `<increment>` is an index to track the number of unique Compositions deployed on the Board to ensure each has a correspondingly unique name.