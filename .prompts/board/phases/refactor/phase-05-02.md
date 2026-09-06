#### Refactor: Phase 05.02 - Simplification & Cleanup

**Overview** 

With the introduction of Widgets and Mechanics, the application architecture needs to be re-evaluated to see if any simplification can be introduced.

!!! "definition"
    Simplification = Simple, readable patterns

In addition, look for redundancies in data structures or logical flows that have materialized as the application has taken shape. Ensure there are no "dead-ends" or "cul-de-sacs" in the code. Ensure everything has a purpose, is well-documented and makes senses.

##### Goal

**Target View (HUD) Schema**

```yaml
  view:
    controller: display
    roots: 
      - id: dark-small
        name: hud-menu
        position:
          px: 0.1
          py: 0.75
        layout: row
        alignment: start
        gap: 10
        margins: 15
        children: 
          - id: transparent-block
            name: hud-meters-pane
            layout: stack
            alignment: center
            gap: 5
            children: 
              - instance: meters
                id: health
                name: health-meter
                bind: 
                  state: context.sprite.state.meters.health
              - instance: meters
                id: magic
                name: magic-meter
                bind: 
                  state: context.sprite.state.meters.magic
          - id: transparent-block
            name: hud-slots-pane
            layout: dock
            alignment: start
            gap: 5
            children:
              # --- NEW: The mathematical bounding box for the Slot ---
              - id: transparent-slot 
                name: weapon-slot-container
                layout: overlay
                alignment: center
                gap: 0
                children:
                  # 1. The Background
                  - instance: buttons
                    id: slot
                    name: weapon-slot
                    status: disabled
                  # 2. The Foreground Decal
                  - instance: icons
                    id: items-sheet 
                    name: weapon-icon
                    bind:
                      state: context.sprite.state.inventory.equipment.weapon
              # --- NEW: The mathematical bounding box for the Shield ---
              - id: transparent-slot
                name: shield-slot-container
                layout: overlay
                alignment: center
                gap: 0
                children:
                  - instance: buttons
                    id: slot
                    name: shield-slot
                    status: disabled
                  - instance: icons
                    id: items-sheet
                    name: shield-icon
                    bind:
                      state: context.sprite.state.inventory.equipment.shield

```

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

* [x] Move `board.paused = True` inside the conditional configuration check in `Engine._drain()` to prevent UI soft-locks.

**Task #4: Spatial Cache Integrity**

**Location:** `app.game.board.Board._cache`
**The Problem:** The `_cached_tilemap` is used for $O(1)$ friction lookups by `MotionMechanics`. However, it is structured as `self._cached_tilemap[layer][(cx, cy)] = asset`. If a `Fore` Tile (like a canopy) and a `Back` Tile (like ice) occupy the same cell, the last one processed overwrites the cell key. If the `Fore` tile overwrites the ice tile, the physics engine will query the canopy's friction instead of the ice's friction.
**The Fix:** The tilemap cache should either store a `List[Asset]` per cell, or it should specifically partition by instance (`Back` vs. `Fore`), allowing physics to query `Back` tiles exclusively for ground friction.

* [x] Update `Board._cached_tilemap` to segregate `AssetInstances.BACK` and `AssetInstances.FORE`.
* [x] Update `Board.tile()` interface to accept an optional `instance` argument, defaulting to `BACK` for friction queries.

**Task #5: Page Widget Consolidation**

* [x] Remove `List[str]` support from `DisplayState.content`. Restrict `Page` widgets to strings/typography exclusively.
* [x] Remove the `text: bool` flag from `DisplayState`.

**Task #6 (CLOSED): Automatic Decal Centering**

!!! "CLOSED"
    Implemented. Determined to break Meter frames due to their use of dual frames. Mixing of responsibilities between the Screen and Layout. Layout should handle all alignment calculations. Icons promoted to first-class Widgets. Infinite Pane recursion implemented in Provider. Utilize nested overlay Panes to render icons on top of Buttons instead of calculating in the Screen.

* [!] Implement `IndexFrame` so Icons gets indexed by the Registry.
* [!] Modify `Screen.interface()` in `app/game/screen.py`.
* [!] When iterating over the `frame_keys` returned by canvas-less widgets, apply centering logic for any key after the first index (`i > 0`).
* [!] *Math:* `dx = widget.state.position.x + (widget.dimensions.w - sw) // 2`

**Task #7: Provider Unpacking for Standalone Icons**

* [x] In `Provider._unpack_widget()`, implement the block for `cfg.instance == AssetInstances.ICONS`.
* [x] Instantiate an `IconState` with a default `frame` (either hardcoded to the first string in `properties.frames` or derived from `cfg.bind`).
* [x] Ensure `IndexFrame` is correctly assigned via the `WidgetRecipe`.
* [x] Create the `ICONS` unpacker block in `Provider._unpack_widget()`.
* [x] Ensure `IndexFrame` correctly translates `IconState.icon` strings into indexed `Registry` crop-maps.

**Task #8: Implement the `OVERLAY` Layout Engine**

* [x] Remove `ROW`, `COLUMN`, and `TAB` from the `Layouts` Enum.
* [x] Update all Menu YAML configurations to replace `row` with `dock`, `column` with `stack`, and `tab` with `overlay`.
* [x] Add `OVERLAY` to the `Layouts` enum.
* [x] In `Layout`, rename `_layout_tab` to `_layout_overlay`.
* [x] In `Layout`, implement `_layout_overlay(pane, children)`.
* *Algorithm:* Center all children on the Pane's anchor. If the Pane is 40x40, and the child is 24x24, `offset = (40 - 24) // 2 = 8`. Add the offset to the absolute coordinates.(if `CENTER`, calculate width/length deltas between the pane and the child to find the centered `Position`).

**Task #9: Isolate Controls from Decals**

* [x] Remove the `icons` attribute from `app.models.state.TraversalState`.
* [x] Update `TraversalFrame.keys()` to return only the button status.
* [x] Strip the Icon binding logic from the `BUTTONS` unpacker in `Provider._unpack_widget()`.

**Task #10: Update Schemas & Documentation**

* [x] Update `menus/main.yaml` to utilize the `OVERLAY` Pane wrapping for all HUD and Inventory slots.
* [x] Add `transparent-slot` (w: 40, l: 40) to `properties/widgets.yaml`.
* [x] Update `06-widgets.md` to formally allow deep Menu tree nesting and define the `OVERLAY` layout.
* [~] Add the `InventoryController`, `DialogueController`, and `ViewController` to the list of defined implementations, noting their distinct responsibilities for mutating `board` state versus routing UI interactions.
