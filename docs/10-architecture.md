# Ontology: Architecture

This section contains an in-depth presentation of the game engine's programmatic architecture.

## Initialization

The engine utilizes a decoupled boot-and-hydrate lifecycle to achieve instantaneous menu rendering and non-blocking scene transitions. The general flow is shwon in the following diagram and detailed further in the following sections,

```mermaid
flowchart LR
    A[Orchestrator Boot] --> B[Registry Indexes (No VRAM)]
    B --> C[Engine Starts (Empty Board)]
    C --> D[MainMenu]
    D --> E[StateEvent]
    E --> F[Migrator/Prewarm (Time-sliced)]
    F --> G[World Simulation]
```

!!! important "Hardware Rendering Context Pre-requisites"
    When running in live (non-headless) mode, the hardware window context (`render.show()`) **must** be instantiated strictly *after* `render.init()` but *before* `Registry` initialization. 
    
    The `Registry` caches textures directly into GPU memory via Cython (`TexturePtr`). If the window context does not exist when the Registry attempts to index and load `.png` files, the textures will silently resolve as empty `0x0` null pointers. This results in a "ghost state" where the entire game board is invisible, but the `Board` database, spatial physics, and collision systems continue to operate normally.

### Phase 1: Boot (Static Memory)

1. **Bootstrapping & Loading (`Orchestrator.__init__`)**: Loads configuration YAML files via Pydantic and instantiates the `Decomposer` singleton.
2. **Cython Context Initialization (`render.init`)**: Initializes SDL2 video, image, and typography subsystems.
3. **Registry Initialization (`Registry`)**: Recursively parses the asset directory, mapping file paths and generating crop-map indexes. **VRAM allocation is completely deferred.**
4. **Mechanics, Menus & Board (`Provider`)**: Instantiates `core` and `world` mechanics, the UI `Provider`, and an empty `Board` database initialized with `loaded = False`. 
5. **Ignition (`Engine.start`)**: The fixed-timestep loop begins. A `MenuEvent('main')` is injected into the Engine bus prior to ignition to immediately render the Main Menu.

### Phase 2: Hydration (Dynamic World Memory)

Triggered by a `StateEvent` (e.g., selecting "New Game" or "Load"), the Engine transitions into world generation without blocking the Python GIL.

1. **Time-Sliced Generation (`Migrator.step`)**: The `LoadController` calls the Migrator each frame. The Migrator applies the Entity-Component-System (ECS) pattern to a batch of assets from the state YAML, injecting Frame, Animation, Properties, and State components, then yields execution back to the Engine to maintain UI responsiveness.
2. **Asset Prewarming (`Registry.prewarm`)**: Concurrently, the Registry parses a queue of dependency string keys, loading `.png` and `.ttf` files into GPU memory (`TexturePtr`) within a strictly enforced millisecond time budget.
3. **Screen Allocation (`Screen.rebake`)**: Once hydration reaches 100%, the Migrator triggers `rebake()` on all active Screens to dynamically calculate max dimensions and allocate independent hardware canvases for the Painter's Algorithm.
4. **Execution**: The `LoadController` emits a `TerminalEvent`, popping the loading screen, setting `board.loaded = True`, and unpausing the `world` Mechanics.

## Mechanics

The Engine delegates behavior to [Mechanics](./05-mechanics.md). Rather than the Engine passing arguments to a system, a Mechanic is responsible for querying the [Board](./00-overview.md#board) for the exact data it requires, processing the state, and optionally pushing Events to the Engine's `bus`.

Mechanics are strictly segregated into `core` pipelines and `world` pipelines. The `Engine._play()` method processes these lists conditionally:

```python
def _play(self, delta) -> None:
    """
    Apply Mechanics.
    """
    for mechanic in self.core:
        mechanic.update(self.board, delta, self.bus)

    if not self.board.paused:
        for mechanic in self.world:
            mechanic.update(self.board, delta, self.bus)

```

* **Core Mechanics:** Systems that must execute every frame regardless of game state. This includes [MenuMechanics](./05-mechanics.md#core) (to process input and layout traversals), [AnimationMechanics](./05-mechanics.md#core) (to keep Assets animating), and RemoveMechanics (garbage collection).
* **World Mechanics:** Systems that govern gameplay logic, physics, and NPC behavior. This includes [MotionMechanics, CombatMechanics, and PlayerMechanics](./05-mechanics.md).

When a [MenuEvent](./06-widgets.md#events) fires and a modal Menu is pushed to the screen, `board.paused` evaluates to `True`. The Engine skips the `world` mechanics loop entirely. The world freezes, but `core` mechanics continue ticking, allowing the Player to navigate the menu while background torches remain animated without the risk of enemies moving or attacking.

## Maps

Maps associate ancillary Asset states to their final Animation state.

See [AnimationMap](./04-intentions.md#animationmap) and [DialogueMap](./04-intentions.md#dialoguemap) for more information.

The `AnimationMap` plays a crucial role in enforcing logical constraints. For example, `TransitionMechanics` and `PlayerMechanics` utilize `AnimationMap.action(state, equipment)` to resolve whether an intended action is possible. This guarantees that an `attack` intention will not translate into a `thrust` animation action if the Sprite currently lacks the required tool or weapon equipped in its inventory.

## Board

### Spatial Grid Caching

To optimize environmental queries during the high-frequency game loop, the Board implements an $O(1)$ spatial hashing grid (`_cached_tilemap`). The Board chunks static Assets into a dictionary grid during initialization, keyed by a fixed `TILE_HASH_SIZE` (defaulting to 32x32 pixels).

When systems like MotionMechanics need to compute the environmental friction acting on a moving Crate or Sprite, the Board divides the Asset's absolute `(x, y)` coordinates by the hash size to retrieve the exact Tile beneath it. 

!!! important
    The `_cached_tilemap` dictionary nests by `[layer][instance][(cx, cy)]` to prevent foreground architectural tiles from overwriting the background terrain tiles necessary for [MotionMechanics](./05-mechanics.md#spatial) friction lookups.
    
## Rendering

### Depth & Height

To accurately render perspective, the Screen `draw()` loop relies on a tuple-based sorting mechanism applied to all active Assets before they are passed across the Cython boundary. This system resolves the "Painter's Algorithm" dilemma where architectural decals (like Doors) need to render *on top of* their parent structures (like Strut), but *behind* dynamic Asset (like Players) that walk in front of the building.

The rendering pipeline sorts Assets using a two-part tuple: `(Primary Key, Secondary Key)`

* **Primary Key: Height**: By default, an Asset's height is calculated dynamically using its Y-coordinate plus its physical length (`state.position.y + dimensions.l`). This ensures Assets closer to the bottom of the screen are drawn last, appearing "in front" of objects higher up. 
    * **The Height Override:** Assets can optionally declare an explicit `state.height`. When present, this value bypasses the geometric calculation entirely. This is heavily utilized by Compositions via late-binding (e.g., `bind(parent.depth)`), forcing Component assets like Doors or Chests to occupy the exact same spatial "slice" as the wall to which they are attached.
* **Secondary Key: Depth** If two Assets share the exact same height (either by coincidence or by explicit binding), the engine falls back to `state.depth` as a tie-breaker. All standard Assets default to `depth: 0`.
    *   **Decal Rendering:** By assigning a component (like a Door) an explicit depth matching its parent Strut, and elevating its `z` index (e.g., `z: 1`), the engine guarantees the Door will always paint directly on top of the Strut, while both objects will collectively sort correctly against a Player walking in front of or behind them.

## Cython

While Python objects are fast enough for general logic, calculating collisions and processing rendering instructions for thousands of entities requires maximum performance. The engine strategically uses Cython to bridge this gap, adhering to a strict **"Zero Heap Allocation in the Inner Loop"** philosophy to prevent frame stutters caused by the Python Garbage Collector.

!!! important
    Zero Heap Allocation is more of an ideal/driving principle than an enforced constraint. 

### Models

- `libs/core/models.pyx`

- Position: 
    - `x: int`
    - `y: int`
- Dimensions:
    - `w: int`
    - `l: int`
- Multiple:
    - `nx: int`
    - `ny: int`
- Velocity:
    - `vx: int`
    - `vy: int`
- Hitbox:
    - `position: Position`
    -` dimension Dimensions`
- ScreenPosition:
    - `px: double`
    - `py: double`

### Math

- `libs/core/math.pyx`

Spatial data like are modeled as Cython Extension Types (`cdef class` in `.pxd` definition files). This structure allows geometry methods like `Geometry.intersects` to access spatial properties (e.g., `position.x`, `hb.dimensions.l`) natively at C-speeds.

The engine explicitly retains the Global Interpreter Lock (GIL) during geometry calculations. This safely manages Python reference counts and preserves readable, Pythonic syntax (like `for hb in hitboxes`), while executing the actual mathematical overlap checks inline using primitive C variables on the CPU stack.

**Collisions**

At the start of every collision, the physics pipeline executes a spatial hashing procedure, given in the following sequence:

1. **Hash (Populate the Grid)**: Maintain a 1D array or hash map (dictionary) where the keys are the `(cell_x, cell_y)` tuples, and the values are lists of integer Asset IDs. Iterate over all dynamic Assets exactly once (`O(N)`). For each Asset, calculate its cell using integer division and append its ID to that cell's list.(Note: If an Asset overlaps a cell boundary, insert it into all cells it touches. This is easily calculated using its width and length divided by the cell size).
2. **Query (Generate Candidate Pairs)**: Iterate over the populated cells. For each cell, look at the list of Asset IDs inside the grid. Only generate collision pairs for Assets that exist in the same cell.
3. **Narrow Phase (Raw Intersection)**: Pass this much smaller list of candidate pairs into `Geometry.intersects`.

The grid's blueprint (`cdef class Space`) is defined in the Cython math library.

### SDL

The engine relies on a Cythonized bridge to C-level SDL2 bindings. To mitigate the overhead of crossing the Python-to-C boundary, the rendering pipeline does not pass heavy Python objects (like `SpriteState` or `Dimensions`) to the renderer. Instead, it extracts raw integers on the Python side and unpacks them cleanly onto the C-stack.

* **Context Initialization (`init`):** Sets up the SDL environment, including video, images, and typography (`SDL2_ttf`). If `headless`, a SDL software rendering context (`_renderer`) is bound directly to a master memory surface (`SDL_Surface`), completely bypassing window creation.
* **Asset & Font Allocation (`_load_image`, `_load_font`):** Loads physical image (`.png`) and font (`.ttf`) assets from disk directly into system memory, returning safe, reference-counted Cython wrappers (`TexturePtr` and `TTFFont`). To prevent styling overhead in the inner loop, fonts are pre-styled (bold, italics, RGBA color, margins) natively via SDL during ingestion using the YAML configuration properties.
* **Typography (`measure`, `write`):** The `measure` function queries the exact pixel dimensions of a string without allocating a rendering surface. The `write` function calculates wrapping bounds and alignment, rendering UTF-8 characters as a blended surface that is permanently stamped (baked) directly onto a target `TexturePtr`. This zero-allocation technique ensures typography does not generate memory garbage during the main game loop.
* **Background Compilation (`canvas` & `construct`):** A blank texture (`SDL_TEXTUREACCESS_TARGET`) is created in memory to match the full size of the Board. Python passes a single list of flattened integer tuples representing the source/destination coordinates and grid multipliers. Cython unpacks these primitives and executes thousands of `SDL_RenderCopy` calls natively via the C-level software rasterizer. This caches a unified map texture, eliminating the need to instantiate and re-render thousands of background tiles every frame.
* **Buffer Management (`clear` & `present`):** Extracted from the core drawing loop to support multi-phase rendering. `clear()` wipes the current VRAM buffer at the start of the frame, and `present()` finalizes the buffer (`SDL_RenderPresent`) while pumping SDL events at the end of the frame.
* **World Rendering (`render`):** During the main game loop, `Screen.draw()` performs lightweight integer-based AABB camera culling natively in Python. The visible world assets are flattened into primitive integer tuples and passed across the C-boundary in a single list. `render()` copies the cropped background texture and then maps world-coordinates to camera-relative coordinates on the fly, stamping the active primitives onto the back buffer.
* **Overlays (`superimpose`):** After the world is rendered, `Screen.interface()` passes a flattened list of active Menu and Widget primitives. `superimpose()` bypasses the camera offset logic entirely, rendering these textures via strict absolute screen coordinates (`SDL_RenderCopy`) directly on top of the world view, ensuring the HUD and Menus remain statically positioned on the glass.

**Memory Management**

The engine uses Cython extension types (`cdef class`) to bridge Python's garbage collector with SDL's manual memory management.

* **`TexturePtr`**: Wraps a raw `SDL_Texture*` pointer alongside its integer dimensions (`w`, `l`).
* **`TTFFont`**: Wraps a raw `TTF_Font*` pointer alongside its pre-configured styling metadata.

Both classes implement the Cython `__dealloc__` method. When the Python interpreter garbage-collects these objects out of scope, they automatically invoke `SDL_DestroyTexture` and `TTF_CloseFont`. This architecture guarantees safe C-level memory cleanup for standard assets and prevents VRAM leaks without requiring explicit teardown commands in the Python application layer.

While `__dealloc__` is sufficient for standard asset garbage collection, relying on Python's non-deterministic GC timing for massive VRAM allocations (e.g., the `Screen` background and foreground canvases) during scene transitions risks Out-Of-Memory (OOM) GPU crashes. 

To mitigate this, the Cython layer exposes a `render.destroy()` interface. During a world transition, `Screen.rebake()` explicitly calls this method to force an immediate, synchronous `SDL_DestroyTexture` on the old `TexturePtr` canvases before allocating the new environment's memory footprint.