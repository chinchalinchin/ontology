#### Implement: Phase 05 - Widgets

##### Bugs

**1. Unsafe Board Sizing (`app.game.board.py`):**

In `Board.size()`, the max calculations (`max([...], default=0)`) assume that `nx` and `ny` correctly define the grid bounds. However, if a Layer contains no tiles (e.g., a purely UI layer or an empty staging layer), the generator expressions will evaluate to empty, defaulting to 0, which yields a `Dimensions(0, 0)` Board size. This will crash the Cython `construct` canvas allocation.

!!! note "CLOSED"
    Not worth fixing yet.

##### Tasks

**Task 0. Engine Deadlock Bug**

*Objective*: Ensure Engine is prepared for Widget and Menu implementations to follow.

* [x] Update Data Model: Modify `app.models.config.MechanicsConfiguration` to replace order with core and world lists.
* [x] Update YAML: Modify `data/config/mechanics/main.yaml` to separate mechanics into core and world pipelines.
* [x] Update Orchestrator: Update `Orchestrator.init()` to parse core and world configurations, instantiate them via` Factory.mechanics()`, and pass both lists into the Engine constructor.
* [x] Update Engine: Modify `Engine.__init__` to accept core_mechanics and world_mechanics.
* [x] Update Mechanics Logic: Modify `Engine.start()` to gate the world mechanics behind `paused`.

**Task 1. Data Models & Application Hooks**

* [x] *Define WidgetProperties:* Implement `WidgetProperties` in `app.models.properties`.
* [x] *Define States:* Implement `TraversalState`, `MeterState`, and `DisplayState` in `app.models.state`. 
    * [x] Implement scrolling methods for `DisplayState`. `content` is either a string to be rendered that needs to be sliced, or it is a list of Icon keys. Leave TODO placeholders for the Icon handling, as the spec has not been completed.
* [x] *Define Menu*: Implement `Menu` in `app.game.menus.core`.
* [x] *Update Recipes*: Add Widgets to the Asset Recipes configuration, `data/config/recipes.yaml`
* [x] *Define Configuration Schema*: Add configuration validation models for Menu configuration in `data/config/menus.yaml`
* [x] *Extend Factory Hydration:* Update `Factory` schemas to parse the new models. Configure `Loader` to ingest `assets/widgets/main.yaml` and `data/config/menus/main.yaml`.
* [x] *Add Menu Stack* Update `Board` to include `menus: List[Menu]` and `overlays: List[Menu]`.
* [x] *Refine Menu Schema:* 
    - [x] Add Action-Reaction bindings to allow Widgets embedded into a Menu, but unpacked into flat Asset lists, to emit signals for other Widgets in the Menu to catch.

**Task 2. Frame & Animation Implementation**

* [x] *Widget Frames* Implement Widget frames.
    * [x] Implement `TraversalFrame`
    * [x] Implement `MeterFrame`:
        * `keys()` must return a list of two keys: `[f"{id}-0", f"{id}-{resolution}"]`.
        * `index()` must map `empty` to `(0, 0, w, l)` and calculate the `fill` crop by dynamically multiplying `w` by the resolution percentage: `(w, 0, int(w * (res/100)), l)`.
    * [x] Modify MeterState to accept an Any reference. Add @property methods for reading and unit that dynamically return `self.reference.current` and `self.reference.maximum`
* [x] *Widget Animations*: Implement `TraversalAnimation` to handle status transitions and `MeterAnimation` for gauge updates.

**Task 3. The Menu Provider & Data Binding**

* [x] *Implement Provider:* Create a service similar to `Decomposer` called the Provider in `app.game.provider`. It accepts a `MenuConfiguration` and an `EventContext`.
* [x] *Context Binding:* Implement `getattr` resolution to parse YAML bindings (e.g., `context.sprite.state.meters.health`) into direct memory references pointing to the runtime objects.
    * **Optimization:** Because Python passes objects by reference, the `Provider` does not need to set up a continuous string-polling loop for the HUD. When parsing `bind: state: context.sprite.state.meters.health` during `Provider` instantiation, use `reduce()` and `getattr()` to resolve the string down to the actual `Meter` dataclass instance in memory. Assign this exact object reference to the `MeterState` of the widget. As the game mutates the Player's health, the Widget inherently reads the mutated values instantly.
* [x] *Text Canvas Allocation*: The Provider must call `render.canvas(w, l)` to allocate a blank TexturePtr when instantiating Page Widgets. It must bind this pointer to DisplayState.canvas`. It should not attempt to write text.
* [x] Provider must resolve bindings, run the `Layout` and instantiate the mapped `MenuController`
* [x] Orchestrator uses the Provider to create View (HUD) and Main Menu. Orchestrator then pushes the resulting Menus onto `board.overlays`.

**Task 4. The Layout Engine**

* [x] *Create Layout Module:* Implement `app.game.menus.layout`.
* [x] *Calculate Anchors:* Convert `ScreenPosition` percentages into absolute `Position(x, y)` pixels for all child Widgets.
* [x] *Z-Sorting Enforcement:* Assign `state.height` and `state.depth` modifiers to embedded Icons and Decals to ensure strict Painter's Algorithm compliance during flattening.
* [x] *Stack/Dock/Tab/Nest Algorithms:* Implement the spatial layout algorithms, incorporating `gap` and `alignment` offsets.
    * [x] Calculate offset mathematics for `CENTER` and `END` alignments.
    * [x] Update `_layout_tab()` to physically assign the parent Pane's absolute `Position(x, y)` to its children instead of passing.
* [x] *Z-Sorting Enforcement:* Assign `state.height` and `state.depth` modifiers to embedded Icons and Decals o ensure strict Painter's Algorithm compliance during flattening.
* [x] **Spatial Traversal Graph*: Implement an AABB spatial projection algorithm to link traversable `Button` widgets based on their absolute coordinates, outputting a directed adjacency dictionary.
* [x] *Return Tuple:* Layout Engine returns `(List[Asset], TraversalGraph)`.

**Task 5. Engine Loop & Event Bus Architecture**

* [x] *Implement Event Queue:* Add an `Event` data class and `bus: collections.deque` to `Engine`.
* [x] *Define Events:* Implement `MenuEvent` (pauses, pushes to `menus`), `UpdateEvent` (updates Menu states), and `TerminalEvent` (pops from `menus`).
* [x] *Trigger Events:* Update `Intentions` (like `barter`, `build`) to push `MenuEvent` to the queue.
* [x] *Implement Bus Draining*: In Engine.start(), drain the bus after Mechanics update but before the Render phase.
    - Route MenuEvent to pause the Board and push to board.menus.
    - Route TerminalEvent to unpause the Board and pop from board.menus.
    - Route UpdateEvent to execute Cython texture clearing and text baking.

**Task 6. Menu Controllers**

* [x] *Define Interface*: Define `MenuController` abstract base class with `open`, `select`, `update`, and `close`.
* [x] *Implement Scrolling*: Implement `app.game.menus.controllers.scroll.ScrollController` (Calls `DisplayState.scroll()` methods).
    * [x] Implement `ScrollController.select()`. It must parse the selection binding (e.g., `SCROLLUP`), locate the target widget via the selector binding and call `scroll()`
* [x] *Implement Heads Up Display*: Implement `app.game.menus.controllers.display.DisplayController` (Mutates `MeterState` (health meters) amd `TraversalState` (disabled Button slots showing equipped items)).

**Task 7. Mechanics & Input Handling**

* [x] *Menu Time vs World Time*: Update `MenuMechanics.update()` to call `animate()` on all Widgets inside `board.overlays` and the top of `board.menus`, ensuring UI animations run independently of the world state.
* [x] *Device Context Switching:* Update `Device` mappings to support a `MENU` context, translating raw SDL inputs into UI commands (Up, Down, Left, Right, Select, Cancel).
    - [x] Add nested attributes, `mappings.<device>.world` and `mappings.<device>.menu`, to the Devive mapping configuration in `data/config/mappings/main.yaml`.
    - [x] Update MappingConfiguration models in `app.models.config`.
    - [x] Updated the Device class to initialize and poll using the new mapping data structure.
    - Implement `Keyboard.context(context: str)`. When `context == 'world'`, map `_scancodes` to Intentions/Goals. When `context == 'menu'`, map to Traversal/Interactions. Update `_last_state` accordingly.
* [x] *Interface*: Update the Mechanic interface to accept the Bus. 
    * [x] Propagate updated interface through previous Mechanics.
* [x] *Focus Resolution & Input Interception:* In `MenuMechanics.update()`:
    * [x] If `len(board.menus) > 0`, intercept `device.poll()` mapped commands.
    * [x] Route directional inputs to update `MenuState.focus` via the `TraversalGraph`.
    * [x] Route `SELECT` input to `active_menu.controller.select()`.
    * [x] Emit `TerminalEvent` to unpause the board when the user exits.
    
**Task 8. Rendering Pipeline**

* [x] *Cython Refactor:* Break `libs/graphics/render.pyx:render()` into `clear()`, `render()`, `superimpose()`, and `present()`. Remove `SDL_RenderClear` and `SDL_RenderPresent` from the core rendering loops.
* [x] *Screen Refactor:* Split `app.game.screen.Screen.draw()` into `draw()` and `interface()`. 
    * [x]: `draw()` retains the current camera culling. 
    * [x]: `interface()` takes Menus and Overlays, extracts their `Widgets`, and passes them to Cython with absolute coordinates. Implement the duck-typing check for `widget.state.canvas`. The Screen must retrieve the base background from the Registry, use `render.construct` to overwrite the existing canvas (clearing old text), and call `render.write `to bake the updated `DisplayState.current()` text`.
    * [x] Implement `_flatten(menus, overlays)`.
    * [x] `stamp()`: Implement this method for re-rendering text and stamping it onto a Page asset.
* [x] *Engine Refactor:* Update `Engine.start()` to explicitly call `screen.clear()`, `screen.draw()`, `screen.interface()`, and `screen.present()` in sequence.
* [x] *Fix Destination Stretching:* In `Screen.draw()`, update the dimension assignment to respect dynamic source cropping from the Registry: `dw, dl = sw, sl`

**Task 9. Layout Engine Completion**

* [x] Implement `Layouts.TAB` recursion in `LayoutEngine.compute()`.
* [x] Implement `Layouts.COLUMN` recursion in `LayoutEngine.compute()`.
* [x] **Schema:** Update `MenuPane.children` in `app.models.config` to `List[Union['MenuPane', MenuWidget]]`.
* [x] **Provider:** Replace linear iteration in `Provider._unpack_pane` with a recursive `_unpack_node` router capable of handling nested Panes.
* [x] **Layout:** Refactor `LayoutEngine.compute` to use a top-down spatial recursion algorithm (`_compute_recursive`), removing dead Z-sorting code.

**Task 10. Unit Test & Documentation Updates**

* [x] *Existing*: Ensure all unit tests are passing after prior Task updates.
* [x] *New*: `tests/unit/test_lib_graphics_registry.py`: Ensure new Widget frame indexing is adequately covered.
* [x] *New*: `tests/unit/test_app_hooks_factory.py`: Ensure new Widget instantiation is adequately covered.
* [x] *New*: `tests/unit/test_app_hooks_provider.py`: Ensure Menu generation is adequately covered.
* [x] Update documentation to reflect the latest state of the application.

**Task 11. In Game Test**

!!! note
    Needs further specification and definition before implementation.

* [!] Create a Sign Object that triggers Text menus.
    * [!] Define Sign State to include `persona` and `lexicon`.
* [!] Create Library for parsing `src/data/config/library/main.yaml`. 