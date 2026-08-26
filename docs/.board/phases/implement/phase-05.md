#### Implement: Phase 05 - Widgets

- Goals: Widget Creation, Menu Configuration and Instantiation, Menu Traversal
- **CURRENT FOCUS**: 

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

##### Tasks

**Task 1. Data Models & Application Hooks**

* [x] **Define WidgetProperties:** Implement `WidgetProperties` in `app.models.properties`.
* [~] **Define States:** Implement `MenuState`, `TraversalState` ,  `MeterState`, etc. in `app.models.state`. 
* [x] **Define Menu**: Implement `MenuInstance` in `app.game.menus.core`.
* [ ] **Extend Factory Hydration:** Update `Factory` schemas to parse the new models. Configure `Loader` to ingest `assets/widgets/main.yaml` and `data/menus/main.yaml`.
* [~] **Add Menu Stack** Update `Board` to include `menus: List[Menu]`

**Task 2. Frame & Animation Implementation**

* [ ] **Widget Frames:** Implement `TraversalFrame` and `MeterFrame`.
* [ ] **Widget Animations:** Implement `TraversalAnimation` to handle status transitions based on `MenuState.focus`.

**Task 3. Engine Loop & Event Bus Architecture**

* [ ] **Fix Engine Deadlock:** Update `Engine.start()` to evaluate `self.board.paused` *per mechanic*, not as a global loop bypass. Add `runs_while_paused` flag to `Mechanic` interface.
* [ ] **Implement Event Queue:** Add an `Event` data class and `bus: collections.deque` to `Board`.
* [ ] **Trigger Events:** Update `Intentions` (like `barter`, `build`) to push `MenuEvent` to the queue.
* [ ] Implement `MenuEvent(menu_id, context_args)`.
* [ ] When `MenuMechanics` drains a `MenuEvent`, it passes `menu_id` and `context_args` to `Factory.menu()`.
* [ ] `Factory.menu()` resolves bindings, runs the `LayoutEngine`, instantiates the mapped `MenuController`, and pushes the resulting `Menu` onto `board.menus`.
* [ ] Implement `MenuEvent(menu_id, context_args)`.
* [ ] When `MenuMechanics` drains a `MenuEvent`, it passes `menu_id` and `context_args` to `Factory.menu()`.
* [ ] `Factory.menu()` resolves bindings, runs the `LayoutEngine`, instantiates the mapped `MenuController`, and pushes the resulting `Menu` onto `board.menus`.

**Task 4. The Menu Factory & Data Binding**

* [ ] **Context Resolver:** Write a helper method in `Factory` that parses the dot-notation `bind` string (e.g., `"sprite.state.inventory"`) and recursively fetches the value from the `EventContext`.
* [ ] **Menu Generation:** Create `Factory.menu(menu_key, context, screensize)`. This method reads the YAML schema, resolves bindings, and passes the raw hierarchical data to the `LayoutEngine`.

**Task 5. The Layout Engine (Spatial & Logical)**

* [ ] **Create Layout Module:** Implement `app.game.menus.layout`.
* [ ] **Calculate Anchors:** Convert `ScreenPosition` percentages into absolute `Position(x, y)`.
* [ ] **Stack/Dock/Tab Algorithms:** Implement the spatial layout algorithms, incorporating `gap` and `alignment` offsets.
* [ ] **Generate Traversal Graph:** During layout generation, build an adjacency dictionary linking traversable `Button` widgets based on their positional matrix.
* [ ] **Return Tuple:** Layout Engine returns `(List[Asset], TraversalGraph)`. Factory injects this into the `MenuState`.

**Task 6. Menu Controllers (Strategy Pattern)**

* [ ] Define `MenuController` abstract base class with `on_open`, `on_select`, `on_update`, and `on_close`.
* [ ] Implement `app.game.menus.controllers.inventory.InventoryController`.
* [ ] Implement `app.game.menus.controllers.main.MainMenuController`.
* [ ] Map `Menu` IDs to their respective controllers in the `Factory`.

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