# Ontology Docs: Compositions

A Composition is collection of multiple Assets organized into a formula to allow their "*virtualization*" and reuse. A Composition Configuration defines a Composition `id` that can be referenced like any other Asset in the [State file](./00-overview.md#state). 

Composition Configuration can be found in `/src/data/config/compositions/main.yml`, otherwise known as the *Composition directory*.

## Category: Crafts

Compositions are used to formalize the spatial relationships of Assets for reuse. For this reason, [Crafts](./01-assets.md#category-crafts) are an essential component of Compositions.

**Palette: Material**

Material alters the color and hue of Assets that possess [Materiality](./01-assets.md#concept-materiality).

--8<-- "static/md/material-palette.md"

**Enum: Genera**

The Partitions of Material space are organized into Genera.

* `ceramics`: 
    * `clay`
* `organics`: 
    * `cotton`, `wood`, `thatches`
* `geologics`: 
    * `limestone`, `feldspar`, `granite`, `marble`
* `metallics`: 
    * `copper`, `iron`, `gold`
* `chromatics`: 
    * `neutral`, `red`, `blue`, `yellow`, `green`

**Enum: Schema**

Blueprints describe specific structural implementations of a Craft. Blueprints are partioned in Schema. A Blueprint Schema must have implementations for every Material in a Craft atlas.
 
* `buildings`:
    * `halls`, `walls`: Support surfaces.
    * `roofs`, `flats`: Elevated surfaces.
    * `paths`, `floor`: Ground surfaces.
* `corridors`:
    * `solids`, `stripes, `designs`: Ground surfaces 
* `columns`:
    * `crowns`: Upper cap for multiplcation.
    * `shafts`: Multiplicand for multiplcation.
    * `bases`: Lower cap for multiplcation.
* `directions`:
    * `up`, `left, `down`, `right`: Directed obstructions.
* `enclosures`:
    * `north`, `south`: End cap for vertical multiplcation, edges for horizontal multiplcation.
    * `east`, `west`:  End cap for horizontal multiplcation, edge for vertical multiplcation.
* `inclines`:
    * `up`: starts along south edge, rises to north edge.
    * `left`: starts in southeast corner, rises to northwest corner.
    * `right`: starts in southwest corner, rises to northeast corner

**Behavior: Multiplication**

Each Blueprint Schema has a unique Multiplication Strategy associated with it in the [Materials Configuration](./appendices/01-schemas.md#configuration-materials) that determines how its `multiple` will be expanded during [Board](./00-overview.md#component-board) hydration.

- `simple`: $(x_0 + i \cdot w, y_0 + j \cdot l) \mid i \leq n_x, j \leq n_y$ 
- `expansion`: $\text{crown} = (x_0, y_0)$, $n_y$, $\text{shafts, base} = (x_0, y_0 + (n_y + 1) \cdot l)$; $\text{anchor} = \text{base.y} + \text{base.l}$
- `oriented`: $(x + i \cdot w, y) \mid i \leq n_x \lor (x, y + j \cdot l) \mid j \leq n_y$ .
- `perimeter`: hollow perimeter of $2(n_x + n_y + 4)$ segments with superimposed `L`-corners and `north` baseline anchor adjustment

### Craft: Struts 

*Struts* are structural Assets that encapsulate architecture. Struts may be placed on the Board through the State files manually, but they are generally instantiated during the [Engine](./00-overview.md#component-engine) loop through the `build` [Intention](./04-intentions.md).

**Behavior: Composability**

Struts are the "*bedrock*" upon which Compositions of Assets can be built. A Strut's main purpose is to provide a coordinate system for the relative positioning of Assets in a Composition. 

### Craft: Decor

TODO

### Craft: Platforms

!!! @TODO(07-03)
    To be subsumed and rendered obsolete by the introduction of Gravity. Slated for removal. Should be using elevated surfaces instead.

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

## Definitions

### Definition: Composition

From the perspective of the [State files](./00-overview.md#core-state), Compositions are another type of Asset that can be deployed onto the Board. However, they are a "*virtual*" Asset composed of other Assets, i.e. they do not have Properties of their own nor are they localized to a single image on the fileystem. 

Compositions are collections of multiple Assets. When a Composition is deployed onto the [Board](./00-overview.md#component-board), its individual Assets are added to the appropriate (Category, Instance)-nodes in the [Asset Hierarchy](./01-assets.md#asset-hierarchy) by the [Decomposer Service](#service-decomposer).

A Composition is a way to reuse common Asset configurations in the state without having to specify their individual components each time they are deployed. Functionally, Compositions serve no purpose from the Board's perspective. They only serve to simplify the amount of state boilerplate that is required to fully declare a complex, high-level game entites on the [Board](./00-overview.md#component-board).

Compositions are organized around [Struts](#craft-struts). They serve as abstract containers (or wrappers) for Struts. Compositions, in a sense, are the *realization* of a Strut. While Struts can be deployed individually onto the Board, their true purpose is to provide a "root" for other Assets in a Composition.

### Defintion: Roots & Branches

Every Composition has atleast one [Strut](./01-assets.md#struts), known as the Root Strut. If it has more than one Strut, the other Struts are known as Branch Struts. 

A Composition contains other Assets in predefined configurations, known as the Composition Components. Each Strut in a Composition has Components.

For example, a `brick-house` Composition might contain a `wall` Strut as its root Strut and then a `panel` Door as a component Asset. The Composition specifies the relative position of the `panel` with respect to the origin of the `wall`, i.e. all Component Assets in a Composition have their positions unpacked relative to the Root Strut's deployed Position. 

In other words, Root Struts provided a *frame of reference* for their components.

### Definition: PseudoState

To achieve this, Compositions have a *Pseudo State* and a *Deployed State*. A Pseudo State is a formula for constructing the State of its component Assets from the Deployed State of the Composition's [Root Strut](#root-struts). The Pseudo State of a Composition is configured in the Composition directory, whereas the Deployed State is set in the State directory, alongside the other Asset States.

The State files specify Compositions to deploy. The game converts these Compositions into ingame Assets that belong to the [Asset Hierarchy](./01-assets.md#asset-hierarchy). When Compositions are unpacked by the [Orchestrator](./00-overview.md#orchestrator) during the [bootstrapping](./11-architecture.md#specification-initialization), each Asset in a Composition is appended to the [Board](./00-overview.md#component-board) state dynamically. In other words, the Assets in Compositions, once unpacked, are treated separately by the Engine, as if they had been specified in the state directory individually.

Components of Compositions have a [Pseudo State](#pseudo-state). During the [application bootstrap](./11-architecture.md#specification-initialization), each component's Pseudo State is hydrated into an actual Asset State and injected into the [Board](./00-overview.md#component-board).

**Model: CompositionPseudoState**

* `root`
    * `strut: PropertyState`
    * `components: StateSchema`
* `branches`
    * `strut: PropertyState`
    * `components: StateSchema`

## Example

Consider the following Composition configuration,

```yaml
compositions:
    brick-house:
        root:
            strut: 
                id: home
                name: house-exterior
                material: feldspar
                blueprint: walls
            components:
                objects:
                    doors:
                        -   id: panel
                            name: house-door
                            anchor: anchor(house-exterior)
                            material: neutral
                            outlayer: house-layer
                            position:
                                x: 20
                                y: 20
                            out:
                                x: 10
                                y: 10
        branches:
            -   strut: 
                    id: hallway
                    name: house-interior
                    material: blue
                    blueprint: solid
                    layer: house-layer
                    position:
                        x: 10
                        y: 10
                components:
                    crafts:
                        struts:
                            -   id: carpet
                                name: house-floor
                                layer: house-layer
                                material: blue
                                blueprint: design
                                position:
                                    x: 0
                                    y: bind(parent.dimensions.l)
```

!!! note "PseudoState"
    `components` is an [Asset State Schema](./00-overview.md#state) schema, identical to a state file.

!!! note "Anchor Macro"
    The Doors in this Configuration utilize the `anchor` macro to ensure they are rendered on top of their parent Struts. The `anchor` macro applies the formula, `anchor(self, target) = (target.y - target.l) - (self.y + self.l)` to dynamically calculate the rendering order, i.e. this ensures the Door is rendered on top of the parent Strut. 

    See [Rendering](./11-architecture.md#rendering-sort) for more information on rendering order.
    
This is a formula for a `brick-house` composed of two Struts on different [Layers](./00-overview.md#layers), each of which have their own [Door](./01-assets.md#doors), each Door being linked to one another through a circuit (`'house-layer' <-> root.layer`). In this way, the "inside" of Assets can be traversed. In other words, each Composition may be composed of separate, independent Layers. 

!!! note "Pseudo State Overrides"
    Except for Position (see immediately below), the Pseudo State overrides the inherited State of the Root Strut. In this example, the `state.layer` of `house-floor` is `house-layer`, regardless of the `layer` passed to the Root Strut when deployed. 

The Root Strut (`brick-house.root`) does not have a Position, whereas the `brick-house.branches` Strut does; this is the defining feature of Composition Pseudo State. The Composition configuration leaves the Root Strut Position State and Layer "empty", so that it can be injected by the State file during deployment. Component Assets and Branching Struts define Pseudo States relative to their hierarchical contexts. 

However, there is subtlety in this process. Consider deploying the above Composition onto a Board, e.g. with the following YAML in the state directory,

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

In this example, the Position, `(100, 100)`, is added to each of the Root Component; *However*, the Components of Branch Struts are positioned *relative to the Branch Parent*. Composition Hydration uses the following rules. See [Decomposition](#process-decomposition) for more information.

Other than Position, any state attribute *not* specified in a Component Asset's Pseudo State automatically inherits the Root Strut's Deployed State, if those attributes exist on the Root Strut. 

Unique names are generated for each component Asset of a Composition according to the schema: `<instance.name>-<strut.name>-<component.name>-<increment>`, where `<increment>` is an index to track the number of unique Compositions deployed on the Board to ensure each has a correspondingly unique name.

!!! warning
    Compositions need to be designed from the *outside-in*, i.e. the Root Strut should correspond to the exterior that gets deployed onto the Board.
    
### Bindings

!!! @TODO(07-04)
    Out of date as Phase 07.04. General idea of binding to root and parents is still correct, but Doors now emit shadows on their linked layers, so this example is not correct anymore.

The Pseudo State of Component Assets can be bound to the Root Strut's Deployed State , to allow for the parameterization of relationships. In this example, the Deployed State `layer` is passed down as a reference to the component `door-frame` Asset, which then uses it to specify its (Pseudo State) attribute for `outlayer` through the use of `bind(root.layer)`; This is how the interior Door leads back to the deployed layer, allowing the Player to return from whence they came. In other words, a binding is a formal constraints between Asset states that makes component Asset states dependent on the root Strut state. This constraint is realized during the Composition unpacking and Pseudo State hydration.

All component Assets can `bind()` to a root Strut state attribute injected into the Composition from the state directory files. When component Asset reference `bind(root.layer)` this is a reference to the root Strut's layer. Only state attributes defined on the root Strut can be bound.

* **Contextual Bindings:** Component Pseudo States can bind attributes to either their immediate parent or the root strut context via regex evaluation:
    * `bind(root.)` or `bind()`: Queries the root deployment context (e.g., `outlayer: bind(root.layer)`).

## Services

### Service: Decomposer

The Decomposer is the service module of the application responsible for translating Composition Configuration into Assets. Taking the example from the previous section, the algorithm for the expansion (decomposition) logic can be modeled as a tree traversal (like Depth-First Search), where spatial data and inherited state propagate downward from parent to child.

#### Process: Decomposition 

Compositions are not processed by the same hydration algorithm as the other Assets in the state file. A special [Decomposer Service](#service-decomposer) is used to process the Composition's Deployed State into its Component Asset States. 

1. **Root Hydration (The Context)**
    * **Action:** Instantiate the root Strut using the exact deployment state provided by the `Board` (e.g., `position: (100, 100)`).
    * **Role:** This instantiated state becomes the "Root Context." It serves as the base coordinate for branching Struts and the dictionary payload for all `bind(root.*)` evaluations across the entire Composition.
2. **State Superposition (Parent to Child)**
    * **Layer Parity Check:** Compare the child's resolved `layer` against `parent_context['layer']`.
    * **Coordinate Translation:**
        * If layers match: `Child Absolute Position = Parent Absolute Position + Child Pseudo Position`.
        * If layers differ: `Child Absolute Position = (0, 0) + Child Pseudo Position`.
    * **Teleport Out Translation:** If the asset defines an `out` coordinate:
        * If `outlayer == root_context['layer']`: `Child Absolute Out = Root Absolute Position + Child Pseudo Out`.
        * Otherwise: `Child Absolute Out = Child Pseudo Out`.
    * **Attribute Inheritance:** If a child's PseudoState omits `owner` or `layer`, it inherits the value from its immediate parent context.
    * **Context Propagation:** Calculate the physical bottom edge (`node_height = pos.y + dim.l`) and record `position`, `layer`, `owner`, `name`, and `height` as the active parent context for subsequent child traversals.
3. **Late-Binding Resolution**
    * **Action:** Scan all string values for `bind\(([^)]+)\)`.
    * **Evaluation:**
        * Matches for `bind(parent.)` query `parent_context`.
        * Matches for `bind(root.)` or `bind()` query `root_context`.
    * **Override:** Substitute the target string with the resolved context value prior to ECS component instantiation.
4. **Unique Nomenclature Generation**
    * **Action:** To prevent namespace collisions on the `Board` when multiple identical Compositions are deployed, apply a global monotonic incrementor.
    * **Format:**
        * For Root/Branches: `<instance>-<deployment_name>-<increment>` (e.g., `strut-player-home-1`)
        * For Components: `<instance>-<parent_name>-<increment>` (e.g., `door-house-interior-1`)
5. **Flattening**
    * **Action:** As each node is fully resolved, instantiated, and named, append it to a flat, 1D list.
    * **Result:** The engine receives a standard list of `Asset` objects, completely ignorant of the fact that they were generated from a nested Composition macro.

#### Process: Initialization

The Decomposer is a standalone Service instantiated *before* the [Board and Cradle](./00-overview.md#component-board); it is used during the initial Asset hydration phase of the bootstrapping **and** it is employed by [Mechanics](./05-mechanics.md) through the [Board's Cradle interface](./00-overview.md#component-board) to instantiate Compositions.

Because the Decomposer inherently generates Asset Instances, it acts as a higher-level orchestrator of the Factory. To accomplish this, it needs access to the global [Asset Properties](./01-assets.md#concept-mutability), [Recipes](./appendices/01-schemas.md#configuration-recipes) and Composition Configuration.

1. **Initialization**: The Decomposer is instantiated inside the [Orchestrator](./00-overview.md#service-orchestrator), immediately after the Configuration files are loaded and validated.
2. **Hydration**: During State migration, the Application parses the State directory.
    * When the Orchestrator loop encounters the Composition list, it passes the Deployed State directly to the Decomposer.
    * The Decomposer returns a list of Assets. The Orchestrator appends these to the Board.
3. **Runtime**: The Orchestrator passes the Decomposer into the Cradle's constructor before injecting the Cradle into the Board.
    *  When a Mechanic requests a Composition, it calls this Cradle method. The Cradle creates a temporary PseudoState and passes it to its internal Decomposer.
    * The Mechanic receives the list o Asset and pushes it onto the Board.

### Service: Materializer

TODO

### Calculation: Cost 

The crafting cost $C$ depends on Material attributes and the Asset's area, $w \times l$, normalized to a standard Tile size,

1. **Unit Footprint ($A_0$)**: $A_0 = 32 \times 32 = 1,024\text{ px}^2$
2. **Normalized Footprint ($N$)**: $N = \frac{w \cdot l}{A_0} = \frac{w \cdot l}{1024}$
3. **Material Factor**: $\mu_{\text{mat}}$
4. **Structural Factor**: $\delta_{\text{struct}}$ 

$$
--8<-- "static/tex/cost.tex"
$$