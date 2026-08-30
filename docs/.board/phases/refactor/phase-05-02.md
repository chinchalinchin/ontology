#### Refactor: Phase 05.02 - Simplification & Cleanup

**Overview** 

With the introduction of Widgets and Mechanics, the application architecture needs to be re-evaluated to see if any simplification can be introduced.

!!! "definition"
    Simplification = Simple, readable patterns

In addition, look for redundancies in data structures or logical flows that have materialized as the application has taken shape. Ensure there are no "dead-ends" or "cul-de-sacs" in the code. Ensure everything has a purpose, is well-documented and makes senses.

##### Tasks

**Task #1: Centralize Input Polling**

*Objective*: Prevent `_last_state` mutation bugs during the game loop.

- [x] Remove `board.device.poll()` from all individual `Mechanic` implementations. 
- [x] Update `Engine._play()` to call `poll()` once per tick and pass the `DevicePayload` alongside the `bus` to the Mechanics interface.

**Task #2: Decompose the Orchestrator**

*Objective*: Decompose the GOD object into its constitutent functions.

- [x] Create an `Context` dataclass to pass along the assembly line.
    * **Holds:** `properties`, `state`, `configurations`, `device_mapping`, and `screensize`.
- [x] Move `Decomposer`, `Provider`, and `Cradle` into the new `app.services.generators` package.
    - [x] Update their constructors to accept only the specific properties and recipes they need from the `Context`, rather than the whole schema.
- [x] Create an `Builder` class that breaks the `Orchestrator`'s monolithic `init()`, `migrate()`, and `inject()` methods into discrete, single-responsibility steps.
    - [x] `load_data(state_key)`: Wraps the `Loader` logic and populates the `EngineContext`.
    - [x] `init_subsystems(screensize, headless)`: Calls `render.init()` to boot the SDL/Cython backend.
    - [x] `build_registry()`: Unboxes Enums and instantiates the `Registry`, caching the fonts and textures.
    - [x] `build_board()`: Uses the `Decomposer` to unpack Compositions, applies the ECS property mappings, and instantiates the `Board`.
    - [x]  `build_services(device)`: Instantiates the `Cradle`, Device mapping, and assigns them to the `Board`.
    - [x] `build_pipeline()`: Instantiates the `Provider`, creates the `screens`, and resolves the `core` and `world` Mechanics lists.
    - [x] `get_engine()`: Injects all the built components into the final `Engine` object and returns it.
- [x] Implement the Director
    - [x] The Director takes the Builder as an argument and executes the steps in the exact sequence required.
    - [x] This removes all sequence-enforcement logic from the construction classes.

**Task #3: Engine Routing Safety**

**Location:** `app.game.engine.Engine._drain`
**The Problem:** When processing a `MenuEvent`, the Engine immediately flags `self.board.paused = True`. It then attempts to look up the `menu_cfg`. If the event passes an invalid `id` (or if the configuration is missing), the `if menu_cfg:` block is skipped, the menu is never appended, and the board remains paused *forever*.
**The Fix:** The `self.board.paused = True` assignment must be moved *inside* the successful `if menu_cfg:` block, directly before or after appending to the stack.

* [ ] Move `board.paused = True` inside the conditional configuration check in `Engine._drain()` to prevent UI soft-locks.

**Task #4: Spatial Cache Integrity**

**Location:** `app.game.board.Board._cache`
**The Problem:** The `_cached_tilemap` is used for $O(1)$ friction lookups by `MotionMechanics`. However, it is structured as `self._cached_tilemap[layer][(cx, cy)] = asset`. If a `Fore` Tile (like a canopy) and a `Back` Tile (like ice) occupy the same cell, the last one processed overwrites the cell key. If the `Fore` tile overwrites the ice tile, the physics engine will query the canopy's friction instead of the ice's friction.
**The Fix:** The tilemap cache should either store a `List[Asset]` per cell, or it should specifically partition by instance (`Back` vs. `Fore`), allowing physics to query `Back` tiles exclusively for ground friction.

* [ ] Update `Board._cached_tilemap` to segregate `AssetInstances.BACK` and `AssetInstances.FORE`.
* [ ] Update `Board.tile()` interface to accept an optional `instance` argument, defaulting to `BACK` for friction queries.

**Task #5: Page Widget Consolidation**

**Location:** `app.services.generators.provider.Provider._unpack_widget`
**The Problem:** The `Page` widget state model allows `content` to be either `str` (text) or `List[str]` (icons). However, the Provider's `_paginate` method assumes the input is always a string and attempts to calculate line breaks via `split(' ')` and `render.measure()`. If a list of icon keys is passed, this will crash.
**The Fix:** `Pages` should probably be strictly reserved for typography and Dialogue (`str`). If the UI needs to render a grid of icons (like an inventory grid), that should be handled by a nested `Pane` with a `Dock` layout and `Button` children, leveraging the layout engine rather than forcing an image array into a text-pagination algorithm.

* [ ] Remove `List[str]` support from `DisplayState.content`. Restrict `Page` widgets to strings/typography exclusively.
* [ ] Remove the `text: bool` flag from `DisplayState`.

**Task #6: Automatic Decal Centering**

* [ ] Implement `IndexFrame` so Icons gets indexed by the Registry.
* [ ] Modify `Screen.interface()` in `app/game/screen.py`.
* [ ] When iterating over the `frame_keys` returned by canvas-less widgets, apply centering logic for any key after the first index (`i > 0`).
* [ ] *Math:* `dx = widget.state.position.x + (widget.dimensions.w - sw) // 2`


**Task #7: Provider Unpacking for Standalone Icons**

* [ ] In `Provider._unpack_widget()`, implement the block for `cfg.instance == AssetInstances.ICONS`.
* [ ] Instantiate an `IconState` with a default `frame` (either hardcoded to the first string in `properties.frames` or derived from `cfg.bind`).
* [ ] Ensure `IndexFrame` is correctly assigned via the `WidgetRecipe`.


**Task #8: Bindings for Embedded Button Icons**

* [ ] Update `Provider._unpack_widget()` for `BUTTONS`.
* [ ] If the `MenuWidget` configuration specifies a binding, set up a dynamic lambda or initialization for `TraversalState.icons`.
* [ ] *(Note: Unlike text which is static, the Controller will handle mutating this list when inventory changes, but it needs an initial state on boot).*
















---

## III. Documentation Updates

To ensure the documentation accurately reflects these architectural clarifications, the following updates are recommended:

1. **Ontology: Widgets (`06-widgets.md`)**
* **Pages Section:** Explicitly state that `Pages` are strictly for Typography and text pagination via the Cython `measure` bindings. Note that grids of images/items are constructed using `MenuPane` layouts containing `Buttons` and `Icons`, *not* `Pages`.
* **Controllers Section:** Add the `InventoryController`, `DialogueController`, and `ViewController` to the list of defined implementations, noting their distinct responsibilities for mutating `board` state versus routing UI interactions.


2. **Ontology: Architecture (`09-architecture.md`)**
* **Spatial Grid Caching Section:** Note that the `_cached_tilemap` dictionary nests by `[layer][instance][(cx, cy)]` to prevent foreground architectural tiles from overwriting the background terrain tiles necessary for `MotionMechanics` friction lookups.