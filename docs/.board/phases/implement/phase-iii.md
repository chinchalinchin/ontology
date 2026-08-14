
#### Implement: Phase III - Widgets

Goals: Widget Creation, Menu Configuration and Instantiation, Menu Traversal

**1. Data Models & Application Hooks**

* [ ] **Define Widget Properties**: Implement `WidgetProperties`, `MenuProperties`, and derived classes (e.g., `ButtonProperties`) in `app.models.properties`.
* [ ] **Define Widget State**: Implement `WidgetState` (managing `status: Enum`), `MenuState` (managing `focus`), and `ScreenPosition` in `app.models.state`.
* [ ] **Extend Factory Hydration**: Update `Factory.PROPERTY_MAP`, `Factory.STATE_MAP`, and `_hydrate` to parse the new schemas.
* [ ] **Configure Loaders**: Update `Loader` and `Orchestrator` to ingest `assets/widgets/main.yaml` and `data/menus/main.yaml`.

**2. Frame & Animation Implementation**

* [ ] **Widget Frames**: Implement `WidgetFrame` in `app.assets.frames`. The key schema must map to the Widget's status (e.g., `{id}-{state.status}`).
* [ ] **Widget Animations**: Implement `WidgetAnimation` in `app.assets.animations` to handle status transitions (e.g., `enabled` -> `selected` -> `active`).

**3. Event Bus & Game Loop Interruption**

* [ ] **Implement Event Queue**: Add an `Event` data class and an event queue to `Board` (or create a dedicated `Bus` class).
* [ ] **Trigger Events via Intentions**: Update `SpeechMechanics` and `CommerceMechanics` to push Events (e.g., `DialogueEvent`, `TradeEvent`) to the queue when specific Intentions are resolved.
* [ ] **Handle Interruptions**: Modify `Board` to process the event queue at the end of a tick. If an Event exists, set `self.paused = True`, instantiate the requested Menu, and load it into a temporary active UI state.

**4. Layout Engine & Instantiation**

* [ ] **Menu Constructor**: Create logic to build Menus based on the `layout` enum (`dock`, `stack`).
* [ ] **Coordinate Translation**: Implement a layout algorithm that converts `ScreenPosition` percentages into absolute `Position` coordinates using `screensize`.
* [ ] **State Injection**: Pass required arguments (e.g., `sprite.state.inventory`, `psyche.communication`) into the Menu constructor to hydrate dynamic Widget labels and icons.

**5. Mechanics & Input Handling**

* [ ] **Device Context Switching**: Update `Device` mappings to support a `MENU` context, translating raw SDL inputs into UI commands (Next, Previous, Select, Cancel).
* [ ] **Implement MenuMechanics**: Create `MenuMechanics.update()`. This system must query the `Device` for UI commands and mutate the `MenuState.focus` and `WidgetState.status`.
* [ ] **Execute in Loop**: Update `Board.menu()` to execute `MenuMechanics` while paused. Resolve menu closures by setting `board.paused = False` and purging the active Menu state.

**6. HUD / Screen Rendering**

* [ ] **Absolute Rendering Pass**: Add a `draw_menu()` method to `Screen` (or update `draw()`) that skips the `camera` clamping logic. Widget primitives must be flattened directly using their absolute `Position` and stamped onto the composite buffer without world-space culling.

---

To make this truly data-driven, the architecture needs two core mechanisms: **Layout Resolution** (where things go) and **Data Binding** (what things display).

#### 1. The YAML Schema (`data/menus/main.yaml`)

You want to define a Menu and have the application do the heavy lifting. The YAML should define the Panes, their layouts, and the Widgets they contain. Crucially, it must also define *where* the Widgets get their state (Data Binding).

```yaml
menus:
  dialogue:
    panes:
      - id: portrait_pane
        position: { px: 0.1, py: 0.75 } # 10% from left, 75% from top
        layout: stack
        alignment: center
        widgets:
          - category: widget
            instance: container
            id: portrait_box
            bind: { content: sprite.state.character.portrait }

      - id: text_pane
        position: { px: 0.3, py: 0.75 }
        layout: dock
        alignment: left
        spacing: 5 # Pixels between widgets
        widgets:
          - category: widget
            instance: language
            id: text_box
            bind: { content: sprite.state.psyche.communication }

```

#### 2. The Layout Engine (Pythonic Composition)

Instead of Widgets holding their coordinates, the Menu instantiation process calculates them and injects them into standard `PositionalState` (or `WidgetState`).

When a Menu is triggered, a `LayoutEngine` class executes the following sequence:

1. **Resolve Pane Anchors**: Convert `ScreenPosition` (e.g., `px: 0.3`) to absolute pixels using `screensize.w * px`. This becomes the Pane's anchor `(x, y)`.
2. **Measure Children**: Query the `Registry` (or `properties`) for the dimensions `(w, l)` of each child Widget.
3. **Apply Algorithm**:
* If `dock` (horizontal) and `alignment == left`: Child 1 gets `(Anchor X, Anchor Y)`. Child 2 gets `(Anchor X + Child 1 Width + spacing, Anchor Y)`.
* If `stack` (vertical) and `alignment == center`: Calculate the maximum width of all children. Offset each child's X coordinate by `(Max Width - Child Width) // 2`.


4. **Flatten**: Return a 1D list of standard `Asset` objects. The engine now treats them exactly like Game Board assets, completely ignoring the UI hierarchy.

#### 3. Data Binding (The Context Injector)

To avoid hardcoding Menu constructors (e.g., writing a specific `DialogueMenu` class), you pass an `EventContext` dictionary when triggering a menu.

When the `Factory` reads the `bind:` key in the YAML, it acts as a dictionary path resolver. If the YAML says `bind: { content: sprite.state.psyche.communication }`, the Factory safely extracts that value from the injected `EventContext` and hydrates the Widget's `State.content`.

---

### Task Board Backlog: Phase III - Widgets (Refined)

Here is the step-by-step breakdown to implement this exact system.

#### 1. Configuration & Models

* [ ] **Menu Layout Enums**: Add `Layouts (DOCK, STACK)` and `Alignments (LEFT, RIGHT, CENTER, TOP, BOTTOM)` to `app.config.enums`.
* [ ] **Menu Models**: Define `PaneProperty` and `MenuProperty` in `app.models.properties`. `MenuProperty` should contain a list of `PaneProperty` objects, which in turn contain `ScreenPosition`, layout enums, spacing integers, and a list of `WidgetConfig` references.
* [ ] **Data Binding Schema**: Create a generic `bind` dictionary mapping in the `WidgetConfig` model to allow YAML properties to map to dynamic state variables.

#### 2. The Layout Engine

* [ ] **Create `app.game.layout**`: Implement a purely mathematical `LayoutEngine` module.
* [ ] **Calculate Anchors**: Write a method that takes `ScreenPosition` and `screensize: Dimensions` and returns a primitive `Position(x, y)`.
* [ ] **Stack Algorithm**: Implement the vertical stacking algorithm, incorporating `spacing` and horizontal `alignment` offsets based on child widths.
* [ ] **Dock Algorithm**: Implement the horizontal docking algorithm, incorporating `spacing` and vertical `alignment` offsets based on child lengths.

#### 3. The Menu Factory

* [ ] **Context Resolver**: Write a helper method in `Factory` that parses the dot-notation `bind` string (e.g., `"sprite.state.inventory"`) and recursively fetches the value from the `EventContext` dictionary passed at runtime.
* [ ] **Asset Generation**: Create a `Factory.menu(menu_key, context, screensize)` method. This method reads the YAML schema, resolves the data bindings, passes the raw data to the `LayoutEngine`, and returns a flat `List[Asset]` representing the fully hydrated UI layer.

#### 4. Engine Integration

* [ ] **UI State Layer**: Update `Board` to maintain an `active_menu: List[Asset]` state.
* [ ] **Render Pass Integration**: Update `Screen.draw()` to append the `active_menu` assets to the Cython primitives list *after* the World Space assets, ensuring UI is rendered on top and bypassing the `pov.x / pov.y` camera subtraction.