#### Implement: Phase 05 - Widgets

- Goals: Widget Creation, Menu Configuration and Instantiation, Menu Traversal

**CURRENT FOCUS**

Consider the `src/data/config/menus/main.yaml` dialogue and inventory menu. Note this schema is not yet finalized. How can the schema be setup so buttons can bind to the state of other components in the menu?

For the dialogue menu, the idea is the page display will have text content that is paged through by the buttons.

For the inventory menu, the idea is a slot will display the currently equipped armor next to a list of slots that contain all of the player's armor inventory. Selecting a slot updates the equipped armor slot.

Consider when events are sent. How does that factor into the binding?

In short, consider how binding can be implemented. How can a system be setup that allows buttons to bind to player state, other widget states, etc?

##### Bugs

**1. The Engine Pause Deadlock (`app.game.engine.py`)**

* **The Bug:** In `Engine.start()`, the fixed-timestep logic `while accumulator >= delta:` is nested *inside* `if not self.board.paused:`.
* **The Consequence:** If `MenuMechanics` (or anything else) sets `board.paused = True`, the game loop will completely stop processing **all** mechanics. `MenuMechanics` will never get its `update()` called to process user input, meaning the menu can never be closed or traversed. The game is deadlocked.
* **The Fix:** Remove `if not self.board.paused:` from wrapping the loop. Instead, pass the `paused` state to the Mechanics, or add a `runs_while_paused: bool` property to the `Mechanic` base class. World mechanics (`Motion`, `Combat`) exit early if paused; UI/Core mechanics (`Menu`, `Animation`) continue executing.

**2. The Render Cache Double-Append (`app.game.board.py`)**

* **The Bug:** In `relayer()`, when an asset is moved to a `new_layer`, it is appended to `self._cached_renderables[new_layer]` unconditionally on line 214. Four lines later, on line 218, it checks `if cat != AssetCategories.TILES:` and appends it to `self._cached_renderables[new_layer]` **again**.
* **The Consequence:** Every time a dynamic asset uses a door or changes layers, it gets duplicated in the render queue. Over time, this will exponentially degrade Cython rendering performance and cause visual artifacts (e.g., stacking alpha-blended shadows).
* **The Fix:** Remove the unconditional `.append(asset)` on line 214.

**3. The UI Camera Culling Annihilation (`app.game.screen.py`)**

* **The Bug:** `Screen.draw()` expects all assets to exist in world-space. It uses `pov.x` and `pov.y` (the camera offset) to cull assets that are off-screen.
* **The Consequence:** Widgets will be hydrated with absolute screen coordinates (e.g., `x: 50, y: 50`). If the player walks to the right and the camera `pov.x` becomes `1000`, the UI assets will fail the condition `dx + dw >= pov.x` and be culled. The HUD will vanish when the player moves.
* **The Fix:** `Screen.draw()` must identify UI assets (e.g., `if asset.category == AssetCategories.WIDGETS:`) and bypass both the `pov` offset subtraction and the boundary culling logic, passing them directly to the Cython payload as absolute screen coordinates.

**4. The Asset Layer Attribute Crash (`app.game.board.py`)**

**The Bug**: On line 232 in Board.add(), the code attempts to cache assets with mass: self._cached_weights[asset.layer].append(asset).
**The Consequence**: Fatal AttributeError. The Asset base class does not have a .layer property. It must be accessed via asset.state.layer.

**5. The ScreenPosition Y-Sort Crash (`app.game.screen.py`)**

**The Bug**: In `Screen.draw()`, the sorting lambda attempts to calculate height via `a.state.position.y`.
**The Consequence**: Fatal AttributeError. PaneState and other UI components use ScreenPosition which possesses px and py attributes, not x and y. When the Cython renderer attempts to sort UI assets against world assets, it will crash.
**The Fix**: The lambda must safely check if the position attribute is a world Position or a UI ScreenPosition, or `Screen.draw()` must separate UI assets from world assets before sorting, rendering UI universally on top.

##### Tasks

**Task 1. Data Models & Application Hooks**

* [x] **Define WidgetProperties:** Implement `WidgetProperties` in `app.models.properties`.
* [~] **Define States:** Implement `MenuState`, `TraversalState`, `MeterState`, and `PageState` in `app.models.state`. Ensure `PageState` includes scrolling logic.
* [x] **Define Menu**: Implement `MenuInstance` in `app.game.menus.core`.
* [ ] **Extend Factory Hydration:** Update `Factory` schemas to parse the new models. Configure `Loader` to ingest `assets/widgets/main.yaml` and `data/menus/main.yaml`.
* [~] **Add Menu Stack** Update `Board` to include `menus: List[Menu]`
* [ ] **Refine UI Schema:** Update `main.yaml` to replace `self.children` references with string-based `intent` payloads (e.g., `intent: scroll_up`).

**Task 2. Frame & Animation Implementation**

* [ ] **Widget Frames:** Implement `TraversalFrame` and `MeterFrame`.
* [ ] **Widget Animations:** Implement `TraversalAnimation` to handle status transitions based on `MenuState.focus`.

**Task 3. The Menu Factory & Data Binding**

* [ ] **Context Resolver:** Write a helper method in `Factory` that parses the dot-notation `bind` string (e.g., `"sprite.state.inventory"`) and recursively fetches the value from the `EventContext`.
* [ ] **Menu Generation:** Create `Factory.menu(menu_key, context, screensize)`. This method reads the YAML schema, uses the Context Resolver to stamp data into the Widget states, and passes the hierarchy to the Layout Engine.

**Task 4. The Layout Engine (Spatial & Logical)**

* [ ] **Create Layout Module:** Implement `app.game.menus.layout`.
* [ ] **Calculate Anchors:** Convert `ScreenPosition` percentages into absolute `Position(x, y)`.
* [ ] **Stack/Dock/Tab Algorithms:** Implement the spatial layout algorithms, incorporating `gap` and `alignment` offsets.
* [ ] **Generate Traversal Graph:** During layout generation, build an adjacency dictionary linking traversable `Button` widgets based on their positional matrix.
* [ ] **Return Tuple:** Layout Engine returns `(List[Asset], TraversalGraph)`. Factory injects this into the `MenuState`.

**Task 5. Engine Loop & Event Bus Architecture**

* [ ] **Implement Event Queue:** Add an `Event` data class and `bus: collections.deque` to `Board`.
* [ ] **Trigger Events:** Update `Intentions` (like `barter`, `build`) to push `MenuEvent` to the queue.
* [ ] Implement `MenuEvent(menu_id, context_args)`.
* [ ] When `MenuMechanics` drains a `MenuEvent`, it passes `menu_id` and `context_args` to `Factory.menu()`.
* [ ] `Factory.menu()` resolves bindings, runs the `LayoutEngine`, instantiates the mapped `MenuController`, and pushes the resulting `Menu` onto `board.menus`.
* [ ] Implement `MenuEvent(menu_id, context_args)`.
* [ ] When `MenuMechanics` drains a `MenuEvent`, it passes `menu_id` and `context_args` to `Factory.menu()`.
* [ ] `Factory.menu()` resolves bindings, runs the `LayoutEngine`, instantiates the mapped `MenuController`, and pushes the resulting `Menu` onto `board.menus`.

**Task 6. Menu Controllers (Strategy Pattern)**

* [ ] Define `MenuController` abstract base class with `open`, `select`, `update`, and `close`.
* [ ] Map `Menu` IDs to their respective controllers in the `Factory`.
* [ ] Implement `app.game.menus.controllers.ScrollController`.
* [ ] Implement `app.game.menus.controllers.DisplayController`.

**Task 7. Mechanics & Input Handling**

* [ ] **Device Context Switching:** Update `Device` mappings to support a `MENU` context, translating raw SDL inputs into UI commands (Up, Down, Left, Right, Select, Cancel).
* [ ] **Implement MenuMechanics:** Drain the `Board.bus`. If a `MenuEvent` exists, set `board.paused = True`, instantiate the Menu via `Factory`, and hold it in `Board.active_menu`.
* [ ] **Focus Resolution:** In `MenuMechanics.update()`, apply directional input against the current `MenuState.graph` to update `MenuState.focus`. Emit `TerminalEvent` to unpause the board when the user exits.
    * [ ] If the stack has a menu, intercept `Device` polling.
    * [ ] Route directional inputs to update `MenuState.focus` via the `TraversalGraph`.
    * [ ] Route `SELECT` input to `active_menu.controller.select()`.

**Task 8. HUD / Screen Rendering Pipeline**

* [ ] **Fix Camera Culling:** Update `Screen.draw()` to identify UI Assets and to iterate over `board.menus`
* [ ] **Absolute UI Rendering:** Bypass the `pov` camera subtraction and visibility culling for UI Assets, appending them to the Cython array with raw screen coordinates at the highest Z-index.