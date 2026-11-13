# Ontology Docs: Widgets

Widgets are a type of specialized [Asset](./01-assets.md) leveraged for user interfaces. Similar to the core [Asset Categories](./01-assets.md#asset-hierarchy), they possess Properties, State and have extensible components injected into their Frame and Animation interfaces. However, they play a unique role in the [Engine Loop](./00-overview.md#component-engine) and have dedicated systems for their processing and deployment.

Widgets are not declared in a [State file](./00-overview.md#core-state) and are thus not migrated onto the [Board](./00-overview.md#component-board) during [hydration](./12-architecture.md#phase-2-hydration). Widgets have their [Bindings](#bindings) and [Layout](#layouts) configured into [Menus](#menus), that are subsequently injected into the [Application](./00-overview.md#application) when [Events](#events) are thrown.

## Widgets: Overview

### Overview: Concepts

#### Concept: Recursivity

Panes provide a canvas on which to lay out other Widgets. All Menus must possess atleast one *Root Pane*. 

All Panes have children. The child of a Pane may also be a Pane. There are no upper bounds (except computationally) to the number of Panes that may be nested within a Menu; Because [Layouts](#layouts) are defined recursively, an arbitary number of Panes can be nested within one another without issue.

#### Concept: Bindability

Widgets bind to [Asset State](./00-overview.md#core-state) on the [Board](./00-overview.md#component-board) when they are instantiated. A Binding represents a mapping to an address on live [Application](./00-overview.md#application) data structure. Bindings 

For example, a [Meter Widget](#instance-meter) may bind to [Player Health](./02-sprites.md#instance-player). Once bound, any update to the Player Health will automatically be reflected in the Meter's Frame keys.

Widgets that are embedded into Menus have their states altered through action-reaction [Selection Bindings](#bindings) which specify how a SelectionEvent propagates through the Menu. This logic is handled by the Controller.

#### Concept: Traversibility

Widgets are *traversible* when they are organized in sequence. In other words, a Menu can be traversed. To accomplish this, a Menu has *`focus`*.

`focus` is a field that points to the currently `active` traversible Widget. When the user issues a command to traverse the Menu, the focus shifts to the next traversible Widget.

For example, suppose a Menu Pane has two traversible Widgets. In this example, Widget A is initially in `active` Status (i.e. it has `focus`), while Widget B is initially in the `idle` Status. When the user issues the command to traverse, these states will shift so A is `idle` and B is `active`. 

**Semantics: Traversal**

* `north`, `south`, `east`, `west`

#### Concept: Asychronicity

Menus (and their component Widgets) are driven through asychronous *Events*.

As an illustration, the [Engine Loop](./00-overview.md#component-engine) may emit an Event containing a [Menu](#menus) key along with Event Data, e.g. Asset State. When an Event is detected by the [Engine](./00-overview.md#component-engine), it causes the [Application](./00-overview.md#application) to pause the [World Loop](./05-mechanics.md#mechanics-world) and switch contexts into the [Menu Loop](./05-mechanics.md#core-mechanic-menumechanics). 

Menus (and their component Widgets) communicate state shifts through the Engine's event bus:

* **MenuEvent**: Signals the Engine to pause the [World Loop](./05-mechanics.md#mechanics-world) and push a Menu onto the [Board](./00-overview.md#component-board) via the [Provider](#service-provider).
* **StateEvent**: Signals the Engine to load and migrate [State](./00-overview.md#core-state) from the filesytem into the [Board](./00-overview.md#component-board)
* **UpdateEvent**: Signals the [Screen](./00-overview.md#component-screen) to recalculate and re-render the Assets on Screen.
* **TerminalEvent**: Signals the Engine to close the active Menu and switch context back into the [World Loop](./05-mechanics.md#mechanics-world)

!!! note "Selections"
    Widget selection does not emit a Event. When [MenuMechanics](./05-mechanics.md#core-mechanic-menumechanics) detects a Selection payload, it invokes the [Controller's](#controllers) `select()` method synchronously. The controller executes domain logic and optionally registers Event Data payloads on the [Engine Bus](./00-overview.md#component-engine).

#### Concept: Contextuality

When the Board is paused by a MenuEvent, [MenuMechanics](./05-mechanics.md#core-mechanic-menumechanics) switches the [Device Context](./02-sprites.md#device-contexts) to `menu` and translates hardware inputs into traversal and selection actions.


[Controllers](#menus-controllers) mutate bound Asset State directly through the Menu's [Context](#menus-context) or emit asynchronous Events onto the [Engine Bus](./00-overview.md#component-engine). 

For example, selecting an item inside the [Equipment or Pouch Menu](#menu-data) mutates the Context, which is immediately reflected on the next Frame via [Binding closures](#menus-bindings). Conversely, selecting a [Board transition](./12-architecture.md#phase-2-hydration) in the [Main or Pause Menu](#menu-data) emits a StateEvent onto the [Engine Bus](./00-overview.md#component-engine).

When the Menu enters certain end states, such as the user selecting an Exit Button, the corresponding Widget will emit a TerminalEvent that bubbles up through the Menu and generates a notification to the Bus the MenuEvent has ended. The [Board](./00-overview.md#component-board) is then unpaused, and the [World Loop](./05-mechanics.md#mechanics-world) resumes.

## Category: Widgets

**Properties: WidgetProperties(AssetProperties)**

* `dimensions: Dimensions`:
* `frames: Optional[List[str]]`: List of frame keys. Used for indexing Widget Frames in a horizontal atlas with arbitary keys.

**Animation: None**

Widgets do not implement Animations. All Widget State changes are instantaneously reflected in the keys returned by the Frame interface.

### Widget: Panes

Panes are Widgets that provide a frame of reference for other Widgets in a Menu. All child Widgets of Pane have their Positions calculated relative to the Position of their parent Pane.

**Atlas: (row: Alignments, column: Alignments)**

Each Pane is registered in the [Asset Property index](./00-overview.md#core-assets) as a single unified Frame with dimensions $(W,L)$; However, when the Pane is indexed by the [Registry](./00-overview.md#library-registry), the Frame is split according to the following schema:

First, define the Dimensions of a Pane Frame cell as,

$$
w_c = \left\lfloor \frac{W}{3} \right\rfloor
$$

$$
l_c = \left\lfloor \frac{L}{3} \right\rfloor
$$

$$
v(i) = \begin{cases} \text{start} & i = 0 \\ \text{end} & i = n + 1 \\ \text{center} & 1 \le i \le n \end{cases}
$$

Then, the Pane can be split into a 9-Frame Atlas using the following mapping,

$$
\text{str(id-v[y]-v[x])} \to (x \cdot w_c, y \cdot l_c)
$$

Where $(x,y)$ range over,

$$
x \in \max\!\left(0,\; \left\lceil \frac{W - 2w_c}{w_c} \right\rceil\right), y \in \max\!\left(0,\; \left\lceil \frac{L - 2l_c}{l_c} \right\rceil\right)
$$

**Field: Scale**

Panes are scaled to a percentage of the underlying [Screen's](./00-overview.md#component-screen) Dimensions. 

* `pw`: Percentage of the [Screen](./00-overview.md#component-screen) width.
* `pl`: Percentage of the [Screen](./00-overview.md#component-screen) length.

Only Panes have a Scale explicitly set in the [Menu Configuration](#menus). All other Widgets have their [Screen](./00-overview.md#component-screen) Positions calculated relative to the Pane in which they are embedded. These Positions are calculated and injected into the Widget during instantation in the [Provider service](#provider).

**Model: AxisAlignment**

* `horizontal: Alignments`
* `vertical: Alignments`

**Field: Justification**

Panes use *Justification* to determine their own rendering location. 

**Field: Alignment**

Panes use *Alignment* to determine the rendering locations of their child Widgets with the Pane's *Layout*.

**Field: Layout**
 
Panes use a *Layout* to determine the general shape that child Widgets assumed when deployed. A Layout specifies a type of *axis* to use when arranging child Widgets.

**Semantics: Alignments**

* `start`: Widgets are aligned at the *start* of the Pane's Layout axis.
* `center`: Widgets are aligned at the *center* of the Pane's Layout axis.
* `end`: Widgets are aligned at the *end* of the Pane's Layout axis.

**Semantics: Layouts**

* `overlay`: A sagittal (out-of-the-screen) axis of Widgets.
* `stack`: A vertical axis of Widgets.
* `dock`: A horizontal axis of Widgets.

**Field: Canvas**

Panes contain a `canvas` to hold a reference to an [Texture](./12-architecture.md#library-graphics). The `canvas` is created at runtime as a blank buffer for rendering [Fonts](./12-architecture.md#rendering-typography) without altering the underlying Asset loaded into the [Registry](./00-overview.md#library-registry).

**State: PaneState**

* `layout: Layout`
* `alignment: AxisAlignment`
* `justification: AxisAlignment`
* `gap: int`
* `margins: Tuple[int, int, int, int]`:
* `multiple: Multiple`
* `span: Dimensions`
* `content: str`
* `pageindex: int`
* `pagesize: int`
* `font: Fonts`
* `canvas: TexturePtr`

**Frame: PaneFrame**

* `keys(id, state): returns TODO`
* `index(id, properties): returns TODO` 

**Pane: Methods**

* `current(): return content[pageindex]`
* `less(): return pageindex > 0`
* `more(): return pageindex < len(content)`
* `scrolldown(): pageindex++`
* `scrollup(): pageindex--`

### Widget: Buttons

Buttons are *traversible* Widgets. They have a *Status* that changes as they are traversed. 

**Semantics: Statuses**

* `idle`, `active`, `selected`, `disabled`

**Atlas: (row: Status)**

* columns: `^(?:idle|active|selected|disabled)$`

**State: TraversalState**

* `position: Position`
* `status: Status`

**Frame: TraversalFrame**

* `keys(id, state): returns [ ("{id}-{state.status}", 0, 0) ]`
* `index(id, properties): { "{id}-{status}": (i*properties.dimensions.w, 0, properties.dimensions.w, properties.dimensions.l) for i, status in enumerate(Statuses)}` 

### Widget: Meters

Meters are indicators for displaying continuous changes to Asset State. 

**Behavior: Gauge**

Meter require a `unit` to calibrate. Once calibrated, all `readings` are expressed relative to the `unit`. When Meters render their Frame, `reading` is the proportion of its `unit` Frame that is filled. 

For example, in the case of Health Meters, the ratio of the current value of the Player's Health is [bound](#concept-bindability) to `reading` and the maximum value of the Player's Health [bound](#concept-bindability) to `unit`. The ratio of these fields is used to determine the length of the Meter's current gauge.

**Atlas: (row: Gauge)**

A Meter Asset has two Frames. The first frame is an Empty. The second frame is Filled at 100% (i.e., $\frac{reading}{unit}=1$). Each Frame is `dimensions.w` wide and `dimensions.l` long. The first Frame is indexed over its dimensions, while the second Frame is sliced and indexed over the *Gauge Resolution*.

**State: MeterState**

* `position: Position`
* `reading: int`
* `unit: int`

**Frame: MeterFrame**

* `key(id, state): returns [ "{id}-{state.animation.frame}" ]`
* `index(self, id, properties, recipe): returns { "{id}-{resolution}" : (0, 0, properties.dimensions.w * meter, properties.dimensions.l) }` 

### Widget: Icons

Icons serves the purpose of labelling within the Widget family. 

**Atlas: (row: Frames)**

Each Icon Asset is a horizontal row of Frames, indexed sequentially by the order of the Property, `frames`, where each Frame has the same dimensions `(w, l)`. 

**Required: Assets**

Due to the nature of Icons as representations of other Assets, Icons have unique constraints. The following Icon sheets *must* exist for the game to function properly,

* `digits`: A sheet of numeric digits 0 - 9, keyed as `zero` - `nine`.
* `weapons`: A sheet of Weapon icons. Keys *must* match Weapon keys specified in the property index `src/assets/sheets/**/*.yaml#sheet.weapons`.
* `armor`: A sheet of Armor icons. Keys *must* match Armor keys specified in the property index `src/assets/sheets/**/*.yaml#sheets.armor`.
* `shields`: A sheet of Shield icons. Keys *must* match Shield keys specified in the property index `src/assets/sheets/**/*.yaml#sheets.shields`
* `utilities`: A sheet of Utility icons. Keys *must*  match Utility keys specified in the property index `/src/assets/sheets/**/*.yaml#sheets.utilities`
* `tools`: A sheet of Tool icons. Keys *must* match Tool keys specified in the property index `src/assets/sheets/**/*.yaml#sheets.tools`
* `portraits`: TODO
* `resources`: TODO
* `items`: TODO
 
**State: IconState**

* `icon: str`: Key determining which frame from the Icon sheet is displayed. 

**Frame: IconFrame**

* `keys(id, state): return [("{id}-{state.icon}", 0, 0)]`
* `index(id, properties): return [{ "{id}-{frame}": (i*w, 0, w, l) for i, frame in enumerate(properties.frames)} ]`

## Configuration: Menus

* Location: `/src/data/menus/**/*.yaml`

Menus are [Configurations](./00-overview.md#core-configuration) of Widgets.

**Model: Menu**

* `id: str`: Unique Menu Identifier 
* `focus: str`: Widget that is currently being focused on for traversal.
* `graph: Dict[str, Dict[str, str]]`: Traversal adjacent graph.
* `context: MenuContext`: Menu Context data payload.
* `widgets: Dict[str, Widget]`: Dictionary of instantiated Menu Assets.
* `controller: MenuController`: MenuController object.

**Model: MenuNodes**

Menus are structured as trees of declarative MenuNodes.

* `id: str`: Physical Asset identifier.
* `name: str`: Unique runtime entity name within the menu instance.
* `instance: str`: Asset instance type (`panes`, `buttons`, `icons`, `pages`, `meters`, or `gizmos`).
* `bind: Optional[MenuBinding]`: Declarative state binding target and schema.
* `parameters: Optional[Union[PaneParameters, GizmoParameters, ButtonParameters]]`: Structural configuration payload.

### Menus: Example

The following example demonstrates how to schematize a simple text display Menu which allows the Menu `focus` to scroll up and down the content by selecting one of the scroll Buttons:

```yaml
menus:
  text:
    controller: scroll
    roots: 
      - instance: panes
        id: neutral
        name: text-menu
        parameters:
          position:
            px: 0.175
            py: 0.60
          layout: dock
          alignment: center
          gap: 15
          font: dialogue
          children: 
            - instance: pages
              id: dark-notification
              name: text-display
              bind:
                schema: library
                target: 
                  plot: context.plot.current
                  persona: context.object.persona
                  lexicon: context.object.lexicon
            - instance: panes
              id: transparent-slot
              name: text-scroll-buttons
              parameters:
                layout: stack
                alignment: center
                gap: 5
                children:
                  - instance: buttons
                    id: arrow-up
                    name: text-scroll-up
                    bind: 
                      schema: select
                      target:
                        selection: scrollup
                        selector: text-display
                  - instance: buttons
                    id: arrow-down
                    name: text-scroll-down
                    bind: 
                      schema: select
                      target:
                        selection: scrolldown
                        selector: text-display
```

### Menus: Lifecycle

* [Orchestrator](./00-overview.md#service-orchestrator) loads the Menu Configuration and injects it into the [Provider](#service-provider).
* An [Event](#concept-asychronicity) triggers the [Provider](#service-provider) to instantiate a Menu.
* The [Layout Module](#module-layouts) recursively walks the Menu Tree, calculating absolute $(X,Y)$ coordinates for each Menu Node.
* The [Layout Module](#module-layouts) flattens the Menu Tree into a list of Widgets, builds a Traversal graph describing the topology of the Menu's [Widget Traversal](#concept-traversibility), and returns the populated Menu.
* The [Screen](./00-overview.md#component-screen) loops over Menu's flattened list of Widgets and pushes primitive tuples across the [Cython boundary](./12-architecture.md#specification-cython-libraries).

!!! note "Rendering is $O(N)$"
    The [Screen](./00-overview.md#component-screen) iterates over a flat list of Assets. 

!!! note "Controller Logic is $O(1)$"
    When Events fire, the Menu Controller looks up Widgets in a pre-compiled Traversal graph. The Traversal graph allows the Menu to shift `focus` without querying the Menu Tree for a Widget's exact MenuNode in complex recursion of a Menu Tree. 

### Menus: Controllers

Every Menu has a Controller for handling domain specific logic. When [MenuMechanics](./05-mechanics.md#core-mechanic-menumechanics) executes, it delegates all processing of Asset State to the appropriate Controlle.

### Menus: Context

Every Menu has a Context. When a Menu is instantiated, it receives a MenuContext object. This payload contains direct references to underlying Asset State data models. 

Widgets populate their State by evaluating their [Binding](#menus-binding) paths against their MenuContext. Because the Context holds the State directly, a meter bound to `context.sprite.meters.health` will traverse the Context to retrieve the live `MeterState` without needing to parse the raw Asset. This *Binding* of Asset State to Widget State is referred to as a *State Closure*.

### Menus: Bindings

Widgets display live Asset State information, such as Player Health, slotted Equipment, etc. Moreover, they do so in a declarative (not imperative) style, to prevent complicated user interface logic from overcrowding the codebase. In other words, [Menu Controllers](#controllers) do not have to worry about managing animation states or updating Widget State references.

However, since Menus are unpacked by the Provider into Widgets, otherwise indistinguishable from standard Assets to the [Engine](./00-overview.md#component-engine) and [Screen](./00-overview.md#component-screen), every Widget bound to Asset State declares and utilizes a *Binding*.

Widget Bindings to Asset State are generated inside of the [Provider](#service-provider) via the [Binder](#service-binder) factory. Each Binding requires a `schema` and a nested `target` dictionary.

* `schema`: Determines the structure of the Binding. 
* `target`: A contextual path to the target Asset State in the Menu Context. The Binder resolves these contextual paths into live Asset State references during Menu instantiation, creating State Closures that ensure the bound Widget implicitly mirrors live Asset State data.

**Model: Binding**

```yaml
# 1. LibraryBinding
bind:
    schema: library
    target: 
        plot: context.<path>.<to>.<plot>
        persona: context.<path>.<to>.<persona>
        lexicon: context.<path>.<to>.<lexicon>

# 2. TextBinding
bind:
    schema: text
    target:
        content: context.<path>.<to>.<content>

# 3. MeterBinding
bind:
    schema: meter
    target: 
        meter: context.<path>.<to>.<meter>

# 4. IconBinding
bind:
    schema: icon
    target: 
        icon: context.<path>.<to>.<icon>

# 5. SelectBinding
bind:
    schema: select
    target:
        selection: scrolldown | scrollup | new | load | menu
        selector: <widget-name> | <board-id> | <menu-id>

```

Each Binding *expects* the nested paths in the `target` dictionary to resolve to valid domain entities in the Menu Context based on the schema. For example, if `schema == meter`, the path mapped to `target.meter` must ultimately resolve to an entity whose data structure exactly matches the Binding schema, i.e. a MeterState.

For example, in the View (HUD) Menu, a Widget is bound to the Player's health meter:

```yaml
-   instance: meters
    id: health
    name: health-meter
    bind: 
        schema: meter
        target: 
            meter: context.sprite.meters.health
```

By decoupling the layout from the logic, Widgets do not need to know what is controlling them; they only require a declarative Binding to know what data they are displaying.

**Selection Bindings**

Selection Bindings define how Widgets interact with user input and game state. Rather than pointing to external game state, their `target` dictionary maps internal Menu commands:

* `selection`: The specific action or command a Control Widget emits when selected by the user (e.g., `scrollup`).
* `selector`: A direct pointer to the unique `name` of another Widget in the Menu, or a destination key. Used when a Control Widget needs to mutate or read another Widget's state.

In the provided `text` Menu example, the `text-scroll-up` and `text-scroll-down` Buttons are bound to the `selection` actions `scrollup` and `scrolldown`. Because these buttons control the Page widget, their `selector` bindings are set to `text-display`—the unique name of the target Page.

When a Button is selected, the MenuMechanics route the input to the appropriate Controller (in this case, the `ScrollController`). The Controller uses the `selector` binding to perform an $O(1)$ dictionary lookup for the target widget and applies the `selection` action:

```python
class ScrollController(Controller):

    def select(self, name: str, menu: Menu, board: Board, bus: collections.deque):
        widget = menu.widgets[name]
        
        selection = widget.binding.selection
        target_key = widget.binding.selector
        
        if not target_key or target_key not in menu.widgets:
            return
            
        target_widget = menu.widgets[target_key]
        
        # apply selection logic to target_widget...

```

Bindings are enumerated and summarized below:

* `selection`: Menu Action commands.
    * `SCROLLUP`: Call `scrollup()` on a Page DisplayState
    * `SCROLLDOWN`: Call `scrolldown()` on a Page DisplayState
    * `SELECT`: Select the focused Widget.
    * `NEW`: 
    * `LOAD`:
    * `MENU`: 
* `selector`: The name of a target to be used in the SelectionEvent.
    * `selections in [SCROLLUP, SCROLLDOWN, SELECT]`: Selector is the target Widget name.
    * `selections == MENU`: Selector is the target Menu.
    * `selections in [NEW, LOAD]`: TODO


### Menus: Gizmos 

A Gizmo is a macro node declared in the Menu Tree. Before the Layout evaluates spatial geometry, the Provider delegates Gizmo MenuNodes to a specialize *Fabricator Service*, transforming the Gizmo Node into concrete structures of Panes, Buttons, Meters and Icons with a synthesizedState attached to the root pane of the Gizmo.

```yaml
- id: weapons
  name: inventory-pack-grid
  instance: gizmos
  bind:
    schema: collection
    target:
      source: context.inventory.pack
  parameters:
    capacity: 8
    columns: 4
    gap: 5
    pane: transparent-slot
    button: slot
```

**Semantics: Gizmo Bindings**

The Binding of a Gizmo's synthesized root Pane is determined by the Binding's `schema`.

* `collections`: A Collection Gizmo is a synthetic grid of Buttons that enumerates and displays a list of Icon strings bound to its `target.source`.

## Menu: Services

### Service: Provider

The Provider, similiar to the [Decomposer](./03-compositions.md#service-decomposer), is responsible for unpacking Menu Configurations into flat lists of Assets for the [Engine](./00-overview.md#component-engine). However, unlike the Decomposer, the Provider must also generate a Traversal graph, inject bindings into Widgets and pass the result to a Menu.

To start, ScreenPosition is a *configuration-time* concept, not a *runtime* concept. When the Provider and Layout engine instantiate a Menu, they must calculate the absolute pixel values `(px * screensize.w, py * screensize.l)` and inject a Position into the Widget state. By flattening the Menu tree and translating all percentages to absolute `Positions`, `Screen.draw()` can consume Widgets exactly like world Assets, satisfying the [zero-allocation principle](./12-architecture.md#cython).

### Service: Binder

The Binder Service instantiates Bindings and generates the callable functions leveraged by Widgets for their State Closures.

### Service: Fabricator

The Fabricator Service synthesizes Gizmo Widgets and their Pane Bindings.

## Menu: Modules

### Module: Layouts

Consider a `stack` Pane with two children `dock` Panes, each with three Buttons, represented by the matrix, `[[a,b,c], [d, e, f]]`. Consider the problem of the Menu `focus` residing on the `b` Button element when the user presses `south`. In this case, the Menu must shift focus to the `e` element. The `graph` attribute of the Menu holds this relational struture. 

As this example illustrates, a Menu must have access to the Traversal graph. This is generated by the Layout of a Menu. A Layout does two things:

1. **Render List:** Calculates a flat list of [Assets](./01-assets.md) with absolute [Screen](./00-overview.md#component-screen) coordinates.
2. **Traversal Graph:** A directed graph (adjacency list) mapping each interactive Button to its logical neighbors (`north`, `south`, `east` and `west`).

**Interface: Render List**

To generate the Render List, when a Menu is triggered, the Layout Module executes the following sequence:

1. **Resolve Pane Anchors**: Convert its root Pane's Scale and Justification to absolute coordinates. This becomes the Pane's anchor `(x, y)`.
2. **Align Children**: Use the Pane's anchor to align its children.
3. **Apply Algorithm**:
    * If `pane.layout == dock`
        * If `alignment == start`: TODO
        * If `alignment == end`: TODO
        * If `alignment == center`: Calculate the maximum width of all children. Offset each child's X coordinate by (Max Width - Child Width) // 2.
    * If `pane.layout == stack`:
        * If `alignment == start`: TODO
        * If `alignment == end`: TODO
        * If `alignment == center`: Calculate the maximum height of all children. Offset each child's Y coordinate by (Max Height - Child Height) // 2.
    * If `pane.layout == tab`: Alignments do not apply. Pane children are Panes. Each receives the same ScreenPosition. Algorithm recurses to find the coordinates of the grandchildren.    
4. **Flatten**: Return a list of standard Asset objects. The engine now treats them exactly like Game Board assets, completely ignoring the Menu hierarchy.

**Interface: Traversal Graph**

The prior example oversimplifies considerations; Irregular shaped grids, e.g. `[[a,b,c], [d, e]]`, need to be treated with special care.

To construct the TraversalGraph, the Layout must use an Axis-Aligned Bounding Box (AABB) ray-casting approach after all absolute coordinates are calculated. The algorithm for the Layout to link `south` from Button A:

* Filter all other Buttons whose absolute `y`-coordinate is strictly greater than Button A's `y`-coordinate.
* Filter this subset to only include Buttons whose `x`-coordinate domain ($state.position.x$ to $state.position.x + dimensions.w$) overlaps with Button A's `x`-coordinate domain.
* Find the Button with the minimum `y`-coordinate from this overlapping subset. 
* This is the `south` neighbor. Repeat for all cardinal directions.

The resultant graph is saved and returned.

When the [MenuMechanics](./05-mechanics.md#core)fires, it does not care about spatial layout. It simply looks at `focus` (e.g., `'a'`), checks the Device poll for a `east` command, looks up `graph['a']['east']`, and updates the focus to `'b'`, decoupleing Menu Layouts from Menu logical relationships.

## Board: Overlays

The [Board](./00-overview.md#component-board) maintains an `overlay` and `menus` field to separate the responsiblities of different Menus. 

The HUD is always painted on top of all dynamic Assets; as such, it is stored in `overlays` and treated separately by the rendering loop. The `menus` field on the Board holds a mutable stack of Menus that are instantiated on the fly during the game loop. When a MenuEvent is emitted by game loop, it will cause the game to pause as a precondition for these Menus to be displayed. These differences are summarized below,

* `board.menus: List[Menu]`: A LIFO stack for *Modal* interfaces (Inventory, Dialogue, Trade). When `len(board.menus) > 0`, world mechanics are paused, and `MenuMechanics` intercepts device polling for traversal.
* `board.overlays: List[Menu]`: A flat list for *Non-blocking* interfaces (HUD, Floating Damage Numbers, Action Prompts). These do not pause the board and do not receive input focus. They passively observe `UpdateEvent` emissions from the Event Bus.

### Menu: Data

1. Dialogue:
    * **Payload**: `DialogueContext(plot: PlotState, sprite: SpriteState, object: DialogueState)`
    * **Events**: `UpdateEvent` (canvas paging and line progression), `TerminalEvent` (closing dialogue loop)
2. Editor: TODO
    * **Payload**: `EditorContext` (TBD)
    * **Events**: TODO
3. Inventory: Instantiated from the world loop via `MenuEvent('inventory')` in `PlayerMechanics`.
    * **Payload**: `InventoryContext(inventory: Inventory)`
    * **Events**: `UpdateEvent` (slot scrolling and selection previews), `TerminalEvent` (closing menu and unpausing world)
4. Market: TODO
    * **Payload**: `MarketContext(buyer: Inventory, seller: Inventory)` (TBD)
    * **Events**: TODO
5. Main: Instantiated at ignition by injecting a `MenuEvent('main')` directly onto the Engine event bus before world simulation begins.
    * **Payload**: `MainContext(registry: Registry)`
    * **Events**: `StateEvent` (triggers `Migrator` hydration for New/Load), `MenuEvent` (opens `options` or `editor` submenus)
    * **Outputs**: `<board-key>` / save slot target for state migration
6. Options: Generic settings modal invoked from the Main Menu or Pause Menu.
    * **Payload**: `MenuContext` (generic or inherited context)
    * **Events**: `UpdateEvent` (live preview text stamping on display canvas), `TerminalEvent` (returns to previous menu)
7. Pause: Modal menu triggered from the world loop via `MenuEvent('pause')` in `PlayerMechanics`. Pauses the engine tick by setting `board.paused = True`.
    * **Payload**: `PauseContext(board: Board)`
    * **Events**: `TerminalEvent` (unpauses game simulation), `StateEvent` (triggers state rehydration for loads), `MenuEvent` (opens `options` submenu or resets board to return to `main`)
8. View: Also known as the Heads-Up Display (HUD). Created during engine bootstrap and stored in `board.overlays` rather than the modal `board.menus` stack. It renders on top of world assets every frame without pausing simulation or intercepting input traversal.
    * **Payload**: `ViewContext(sprite: SpriteState)`
    * **Events**: None (passively evaluates live state bindings each tick)