#### Implement: Phase 05 - Widgets

- Goals: Widget Creation, Menu Configuration and Instantiation, Menu Traversal

**CURRENT FOCUS:** 

- Define the pseudocode on the `06-widgets.md` docs page for the various alignment and layout algorithms.
- Where should Widgets be animated? Currently, the AnimationMechanics handle animating dynamic Assets on the Board. However, Widgets only need to animated when their state changes in response to events. Where in the Menu flow should the `animate()` method be called on Widgets?
- Identify any areas of the Widget/Menu architecture that are ambiguous or ill-defined.

##### Bugs

**1. The Engine Pause Deadlock (`app.game.engine.py`)**

In `Engine.start()`, the fixed-timestep logic `while accumulator >= delta:` is nested *inside* `if not self.board.paused:`.

If `MenuMechanics` (or anything else) sets `board.paused = True`, the game loop will completely stop processing **all** mechanics. `MenuMechanics` will never get its `update()` called to process user input, meaning the menu can never be closed or traversed. The game is deadlocked.

- Fix: Separate `Engine.mechanics` into `self.core_mechanics` and `self.world_mechanics`. Wrap only `world_mechanics` in the `if not self.board.paused:` condition.

**2. The UI Camera Culling Annihilation (`app.game.screen.py`)**

`Screen.draw()` expects all assets to exist in world-space. It uses `pov.x` and `pov.y` (the camera offset) to cull assets that are off-screen.

Widgets will be hydrated with absolute screen coordinates (e.g., `x: 50, y: 50`). If the player walks to the right and the camera `pov.x` becomes `1000`, the UI assets will fail the condition `dx + dw >= pov.x` and be culled. The HUD will vanish when the player moves.

- Fix: Decouple world and interface Assets in the rendering pipeline. See next section.

**3. The ScreenPosition Y-Sort Crash (`app.game.screen.py`)**

In `Screen.draw()`, the sorting lambda attempts to calculate height via `state.position.y`.

PaneState and other UI components use ScreenPosition which possesses px and py attributes, not x and y. When the Cython renderer attempts to sort UI assets against world assets, it will crash.

- Fix: Decouple world and interface Assets in the rendering pipeline. See next section.

**4. Unsafe Board Sizing (`app.game.board.py`):**

In `Board.size()`, the max calculations (`max([...], default=0)`) assume that `nx` and `ny` correctly define the grid bounds. However, if a Layer contains no tiles (e.g., a purely UI layer or an empty staging layer), the generator expressions will evaluate to empty, defaulting to 0, which yields a `Dimensions(0, 0)` Board size. This will crash the Cython `construct` canvas allocation.

!!! note "CLOSED"
    Not worth fixing yet.

**5. Cython Text Alignment Calculation (`libs.graphics.render.pyx`):**

In `write()`, the margin pixel offset `margin_px_h` is added to `sy` (source Y), but the destination rectangle `dst_rect.y` is calculated using `sy`. `dst_rect.y` should map to `dy` (destination Y) when rendering directly to screen, OR `sy` if rendering to an intermediate texture atlas. Because text is baked directly onto the widget's texture, `dst_rect.y` relative to `0` (the top of the asset's own texture) must be used. Adding `sy` offsets the text incorrectly if the asset is pulled from a sprite sheet.

- Fix: Change `dst_rect.y = sy + margin_px_h` to `dst_rect.y = margin_px_h` to respect the local target coordinates of the asset's texture, not the sprite sheet coordinates.

##### Goal: Render Pipeline Decoupling

To address the bugs that will be introduced by Widgets and Menus (see next section), the following strategy is to be adopted,

**1. Cython Interfacing (`libs/graphics/render.pyx`)**

Strip `SDL_RenderClear` and `SDL_RenderPresent` out of the monolithic `render` function and expose them as individual lifecycle primitives.

* `clear()`: Clears the backbuffer.
* `render(bg, fg, assets, cam_x, cam_y, w, l)`: Renders the world, applying camera subtractions.
* `superimpose(assets)`: Superimposes UI assets at absolute screen coordinates with zero offsets.
* `present()`: Swaps the buffer to the window and pumps SDL events.

**2. Python Abstraction (`app.game.screen.py`)**

The `Screen` class mirrors the Cython primitives, strictly separating the sorting and culling logic of the world from the flat-list generation of the Menu.

* `Screen.clear()`
* `Screen.draw(assets, focus, dim)`: Handles AABB camera culling and Y-sorting, then calls `draw`.
* `Screen.interface(menus, overlays)`: Flattens the active Menu trees, applies Painter's Algorithm sorting, and calls `interface`.
* `Screen.present()`

**3. The Engine Orchestrator (`app.game.engine.py`)**

The fixed-timestep loop inside `Engine.start()` now clearly expresses the intent of the frame rendering pipeline:

```python
# 2. Rendering
screen = self.screens[player.state.layer]

screen.clear()
screen.draw(
    self.board.renderables(player.state.layer), 
    player.state.position,
    player.dimensions
)
screen.interface(
    self.board.menus, 
    self.board.overlays
)
screen.present()
```

##### Tasks

**Task 1. Data Models & Application Hooks**

* [x] *Define WidgetProperties:* Implement `WidgetProperties` in `app.models.properties`.
* [~] *Define States:* Implement `TraversalState`, `MeterState`, and `DisplayState` in `app.models.state`. 
* [x] *Define Menu*: Implement `Menu` in `app.game.menus.core`.
* [x] *Update Recipes*: Add Widgets to the Asset Recipes configuration, `data/config/recipes.yaml`
* [x] *Define Configuration Schema*: Add configuration validation models for Menu configuration in `data/config/menus.yaml`
* [ ] *Extend Factory Hydration:* Update `Factory` schemas to parse the new models. Configure `Loader` to ingest `assets/widgets/main.yaml` and `data/config/menus/main.yaml`.
* [~] *Add Menu Stack* Update `Board` to include `menus: List[Menu]` and `overlays: List[Menu]`.
* [~] *Refine Menu Schema:* 
    - [~] Add Action-Reaction bindings to allow Widgets embedded into a Menu, but unpacked into flat Asset lists, to emit signals for other Widgets in the Menu to catch.

**Task 2. Frame & Animation Implementation**

* [ ] *Widget Frames** Implement Widget frames.
    * [ ] *Implement `MeterFrame`:*
        * `keys()` must return a list of two keys: `[f"{id}-empty", f"{id}-fill-{resolution}"]`.
        * `index()` must map `empty` to `(0, 0, w, l)` and calculate the `fill` crop by dynamically multiplying `w` by the resolution percentage: `(w, 0, int(w * (res/100)), l)`.
* [ ] *Widget Animations:* Implement `TraversalAnimation` to handle status transitions based on `MenuState.focus`.


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
* [ ] *Implement Heads Up Display*: Implement `app.game.menus.controllers.display.DisplayController` (Parses `UpdateEvent` to mutate `MeterState` (health meters) amd `TraversalState` (disabled Button slots showing equipped items)).

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

* [ ] *Cython Refactor:* Break `libs/graphics/render.pyx:render()` into `clear()`, `render()`, `superimpose()`, and `present()`. Remove `SDL_RenderClear` and `SDL_RenderPresent` from the core rendering loops.
* [ ] *Screen Refactor:* Split `app.game.screen.Screen.draw()` into `draw()` and `interface()`. `draw()` retains the current camera culling. `interface()` takes Menus and Overlays, extracts their `Widgets`, and passes them to Cython with absolute coordinates.
* [ ] *Engine Refactor:* Update `Engine.start()` to explicitly call `screen.clear()`, `screen.draw()`, `screen.interface()`, and `screen.present()` in sequence.
* [ ] *Fix Destination Stretching:* In `Screen.draw()`, update the dimension assignment to respect dynamic source cropping from the Registry: `dw, dl = sw, sl`

**Task 10. Unit Test Updates**

* [ ] *Existing*: Ensure all unit tests are passing after prior Task updates.
* [ ] *New*: `tests/unit/test_lib_graphics_registry.py`: Ensure new Widget frame indexing is adequately covered.
* [ ] *New*: `tests/unit/test_hooks_factory.py`: Ensure new Widget instantiation is adequately covered.
* [ ] *New*: `tests/unit/test_hooks_provider.py`: Ensure Menu generation is adequately covered.
