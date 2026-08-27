#### Implement: Phase 05 - Widgets

- Goals: Widget Creation, Menu Configuration and Instantiation, Menu Traversal

**CURRENT FOCUS:** 

- Define the pseudocode on the 06-widgets.md docs page for the various alignment and layout algorithms.

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

**The Bug**: In `Screen.draw()`, the sorting lambda attempts to calculate height via `state.position.y`.
**The Consequence**: Fatal AttributeError. PaneState and other UI components use ScreenPosition which possesses px and py attributes, not x and y. When the Cython renderer attempts to sort UI assets against world assets, it will crash.
**The Fix**: The lambda must safely check if the position attribute is a world Position or a UI ScreenPosition, or `Screen.draw()` must separate UI assets from world assets before sorting, rendering UI universally on top.

**6. Unsafe Board Sizing (`app.game.board.py`):**

In `Board.size()`, the max calculations (`max([...], default=0)`) assume that `nx` and `ny` correctly define the grid bounds. However, if a Layer contains no tiles (e.g., a purely UI layer or an empty staging layer), the generator expressions will evaluate to empty, defaulting to 0, which yields a `Dimensions(0, 0)` Board size. This will crash the Cython `construct` canvas allocation.

**7. Decomposer Rigidity (`app.hooks.decomposer.py`):**

The `Decomposer` strictly outputs `Asset` objects tied to `PropertyState`. If the `Provider` attempts to use the `Decomposer` to unpack a nested Menu configuration, it will fail because Widgets require `PaneState`, `TraversalState`, etc. The Menu generation logic (`Provider/Layout`) must be structurally isolated from the Composition `Decomposer`.

**8. Cython Text Alignment Calculation (`libs.graphics.render.pyx`):**

In `write()`, the margin pixel offset `margin_px_h` is added to `sy` (source Y), but the destination rectangle `dst_rect.y` is calculated using `sy`. `dst_rect.y` should map to `dy` (destination Y) when rendering directly to screen, OR `sy` if rendering to an intermediate texture atlas. Because text is baked directly onto the widget's texture, `dst_rect.y` relative to `0` (the top of the asset's own texture) must be used. Adding `sy` offsets the text incorrectly if the asset is pulled from a sprite sheet.

##### Tasks

**Task 1. Data Models & Application Hooks**

* [x] *Define WidgetProperties:* Implement `WidgetProperties` in `app.models.properties`.
* [~] *Define States:* Implement `TraversalState`, `GaugeState`, and `DisplayState` in `app.models.state`. 
* [x] *Define Menu*: Implement `Menu` in `app.game.menus.core`.
* [x] *Update Recipes*: Add Widgets to the Asset Recipes configuration, `data/config/recipes.yaml`
* [x] *Define Configuration Schema*: Add configuration validation models for Menu configuration in `data/config/menus.yaml`
* [ ] *Extend Factory Hydration:* Update `Factory` schemas to parse the new models. Configure `Loader` to ingest `assets/widgets/main.yaml` and `data/config/menus/main.yaml`.
* [~] *Add Menu Stack* Update `Board` to include `menus: List[Menu]` and `overlays: List[Menu]`.
* [~] *Refine Menu Schema:* 
    - [~] Add Action-Reaction bindings to allow Widgets embedded into a Menu, but unpacked into flat Asset lists, to emit signals for other Widgets in the Menu to catch.

**Task 2. Frame & Animation Implementation**

* [ ] *Widget Frames** Implement `TraversalFrame` and `MeterFrame`.
* [ ] **idget Animations:* Implement `TraversalAnimation` to handle status transitions based on `MenuState.focus`.

**Task 3. The Menu Provider & Data Binding**

* [~] *Implement Provider:* Create a service similar to `Decomposer` called the Provider in `app.game.provider`. It accepts a `MenuConfiguration` and an `EventContext`.
* [ ] *Context Binding:* Implement regex parsing to replace YAML bindings (e.g., `context.sprite.state.psyche`) with values from the runtime `EventContext`.
* [ ] *Text Canvas Allocation:* Ensure `Page` widgets dynamically allocate a blank `TexturePtr` canvas upon instantiation to avoid mutating shared VRAM caches.
* [ ] Provider must resolve bindings, run the `Layout` and instantiate the mapped `MenuController`
* [ ] Orchestrator uses the Provider to create View (HUD) and Main Menu. Orchestrator then pushes the resulting Menus onto `board.overlays`.

**Task 4. The Layout Engine**

* [ ] *Create Layout Module:* Implement `app.game.menus.layout`.
* [ ] *Calculate Anchors:* Convert `ScreenPosition` percentages into absolute `Position(x, y)` pixels for all child Widgets.
* [ ] *Z-Sorting Enforcement:* Assign `state.height` and `state.depth` modifiers to embedded Icons and Decals to ensure strict Painter's Algorithm compliance during flattening.
* [ ] *Stack/Dock/Tab/Nest Algorithms:* Implement the spatial layout algorithms, incorporating `gap` and `alignment` offsets.
* [ ] *Z-Sorting Enforcement:* Assign `state.height` and `state.depth` modifiers to embedded Icons and Decals to ensure strict Painter's Algorithm compliance during flattening.
* [ ] *Generate Traversal Graph:* During layout generation, build an adjacency dictionary linking traversable `Button` widgets based on their positional matrix.
* [ ] *Return Tuple:* Layout Engine returns `(List[Asset], TraversalGraph)`.

**Task 5. Engine Loop & Event Bus Architecture**

* [ ] *Implement Event Queue:* Add an `Event` data class and `bus: collections.deque` to `Board`.
* [ ] *Define Events:* Implement `MenuEvent` (pauses, pushes to `menus`), `UpdateEvent` (updates `overlays`), and `TerminalEvent` (pops from `menus`).
* [ ] *Trigger Events:* Update `Intentions` (like `barter`, `build`) to push `MenuEvent` to the queue.


**Task 6. Menu Controllers**

* [x] *Define Interface*: Define `MenuController` abstract base class with `open`, `select`, `update`, and `close`.
* [ ] *Implement Scrolling*: Implement `app.game.menus.controllers.scroll.ScrollController` (Modifies `DisplayState.pageindex`).
* [ ] *Implement Heads Up Display*: Implement `app.game.menus.controllers.display.DisplayController` (Parses `UpdateEvent` to mutate `GaugeState` amd `TraversalState` (disabled Button slots showing equipped items)).

**Task 7. Mechanics & Input Handling**

* [ ] *Device Context Switching:* Update `Device` mappings to support a `MENU` context, translating raw SDL inputs into UI commands (Up, Down, Left, Right, Select, Cancel).
    - [ ] Add nested attributes, `mappings.<device>.game` and `mappings.<device>.menu`, to the Devive mapping configuration in `data/config/mappings/main.yaml`.
* [ ] *Implement MenuMechanics:* Drain the `Board.bus`.
    * If `bus` contains `MenuEvent`, push to `board.menus` and set `board.paused = True`.
    * If `bus` contains `UpdateEvent`, route to `board.overlays` controllers.
* [ ] *Focus Resolution:* In `MenuMechanics.update()`, apply directional input against the current `MenuState.graph` to update `MenuState.focus`. Emit `TerminalEvent` to unpause the board when the user exits.
    * [ ] If the stack has a menu, intercept `Device` polling.
    * [ ] Route directional inputs to update `MenuState.focus` via the `TraversalGraph`.
    * [ ] Route `SELECT` input to `active_menu.controller.select()`.

**Task 8. Rendering Pipeline**

* [ ] *Fix Camera Culling:* Update `Screen.draw()` to identify UI Assets and to iterate over `board.menus`
* [ ] *Absolute UI Rendering:* Bypass the `pov` camera subtraction and visibility culling for UI Assets, appending them to the Cython array with raw screen coordinates at the highest Z-index.
* [ ] *Widget Indexing*: Ensure the frame index/key schemas properly index Widget assets.
* [ ] *Implement `GaugeFrame`:*
    * `keys()` must return a list of two keys: `[f"{id}-empty", f"{id}-fill-{resolution}"]`.
    * `index()` must map `empty` to `(0, 0, w, l)` and calculate the `fill` crop by dynamically multiplying `w` by the resolution percentage: `(w, 0, int(w * (res/100)), l)`.
* [ ] *Fix Destination Stretching:* In `Screen.draw()`, update the dimension assignment to respect dynamic source cropping from the Registry: `dw, dl = sw, sl`

**Task 10. Unit Test Updates**

* [ ] *Existing*: Ensure all unit tests are passing after prior Task updates.
* [ ] *New*: `tests/unit/test_lib_graphics_registry.py`: Ensure new Widget frame indexing is adequately covered.
* [ ] *New*: `tests/unit/test_hooks_factory.py`: Ensure new Widget instantiation is adequately covered.
* [ ] *New*: `tests/unit/test_hooks_provder.py`: Ensure Menu generation is adequately covered.