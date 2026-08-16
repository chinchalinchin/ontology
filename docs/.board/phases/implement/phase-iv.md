#### Implement: Phase IV - Widgets

Goals: Widget Creation, Menu Configuration and Instantiation, Menu Traversal

##### Part 1: Logic

**1. Data Models & Application Hooks**

* [ ] **Define Widget Properties**: Implement `WidgetProperties` in `app.models.properties`.
* [ ] **Define Widget State**: Implement `WidgetState` (managing `status: Enum`), `MenuState` (managing `focus`) in `app.models.state`. `ScreenPosition` should be a core Cython model.
* [ ] **Extend Factory Hydration**: Update `Factory.PROPERTY_MAP`, `Factory.STATE_MAP`, and `_hydrate` to parse the new schemas.
* [ ] **Configure Loaders**: Update `Loader` and `Orchestrator` to ingest `assets/widgets/main.yaml` and `data/menus/main.yaml`.

**2. Frame & Animation Implementation**

* [ ] **Widget Frames**: Implement `TraversalFrame` in `app.assets.frames`. The key schema must map to the Widget's status (e.g., `{id}-{state.status}`).
* [ ] **Widget Animations**: Implement `TraversalAnimation` in `app.assets.animations` to handle status transitions (e.g., `enabled` -> `selected` -> `active`).

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

##### Part 2: Schema

**Task 1. Configuration & Models**

* [ ] **Menu Layout Enums**: Add `Layouts (DOCK, STACK)` and `Alignments (LEFT, RIGHT, CENTER, TOP, BOTTOM)` to `app.config.enums`.
* [ ] **Menu Models**: Define `Menu` schema.
* [ ] **Data Binding Schema**: Create a generic `bind` dictionary mapping in the model to allow YAML properties to map to dynamic state variables.

**2. The Layout Engine**

* [ ] **Create `app.game.menus.layout**`: Implement a purely mathematical `LayoutEngine` module.
* [ ] **Calculate Anchors**: Write a method that takes `ScreenPosition` and `screensize: Dimensions` and returns a primitive `Position(x, y)`.
* [ ] **Stack Algorithm**: Implement the stacking algorithm, incorporating `gap` and `alignment` offsets based on child widths.
* [ ] **Dock Algorithm**: Implement the docking algorithm, incorporating `gap` and `alignment` offsets based on child lengths.
* [ ] **Tab Algorithm**: Implement the tabbing algorithms.

**3. The Menu Factory**

* [ ] **Context Resolver**: Write a helper method in `Factory` that parses the dot-notation `bind` string (e.g., `"sprite.state.inventory"`) and recursively fetches the value from the `EventContext` dictionary passed at runtime.
* [ ] **Asset Generation**: Create a `Factory.menu(menu_key, context, screensize)` method. This method reads the YAML schema, resolves the data bindings, passes the raw data to the `LayoutEngine`, and returns a flat `List[Asset]` representing the fully hydrated UI layer.

**4. Engine Integration**

* [ ] **UI State Layer**: Update `Board` to maintain an `active_menu: List[Asset]` state.
* [ ] **Render Pass Integration**: Update `Screen.draw()` to append the `active_menu` assets to the Cython primitives list *after* the World Space assets, ensuring UI is rendered on top and bypassing the `pov.x / pov.y` camera subtraction.

##### Part 3: Tabs

#### 1. Schema & Models

* [ ] **Tab Enums & Types**: Add `tab` to `Layouts` enum.
* [ ] **MenuState Dictionary**: Add `active_tabs: Dict[str, str]` to `MenuState` to track active tab IDs by Pane ID.

#### 2. Layout Engine Expansion

* [ ] **Tab Header Generation**: Inside `Layout`, implement logic to dynamically instantiate `Button` widgets for Tab headers based on the schema, anchoring them horizontally.
* [ ] **Conditional Flattening**: Implement logic so that when processing a `tab` pane, the engine checks `pane.children`, executes the layout algorithm *only* on the matching sub-pane, and shifts its Y-anchor below the headers.

#### 3. MenuMechanics Controls

* [ ] **Tab Cycling Input**: Map specific device inputs (e.g., Bumpers/Triggers or specific keys) to `UI_NEXT_TAB` and `UI_PREV_TAB` in the Device mappings.
* [ ] **State Mutation**: Update `MenuMechanics` to intercept these inputs, look up the active Pane's tab list, and cycle the `MenuState.active_tabs` string value.