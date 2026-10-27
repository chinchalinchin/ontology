# Ontology Docs: Compositions

A Composition is collection of multiple Assets organized into a formula to allow their "*virtualization*" and reuse. A Composition Configuration defines a Composition `id` that can be referenced like any other Asset in the [State file](./00-overview.md#state). 

Composition Configuration can be found in `/src/data/config/compositions/**/*.yml`, otherwise known as the *Composition directories*.

## Category: Crafts

Compositions are used to formalize the spatial relationships of Assets for reuse. For this reason, [Crafts](./01-assets.md#category-crafts) are an essential component of Compositions.

**Palette: Material**

Material alters the color and hue of Assets that possess [Materiality](./01-assets.md#concept-materiality).

--8<-- "static/md/material-palette.md"

**Enum: Genera**

The Partitions of Material space are organized into Genera. Each Genus contains an ordered partition of Material values. Assets specify a Genus in their Properties and bind to a Material value in that Genus in their State.

* Cermaics: `clay`
* Organics:  `cotton`, `wood`, `thatches`
* Geologics: `limestone`, `feldspar`, `granite`, `marble`
* Metallics:  `copper`, `iron`, `gold`
* Chromatics: `neutral`, `red`, `blue`, `yellow`, `green`

**Enum: Schema**

Blueprints describe specific structural implementations of a Craft. Blueprints are partioned in Schema. Each Schema contains an ordered partition of Blueprint values. A Blueprint Schema must have implementations for every Material in a Craft atlas. Assets specify a Schema in their Properties and then bind to a Blueprint value in their State.
 
* Buildings:
    * `halls`: Interior support surfaces.
    * `walls`: Exterior support surfaces.
    * `roofs`: Exterior, non-walkable elevated surfaces (building enclosures).
    * `flats`: Exterior, walkable elevated surfaces.
    * `paths`: Exterior ground surfaces.
    * `floors`: Interior ground surfaces.
* Corridors:
    * `solids`, `stripes`, `designs`: Ground overlay surfaces.
* Columns:
    * `crowns`: Upper cap for multiplication.
    * `shafts`: Multiplicand for multiplication.
    * `bases`: Lower cap for multiplication.
* Decor:
    * `decor`: Singleton partition for static decals (paintings, fixtures, etc.)
* Directions:
    * `up`, `left`, `down`, `right`: Directed obstructions and carpentry.
* Enclosures:
    * `north`, `south`: End cap for vertical multiplication, edges for horizontal multiplication.
    * `east`, `west`:  End cap for horizontal multiplication, edge for vertical multiplication.
* Inclines:
    * `up`: starts along south edge, rises to north edge.
    * `left`: starts in southeast corner, rises to northwest corner.
    * `right`: starts in southwest corner, rises to northeast corner
* Orientations: 
    * `horizontal`, `vertical`: Axis-locked linear spans.

**Behavior: Multiplication**

Each Blueprint Schema has a unique Multiplication Strategy associated with it in the [Materials Configuration](./appendices/01-schemas.md#configuration-materials) that determines how its `multiple` will be expanded during [Board](./00-overview.md#component-board) hydration. Multiplication is executed by a dedicated Multiplier implementation dispatched by the [Decomposer](#service-decomposer).

* `simple` (SimpleMultiplier): 2D grid tiling across $(x_0 + i_x \cdot w,\; y_0 + i_y \cdot l)$ for $i_x \in [0, n_x),\; i_y \in [0, n_y)$[cite: 1].
- `oriented` (`OrientedMultiplier`): 1D axis-locked tiling across $(x_0 + i_x \cdot w,\; y_0)$ when `blueprint == 'horizontal'` ($n_x \times 1$) or $(x_0,\; y_0 + i_y \cdot l)$ when `blueprint == 'vertical'` ($1 \times n_y$)[cite: 1].
* `expansion` (ExpansionMultiplier): Vertical column interpolation placing `crowns` at $(x_0 + i_x \cdot w,\; y_0)$, $n_y$ contiguous `shafts` at $(x_0 + i_x \cdot w,\; y_0 + (k + 1) \cdot l)$, and `bases` at $(x_0 + i_x \cdot w,\; y_0 + (n_y + 1) \cdot l)$, locking each segment's perspective `anchor` to the column's `base` ground line ($\text{base.y} + l$)[cite: 1].
* `perimeter` (PerimeterMultiplier): Hollow 2D boundary of $2(n_x + n_y + 4)$ segments spanning $(n_x + 2)w \times (n_y + 2)l$ with superimposed `L`-corners, an open interior, and `north` baseline `anchor` adjustment[cite: 1].

### Craft: Struts 

*Struts* are structural Assets that encapsulate architecture. Struts may be placed on the Board through the State files manually, but they are generally instantiated during the [Engine Loop](./00-overview.md#component-engine) through the `build` [Intention](./04-intentions.md).

**Behavior: Composability**

Struts are the "*bedrock*" upon which Compositions of Assets can be built. A Strut's main purpose is to provide a coordinate system for the relative positioning of Assets in a Composition. 

### Craft: Platforms

!!! @TODO(07-03)
    To be subsumed and rendered obsolete by the introduction of Gravity. Slated for removal. Should be using elevated surfaces instead. "Platforming" should fall naturally out of the physics.

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

From the perspective of the [State files](./00-overview.md#core-state), Compositions are another type of Asset that can be deployed onto the [Board](./00-overview.md#component-board). However, they are a "*virtual*" Asset composed of other Assets, i.e. they do not have Properties of their own nor are they localized to a single image on the fileystem. 

Compositions are collections of multiple Assets. When a Composition is deployed onto the [Board](./00-overview.md#component-board), its individual Assets are added to the appropriate `(Category, Instance)`-nodes in the [Asset Hierarchy](./01-assets.md#asset-hierarchy) by the [Decomposer Service](#service-decomposer).

A Composition is a way to reuse common Asset configurations in the State without having to specify their individual components each time they are deployed. Functionally, Compositions serve no purpose from the [Board](./00-overview.md#component-board)'s perspective. They only serve to simplify the amount of State file boilerplate that is required to fully declare a complex, high-level entity on the [Board](./00-overview.md#component-board).

Compositions are organized around [Struts](#craft-struts). They serve as abstract containers (or wrappers) for Struts. Compositions, in a sense, are the *realization* of a Strut. While Struts can be deployed individually onto the Board, their true purpose is to provide a "root" for other Assets in a Composition.

### Defintion: Roots & Branches

Every Composition has atleast one [Strut](./01-assets.md#struts), known as the Root Strut. If it has more than one Strut, the other Struts are known as Branch Struts. 

A Composition contains other Assets in predefined configurations, known as the Composition Components. Each Strut in a Composition has its own Components.

For example, a `brick-house` Composition might contain a `home` Strut as its Root Strut and a `panel` Door as a Component Asset. The Composition specifies the relative position of the `panel` with respect to the origin of the Root Strut, i.e. all Component Assets in a Composition have their Positions unpacked relative to their parent Strut's Position.

In other words, Root and Branch Struts provide a *frame of reference* for their Components.

### Definition: PseudoState

To achieve this, Compositions have a *Pseudo State* and a *Deployed State*. A Pseudo State is a formula for constructing the State of its Component Assets from the Deployed State of the Composition's [Root Strut](#definition-roots--branches). The Pseudo State of a Composition is configured in the Composition directory, whereas the Deployed State is set in the State directory, alongside the other Asset States.

The State files specify Compositions to deploy. The [Application](./00-overview.md#application) converts these Compositions into Assets in the [Asset Hierarchy](./01-assets.md#asset-hierarchy). When Compositions are unpacked by the [Orchestrator](./00-overview.md#orchestrator) during the [bootstrapping](./11-architecture.md#specification-initialization), each Asset in a Composition is appended to the [Board](./00-overview.md#component-board) state dynamically. In other words, the Assets in Compositions, once unpacked, are treated separately by the [Engine](./00-overview.md#component-engine), as if they had been specified in the State directory individually.

**Model: CompositionPseudoState**

* `root`
    * `strut: PropertyState`
    * `components: StateSchema`
* `branches`
    * `strut: PropertyState`
    * `components: StateSchema`

### Definition: Macros

Compositions abstract the static and contextual relationships of Assets into formulaic Macros. A Macro binds an Asset's attributes to its own properties (`self`), its enclosing Struts (`parent`, `root`), or any named Asset `<name>` within the Composition, and supports algebraic arithmetic (`+`, `-`, `*`, `/`, `//`, `%`, parentheses). Using this procedure, a Composition can be authored as a purely formal container of relational formulas without hardcoded coordinates.

**Concept: Macro Scopes**

* `self`: The current Component or Strut being evaluated.
* `parent`: The immediate enclosing Strut (`root.strut` for Root Components and Branch Struts; `branch.strut` for Branch Components)[cite: 4].
* `root`: The Composition's Root Strut (`root.strut`)[cite: 4].
* `<name>`: Any Strut or Component in the Composition (across `root` or `branches`) that declares `name: <name>`[cite: 4].

Each Scope exposes its PseudoState attributes (`position.x`, `position.y`, `material`, `blueprint`, `layer`, `owner`), its static Properties (`dimensions.w`, `dimensions.l`, `mass`, `priority`), and its multiplied `span` (`span.w`, `span.l`).

**Interface: Composition Macros**

* `anchor(<target>)`: Calculates and returns the integer `anchor` offset required to align `self`'s rendering baseline (`ground_y`) with `<target>`'s rendering baseline[cite: 4]:
  $$\text{anchor}(\text{self}, A) = \big(A.\text{position}.y + A.\text{span}.l\big) - \big(\text{self}.\text{position}.y + \text{self}.\text{span}.l\big)$$
* `bind(<target>.<field>)`: Resolves `<field>` (e.g., `dimensions.l`, `span.l`, `position.y`, `material`, `layer`) on `<target>`. Multiple `bind(...)` and `anchor(...)` calls may be combined in algebraic expressions.

The following snippet illustrates how Macros may be utilized in a Composition to dynamically resolve State,

```yaml
x: (bind(parent.dimensions.w) - bind(self.dimensions.w)) // 2
y: bind(exterior.position.y) + bind(exterior.dimensions.l) - bind(self.dimensions.l)
```

## Example

Consider the following Composition configuration,

```yaml
compositions:
  brick-house:
    root:
      strut:
        id: home
        name: roof
        material: granite
        blueprint: roofs
      components:
        objects:
          doors:
            - id: panel
              name: door
              anchor: anchor(exterior)
              material: neutral
              outlayer: house-layer
              position:
                x: (bind(parent.dimensions.w) - bind(self.dimensions.w)) // 2
                y: bind(exterior.position.y) + bind(exterior.dimensions.l) - bind(self.dimensions.l)
              out:
                x: bind(interior.position.x) + (bind(interior.dimensions.w) - bind(self.dimensions.w)) // 2
                y: bind(interior.position.y) + bind(floor.position.y) + bind(floor.dimensions.l) - bind(self.dimensions.l)
        crafts:
          struts:
            - id: home
              name: exterior
              material: feldspar
              blueprint: walls
              position:
                x: 0
                y: bind(parent.dimensions.l)
    branches:
      - strut:
          id: hallway
          name: interior
          material: blue
          blueprint: solids
          layer: house-layer
          position:
            x: 10
            y: 10
        components:
          crafts:
            struts:
              - id: carpet
                name: floor
                layer: house-layer
                material: blue
                blueprint: designs
                position:
                  x: 0
                  y: bind(parent.dimensions.l)
```

!!! note "PseudoState"
    `components` is an [Asset State Schema](./00-overview.md#state) schema, identical to a State file.

!!! note "Anchor Macro"
    The Door in this Configuration utilizes the `anchor` macro to ensure it renders in front of `exterior`. The `anchor` macro applies the formula `anchor(self, target) = (target.y + target.span.l) - (self.y + self.span.l)` at compile time so the Door's perspective baseline matches the bottom edge of `exterior`.

    See [Rendering](./11-architecture.md#rendering-sort) for more information on rendering order.
    
!!! note "Door Projection"
    [Doors](./01-assets.md#object-doors) automatically project a reciprocal shadow footprint onto their `outlayer` at `out` (`Substrates.OVERLAYS = -1`, `ChannelTypes.TINT`). When `door` (`panel`) is deployed on the Root Layer, the [Decomposer](#service-decomposer) automatically instantiates its reciprocal return shadow Door on `house-layer` without requiring a second Door declaration in `branches`.


This is a formula for a `brick-house` spanning two [Layers](./00-overview.md#concept-layers) (`root.layer` and `house-layer`), linked bidirectionally by `door` and its projected shadow footprint ($\text{house-layer} \leftrightarrow \text{root.layer}$). In this way, the interior of Compositions can be traversed across independent Layers.


!!! note "Pseudo State Overrides"
    Except for Position (see immediately below), the Pseudo State overrides the inherited State of the Root Strut. In this example, the `state.layer` of `floor` is is `house-layer-<increment>`, regardless of the `layer` passed to the Root Strut when deployed.

The Root Strut (`brick-house.root.strut`) does not specify a Position or Layer, whereas the Branch Strut (`brick-house.branches[0].strut`) does; this is the defining feature of Composition Pseudo State. The Composition configuration leaves the Root Strut Position and Layer empty so that they can be injected from the State file during deployment. Component Assets and Branch Struts define Pseudo States relative to their hierarchical contexts.

Consider deploying the above Composition onto a Board with the following YAML in the state directory:

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

When deployed at `(100, 100)` on layer `'0'`:

* Same-layer Root Components (`door`, `exterior`) have the Root Position `(100, 100)` added to their compiled Pseudo Positions.
* Because `interior` transitions to a different layer (`house-layer-1` $\neq$ `'0'`), its coordinate origin resets to `(0, 0)`, placing `interior` at `(10, 10)` on `house-layer-1`.
* `floor` shares `house-layer-1` with its parent `interior`, so its Position is translated relative to `interior` (`(10, 10) + (0, 96) = (10, 106)`).

Other than Position, any state attribute (`layer`, `owner`, `elevation`) *not* specified in a Component Asset's Pseudo State automatically inherits from its parent Strut's hydrated state.

## Process: Decomposition 

Compositions are processed in two stages: **Compile-Time Macro Evaluation** during configuration loading, and **Deployment-Time Hydration & Multiplication**  during Board migration or runtime spawning.

### Macros: CompositionCompiler

* Address: `app.static.macros.compositions`

The CompositionCompiler runs during [bootstrapping](./11-architecture.md#specification-initialization) after all configuration YAML files are merged and the Property Schema is loaded, but *prior* to model validation to ensure all fields resolve to their required types.

#### CompositionCompiler: Evaluation

1. **Composition-Wide Scope Indexing**:
    * **Action**: Traverse `root.strut`, `root.components`, and every `branch.strut` and `branch.components`, wrapping each raw dictionary in a `ScopeNode` bound to its static Properties (`dimensions`) and strategy-aware multiplied `span`.
    * **Role**: Registers every named entity in a composition-wide lookup table so forward references (e.g., `door` referencing `exterior` declared later in the file) and cross-branch references (e.g., `door.out` referencing `interior` and `floor` in `branches`) resolve regardless of YAML ordering.
2. **`bind(...)` Evaluation**:
    * **Action**: Recursively evaluate all string fields containing `bind(...)` across every node, binding `self`, `parent`, and `root` to the active node's lexical hierarchy.
    * **Dependency Resolution**: If an expression references a field on another node that itself contains an unevaluated macro (e.g., `bind(exterior.position.y)`), the compiler resolves and memoizes the target field on demand (with cycle detection).
    * **Algebraic AST Evaluation**: Expressions combining multiple `bind(...)` tokens and arithmetic operators (`+`, `-`, `*`, `/`, `//`, `%`) are substituted and evaluated via Python's `ast` module into concrete integers.
    * **Deferred Runtime Bindings**: If a `bind(...)` expression targets an extrinsic attribute that is `None` prior to deployment (such as `bind(root.layer)` or `bind(root.owner)`), the raw string is preserved for late-binding by the [Decomposer](#service-decomposer).
3. **Baseline `anchor(...)` Evaluation**:
    * **Action**: Once all local `position` coordinates and `span` dimensions are concrete, evaluate `anchor(<target>)` macros into integer offsets.
4. **Schema Validation**:
    * **Action**: Pass the compiled dictionary tree to model validation for application runtime.

### Service: Decomposer

* Address: `app.services.generators.game.decomposer`

The Decomposer translates validated Composition models into flat lists of concrete [Asset](./01-assets.md) instances when deployed onto the [Board](./00-overview.md#component-board).

#### Decomposer: Hydration

1. **Root Context Initialization & Link Pre-Indexing**
    * **Action**: Increment the monotonic deployment counter (`_increment`), initialize `root_context` from the deployed `PropertyState` (`id`, `name`, `layer`, `owner`, `position`, `elevation`), and pre-index all named components into `_link_map`.
    * **Role**: Ensures all [SwitchState](./01-assets.md#category-objects) references (e.g., between `plates` and `gates`) and internal layer names (`<layer>-<increment>`) are consistently namespaced across the entire Composition deployment.
2. **State Superposition**
    * **Layer Namespacing & Parity Check**: Internal layers distinct from `root_context['layer']` are namespaced to `<layer>-<increment>`. Compare the child's resolved `layer` against `parent_context['layer']`.
    * **Coordinate Translation**:
        * If layers match: $\text{Child Absolute Position} = \text{Parent Absolute Position} + \text{Child Pseudo Position}$.
        * If layers differ: $\text{Child Absolute Position} = (0, 0) + \text{Child Pseudo Position}$.
    * **Teleport Out Translation**: If the Asset defines an `out` coordinate:
        * If `outlayer == root_context['layer']`: $\text{Child Absolute Out} = \text{Root Absolute Position} + \text{Child Pseudo Out}$.
        * Otherwise: $\text{Child Absolute Out} = \text{Child Pseudo Out}$.
    * **Attribute Inheritance**: If a child's PseudoState omits `owner`, `layer`, or `elevation`, it inherits the value from `parent_context`.
    * **Deferred Late-Binding Resolution**: Any remaining runtime `bind(root.*)` or `bind(parent.*)` strings are substituted from `root_context` or `parent_context`.
3. **Unique Nomenclature Generation**
    * **Action**: Apply the deployment increment `<inc>` to guarantee globally unique entity names on the `Board`:
    * **Root/Branch Struts**: `<base_inst>-<strut_name>-<inc>` (e.g., `strut-roof-1`, `strut-interior-1`).
    * **Components**: `<base_inst>-<parent_name>-<comp_name>-<inc>` (e.g., `door-strut-roof-1-door-1`).
    * **Multiplied Units**: Appends `-<blueprint>-<unit_idx>` or `-<unit_idx>` via the active `Multiplier`.
    * **Projected Shadow Doors**: Appends `-out` to the primary Door's hydrated name.
4. **Strategy Dispatch, Door Projection & Flattening**
    * **Multiplied Crafts (`struts`, `bridges`, `stairs`)**: Routed through the Multiplier implementations to produce the correct distribution of Assets.
    * **Doors (`doors`)**: Routed through Layer Projection instantiating both the primary `IN` Door on `state.layer` (`Substrates.STANDARD = 0`) and its reciprocal `OUT` shadow Door on `state.outlayer` (`Substrates.OVERLAYS = -1`, with its return `out` coordinate offset clear of the primary Door's solid hitbox).
    * **Standard Assets**: Instantiated directly via [Dependency Injection](./00-overview.md#service-orchestrator).

#### Decomposer: Initialization

The Decomposer is a standalone Service instantiated *before* the [Board and Cradle](./00-overview.md#component-board); it is used during state hydration by the [Migrator](./00-overview.md#component-board) **and** at runtime by [Mechanics](./05-mechanics.md) through the [Board's Cradle interface](./00-overview.md#component-board).

1. **Initialization**: The `Decomposer` is instantiated with Configurations, Properties and the [MaterialIndex](./appendices/01-schemas.md#configuration-materials).
2. **Hydration**: During State loading, Compositions are passed to the Decomposer, while standalone multiplied Crafts (`struts`, `bridges`, `stairs`) are routed through Multipliers and standalone `doors` through Layer Projections.
3. **Runtime**: Orchestration injects the Decomposer instance into Cradle. When a Mechanic calls the Cradle, the Cradle constructs a deployment State and passes it to the Decomposer.

### Service: Materializer

* Address: `app.services.markets.materializer`

The Materializer service computes the crafting Resource Cost for any materialized Asset from its Dimensions, Material, Blueprint, and Multiple using the relational weights compiled in [MaterialIndex](./appendices/01-schemas.md#configuration-materials).

#### Materializer: Cost 

The crafting cost $C$ depends on Material valuation weights ($\mu_{\text{mat}}$), Blueprint structural volume factors ($\delta_{\text{blueprint}}$), and the Asset's total multiplied footprint normalized to a standard Tile size ($A_0 = 32 \times 32 = 1,024\text{ px}^2$):

1. **Unit Count ($U$) by Multiplication Strategy**:
    * `simple`: $U = n_x \cdot n_y$
    * `oriented`: $U = n_x$ (`horizontal`) or $U = n_y$ (`vertical`)
    * `expansion`: $U = n_x \cdot (n_y + 2)$
    * `perimeter`: $U = 2 \cdot (n_x + n_y + 2)$
2. **Normalized Footprint ($N$)**: 
    * $N = \frac{w \cdot l}{1024} \cdot U$
3. **Material & Chromatic Host Valuation**:
    * For non-chromatic genera (`organics`, `geologics`, `metallics`, `ceramics`): $\text{Cost} = \Big[\;\text{Cost}\big(\text{item} = m,\; \text{quantity} = \max(1, \text{round}(N \cdot \mu_m \cdot \delta_b))\big)\;\Big]$
    * For `chromatics` (with host material $h \in \text{organics} \cup \text{ceramics}$): emits the structural host cost using $\mu_h \cdot \delta_b$, plus an additional dye cost $\max(1, \text{round}(N \cdot \mu_{\text{chromatic}}))$ when $m \neq \text{'neutral'}$.

**Formula: Cost**

$$
--8<-- "static/tex/cost.tex"
$$