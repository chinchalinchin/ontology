# Ontology: Compositions

A Composition is collection of multiple Assets organized into a common configuration to allow their "*virtualization*" and reuse. A Composition Configuration defines a Composition `id` that can be referenced like any other Asset in the [state file](./00-overview.md#state). 

Composition Configuration can be found in `/src/data/config/compositions/main.yml`, otherwise known as the *composition directory*.

## Overview

From the perspective of the [state files](./00-overview.md#state), Compositions are another type of Asset that can be deployed onto the Board. Similar to the [Player](./02-sprites.md#player), they are a "*virtual*" Asset composed of other Assets, i.e. they do not have properties of their own. Unlike the Player, which is a special type of Sprite, Compositions are collections of multiple Assets. When a Composition is deployed onto the Board, its individual Assets are added to the appropriate (Category, Instance)-nodes in the [Asset Hierarchy](./01-assets.md#asset-hierarchy)

Compositions are organized around [Struts](./01-assets.md#struts). They serve as abstract containers (or wrappers) around Struts. Compositions, in a sense, are the *realization* of a Strut. While Struts can be deployed individually onto the Board, their true purpose to provide a "root" for other Assets.

A Composition is a way to reuse common Asset configurations in the state without having to specify their individual components each time they are deployed. Functionally, Compositions serve no purpose from the Board's perspective. They only serve to simplify the amount of state specification that is required to fully declare a complex, high-level game Board.

To achieve this, Compositions have a *Pseudo State* and a *Deployed State*. A Composition Pseudo State is a formula for constructing the game state of its component Assets from its Deployed State. The Pseudo State of a Composition is configured in the composition directory, whereas the Deployed State is set in the state directory, alongside the other Asset states.

**Pseudo State: CompositionPseudoState**

- `root`
    - `strut: PropertyState`
    - `components: StateSchema`
- `branches`
    - `strut: PropertyState`
    - `components: StateSchema`

**Deployed State: PropertyState**

- `layer: str`
- `position: Position`
- `owner: str`

### Root Struts

Every Composition has atleast one [Strut](./01-assets.md#struts), known as the root Strut. If it has more than one, the other Struts are known as branch Struts. 

A Composition contains other Assets in predefined configurations, known as the Composition components. Each Strut in a Composition has components.

For example, a `brick-house` Composition might contain a `frame-brick` Strut as its root Strut and then a `mansion` Door as a component Asset. The Composition specifies the relative position of the `mansion` Door with respect to the origin of the `frame-brick` Strut, i.e. all component Assets in a Composition have their positions unpacked relative to the root Strut's deployed position. 

### Pseudo State

The state files specify Compositions to deploy. The game converts these Compositions into ingame Assets that belong to the [Asset Hierarchy](./01-assets.md#asset-hierarchy). When Compositions are unpacked by the [Orchestrator](./00-overview.md#orchestrator) during the [bootstrapping](./09-architecture.md#initialization), each Asset in a Composition is appended to the [Board](./00-overview.md#board) state dynamically. In other words, the Assets in Compositions, once unpacked, are treated separately by the Engine, as if they had been specified in the state directory individually.

Components of Compositions have a Pseud State. During the [application bootstrap](./09-architecture.md#initialization), each component's Pseud State is hydrated into an actual Asset State and injected into the Board.

For example, consider the following Composition configuration,

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
    Except for Position (see immediately below), the Pseudo State of the components of a Composition overrides the deployed state of the root Strut. In this example, the `state.layer` of `door-frame` would be `compose-layer`, regardless of the `layer` passed to the root Strut when deployed. 

The root Strut (`brick-house.root`) does not have a Position, where as the `brick-house.branches` Strut does; this is the defining featuer of Composition Pseudo State. The Composition configuration leaves the root Strut Position state and layer "empty", so that it can be injected by the state file during deployment; however the configuration for component Assets contain information for constructing their states from the root Strut state. Consider deploying the above Composition onto a Board, e.g. with the following YAML in the state directory,

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

Compositions are not processed by the same hydration algorithm as the other Assets in the state file. A special Decomposer class is used to process the Composition's Deployed State into its component Asset states. 

In the current example, the branch of the Composition has its Strut position calculated relative to the root Strut. The components of each Strut are then calculated relative to its parent Strut.

The root Position, `(100, 100)`, is added to each of its individual components **and** the branching Strut, whose position is then used to calculated its own component Assets' Positions. In this example, `house-door` is located at `(120, 120)`, whereas the `house-interior` is located at `(110, 110)` so that `door-frame` inherits this branch's starting location and is calculated as `(130, 130)`. The details of this calculation are given below,

* **Coordinate Translation:** `Child Absolute Position = Parent Absolute Position + Child Pseudo Position`.
    * *Root's Component:* `(100, 100) + (20, 20) = (120, 120)`
    * *Branching Strut:* `(100, 100) + (10, 10) = (110, 110)`
    * *Branch's Component:* `(110, 110) + (20, 20) = (130, 130)`

Other than Position, which is calculated according to the above formula, any state attribute *not* specified in a component Asset Pseudo State automatically inherits the root Strut's Deployed State, if those attributes exist on the root Strut. 

The Pseudo State of component Assets (and branching Struts) can be bound to the root Struts Deployed State as well, to allow for the parameterization of relationships. In this example, the Deployed State `layer` is passed down as a reference to the component `door-frame` Asset, which then uses it to specify its (Pseudo State) attribute for `outlayer` through the use of `bind(root.layer)`; This is how the interior Door leads back to the deployed layer, allowing the Player to return from whence they came. In other words, a binding is a formal constraints between Asset states that makes component Asset states dependent on the root Strut state. This constraint is realized during the Composition unpacking and Pseudo State hydration.

All component Assets can `bind(state)` to a root Strut state attribute injected into the Composition from the state directory files. When component Asset reference `bind(root.layer)` this is a reference to the root Strut's layer. Only state attributes defined on the root Strut can be bound.

In addition, unique names are generated for each component Asset of a Composition according to the schema: `<instance.name>-<strut.name>-<component.name>-<increment>`, where `<increment>` is an index to track the number of unique Compositions deployed on the Board to ensure each has a correspondingly unique name.

## Decomposer

The Decomposer is the package of the application responsible for translating Composition Configuration into Assets. Taking the example from the previous section, the algorithm for the expansion (decomposition) logic can be modeled as a tree traversal (like Depth-First Search), where spatial data and inherited state propagate downward from parent to child.

### Decomposition 

**1. Root Hydration (The Context)**

* **Action:** Instantiate the root Strut using the exact deployment state provided by the `Board` (e.g., `position: (100, 100)`).
* **Role:** This instantiated state becomes the "Root Context." It serves as the base coordinate for branching Struts and the dictionary payload for all `bind(root.*)` evaluations across the entire Composition.

**2. State Superposition (Parent to Child)**

For every child node (whether it is a component of the root, or a branching Strut), apply the following logic:

* **Coordinate Translation:** `Child Absolute Position = Parent Absolute Position + Child Pseudo Position`.
    * *Root's Component:* `(100, 100) + (20, 20) = (120, 120)`
    * *Branching Strut:* `(100, 100) + (10, 10) = (110, 110)`
    * *Branch's Component:* `(110, 110) + (20, 20) = (130, 130)`
* **Attribute Inheritance:** If a child's PseudoState lacks a required field (like `owner` or `layer`), it inherits that value directly from its immediate Parent, not necessarily the Root.

**3. Late-Binding Resolution**

* **Action:** Before finalizing a child's state, scan all of its string values for the regex pattern `bind\(([^)]+)\)`.
* **Evaluation:** If a match like `bind(root.layer)` is found, parse the target (`layer`) and query the "Root Context" created in Step 1.
* **Override:** Replace the string with the resolved value. If a branch specifies `outlayer: bind(root.layer)`, and the deployed root layer is `'0'`, the branch's outlayer becomes `'0'`.

**4. Unique Nomenclature Generation**

* **Action:** To prevent namespace collisions on the `Board` when multiple identical Compositions are deployed, apply a global monotonic incrementor.
* **Format:**
    * For Root/Branches: `<instance>-<deployment_name>-<increment>` (e.g., `strut-player-home-1`)
    * For Components: `<instance>-<parent_name>-<increment>` (e.g., `door-house-interior-1`)

**5. Flattening**

* **Action:** As each node is fully resolved, instantiated, and named, append it to a flat, 1D list.
* **Result:** The engine receives a standard list of `Asset` objects, completely ignorant of the fact that they were generated from a nested Composition macro.

### Application Flow

The Decomposer is a standalone service instantiated *before* the Board and Cradle; it is used during the initial Asset hydration phase of the bootstrapping **and** it is employed ingame by [Mechanics](./05-mechanics.md) through the Board interface of the Cradle to instantiate Compositions through the [`build` Intention](./04-intentions.md).

Because the Decomposer inherently generates `Asset` instances, it acts as a higher-level orchestrator of the `Factory`. To do this, it needs access to the global [Asset properties](./00-overview.md#assets), [Recipes](./appendices/01-schemas.md#recipe-configuration) and Composition configuraiton.

**1. Initialization (The Setup)**

The Decomposer must be instantiated inside the `Orchestrator`, immediately after the YAML files are loaded and validated, but *before* `migrate()` is called.

* **Dependencies:** The Orchestrator passes the `configurations.compositions` (the macro blueprints), the `properties` (for hitbox/dimension lookups), and the `configurations.recipes` into the Decomposer's constructor.
* **Statefulness:** Because it is instantiated once as a singleton-like service for the session, its internal `increment` counter starts at 0 and safely scales upwards, guaranteeing unique names whether a Composition is spawned at boot or 10 hours into the game.

**2. Bootstrap Hydration (The Orchestrator Flow)**

During `Orchestrator.migrate()`, the application parses the `state` directory.

* **Interception:** When the Orchestrator loop encounters the `self.state.compositions` list (the Compositions placed manually in the YAML state files), it does not try to process them natively.
* **Execution:** Instead, it passes each deployed state object directly to `Decomposer.unpack(deployed_state)`.
* **Flattening:** The Decomposer returns a flat `List[Asset]`. The Orchestrator simply calls `.extend()` to append these to the master `assets` list being compiled for the `Board`. The Board boots up completely unaware that these assets originated from a macro.

**3. Runtime Injection (The Cradle Flow)**

During `Orchestrator.inject()`, when the `Cradle` is instantiated, the Orchestrator passes the *exact same Decomposer instance* into the Cradle's constructor.

* **The Interface:** The Cradle exposes a new method: `spawn_composition(id, position, layer, owner)`.
* **Execution:** When a Mechanic (like `IndustryMechanics` processing a `build` Intention) requests a Composition, it calls this Cradle method. The Cradle creates a temporary pseudo-state from the arguments and passes it to its internal `Decomposer.unpack()`.
* **The Return:** The Decomposer applies the exact same relative positioning, string binding, and unique incrementing as it did at boot, returning the flat `List[Asset]`.
* **Board Integration:** The Mechanic receives the list and pushes it directly into the game loop via `Board.add()`.

**Result**

1. **Single Source of Truth:** Whether a house is placed in a YAML file or built by an NPC Sprite dynamically, the exact same mathematical superposition and binding logic executes.
2. **State Safety:** The global increment tracker lives safely inside the Decomposer. Because both the Orchestrator and the Cradle share the exact same Decomposer instance in memory, `house-door-1` at boot ensures that the first runtime built door becomes `house-door-2`.
3. **Strict Boundaries:** The `Board` remains a dumb database. It never knows what a "Composition" is; it just holds the resulting tiles, doors, and struts.