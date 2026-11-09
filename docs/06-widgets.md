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

#### Concept: Traversibility

Widgets are *traversible* when they are organized in sequence. In other words, a Menu can be traversed. To accomplish this, a Menu has *`focus`*.

`focus` is a field that points to the currently `active` traversible Widget. When the user issues a command to traverse the Menu, the focus shifts to the next traversible Widget.

For example, suppose a Menu Pane has two traversible Widgets. In this example, Widget A is initially in `active` Status (i.e. it has `focus`), while Widget B is initially in the `idle` Status. When the user issues the command to traverse, these states will shift so A is `idle` and B is `active`. 

**Enum: Traversal**

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

When the Board is paused by a MenuEvent, a dedicated [Mechanic](./05-mechanics.md) takes over. During this phase, [MenuMechanic](./05-mechanics.md) switches [Device Context](./02-sprites.md#device-contexts) contexts and translates the [Device mappings](./02-sprites.md#device) to Widget State changes. 

These State changes then map back onto Asset State changes through Event notifications sent to the Engine Bus. For example, a Player may traverse the Button Widgets in an Inventory Menu and select a new piece of Equipment (see [Inventory Menu](#menus) below for more detail); This generates an StateEvent from the Inventory Menu. This Event is processed by the Bus and the Player state is in turn updated.  

When the Menu enters certain end states, such as the user selecting an Exit Button, the corresponding Widget will emit a TerminalEvent that bubbles up through the Menu and generates a notification to the Bus the MenuEvent has ended. The Board is unpaused, and the game resumes.

## Category: Widgets

**Properties: WidgetProperties(AssetProperties)**

* `dimensions: Dimension`: Dimensions of a single frame.
* `frames: Optional[List[str]]`: List of frame keys. Used for indexing Widget Frames in a horizontal atlas with arbitary keys.

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

**Enum: Alignments**

* `start`: Widgets are aligned at the *start* of the Pane's Layout axis.
* `center`: Widgets are aligned at the *center* of the Pane's Layout axis.
* `end`: Widgets are aligned at the *end* of the Pane's Layout axis.

**Enum: Layouts**

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

Buttons are Widgets that are *traversed*. They have a *Status* that changes as they are traversed. When a Button enters into the `selected` Status, they emit Selection events. 

**Enum: Traversal**

* `idle`, `active`, `selected`, `disabled`

**Atlas: (row: Traversal)**

* columns: `^(?:idle|active|selected|disabled)$`

**State: TraversalState**

* `position: Position`
* `status: Status`

**Frame: TraversalFrame**

* `key(id, state): returns [ ("{id}-{state.status}", 0, 0) ]`
* `index(self, id, properties, recipe): returns TODO` 

### Widget: Meters

Meters are *continuous* indicators. 

**Behavior: Gauge**

Meter require a `unit` to calibrate their reading and then express a `reading` in terms of the `unit`; All readings are expressed relative to the `unit`, e.g. the ratio of the current value of the Player's health to maximum value of the Player's health is expressed as the proportion of a Meter that is filled.

**Atlas: (row: Gauge)**

A Meter Asset has two frames. The first frame is an Empty. The second frame is Filled at 100% (i.e., $\frac{reading}{unit}=1$). Each frame is `dimensions.w` wide and `dimensions.l` long. These two frames are indexed as `<id>-empty` and `<id>-filled`, where `<id>` is the Asset file name.

However, when the game retreives the `-filled` frame, the *amount* of the frame that is returned in the index crop-map is determined by the Meter width. For example, if `state.reading/state.unit = 0.75`, the index crop-map will return the tuple `(0, 0, 0.75w, l)`. The `-filled` frame is then superimposed over top of the `-empty` frame, thus creating the appearance of a "gauge" or "meter".

When the Asset key for a Meter is retrieved by the [Screen](./00-overview.md#screen), the current ratio of `reading` and `unit` is rounded to the nearest resolution.

**State: MeterState**

* `position: Position`
* `reading: int`
* `unit: int`

**Frame: MeterFrame**

* `key(id, state): returns [ "{id}-{state.animation.frame}" ]`
* `index(self, id, properties, recipe): returns { "{id}-{resolution}" : (0, 0, properties.dimensions.w * meter, properties.dimensions.l) }` 

### Widget: Icons

**Taxonomy**

* `category: widgets`
* `instance: icons`

Icons serves the purpose of labelling within the Widget family. Each Icon sheet can be thought of as a dictionary of frames, indexed by their frame keys. The frame keys for each image in a Icon sheet are defined by the `properties.frames` field; The order of frames in this attribute *must* match the order of horizontal frames in the actual Asset file. 

Due to the nature of Icons as representations of other ingame Assets, Icons have unique constraints. The following Icon sheets *must* exist for the game to function properly,

- `digits`: A sheet of numeric digits 0 - 9, keyed as `zero` - `nine`.
- `weapons`: A sheet of Weapon icons. Keys *must* match Weapon keys specified in the property index `src/assets/sheets/*.yaml#weapons`.
- `armor`: A sheet of Armor icons. Keys *must* match Armor keys specified in the property index `src/assets/sheets/*.yaml#armor`.
- `shields`: A sheet of Shield icons. Keys *must* match Shield keys specified in the property index `src/assets/sheets/*.yaml#shields`
- `utilities`: A sheet of Utility icons. Keys *must*  match Utility keys specified in the property index `/src/assets/sheets/*.yaml#utilities`
- `tools`: A sheet of Tool icons. Kes *must* match Tool keys specified in the property index `src/assets/sheets/*.yaml#tools`
- `portraits`: TODO
- `loot`: TODO

**State: IconState**

- `icon: str`: Frame key (from `properties.frames`) determining which frame from Icon sheet is displayed. 

**Animation: None**

N/A

**Frame: IndexFrame**

- `keys(id: str, state: AssetState): return [(state.icon, 0, 0)]`
- `index(id, properties: AssetProperties): return [{ }]`

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

**Nodes**

Menus are structured as trees of declarative `MenuNode` specifications. Every node conforms to a unified schema:

* `id: str`: Physical asset identifier (e.g., texture reference or proto-widget key).
* `name: str`: Unique runtime entity name within the menu instance.
* `instance: str`: Asset instance type (`panes`, `buttons`, `icons`, `pages`, `meters`, or `gizmos`).
* `bind: Optional[MenuBinding]`: Declarative state binding target and schema.
* `parameters: Optional[Union[PaneParameters, GizmoParameters, ButtonParameters]]`: Structural configuration payload.

**Example**

The following example demonstrates how to schematize a simple text display Menu which allows the focus to scroll up and down the content by selecting one of the scroll Buttons:

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

This example will be referenced throughout the section.

**Lifecycle**

To summarize the lifecycle:

* Orchestrator loads `data/config/menus/main.yaml` into the MenuConfiguration.
* An event triggers the Provider to instantiate a Menu.
* The Layout engine recursively walks the MenuConfiguration tree, calculating absolute $(X,Y)$ coordinates.
* The Layout engine flattens the tree into a 1D sequence, builds the graph, and returns the populated Menu object.
* The Screen loops over `menu.widgets` and pushes primitive tuples across the Cython boundary.

- Rendering is $O(N)$: `Screen.interface()` simply iterates over `menu.widgets`. Because Python 3.7+ dictionaries maintain insertion order, the Provider can guarantee the Painter's Algorithm is respected by inserting Panes into the dictionary first, followed by their children.
- Controller Logic is $O(1)$: When a SelectionEvent fires, the MenuController must update states. If widgets are stored in a List, the Controller must loop through the list to find `health-meter` every time a player takes damage. With a Dictionary, the Controller executes `menu.widgets["health-meter"].state.reading = new_health` instantly.
- Traversal is Decoupled: MenuMechanics queries `menu.graph` to determine focus shifts. It does not need to know that Button A and Button B share the same parent Pane; it only needs to know they are spatially adjacent.

### Gizmos 

A Gizmo is similar to a [Composition](./03-compositions.md), representing a "virtualized" node of Widgets. A Gizmo is a macro node declared with `instance: gizmos`. Before `Layout.compute()` evaluates spatial geometry, `Provider._expand_tree()` delegates the node to `Fabricator.expand()`, transforming it into concrete nested `panes`, `buttons`, and `icons` with synthesized state attached to the root pane of the Gizmo.

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

The type of state a Gizmo binds to a Pane is dependent on the schema passed into the Gizmo's `bind`.

- Collection: A Collection gizmo is a synthetic grid of Buttons that enumerates and displays a list of Icon strings bound to its `target.source`.

### Services

#### Service: Provider

The Provider, similiar to the [Decomposer](./03-compositions.md#decomposer), is responsible for unpacking Menu configurations into flat lists of Assets for the Engine. However, unlike the Decomposer, the Provider must also generate a traversal graph, inject bindings into Widgets and pass the result to a Menu.

To start, ScreenPosition is a *configuration-time* concept, not a *runtime* concept. When the Provider and Layout engine instantiate a Menu, they must calculate the absolute pixel values `(px * screensize.w, py * screensize.l)` and inject a Position into the Widget state. By flattening the Menu tree and translating all percentages to absolute `Positions`, `Screen.draw()` can consume Widgets exactly like world Assets, satisfying the [zero-allocation principle](./12-architecture.md#cython).

### Controllers

Every Menu has a Controller that handles Menu-specific logic. 

**Selection Logic**

Widgets that are embedded into Menus have their states altered through action-reaction [Selection Bindings](#bindings) which specify how a SelectionEvent propagates through the Menu. This logic is handled by the Controller.

### Context

Every Menu has a Context that holds Menu-specific state data. 

When a Menu is instantiated, it receives a MenuContext object (e.g., `ViewContext`, `LoadContext`, `DialogueContext`). This payload contains direct references to underlying game state data models. For example, the `ViewContext` holds a direct reference to the Player's `SpriteState`. 

Widgets populate their state by evaluating their `target` binding paths against this MenuContext. Because the Context holds the state directly, a meter bound to `context.sprite.meters.health` will traverse the `ViewContext` to retrieve the live `MeterState` without needing to parse the raw `Asset`.

### Bindings

Widgets display live game state information, such as Player Health, slotted Equipment, etc. Moreover, they do so in a declarative (not imperative) style, to prevent complicated UI logic from overcrowding the codebase. In other words, [Menu Controllers](#controllers) do not have to worry about managing animation states or updating Widget state references.

However, since Menus are unpacked by the Provider into Widgets—which are otherwise indistinguishable from standard Assets to the rendering engine—an interface is required to abstract the game state references. To facilitate this, every child Widget of a Menu Pane utilizing live data must utilize a *Binding*.

Widget Bindings to game state are generated inside of the Provider via the Binder factory. Each Binding requires a `schema` and a nested `target` dictionary.

- `schema`: Determines which `Binding` subclass is instantiated (e.g., `MeterBinding`, `LibraryBinding`).
- `target`: A dictionary mapping expected binding keys to string paths in the `MenuContext`. The Binder resolves these string paths into live state references during Menu instantiation, creating runtime closures (Callables) that ensure the bound Widget inherently mirrors live state data.

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

Each binding *expects* the nested paths in the `target` dictionary to resolve to valid domain objects based on the schema. For example, if `schema == meter`, the path mapped to `target.meter` must ultimately resolve to a `MeterState` object.

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

### Layouts

Consider a `nest` Pane with two children `dock` Panes, each with three buttons, represented by the matrix, `[[a,b,c], [d, e, f]]`. Consider the problem of the Menu focus residing on the `b` Button element when the user presses `SOUTH`. In this case, the Menu must shift focus to the `e` element. The `graph` attribute of the Menu holds this relational struture. 

As this example illustrates, a Menu must have access to the traversal graph. This is generated by the Layout of a Menu. A Layout does two things. When `Factory.menu()` calls the Layout, this class outputs:

1. **Render List:** A flat list of `Asset` objects with absolute screen coordinates (for `Screen.draw()`).
2. **Traversal Graph:** A directed graph (adjacency list) mapping each interactive `Button.name` to its logical neighbors (`NORTH`, `SOUTH`, `EAST` and `WEST`).

**Render List**

To generate the Render List, when a Menu is triggered, a `Layout` class executes the following sequence:

1. **Resolve Pane Anchors**: Convert `ScreenPosition` (e.g., `px: 0.3`) to absolute pixels using `screensize.w * px`. This becomes the Pane's anchor `(x, y)`.
2. **Measure Children**: Retrieve the `properties` for the dimensions `(w, l)` of each child Widget.
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

**Traversal Graph**

The prior example oversimplifies considerations; Irregular shaped grids, e.g. `[[a,b,c], [d, e]]`, need to be treated with special care.

To construct the TraversalGraph, the Layout must use an Axis-Aligned Bounding Box (AABB) ray-casting approach after all absolute coordinates are calculated. The algorithm for the Layout to link `SOUTH` from Button A:

* Filter all other Buttons whose absolute `y`-coordinate is strictly greater than Button A's `y`-coordinate.
* Filter this subset to only include Buttons whose `x`-coordinate domain ($state.position.x$ to $state.position.x + dimensions.w$) overlaps with Button A's `x`-coordinate domain.
* Find the Button with the minimum `y`-coordinate from this overlapping subset. 
* This is the `SOUTH` neighbor.Repeat for all cardinal directions.

The resultant graph is saved in `Menu.graph`.

When the [MenuMechanics](./05-mechanics.md#core) `update()` method fires, it does not care about spatial layout. It simply looks at `focus` (e.g., `'a'`), checks the Device poll for a `EAST` command, looks up `graph['a'][EAST]`, and updates the focus to `'b'`. This entirely decouples Menu visual layout from Menu logical input.

### Overlays

The [Board](./00-overview.md#component-board) maintains an `overlay` and `menus` field to separate the responsiblities of different Menus. 

The HUD is always painted on top of all dynamic Assets; as such, it is stored in `overlays` and treated separately by the rendering loop. The `menus` field on the Board holds a mutable stack of Menus that are instantiated on the fly during the game loop. When a MenuEvent is emitted by game loop, it will cause the game to pause as a precondition for these Menus to be displayed. These differences are summarized below,

* `board.menus: List[Menu]`: A LIFO stack for *Modal* interfaces (Inventory, Dialogue, Trade). When `len(board.menus) > 0`, world mechanics are paused, and `MenuMechanics` intercepts device polling for traversal.
* `board.overlays: List[Menu]`: A flat list for *Non-blocking* interfaces (HUD, Floating Damage Numbers, Action Prompts). These do not pause the board and do not receive input focus. They passively observe `UpdateEvent` emissions from the Event Bus.

### Configurations

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

## Design

### Strategies

**Icon Buttons**

An [Icon](#icons) is not embedded into a Button, in the traditional sense of the Button "containing" the Icon. Instead, Icons and Buttons are overlaid in sequence on top of a transparent root [Pane](#panes) to achieve the effect of an "Icon Button". The following [Menu Configuration](#menus) demonstrates how to formalizes an Icon Button, in this case a Button Slot that displays the equipped Weapon,

```yaml
-   id: transparent-block
    name: hud-slots-pane
    layout: dock
    alignment: start
    gap: 5
    children:
        # --- bounding box for the slot ---
        -   id: transparent-slot 
            name: weapon-slot-container
            layout: overlay
            alignment: center
            gap: 0
            children:
                # 1. The Background
                -   instance: buttons
                    id: slot
                    name: weapon-slot
                    status: disabled
                # 2. The Foreground Decal
                -   instance: icons
                    id: weapons
                    name: weapon-icon
                    bind:
                        schema: icon
                        target: 
                        icon: context.sprite.inventory.equipment.weapon
```
