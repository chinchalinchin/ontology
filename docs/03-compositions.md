# Ontology: Compositions

A Composition is collection of multiple Assets organized into a common configuration to allow their "*virtualization*" and reuse. A Composition Configuration defines a Composition `id` that can be referenced like any other Asset in the [state file](./00-overview.md#state). 

Composition Configuration can be found in `/src/data/config/compositions/main.yml`, otherwise known as the *composition directory*.

## Asset Specification: Crafts

Compositions are used to formalize Asset relationships for reuse. For this reason, [Crafts](./01-assets.md#crafts) are an essential component of Compositions. The following section provides an in-depth description of each Craft Instance.

**Properties: CraftProperties**

* `dimensions: Dimensions`
* `hitboxes: List[Hitbox]`
* `materials: List[str]`
* `blueprints: List[str]`
* `mass: int`
* `priority: int`

### Struts 

*Struts* are inanimate, immutable Assets. Struts are meant to encapsulate the concept of property in the game, e.g. houses, fences, etc. In other words, they possess an `owner`. 

Struts may be placed on the Board through the state files manually, but they are generally instantiated ingame through the `build` [Intention](./04-intentions.md). 

Struts are closely related to [Asset Compositions](./03-compositions.md), as they provide a "foundation" upon which configurations of Assets can be built. In other words, a Strut's main purpose is to provide a coordinate system for the relative positioning of reusable Asset configurations. 

**Strut Hierarchy**

Struts are the basic element of Compositions. They are classified according to Material and Blueprint. All Struts are functionally equivalent (but may differ in the declaration of their properties), yet serve different atmospheric, vanity or aesthetic purposes; Material and Blueprint describe the axes of this "*aesthetic*" space.

**Materials**

Material serves mainly to alter the color and shading of the Strut.

- Organics: `wood`, `thatches`
- Geologics: `brick`, `granite`, `marble`, `stone`, `sandstone`
- Metallics: `copper`, `iron`, `gold`
- Chromatics: `white`, `red`, `blue`, `yellow`, `green`

**Material Palette**

--8<-- "static/md/composition-material-palette.md"

**Blueprints**

Blueprints describe specific structural implementations.
 
- Building Blueprints:
    - `floors`: Interior ground surfaces.
    - `walls`: Exterior support surfaces.
    - `flats`: Elevated surfaces.
    - `roofs`: Building enclosures.
    - `paths`: Exterior ground surfaces.
    - `halls`: Interior support surfaces.
- Interior Blueprints:
    - `carpets`
    - `wallpapers`

**Animation: None**

N/A

**Frame: MaterialFrame**

* `keys(id, state): returns [ (f"{id}-{state.material}-{state.blueprint}", 0, 0) ]`
* `index(id, properties): returns { f"{id}-{properties.materials.*}-{properties.blueprints.*}: (0, 0, properties.dimension.w, properties.dimensions.l) }`

**State: PropertyState**

* `layer: str`
* `elevaiton: int`
* `position: Position`
* `material: str`
* `blueprint: str`
* `owner: str`

**Hitbox: StaticHitbox**

* `get(properties, state, frame): returns properties.hitboxes`

### Stairs

Stairs are static Crafts sensors ($m = -1$) that provide elevation transitions when traversed. 

**Directed Specification**

- `right`: Stair starts in lower right corner and ends in upper left corner.
- `left`: Stair starts in lower left corner and ends in upper right corner.
- `up`: Stairs start along bottom edge and end along top edge.
- `down`: Stairs start along top edge and end along top edge.

!!! important
    Due to the nature of top-down two-dimensionsal graphics, to preserve perspective, the `down` direction frame must be truncated, i.e. this direction does not fill the full dimensions of the Stair frame.

**Elevation Transitions**

The direction of the elevation transition calculation is dependent on the direction of the transitioning Asset's velocity. For example, once an Asset intersects a Stair, the following conditions are elevated,

- `stairs.state.direction == 'right' and asset.state.velocity.vx < 0: asset.state.elevation += stairs.state.delta`
- `stairs.state.direction == 'right' and asset.state.velocity.vx > 0: asset.state.elevation -= stairs.state.delta`
- `stairs.state.direction == 'left' and asset.state.velocity.vx < 0: asset.state.elevation -= stairs.state.delta`
- `stairs.state.direction == 'left' and asset.state.velocity.vx > 0: asset.state.elevation += stairs.state.delta`
- `stairs.state.direction == 'up' and asset.state.velocity.vy < 0: asset.state.elevation += stairs.state.delta`
- `stairs.state.direction == 'up' and asset.state.velocity.vx > 0: asset.state.elevation -= stairs.state.delta`
- `stairs.state.direction == 'down' and asset.state.velocity.vy > 0: asset.state.elevation += stairs.state.delta`
- `stairs.state.direction == 'down' and asset.state.velocity.vx < 0: asset.state.elevation -= stairs.state.delta`

**Frame: DirectedFrame**

* `keys(id, state)`: returns `[(f"{id}-{state.direction}", 0, 0)]`
* `index(id, properties)`: returns `{f"{id}-{Directions.*}": (0, 0, w, l)}`

**State: StairState**

* `layer: str`
* `position: Position`
* `elevation: int = 0`
* `direction: str` (`up`, `down`, `left`, `right`)
* `delta: int = 1`
* `owner: Optional[str] = None`

**Hitbox: DirectedHitbox**

* `get(state, properties, frame): returns properties.hitboxes[state.direction]`

### Platforms

Platforms are inanimate, immutable Assets that model elevated surfaces. In order to be traversed, the Asset traversing must be on the same elevation as the Platform. 

Platforms have two kinds of hitboxes: baseline hitboxes and elevated hitboxes, where the former determines the Platform's collision physics on its ground level (`platform.state.elevation`) and the latter determines the Platform's collision physics on the elevated level (`platform.state.elevation + properties.hitboxes[target.state.elevation]`)

**Frame: SingleFrame**

- `keys(id, state): returns [(id, 0, 0)]`
- `index(id, properties): returns {id: (0, 0, properties.dimensions.w, properties.dimensions.l)}`

**State: PlatformState**

- `position: Position`
- `elevation: int = 0`
- `owner: Optional[str] = None`

**Hitbox: ElevatedHitbox**

- `elevations(properties, state): returns [state.elevation + k for k in properties.hitboxes.keys()]`
- `get(properties, state, elevation, frame): returns properties.hitboxes.get(elevation - state.elevation, [])`

### Carpentry

Carpentry is a collection of inanimate, immutable Crafts. It is distinguished from other Crafts by its directed frame indexing schema. Carpentry encapsulate furniture, living space fixtures and other common household furnishings.

**Frame: DirectedFrame**

TODO

**State: DirectedState**

TODO

**Hitbox: DirectedHitbox**

TODO

### Railings

Railings are a collection of inanimate, immutable Crafts. They are distinguished from other Crafts by its oriented frame indexing schema.


**Frame: OrientedFrame**

* `keys(id, state): returns [(f"{id}-{state.orientation}", 0, 0)]`
* `index(id, properties): returns {f"{id}-{Orientations.*}": (0, 0, w, l)}`


**State: OrientedState**

* `layer: str`
* `position: Position`
* `elevation: int`
* `orientation: str` (`horizontal`, `vertical`)
* `multiple: Multiple` (`nx > 1` or `ny > 1`)
* `owner: Optional[str]`

**Hitbox: OrientedHitbox**

* `get(properties, state, frame): returns properties.hitboxes[state.orientation]`

## Composition Overview

From the perspective of the [state files](./00-overview.md#state), Compositions are another type of Asset that can be deployed onto the Board. Similar to the [Player](./02-sprites.md#player), they are a "*virtual*" Asset composed of other Assets, i.e. they do not have properties of their own. Unlike the Player, which is a special type of Sprite, Compositions are collections of multiple Assets. When a Composition is deployed onto the Board, its individual Assets are added to the appropriate (Category, Instance)-nodes in the [Asset Hierarchy](./01-assets.md#asset-hierarchy)

A Composition is a way to reuse common Asset configurations in the state without having to specify their individual components each time they are deployed. Functionally, Compositions serve no purpose from the Board's perspective. They only serve to simplify the amount of state specification that is required to fully declare a complex, high-level game Board.

Compositions are organized around [Struts](./01-assets.md#struts). They serve as abstract containers (or wrappers) for Struts. Compositions, in a sense, are the *realization* of a Strut. While Struts can be deployed individually onto the Board, their true purpose is to provide a "root" for other Assets.

To achieve this, Compositions have a *Pseudo State* and a *Deployed State*. A Composition Pseudo State is a formula for constructing the game state of its component Assets from its Deployed State. The Pseudo State of a Composition is configured in the composition directory, whereas the Deployed State is set in the state directory, alongside the other Asset states.

**Pseudo State: CompositionPseudoState**

* `root`
    * `strut: PropertyState`
    * `components: StateSchema`
* `branches`
    * `strut: PropertyState`
    * `components: StateSchema`

**Deployed State: PropertyState**

* `layer: str`
* `position: Position`
* `elevation: int`
* `owner: str`

### Root Struts

Every Composition has atleast one [Strut](./01-assets.md#struts), known as the root Strut. If it has more than one Strut, the other Struts are known as branch Struts. 

A Composition contains other Assets in predefined configurations, known as the Composition components. Each Strut in a Composition has components.

For example, a `brick-house` Composition might contain a `frame-brick` Strut as its root Strut and then a `door-mansion` Door as a component Asset. The Composition specifies the relative position of the `door-mansion` Door with respect to the origin of the `frame-brick` Strut, i.e. all component Assets in a Composition have their positions unpacked relative to the root Strut's deployed position. 

In other words, Struts provided a *frame of reference* for their components.

### Pseudo State

The state files specify Compositions to deploy. The game converts these Compositions into ingame Assets that belong to the [Asset Hierarchy](./01-assets.md#asset-hierarchy). When Compositions are unpacked by the [Orchestrator](./00-overview.md#orchestrator) during the [bootstrapping](./11-architecture.md#initialization), each Asset in a Composition is appended to the [Board](./00-overview.md#board) state dynamically. In other words, the Assets in Compositions, once unpacked, are treated separately by the Engine, as if they had been specified in the state directory individually.

Components of Compositions have a [Pseudo State](#pseudo-state). During the [application bootstrap](./11-architecture.md#initialization), each component's Pseudo State is hydrated into an actual Asset State and injected into the [Board](./00-overview.md#board).

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
                            anchor: anchor(house-exterior)
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
                                anchor: anchor(house-interior)
                                outlayer: bind(root.layer)
                                position:
                                    x: 20
                                    y: 20
                                out:
                                    x: 10
                                    y: 10
```

!!! note "Pseudo State"
    `components` is an [Asset State](./00-overview.md#state) schema, identical to a state file.

!!! note "anchor() Macro"
    The Doors in this Configuration utilize the `anchor` macro to ensure they are rendered on top of their parent Struts. The `anchor` macro applies the formula, `anchor(self, target) = (target.y - target.l) - (self.y + self.l)` to dynamically calculate the rendering order, i.e. this ensures the Door is rendered on top of the parent Strut. 

    See [Rendering](./11-architecture.md#rendering) for more information on rendering order.
    
This is a formula for a `brick-house` composed of two Struts on different [Layers](./00-overview.md#layers), each of which have their own [Door](./01-assets.md#doors), each Door being linked to one another through a circuit (`'compose-layer' <-> bind(root.layer)`). In this way, the "inside" of Assets can be traversed. In other words, each Composition may be composed of separate, independent Layers. 

!!! note "Pseudo State Overrides"
    Except for Position (see immediately below), the Pseudo State of the components of a Composition overrides the deployed state of the root Strut. In this example, the `state.layer` of `door-frame` would be `compose-layer`, regardless of the `layer` passed to the root Strut when deployed. 

The root Strut (`brick-house.root`) does not have a Position, where as the `brick-house.branches` Strut does; this is the defining feature of Composition Pseudo State. The Composition configuration leaves the root Strut Position state and layer "empty", so that it can be injected by the state file during deployment. Component Assets and branching Struts define Pseudo States relative to their hierarchical contexts. Consider deploying the above Composition onto a Board, e.g. with the following YAML in the state directory,

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

Compositions are not processed by the same hydration algorithm as the other Assets in the state file. A special Decomposer service is used to process the Composition's Deployed State into its component Asset states. 

In the current example, the branch of the Composition has its Strut position calculated relative to the root Strut. The components of each Strut are then calculated relative to its parent Strut.

The root Position, `(100, 100)`, is added to each of its individual components **and** the branching Strut, whose position is then used to calculated its own component Assets' Positions. In this example, `house-door` is located at `(120, 120)`, whereas the `house-interior` is located at `(110, 110)` so that `door-frame` inherits this branch's starting location and is calculated as `(130, 130)`. The details of this calculation are given below,

Hydration uses the following rules:

* **Layer-Bounded Coordinate Translation:**
    * **Same Layer:** `Child Position = Parent Position + Child Pseudo Position`.
    * **Cross Layer:** When an entity defines a `layer` differing from its immediate parent, coordinates decouple from the parent's world position and anchor to layer origin `(0, 0)`: `Child Position = (0, 0) + Child Pseudo Position`.
        * *Root Component (`house-door` on `'0'`):* `(100, 100) + (20, 20) = (120, 120)`
        * *Branching Strut (`house-interior` on `'compose-layer'`):* `(0, 0) + (10, 10) = (10, 10)`
        * *Branch Component (`door-frame` on `'compose-layer'`):* `(10, 10) + (20, 20) = (30, 30)`
        * **Teleport `out` Resolution:**
* **Returning to Root Layer (`outlayer == root.layer`):** Teleport exit positions offset by the deployed root position: `Child Out = Root Position + Child Pseudo Out`. (`door-frame.out` evaluates to `(100, 100) + (10, 10) = (110, 110)`).
* **Entering Interior Layers (`outlayer != root.layer`):** Teleport exit positions remain local to the destination layer's coordinate plane: `Child Out = Child Pseudo Out`. (`house-door.out` evaluates to `(10, 10)`).

Other than Position, which is calculated according to the above formula, any state attribute *not* specified in a component Asset Pseudo State automatically inherits the root Strut's Deployed State, if those attributes exist on the root Strut. 

In addition, unique names are generated for each component Asset of a Composition according to the schema: `<instance.name>-<strut.name>-<component.name>-<increment>`, where `<increment>` is an index to track the number of unique Compositions deployed on the Board to ensure each has a correspondingly unique name.

#### Bindings

The Pseudo State of component Assets (and branching Struts) can be bound to the root Struts Deployed State as well, to allow for the parameterization of relationships. In this example, the Deployed State `layer` is passed down as a reference to the component `door-frame` Asset, which then uses it to specify its (Pseudo State) attribute for `outlayer` through the use of `bind(root.layer)`; This is how the interior Door leads back to the deployed layer, allowing the Player to return from whence they came. In other words, a binding is a formal constraints between Asset states that makes component Asset states dependent on the root Strut state. This constraint is realized during the Composition unpacking and Pseudo State hydration.

All component Assets can `bind()` to a root Strut state attribute injected into the Composition from the state directory files. When component Asset reference `bind(root.layer)` this is a reference to the root Strut's layer. Only state attributes defined on the root Strut can be bound.

* **Contextual Bindings:** Component Pseudo States can bind attributes to either their immediate parent or the root strut context via regex evaluation:
    * `bind(root.)` or `bind()`: Queries the root deployment context (e.g., `outlayer: bind(root.layer)`).

### Decomposer

The Decomposer is the service module of the application responsible for translating Composition Configuration into Assets. Taking the example from the previous section, the algorithm for the expansion (decomposition) logic can be modeled as a tree traversal (like Depth-First Search), where spatial data and inherited state propagate downward from parent to child.

#### Decomposition 

**1. Root Hydration (The Context)**

* **Action:** Instantiate the root Strut using the exact deployment state provided by the `Board` (e.g., `position: (100, 100)`).
* **Role:** This instantiated state becomes the "Root Context." It serves as the base coordinate for branching Struts and the dictionary payload for all `bind(root.*)` evaluations across the entire Composition.

**2. State Superposition (Parent to Child)**

For every child node (whether it is a component of the root, or a branching Strut), apply the following logic:

* **Layer Parity Check:** Compare the child's resolved `layer` against `parent_context['layer']`.
* **Coordinate Translation:**
    * If layers match: `Child Absolute Position = Parent Absolute Position + Child Pseudo Position`.
    * If layers differ: `Child Absolute Position = (0, 0) + Child Pseudo Position`.
* **Teleport Out Translation:** If the asset defines an `out` coordinate:
    * If `outlayer == root_context['layer']`: `Child Absolute Out = Root Absolute Position + Child Pseudo Out`.
    * Otherwise: `Child Absolute Out = Child Pseudo Out`.
* **Attribute Inheritance:** If a child's PseudoState omits `owner` or `layer`, it inherits the value from its immediate parent context.
* **Context Propagation:** Calculate the physical bottom edge (`node_height = pos.y + dim.l`) and record `position`, `layer`, `owner`, `name`, and `height` as the active parent context for subsequent child traversals.

**3. Late-Binding Resolution**

* **Action:** Scan all string values for `bind\(([^)]+)\)`.
* **Evaluation:**
    * Matches for `bind(parent.)` query `parent_context`.
    * Matches for `bind(root.)` or `bind()` query `root_context`.
* **Override:** Substitute the target string with the resolved context value prior to ECS component instantiation.

**4. Unique Nomenclature Generation**

* **Action:** To prevent namespace collisions on the `Board` when multiple identical Compositions are deployed, apply a global monotonic incrementor.
* **Format:**
    * For Root/Branches: `<instance>-<deployment_name>-<increment>` (e.g., `strut-player-home-1`)
    * For Components: `<instance>-<parent_name>-<increment>` (e.g., `door-house-interior-1`)

**5. Flattening**

* **Action:** As each node is fully resolved, instantiated, and named, append it to a flat, 1D list.
* **Result:** The engine receives a standard list of `Asset` objects, completely ignorant of the fact that they were generated from a nested Composition macro.

#### Application Flow

The Decomposer is a standalone service instantiated *before* the Board and Cradle; it is used during the initial Asset hydration phase of the bootstrapping **and** it is employed ingame by [Mechanics](./05-mechanics.md) through the [Board's Cradle interface](./00-overview.md#board) to instantiate Compositions through the [`build` Intention](./04-intentions.md).

Because the Decomposer inherently generates Asset instances, it acts as a higher-level orchestrator of the Factory. To do this, it needs access to the global [Asset properties](./00-overview.md#assets), [Recipes](./appendices/01-schemas.md#configuration-recipes) and Composition configuraiton.

**1. Initialization (The Setup)**

The Decomposer must be instantiated inside the Orchestrator, immediately after the YAML files are loaded and validated, but *before* `migrate()` is called.

* **Dependencies:** The Orchestrator passes the `configurations.compositions` (the macro blueprints), the `properties` (for hitbox/dimension lookups), and the `configurations.recipes` into the Decomposer's constructor.
* **Statefulness:** Because it is instantiated once as a singleton-like service for the session, its internal `increment` counter starts at 0 and safely scales upwards, guaranteeing unique names whether a Composition is spawned at boot or 10 hours into the game.

**2. Bootstrap Hydration (The Orchestrator Flow)**

During `Orchestrator.migrate()`, the application parses the state directory.

* **Interception:** When the Orchestrator loop encounters the `self.state.compositions` list (the Compositions placed manually in the YAML state files), it does not try to process them natively.
* **Execution:** Instead, it passes each deployed state object directly to `Decomposer.unpack(deployed_state)`.
* **Flattening:** The Decomposer returns a flat list of Assets. The Orchestrator appends these to the master Asset list being compiled for the Board. The Board boots up completely unaware that these assets originated from a macro.

**3. Runtime Injection (The Cradle Flow)**

During orchestrationg, when the Cradle is instantiated, the Orchestrator passes the *exact same Decomposer instance* into the Cradle's constructor.

* **The Interface:** The Cradle exposes a new method: `spawn_composition(id, position, layer, owner)`.
* **Execution:** When a Mechanic requests a Composition, it calls this Cradle method. The Cradle creates a temporary pseudo-state from the arguments and passes it to its internal Decomposer.
* **The Return:** The Decomposer applies the same relative positioning, string binding, and name incrementing as it did at boot, returning the flat list of Assets.
* **Board Integration:** The Mechanic receives the list and pushes it directly into the game loop via the Board.

### Cost 

The crafting cost $C$ depends on the Asset's area, $w \times l$, normalized to a standard Tile size and material-structural densities.

1. **Unit Footprint ($A_0$)**: $A_0 = 32 \times 32 = 1,024\text{ px}^2$
2. **Normalized Footprint ($N$)**: $N = \frac{w \cdot l}{A_0} = \frac{w \cdot l}{1024}$
3. **Material Weight**: $\mu_{\text{mat}}$
4. **Structural Volume Factor**: $\delta_{\text{struct}}$ 

$$
--8<-- "static/tex/cost.tex"
$$

#### Cost 

**Formula**

$$
--8<-- "static/tex/composition-cost.tex"
$$

##### Factors

**Material**

--8<-- "static/md/composition-material-factor.md"

**Blueprint**

--8<-- "static/md/composition-blueprint-factor.md"

##### Ledger

--8<-- "static/md/composition-cost-ledger.md"
