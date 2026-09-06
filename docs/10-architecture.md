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
   - The StateSchema distinguishes between Physical Assets (Assets requiring state, frames, and logic, such as Tiles or Sprites) and World Metadata (abstract governing states, such as the current Plot). During hydration, the Migrator parses World Metadata instantly ($O(1)$) and assigns it directly to the Board, explicitly bypassing the time-sliced ECS component injection loop reserved for Physical Assets.
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

- `libs/core/math/geometry.pyx`
- `libs/core/math/physics.pyx`
- `libs/core/math/space.pyx`

The engine leverages Cython for high-frequency mathematical, geometric, and physical calculations. To achieve maximum throughput, stateless operations are implemented as module-level `cpdef` functions within the `libs.core.math` package, completely avoiding the Virtual Method Table (vtable) overhead of class wrappers.

Spatial data (such as `Position`, `Velocity`, `Dimensions`, and `Hitbox`) are modeled as Cython Extension Types (`cdef class` in `libs.core.models`). This structure allows the engine to pass objects across the boundary while allowing C-level functions to access spatial properties (e.g., `pos.x`, `hb.dimensions.l`) natively without falling back to slow Python dictionary lookups.

The engine explicitly retains the Global Interpreter Lock (GIL) during math calculations. This safely manages Python reference counts and preserves readable, Pythonic syntax when iterating over collections (e.g., `for hb in hitboxes`), while executing the actual arithmetic inline using primitive C variables (`int`, `double`) on the CPU stack.

**Geometry (`libs/core/math/geometry.pyx`)**

This module houses pure geometric evaluations, translating expensive Python float and distance mathematics into C-level primitives.

* **`intersects`**: Calculates Axis-Aligned Bounding Box (AABB) intersections. It iterates through an entity's hitboxes, explicitly typecasting them (`<Hitbox>item`) to enforce C-struct memory layouts, returning the overlapping tuple pair or `None`.
* **`onscreen`**: A fast AABB camera culling check used by the renderer. Evaluates if an asset's absolute position intersects with the camera's viewport by calculating bounds entirely via C integers.
* **`cone`**: A zero-allocation field-of-view check. Bypasses Python's `math` module overhead by utilizing C's `<math.h>` to compute Euclidean magnitude and orthogonal dot products (`dx * ux + dy * uy`). Validates if a target falls within a parameterized directional vision cone.
* **`nearby`**: A pure integer squared-distance check (`dx*dx + dy*dy < r*r`). Replacing Python-side radial evaluations prevents the continuous creation and destruction of intermediate boolean and float objects during environment scans.

**Space (`libs/core/math/space.pyx`)**

This module manages the broad-phase spatial partitioning grid, reducing collision detection complexity from $O(N^2)$ to $O(N)$ for local clusters.

* **Memory Management (`__init__`, `__dealloc__`)**: Unlike standard Python objects, `Space` manually allocates continuous blocks of system memory (`malloc`) for its `bucket_counts` and `bucket_data` arrays. It enforces safe teardown via `__dealloc__` calling `free()`, preventing memory leaks when the grid is garbage collected.
* **`clear`**: Resets the grid for the current frame by zeroing out the allocated memory block using C's `memset()`.
* **`insert` & `_hash**`: Maps 2D spatial coordinates to a 1D flat array. Assets intersecting cell boundaries are hashed into multiple buckets dynamically.
* **`query`**: Iterates through the populated buckets and yields a list of unique `(id1, id2)` integer tuples, generating candidate pairs for the narrow-phase evaluation.

**Physics (`libs/core/math/physics.pyx`)**

This module orchestrates the physical simulation, bridging the broad-phase grid with narrow-phase resolution and applying forces to engine states.

* **`collisions`**: The master collision pipeline. It ingests a flat list of primitive integer tuples to avoid Python object overhead. The sequence executes as follows:
    1. **Hash**: Iterates over all dynamic assets and inserts them into the `Space` grid using their bounding boxes.
    2. **Query**: Retrieves the reduced list of candidate pairs occupying the same spatial buckets.
    3. **Narrow Phase**: Pre-allocates dummy `Position` and `Dimensions` objects on the C-stack. Iterates through the candidate pairs, unpacking their primitives into the dummy objects, and passes them to `geometry.intersects`. Returns verified colliding pairs.
* **`collide`**: Resolves confirmed physical overlaps.
    1. **Spatial Resolution**: Shifts overlapping entities apart based on inverse mass ratios (e.g., an $m=0$ wall absorbs 0% of the shift, forcing the dynamic asset out).
    2. **Momentum Transfer**: Evaluates 1D elastic collision formulas, updating the `.vx` and `.vy` attributes of the participating `Velocity` objects. Kinematic assets (like the Player) bypass the momentum transfer, retaining immediate control over their vectors.
* **`integrate`**: Executes Symplectic Euler Integration ($x_{n+1} = x_n + v_n \Delta t$). Because the game board utilizes integer grid coordinates, this function maintains sub-pixel accumulators (`rx`, `ry`). When an accumulator exceeds `1.0` or `-1.0`, it casts the shift to an integer, updates the physical `Position`, and decrements the accumulator.

### Graphics

- `libs/core/graphics.pyx`

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