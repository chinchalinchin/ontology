#### Refactor: Phase 05.05 - Main Menu & Saving

**Overview** 

The goal is to instantiate the Main Menu instantaneously before the main loop takes over, and establish the serialization logic for saving/loading game states. To achieve an instant UI render without the "blank screen" blocking, the Registry will be refactored to allocate VRAM on-demand, and the Orchestrator will implement a minimal `boot` state.

The Board will initialize empty, allowing the Main Menu to run immediately. World states will be hydrated dynamically via a `Migrator` object controlled by a Loading Menu, effectively achieving seamless scene transitions.

To achieve instantaneous Main Menu rendering, decouple *Schema Indexing* from *VRAM Allocation*, and introduce a minimal boot environment.

When the user selects "New Game", a `MainController` transitions the state, builds the `world-01` Board, and as the Screen renders the first frame of the world, the `Registry` lazily loads the required sprites and tiles. 

To avoid a frame-stutter on "New Game", implement a `registry.prewarm(assets)` method that runs while a loading screen is active.

**Schema**

```yaml
# --- DRAFT: MAIN MENU SCHEMA
menus:
  main:
    controller: display
    roots: 
      - id: neutral
        name: main-menu
        position:
          px: 0
          py: 0
        layout: stack
        alignment: center
        gap: 10
        children: 
          - instance: buttons
            id: label
            name: new-game
            bind: 
              selection: new
          - instance: buttons
            id: label
            name: load-game
            bind: 
              selection: load
          - instance: buttons
            id: label
            name: options-menu
            bind:
              selector: options
              selection: menu
          - instance: buttons
            id: label
            name: editor-menu
            bind:
              selector: editor
              selection: menu
# --- DRAFT: LOAD MENU SCHEMA
menus:
  load:
    controller: display
    roots: 
      - id: neutral
        name: main-menu
        position:
          px: 0
          py: 0
        layout: stack
        alignment: center
        gap: 10
        children: 
          - instance: meters
            id: health
            name: load-bar
            bind: 
              state: context.registry
```

#### Goal: Registry Lazy Loading

Decouple the *knowledge* of the assets (file paths and crop maps) from the *physical VRAM pointers* (`TexturePtr`), to achieve the following,

- **Instant Boot (On-Demand):** The Registry maps all the file paths and crop coordinates immediately but loads *nothing* into VRAM. When the Main Menu asks for a widget texture, the Registry loads it synchronously right then. Because it's only a few widgets, it takes less than a millisecond.
- **The "New Game" Prewarm:** When the player clicks "New Game", the MainController triggers a Loading Screen. The Engine calls a `registry.prewarm(time_budget_ms=10)` method every tick. The Registry loads as many textures as it can in 10 milliseconds, yields back to the Engine so the Engine can update the loading bar, and repeats until everything is loaded.

1. Change what `_cache` stores

Instead of calling `_load_image`, `_cache` should just build a dictionary of filepaths.

```python
    # New Hidden Field
    _filepaths: dict

    def _cache(self):
        """Recursively maps physical PNG and TTF filepaths without loading them."""
        asset_dir = str(settings.ASSET_DIR)
        self._filepaths = {}
        for root, _, files in os.walk(asset_dir):
            for file in files:
                asset_key = file[:-4]
                filepath = os.path.join(root, file)
                self._filepaths[asset_key] = filepath
```

2. Introduce `_get_or_load` handlers

Create safe accessors that check if a `TexturePtr` or `TTFFont` exists in memory. If it doesn't, load it synchronously and cache it.

```python
    def _get_or_load_texture(self, asset_key: str):
        if asset_key in self._textures:
            return self._textures[asset_key]
        
        filepath = self._filepaths.get(asset_key)
        if not filepath or not filepath.endswith('.png'):
            return None
            
        tex = self._load_image(asset_key, filepath)
        self._textures[asset_key] = tex
        return tex
```

3. Refactor `_index` to store IDs, not Pointers

Currently, `_index()` locks in the `TexturePtr` directly into the `_frames` tuple. If the texture hasn't been loaded yet, this fails. Change it so `_frames` stores the string `item_id`.

```python
    def _index(self):
        # ... (keep early loops the same) ...
                    
                    crop_map = frame_worker.index(item_id, item_props)
                    
                    for frame_key, crop in crop_map.items():
                        # Store the string item_id instead of self._textures[item_id]
                        self._frames[frame_key] = (
                            item_id, 
                            crop[0], crop[1], crop[2], crop[3]
                        )
```

4. Refactor `image()` to lazily evaluate

When the `Screen` calls `image(frame_key)`, the Registry looks up the crop map, sees the `item_id`, and passes it to the `_get_or_load` handler.

```python
    def image(self, frame_key: str) -> Tuple:
        """
        Returns a lightweight Python tuple resolving mapped texture configurations.
        Loads the texture into VRAM on-the-fly if it hasn't been cached yet.
        """
        # 1. Check if it's a cropped frame
        if frame_key in self._frames:
            item_id, sx, sy, sw, sl = self._frames[frame_key]
            tex = self._get_or_load_texture(item_id)
            if tex:
                return (tex, sx, sy, sw, sl)
            
        # 2. Check if it's a raw un-cropped asset
        if frame_key in self._filepaths:
            tex = self._get_or_load_texture(frame_key)
            if tex:
                return (tex, 0, 0, tex.w, tex.l)
            
        return None
```

5. Deferring `_stack()`

The `_stack()` method relies on composing two loaded textures together via `render.compose()`. Because assets are now lazy-loaded, `_stack()` cannot run during `__init__`.

Need to update `_get_or_load_texture()` to check if the requested `asset_key` has a `stack` property in `self.properties`. If it does, recursively call `_get_or_load_texture()` on the base and overlay images, composite them, and return the composited `TexturePtr`.

**Summary of the Flow**

1. The Engine boots.
2. The `Registry` initializes, parses the directory, and indexes `self._frames` in **less than 5 milliseconds**. VRAM is empty.
3. The Engine displays the Main Menu.
4. The `Screen` asks the Registry for the `button-idle` frame.
5. The Registry sees `button-idle` points to the `widgets` PNG. It loads `widgets.png` into VRAM synchronously, caches it, and returns the crop tuple.
6. The Main Menu appears perfectly. Boot time is near-instantaneous. No threading synchronization, race conditions, or SDL hardware crashes.

##### Goal: Asset Warming

**1. Main Menu Idle Prewarming (Background Loading)**

Start prewarming the moment the Main Menu is instantiated.

Because `MenuMechanics` calls the active Menu's `Controller.update()` every single tick, `MainController.update()` will execute the time-sliced loading.

During a typical frame on the Main Menu, the engine might take 2ms to process inputs and render the UI, leaving ~14ms of idle time before the next frame is due (assuming 60 FPS). Instead of sleeping, `MainController.update()` can call `registry.prewarm(time_budget_ms=5)`. The Registry will load 1 or 2 assets into VRAM, hit the 5ms budget limit, and yield back. The Main Menu remains responsive at 60 FPS while the game silently loads in the background.

**2. The Fast-Click Scenario & The Loading Menu**

Issue arises if the user clicks "New Game" before the background prewarm hits 100%. This is where the dedicated Loading Menu comes in.

When the user selects "New Game", the flow looks like this:

1. `MainController.select()` catches the event.
2. It pushes a `MenuEvent('loading')` to the Engine's bus.
3. The Engine pauses the Main Menu and pushes the Loading Menu onto the `board.menus` stack.
4. The Loading Menu is controlled by a `LoadingController`.

Because the `LoadingController` doesn't have to worry about user input, its `update()` method can allocate a much larger time budget to the Registry (e.g., `registry.prewarm(time_budget_ms=16)`).

**3. Binding the Loading Meter**

Since `Meter` widget aws designed to bind to live state functions, tying it to the `Registry`'s progress should require almost no new code.

When the Provider unpacks the Loading Menu, it injects the `Registry` into the context. The `Meter` binds directly to it:

```python
# Provider._unpack_meter() translation
reading_function = lambda: registry.current
unit_function = lambda: registry.maximum
```

As `LoadingController.update()` calls `registry.prewarm()`, `registry.loaded` increments. The Engine's `MenuMechanics` calls `MeterAnimation`, which evaluates the ratio, updates the crop-map for the filled frame, and the `Screen` renders the progressing bar.

When `loaded_count == total_count`, the `LoadingController` intercepts this in its `update()` loop, instructs the `Orchestrator` to build `world-01` (TODO: parameterize `<board-key>`), and fires a `TerminalEvent` to pop the menus and start the game.

**Summary**

To support both the background loading and the meter, the `Registry` needs a simple queue and counters:

```python
class Registry:
    # ...
    def _cache(self):
        # ... standard filepath walk ...
        self._pending_assets = list(self._filepaths.keys())
        self.maximum = len(self._pending_assets)
        self.current = 0

    def prewarm(self, budget_ms: int) -> bool:
        """
        Loads assets until the time budget is exhausted or queue is empty.
        Returns True if fully loaded, False otherwise.
        """
        import time
        start = time.perf_counter()
        
        while self._pending_assets:
            if (time.perf_counter() - start) * 1000 > budget_ms:
                return False
                
            asset_key = self._pending_assets.pop()
            self._get_or_load_texture(asset_key)
            self.loaded_count += 1
            
        return True
```

##### Goal: Asset Migration Decoupling

**1. The Engine Loop Termination**

In `engine.py`, game loop is currently governed by:

```python
while self.board.loaded:
```

If the `Board` initializes with `loaded = False`, `Engine.start()` will immediately exit the loop and terminate the application.

**The Fix:** Need a broader `self.running = True` flag for the Engine loop. `board.loaded` should instead be used as a gate inside `_play()` to completely bypass the `world` mechanics execution while the board is empty.

**2. The Screen Canvas Allocation Trap (Crucial)**

Look at `Screen.__init__` and `Screen._prerender`. The `Screen` dynamically calculates its bounding box (`boardsize`) based on the outermost `Tiles` and bakes a static hardware background (`bg_canvas`) in Cython *during initialization*.

If initializing the Engine with an empty Board, the `Screen` will allocate a `0x0` hardware texture. When `Migrator` later calls `board.add(assets)`, the assets will populate the database, but the `Screen`'s VRAM canvas will remain a `0x0` null-space.

**The Fix:** The `Migrator` must coordinate with the `Screens`. After the `Migrator` finishes injecting assets into the `Board`, it must iterate over `engine.screens` and call a new method, e.g., `screen.rebake(tiles, new_boardsize)`, which reallocates the Cython `TexturePtr` canvases and calls `construct()` with the newly loaded Tile primitives.

**3. Blocking the Loading Menu (Time-Slicing)**

If `LoadController.update()` calls `Migrator.migrate()` and that method is a single synchronous loop that builds 10,000 assets, the Python GIL will lock. The Engine will not hit its `_render()` phase, and the Loading Menu will freeze on screen at 0% until the entire board pops into existence at 100%.

**The Fix:** `Migrator.migrate()` must be a state machine or a Python generator (`yield`). `LoadController.update()` should call `migrator.step()` each frame. This allows the `Migrator` to instantiate a batch of assets, yield back to the Engine, and let the `Meter` update its progress visually.

**Summary**

1. **Boot:** `Orchestrator` initializes `Registry`, `Provider`, and an empty `Board`.
2. **Ignition:** `Engine.start()` runs. It immediately processes a hardcoded `MenuEvent('main')`.
3. **Trigger:** User clicks "New Game". `MainController` fires `StateEvent('world-01')`.
4. **Transition:** `Engine._drain` catches the event, pushes `MenuEvent('loading')`, and injects the `StateEvent` payload (`world-01`) into the `Migrator`.
5. **Hydration:** `LoadController.update()` calls `board.migrator.step()`. The Migrator yields progress back. The `Meter` widget visualizes this progress.
6. **Finalization:** When `Migrator` finishes, it calls `screen.rebake()`, sets `board.loaded = True`, and the `LoadController` fires a `TerminalEvent` to unpause the world.

##### Bugs

**1. The Primitive Binding Trap (`Provider._unpack_meter`)**

In `Provider._unpack_meter`, Meters are bound to live game state using string paths (e.g., `context.sprite.state.health`).

```python
resolved = self._resolve(cfg.bind.state, context)
reading_function = lambda r=resolved: (
    r.current if hasattr(r, 'current') else (r if isinstance(r, (int, float)) else 0)
)
```

- **The Bug:** Python integers are immutable. If `_resolve` evaluates the string path down to a primitive integer (e.g., `50`), `resolved` points to that static integer. The `lambda` captures this static value. When the Sprite takes damage and its health becomes `40`, the meter's `lambda` will forever return `50` because it closed over the value, not the reference.
- **The Fix:** `_resolve` must be updated to return a tuple of `(parent_object, attribute_name)`. The `reading_function` lambda must then dynamically call `getattr(parent_object, attribute_name)` on every tick to retrieve the live primitive value.
- **The Catch:** This exact same bug exists in `Provider._unpack_page` and `Provider._unpack_icon`.
- **The Fix:** `IconState` and `DisplayState` must be refactored to accept `Callable[[], str]` closures, exactly like the proposed fix for `MeterState`. `Provider._resolve` must return `(parent, attribute)`, and all Widget states must evaluate their bound properties dynamically on the fly.

**2. Height Sorting Crash (`Screen.draw`)**

In the Painter's Algorithm sorting logic:

```python
assets.sort(key=lambda a: (
    a.state.height if getattr(a.state, 'height', None) is not None else ...
```

- **The Bug:** The `AssetState` type definition allows `height` to be an `Optional[Union[int, str]]`. The documentation states that Compositions use late-binding string references like `"parent.depth"`. If the `Decomposer` fails to mutate that string into an absolute integer during board hydration, `Screen.draw` will receive a string. Python's `list.sort()` will crash with a `TypeError` when it attempts to compare a string height against an integer height.
- **The Fix:** Ensure the `Decomposer` strips all late-binding strings into integers during `Orchestrator.migrate`. Add a runtime guard in `Screen.draw` to cast or fallback if `type(height) is str`.

**3. The Stacking / Lazy-Loading Paradox**

Currently, `Registry._stack()` runs during `__init__`. It uses `render.compose()` to physically combine `TexturePtr` objects in VRAM (e.g., stacking a sword PNG over a player PNG).

* **The Flaw:** If `Registry._cache()` is refactored to only map string filepaths and defer VRAM loading, `_stack()` will crash because the base textures do not exist in VRAM yet.
* **The Fix:** Virtual "stacked" assets must be added to the `_filepaths` mapping as dependency graphs (e.g., `_filepaths['player-sword'] = ['player-base', 'sword-equip']`). When `_get_or_load_texture('player-sword')` is called, the Registry must recursively load the dependencies and execute the Cython `render.compose()` Just-In-Time (JIT).

##### Tasks

**BUG. Task: Provider Binding Trap (Universal Fix)**

*Objective*: Fix pass-by-value primitive traps across all UI Widgets.

- [ ] Subtask: Refactor `Provider._resolve()` to return a `(parent_object, property_name)` tuple instead of an evaluated primitive.
- [ ] Subtask: Update `MeterState`, `IconState`, and `DisplayState` to accept `Callable` closures instead of static primitives.
- [ ] Subtask: Refactor `Provider._unpack_meter`, `_unpack_icon`, and `_unpack_page` to generate `lambda: getattr(parent, prop)` closures.

**1. Task: Engine & Board Preparation**

*Objective*: Allow the Engine to tick while the Board is completely empty.

- [ ] Subtask: In `Engine`, replace `while self.board.loaded` with a generic `while self.running` loop condition.
- [ ] Subtask: In `Engine.__init__`, add `self.running = False`.
- [ ] Subtask: In `Engine.start()`, set `self.running = True`. Replace `while self.board.loaded` with `while self.running`.
- [ ] Subtask: Create `StateEvent(id: str)` to manage Board migration events.  `StateEvent` must be added to `events.py`. `Engine._drain()` must explicitly catch `StateEvent`, configure the `board.migrator.target = event.id`, and automatically append `MenuEvent('load')` to the bus to summon the loading screen.
- [ ] Subtask: In `Engine._drain()`, implement `StateEvent` catching: assign the event payload (`id`) to the `Migrator`, and append `MenuEvent('load')` to the bus.

**2. Task: Registry Lazy-Loading & JIT Stacking**

*Objective*: Decouple asset indexing from VRAM allocation for instant engine booting.
- [ ] Subtask: Refactor `Registry._cache()` to map filepaths to keys without invoking `IMG_LoadTexture`.
- [ ] Subtask: Refactor `Registry._index()` to store string `item_id`s in the `_frames` tuple instead of `TexturePtr`s.
- [ ] Subtask: Implement `Registry._get_or_load_texture(asset_key)`.
- [ ] Subtask: Refactor `Registry._stack()` logic. Instead of running at init, store stack recipes. Update `_get_or_load_texture` to recursively load and composite stack dependencies Just-In-Time.
- [ ] Subtask: Implement `Registry.prewarm(budget_ms: int)`. Use `time.perf_counter()` to load textures from a pending queue until the budget is exhausted. Maintain `loaded_count` and `maximum_count` for Meter bindings.

**3. Task: The Migrator Object**

*Objective*: Extract hydration logic from `Builder` into a state machine that yields execution.

- [ ] Subtask: Create `Migrator` class. Migrate the loop from `Builder.build_board()` into `Migrator.step()`.
- [ ] Subtask: Implement `Migrator.step(budget_ms: int)` to process a slice of the state YAML per tick, returning a boolean (`True` when complete).
- [ ] Subtask: Inject `Migrator` into `Board`. Add `board.loaded = False` to Board initialization.

**4. Task: Dynamic Screen Allocation (Memory Safe)**

*Objective*: Allow Cython canvases to resize safely between game states.

- [x] Subtask: In `libs.graphics.render.pyx`, expose a `destroy(TexturePtr)` function that explicitly calls `SDL_DestroyTexture` and nullifies the pointer.
- [x] Subtask: Implement `Screen.rebake(tiles, boardsize)`. It must call `render.destroy()` on existing canvases, allocate new ones via `render.canvas()`, and call `construct()`.

**5. Task: Menu Controllers (Main & Load)**

*Objective*: Orchestrate the transition from Boot -> Menu -> Gameplay.

- [ ] Subtask: Implement `MainController`. `select('new-game')` pushes `StateEvent('world-01')` to the bus.
- [ ] Subtask: Implement `LoadController`. In `update()`, call `registry.prewarm()` and `board.migrator.step()`. 
- [ ] Subtask: When `Migrator` and `Registry` both report 100%, `LoadController.update()` must call `screen.rebake()` on all active screens, set `board.loaded = True`, and emit a `TerminalEvent`.
- [ ] Subtask: In `Orchestrator.orchestrate()`, inject a `MenuEvent('main')` into the Engine bus immediately before calling `engine.start()`.

**6. Task: State Serialization (Saving)**

*Objective*: Dump runtime Board state to YAML.

- [ ] Subtask: Implement `Board.serialize()`. Iterate `_assets`, converting mutable `AssetState` dataclasses to dictionary structures. Exclude stateless assets (e.g., Widgets, Tiles, Equipment).
- [ ] Subtask: Write output to `/data/save/<slot>.yaml`.