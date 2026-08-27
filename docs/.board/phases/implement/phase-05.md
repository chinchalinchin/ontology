#### Implement: Phase 05 - Widgets

- Goals: Widget Creation, Menu Configuration and Instantiation, Menu Traversal

**CURRENT FOCUS:** WHAT NEEDS FURTHER DEFINITION BEFORE IMPLEMENTATION? 

- Consider how Icons will be embedded onto Buttons
- Consider how text will be embedded onto Pages.
- Consider how MenuMechanics knows not to process View (HUD) unless it receives an UpdateEvent, i.e. how does the HUD get painted to screen?
- What other areas of Widgets and Menus are ill-defined?

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

* [x] **Define WidgetProperties:** Implement `WidgetProperties` in `app.models.properties`.
* [~] **Define States:** Implement `MenuState`, `TraversalState`, `MeterState`, and `PageState` in `app.models.state`. Ensure `PageState` includes scrolling logic.
* [x] **Define Menu**: Implement `MenuInstance` in `app.game.menus.core`.
* [ ] **Extend Factory Hydration:** Update `Factory` schemas to parse the new models. Configure `Loader` to ingest `assets/widgets/main.yaml` and `data/menus/main.yaml`.
* [~] **Add Menu Stack** Update `Board` to include `menus: List[Menu]`
* [ ] **Refine UI Schema:** Update `main.yaml` to replace `self.children` references with string-based `intent` payloads (e.g., `intent: scroll_up`).

**Task 2. Frame & Animation Implementation**

* [ ] **Widget Frames:** Implement `TraversalFrame` and `MeterFrame`.
* [ ] **Widget Animations:** Implement `TraversalAnimation` to handle status transitions based on `MenuState.focus`.

**Task 3. The Menu Provider & Data Binding**

* [~] **Implement Provider:** Create a service similar to `Decomposer` called the Provider in `app.game.provider`. It accepts a `MenuConfiguration` and an `EventContext`.
* [ ] **Context Binding:** Implement regex parsing to replace YAML bindings (e.g., `context.sprite.state.psyche`) with values from the runtime `EventContext`.
* [ ] **Text Canvas Allocation:** Ensure `Page` widgets dynamically allocate a blank `TexturePtr` canvas upon instantiation to avoid mutating shared VRAM caches.
* [ ] Provider must resolve bindings, run the `Layout` and instantiate the mapped `MenuController`
* [ ] Orchestrator uses the Provider to create View (HUD) and Main Menu. Orchestrator then pushes the resulting Menus onto `board.overlays`.

**Task 4. The Layout Engine (Spatial & Logical)**

* [ ] **Create Layout Module:** Implement `app.game.menus.layout`.
* [ ] **Calculate Anchors:** Convert `ScreenPosition` percentages into absolute `Position(x, y)` pixels for all child Widgets.
* [ ] **Z-Sorting Enforcement:** Assign `state.height` and `state.depth` modifiers to embedded Icons and Decals to ensure strict Painter's Algorithm compliance during flattening.
* [ ] **Stack/Dock/Tab/Nest Algorithms:** Implement the spatial layout algorithms, incorporating `gap` and `alignment` offsets.
* [ ] **Generate Traversal Graph:** During layout generation, build an adjacency dictionary linking traversable `Button` widgets based on their positional matrix.
* [ ] **Return Tuple:** Layout Engine returns `(List[Asset], TraversalGraph)`. Factory injects this into the `MenuState`.

**Task 5. Engine Loop & Event Bus Architecture**

* [ ] **Implement Event Queue:** Add an `Event` data class and `bus: collections.deque` to `Board`.
* [ ] **Trigger Events:** Update `Intentions` (like `barter`, `build`) to push `MenuEvent` to the queue.
* [ ] Implement `MenuEvent(menu_id, context_args)`.
* [ ] When `MenuMechanics` drains a `MenuEvent`, it passes `menu_id` and `context_args` to `Factory.menu()`.
* [ ] Implement `MenuEvent(menu_id, context_args)`.
* [ ] When `MenuMechanics` drains a `MenuEvent`, it passes `menu_id` and `context_args` to `Factory.menu()`.

**Task 6. Menu Controllers**

* [x] Define `MenuController` abstract base class with `open`, `select`, `update`, and `close`.
* [ ] Map `Menu` IDs to their respective controllers in the `Factory`.
* [ ] Implement `app.game.menus.controllers.scroll.ScrollController`.
    * [ ] TODO
* [ ] Implement `app.game.menus.controllers.display.DisplayController`.
    * [ ] TODO

**Task 7. Mechanics & Input Handling**

* [ ] **Device Context Switching:** Update `Device` mappings to support a `MENU` context, translating raw SDL inputs into UI commands (Up, Down, Left, Right, Select, Cancel).
    - [ ] Add nested attributes, `mappings.<device>.game` and `mappings.<device>.menu`
* [ ] **Implement MenuMechanics:** Drain the `Board.bus`.
    * If `bus` contains `MenuEvent`, push to `board.menus` and set `board.paused = True`.
    * If `bus` contains `UpdateEvent`, route to `board.overlays` controllers.
* [ ] **Focus Resolution:** In `MenuMechanics.update()`, apply directional input against the current `MenuState.graph` to update `MenuState.focus`. Emit `TerminalEvent` to unpause the board when the user exits.
    * [ ] If the stack has a menu, intercept `Device` polling.
    * [ ] Route directional inputs to update `MenuState.focus` via the `TraversalGraph`.
    * [ ] Route `SELECT` input to `active_menu.controller.select()`.

**Task 8. HUD / Screen Rendering Pipeline**

* [ ] **Fix Camera Culling:** Update `Screen.draw()` to identify UI Assets and to iterate over `board.menus`
* [ ] **Absolute UI Rendering:** Bypass the `pov` camera subtraction and visibility culling for UI Assets, appending them to the Cython array with raw screen coordinates at the highest Z-index.
* [ ] **Widget Indexing**: Ensure the frame index/key schemas properly index Widget assets.

**Task 9. Unit Test Updates**

* [ ] Ensure all unit tests are passing after prior Task updates.
* [ ] `tests/unit/test_lib_graphics_registry.py`: Ensure new Widget frame indexing is adequately covered.
* [ ] `tests/unit/test_hooks_factory.py`: Ensure new Widget instantiation is adequately covered.



---



Here is an analysis of the Ontology Phase 05 (Widgets) architecture.

### Formal Assumptions

Before proceeding with the architectural critique, the following assumptions regarding the engine's design are established:

1. **Zero Heap Allocation in the Inner Loop:** The Cython renderer expects a flat list of primitive geometries. It should remain ignorant of UI hierarchy, graph traversal, or tree logic.
2. **Deterministic Layout:** All relative widget positions (`ScreenPosition`, `Alignments`, `Layouts`) can be calculated once upon Menu instantiation and reduced to absolute screen coordinates.
3. **State Integrity:** A game pause (`board.paused = True`) suspends spatial and combat updates but must permit UI input polling and rendering updates.

---

### Architecture & Logical Flow Analysis

The current design of the Widgets and Menus phase contains overlapping responsibilities and conflicting state definitions. Below is a rigorous breakdown of the logical flow and required architectural adjustments to fulfill the Phase 05 directives.

#### 1. The Modal vs. Overlay Dichotomy (HUD Deadlock)

**The Problem:** The documentation and task board imply that the HUD (View Menu) is managed by `MenuMechanics` and pushed onto `Board.menus`. However, `MenuMechanics` operates under the premise that an active menu pauses the game loop. If the HUD is placed on `Board.menus`, the game will permanently deadlock upon initialization.

**The Solution:** The `Board` must separate UI into two distinct collections:

* `board.menus: List[Menu]`: A LIFO stack for *Modal* interfaces (Inventory, Dialogue, Trade). When `len(board.menus) > 0`, world mechanics are paused, and `MenuMechanics` intercepts device polling for traversal.
* `board.overlays: List[Menu]`: A flat list for *Non-blocking* interfaces (HUD, Floating Damage Numbers, Action Prompts). These do not pause the board and do not receive input focus. They passively observe `UpdateEvent` emissions from the Event Bus.

#### 2. Coordinate Unification (Y-Sort and Culling Crashes)

**The Problem:** The documentation states Panes use `ScreenPosition` (percentages), while `Screen.draw()` strictly expects `Position` (absolute pixels) and calculates height via `state.position.y`. Mixing these models at render-time will trigger fatal `AttributeError`s and Cython casting failures.

**The Solution:** `ScreenPosition` is a *configuration-time* concept, not a *runtime* concept.
When the `Provider` and `Layout` engine instantiate a Menu, they must calculate the absolute pixel values `(px * screensize.w, py * screensize.l)` and inject a standard `Position(x, y)` into the `WidgetState`. By flattening the UI tree and translating all percentages to absolute `Position`s, `Screen.draw()` can consume Widgets exactly like world Assets, satisfying the zero-allocation prior.

#### 3. Text and Icon Embedding

**The Problem:** The documentation asks how text and icons are embedded onto Pages and Buttons.

**The Solution (Icons):** Icons should be treated mathematically identically to `Compositions`. An Icon is simply a child component of a Button. The `Layout` engine computes the Icon's absolute `Position(x, y)` relative to the Button's absolute `Position`. `Screen.draw()` receives both the Button asset and the Icon asset as flat siblings. To guarantee the Icon renders on top, the `Layout` engine assigns the Icon a `state.height` equal to `button.state.height`, and increments the `state.depth` by 1.

**The Solution (Text):** Text rendering requires caution due to the Cython `write()` implementation. The `write()` function stamps text permanently into the `TexturePtr` target.
If a `Page` widget uses a shared global texture, writing to it will mutate the texture for all instances of that Page. Therefore, during `Provider` instantiation, a `Page` widget must request a dedicated, blank `canvas()` from the Cython layer, sized to its dimensions. The `DisplayController` handles text updates by clearing this specific canvas and re-invoking `write()`.

#### 4. Contextual Device Polling

**The Problem:** `Device.poll()` maps physical keys to `Intentions` and `Goals`. A Menu requires traversal commands (Up, Down, Left, Right, Select, Cancel). If the `SPACE` bar maps to the `attack` Intention in the game, it cannot simultaneously map to `SELECT` without a contextual switch.

**The Solution:** The `Device` class must implement a stateful context flag (`Context.WORLD` vs `Context.MENU`). The `MappingConfiguration` must be updated to include a `menu: Dict[MenuCommands, int]` mapping. When `board.menus` is populated, `MenuMechanics` toggles the device context, causing `poll()` to return menu commands instead of world intentions.

---

### Task Backlog Grooming

The following modifications to the Phase 05 backlog are required to align implementation with the architecture.

#### Implement: Phase 05 - Widgets

**Task 1. Data Models & Application Hooks (Modified)**

* [x] **Define WidgetProperties:** Implement `WidgetProperties` in `app.models.properties`.
* [~] **Define States:** Implement `MenuState`, `TraversalState`, `MeterState`, and `PageState`.
* [x] **Define Menu**: Implement `MenuInstance` in `app.game.menus.core`.
* [ ] **Separate Menu Stacks:** Update `Board` to include `menus: List[Menu]` (Modal) and `overlays: List[Menu]` (Non-blocking).
* [ ] **Extend Factory Hydration:** Update `Factory` schemas to parse the new models.

**Task 2. Frame & Animation Implementation**

* [ ] **Widget Frames:** Implement `TraversalFrame` and `MeterFrame`.
* [ ] **Widget Animations:** Implement `TraversalAnimation` to handle status transitions based on `MenuState.focus`.

**Task 3. The Menu "Provider" & Data Binding (Modified)**

* [~] **Implement Provider:** Create `Provider` in `app.game.provider` to parse `MenuConfiguration`.
* [ ] **Context Binding:** Implement regex parsing to replace YAML bindings (e.g., `context.sprite.state.psyche`) with values from the runtime `EventContext`.
* [ ] **Text Canvas Allocation:** Ensure `Page` widgets dynamically allocate a blank `TexturePtr` canvas upon instantiation to avoid mutating shared VRAM caches.

**Task 4. The Layout Engine (Modified)**

* [ ] **Create Layout Module:** Implement `app.game.menus.layout`.
* [ ] **Coordinate Translation:** Convert `ScreenPosition` percentages into absolute `Position(x, y)` pixels for all child Widgets.
* [ ] **Z-Sorting Enforcement:** Assign `state.height` and `state.depth` modifiers to embedded Icons and Decals to ensure strict Painter's Algorithm compliance during flattening.
* [ ] **Generate Traversal Graph:** Build the adjacency dictionary linking traversable `Button` widgets.
* [ ] **Return Tuple:** Layout Engine returns `(List[Asset], TraversalGraph)`.

**Task 5. Event Bus Architecture & Overlays**

* [ ] **Implement Event Queue:** Add an `Event` data class and `bus: collections.deque` to `Board`.
* [ ] **Define Events:** Implement `MenuEvent` (pauses, pushes to `menus`), `UpdateEvent` (updates `overlays`), and `TerminalEvent` (pops from `menus`).
* [ ] **Trigger Events:** Update `Intentions` (like `barter`, `build`) to push `MenuEvent` to the queue.

**Task 6. Menu Controllers**

* [x] Define `MenuController` abstract base class.
* [ ] Implement `ScrollController` (Modifies `PageState.pageindex`).
* [ ] Implement `DisplayController` (Parses `UpdateEvent` to mutate `MeterState`).

**Task 7. Mechanics & Input Handling (Modified)**

* [ ] **Device Context Switching:** Update `Device.poll()` to accept a `context` argument, routing raw SDL inputs into either World Commands or Menu Commands.
* [ ] **Implement MenuMechanics:**
* If `bus` contains `MenuEvent`, push to `board.menus` and set `board.paused = True`.
* If `bus` contains `UpdateEvent`, route to `board.overlays` controllers.


* [ ] **Focus Resolution:** Apply directional input against the current `MenuState.graph` to update `MenuState.focus`. Route `SELECT` input to `active_menu.controller.select()`.

**Task 8. HUD / Screen Rendering Pipeline (Modified)**

* [ ] **Fix Camera Culling:** Update `Screen.draw()` to identify UI Assets by `AssetCategories.WIDGETS`.
* [ ] **Absolute UI Rendering:** Bypass the `pov` camera subtraction and visibility culling for UI Assets.
* [ ] **Update Cython Write:** Fix the `dst_rect.y` and `dst_rect.x` calculations in `libs.graphics.render.pyx` to correctly orient relative to `0` when stamping text onto an asset's local texture.