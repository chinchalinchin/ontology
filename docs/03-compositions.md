# Ontology: Compositions

TODO

Every Composition has atleast one root Strut. A Composition also contains other Assets in predefined configurations. For example, a `brick` Composition might contain a `frame-brick` Strut as its root Strut and then a `mansion` Door as a component Asset. The Composition specifies the relative position of the `mansion` Door to the origin of the `frame-brick` Strut. In other words, all Assets in a Composition have their positions unpacked relative to the root Strut's deployed position. 

From the perspective of the state directory, Compositions are another type of Asset that can be deployed onto a Board. Similar to the [Player](./02-sprites.md#player), they are a "*virtual*" Asset composed of other Assets. Unlike the Player, which is a special type of Sprite, Compositions are collections of multiple Assets.

The state files specify Compositions to deploy. The game converts these Compositions into ingame Assets that belong to the [Asset Hierarchy](./01-assets.md#asset-hierarchy). When Compositions are unpacked by the [Orchestrator](./00-overview.md#orchestrator) during the [bootstrapping](./09-architecture.md#initialization), each Asset in a Composition is appended to the [Board](./00-overview.md#board) state dynamically. 

Components of Compositions have a PseudoState. Each component's PseudoState is hydrated into Asset State and injected the Board. A unique name is generated based on the Composition `name` and an index that tracks the number of unique Compositions of a particular `name` that have been deployed. For example, consider the following Composition,

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
                    layer: '0'
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
                layer: 'compose-layer'
            components:
                -   id: door-shadow
                    name: house-door
                    category: objects
                    instance: doors
                    layer: 'compose-layer'
                    outlayer: bind(root[0])
                    position:
                        x: 10
                        y: 10
                    out:
                        x: 10
                        y: 10
```

This would be a formula for a `brick-house` composed of two root Struts on different layer, each which have their own Door. Each Door is linked to one another. In this way, the "inside" of Assets can be traversed, where each Composition may be composed of separate, independent Layers. 

!!! note
    The PseudoState of the Composition overrides the deployed State.

TODO

All Component Assets "inherit" the `owner` of the root Strut.

TODO