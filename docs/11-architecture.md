# Ontology: Architecture

This section contains an in-depth presentation of the [Application's](./00-overview.md#application) architecture.

## Specifications

### Specification: Initialization

The engine utilizes a decoupled boot-and-hydrate lifecycle to achieve instantaneous menu rendering and non-blocking transitions. The general flow is shwon in the following diagram and detailed further in the following sections,

```mermaid
flowchart LR
    A[Orchestrator] --> B[Registry]
    B --> C[Engine]
    C --> D[MainMenu]
    D --> E[StateEvent]
    E --> F[Migrator]
    F --> G[LoadController]
    G --> H[Engine]
```

!!! important "Hardware Rendering Context Pre-requisites"
    When running in live (non-headless) mode, the hardware window context (`render.show()`) **must** be instantiated strictly *after* `render.init()` but *before* Registry initialization. 
    
    The Registry caches textures directly into GPU memory via Cython (`TexturePtr`). If the window context does not exist when the Registry attempts to index and load `.png` files, the textures will silently resolve as empty `0x0` null pointers. This results in a "ghost state" where the entire game board is invisible, but the Board database and Mechanic systems continue to operate normally.

#### Phase 1: Boot

1. **Bootstrapping**: Loads Configuration files via Pydantic TypeAdaptor, instantiates Service singletons, compiles [Executors](./05-mechanics.md#dependency-executors) and [Relations](./05-mechanics.md#dependency-relations)
2. **Cython**: Initializes SDL2 video, image, and typography subsystems.
3. **Registry**: Recursively parses the Asset directory, mapping file paths and generating crop-map indexes. *VRAM allocation is completely deferred.*
4. **Components**: Instantiates [Mechanics](./05-mechanics.md) and an empty [Board database](./00-overview.md#component-board). 
5. **Ignition**: The fixed-timestep loop begins. A [MenuEvent('main')](./06-widgets.md#events) is injected into the Engine bus prior to ignition to immediately render the [Main Menu](./06-widgets.md#menus).

#### Phase 2: Hydration

Triggered by a StateEvent (e.g., selecting "*New Game*" or "*Load*"), the Engine transitions into world generation without blocking the Python GIL.

1. **Generation**: The [LoadController](./06-widgets.md#controllers) calls the Migrator each frame. The Migrator applies calls the [Factory](./00-overview.md#service-factory) to generate batches of Assets from the State file, injecting Frame, Animation, Hitbox, Properties, and State components, then yields execution back to the Engine.
   *The StateSchema distinguishes between Physical Asset State (Assets requiring State, Frames, etc.) and World State. During hydration, the Migrator parses World State and assigns it to the Board.
2. **Prewarming**: Concurrently, the Registry parses a queue of keys, loading Asset files into memory within a time budget.
3. **Allocation**: Once hydration is complete, the Migrator triggers  all Screens to recalculate max dimensions and reallocate canvases for the Painter's Algorithm.
4. **Execution**: The LoadController emits a [TerminalEvent](./06-widgets.md#events), popping the loading screen, activating the Board, and unpausing the [World Mechanics](./05-mechanics.md#mechanics-world).

### Specification: Engine Loop

The Engine delegates behavior to [Mechanics](./05-mechanics.md). Rather than the [Engine](./00-overview.md#component-engine) passing arguments to a system, a Mechanic is responsible for querying the [Board](./00-overview.md#component=board) for the exact data it requires, processing the state, and optionally pushing Events to the Engine's Bus.

Mechanics are strictly segregated into `core` pipelines and `world` pipelines. The [Engine](./00-overview.md#component-engine) method processes these pipelines conditionally:

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

When a [MenuEvent](./06-widgets.md#events) fires and a modal Menu is pushed to the screen, the Board is paused. The Engine skips the World Mechanics loop entirely. The World freezes, but Core Mechanics continue ticking, allowing the User to navigate the Menu.

### Specification: Board Caches

#### Cache: Spatial Grid

To optimize environmental lookups without traversing linear asset arrays, the Board utilizes two discrete ($O(1)$) spatial hash grids managed by `BoardCaches`:

1. **Tile Spatial Grid (`tilemap`)**:

Partitions Tiles into spatial buckets. To prevent [Canopy Tiles](./01-assets.md#tile-canopy) from overwriting [Environ Tiles](./01-assets.md#tile-environ), buckets nest by layer and instance:

$$
\text{tilemap}[\text{layer}][\text{instance}][(c_x, c_y)] \to \text{Asset}
$$

2. **Hydrological Broad-Phase Grid**:

Indexes active Fluid streams, annular pools, and branching corridors into spatial buckets. Each bucket stores references to overlapping Fluids:

$$
\text{fluidmap}[\text{layer}][(c_x, c_y)] \to \text{List}[\text{Asset}]
$$

When asserting Fluid immersion, the Engine queries the bucket corresponding to the coordinate, then delegates to narrow-phase AABB segment validation.

### Specification: Graphics

#### Rendering: Sort

World rendering evaluates spatial geometry using discrete elevations, intra-elevation substrate planes, ground perspective, and coplanar priority:

$$
\text{sort_key}(A) = \Big(A.\text{elevation}, A.\text{substrate}, \text{ground_y}(A), A.\text{properties.priority}\Big)
$$

1. **Primary Key (`A.elevation` $\in \mathbb{Z}_{\ge 0}$)**: Discrete elevation (`0`, `1`, `2`, ...).
2. **Secondary Key (`A.substrate` $\in \mathbb{Z}_{\le 0}$)**: Intra-elevation rendering plane within $E$:
   * `Substrates.ENVIRON (-4)`: `tiles.environ`
   * `Substrates.FLUIDS (-3)`: `effects.fluids`
   * `Substrates.SURFACES (-2)`: `geography.shorelines`, `crafts.struts.floors`, `crafts.struts.paths`, `crafts.strtuts.flats`
   * `Substrates.OVERLAYS (-1)`: `crafts.bridges`, `crafts.stairs`, `objects.doors`, `crafts.struts.solids`, `crafts.struts.stripes`, `crafts.struts.designs`
   * `Substrates.STANDARD (0)`: All upright entities, walls, columns, enclosures, objects, and sheets.
3. **Tertiary Key (`ground_y` $\in \mathbb{Z}$)**: Geometric perspective offset by Anchor: $\text{ground_y} = \text{int}(A.\text{state.position.y} + A.\text{dimensions.l} + A.\text{state.anchor})$.
4. **Quaternary Key (`priority` $\in \mathbb{Z}$)**: Coplanar tie-breaker for Assets sharing an identical `(elevation, substrate, ground_y)` baseline.

#### Rendering: Typography

A Font configuration pairs a `.ttf` file with styling rules. During bootstrap, the Registry ingests each Font declared in `/src/assets/fonts/**/*.yaml`, storing them as styled Cython `TTFFont` wrappers. When `outline` is specified, the Registry instantiates a secondary internal outline pointer configured via `TTF_SetFontOutline`, enabling `render.write()` to execute two-pass blended rendering (outline pass followed by foreground fill) without runtime glyph cache invalidation.

In Menu hierarchies, Font are scoped lexically at the MenuPane level: any `font` declared on a parent pane cascades down to all child Widgets unless explicitly shadowed by a nested pane.

See [Library: Graphics](#library-graphics) for more implementation details.

**Properties: FontProperties**

* `size: int`: Point size used during glyph rasterization (defaults to `24`).
* `alignment: str`: Text alignment within the bounding box (`left`, `center`, `right`).
* `bold: bool`: Toggles `TTF_STYLE_BOLD`.
* `italics: bool`: Toggles `TTF_STYLE_ITALIC`.
* `underline: bool`: Toggles `TTF_STYLE_UNDERLINE`.
* `strikethrough: bool`: Toggles `TTF_STYLE_STRIKETHROUGH`.
* `margins: float`: Fractional padding applied to the target canvas bounds before wrapping (e.g., `0.05` for 5%).
* `color`: Primary glyph fill color.
    * `r: int` (0–255)
    * `g: int` (0–255)
    * `b: int` (0–255)
    * `a: int` (0–255)
* `outline`: (*Optional*) Border styling configuration.
    * `width: int`: Perimeter thickness in pixels (`outline > 0` enables two-pass rendering).
    * `color`:
        * `r: int` (0–255)
        * `g: int` (0–255)
        * `b: int` (0–255)
        * `a: int` (0–255)

**Required: Fonts**

* `dialogue`: Standard proportional font used to render NPC conversations and narrative logs.
* `menu`: High-contrast, styled font used for interactive UI controls and button labels.
* `title`: Large-format font used for menu headers and screen titles.

### Specification: Cython Libraries

While Python objects are fast enough for general logic, calculating collisions and processing rendering instructions for thousands of entities requires maximum performance. The engine uses Cython to bridge this gap, adhering to a **"Zero Heap Allocation in the Inner Loop"** philosophy to prevent frame stutters caused by the Python Garbage Collector.

!!! important
    Zero Heap Allocation is more of an ideal/driving principle than an enforced constraint. 

#### Library: Models

* Address `libs.core.models`

**Model: Position**

- `x: int`
- `y: int`

**Model: Dimensions**

* `w: int`
* `l: int`

**Model: Multiple**

* `nx: int`
* `ny: int`

**Model: Velocity**

* `vx: int`
* `vy: int`

**Model: Hitbox**

* `position: Position`
* `dimension Dimensions`

**ScreenPosition**:

* `px: double`
* `py: double`

#### Library: Math

* Address: `libs.core.math`

The engine leverages Cython for high-frequency mathematical, geometric, and physical calculations. To achieve maximum throughput, stateless operations are implemented as module-level `cpdef` and `cdef` functions within the `libs.core.math` package, avoiding the Virtual Method Table (vtable) overhead of class wrappers.

Spatial data (such as `Position`, `Velocity`, `Dimensions`, and `Hitbox`) are modeled as Cython Extension Types (`cdef class` in `libs.core.models`). This structure allows the engine to pass objects across the Python/C boundary while allowing C-level functions to access spatial properties (e.g., `pos.x`, `hb.dimensions.l`) natively without dictionary lookups.

The engine selectively manages the Global Interpreter Lock (GIL). Standard spatial routines retain the GIL to preserve reference counting and clean iteration syntax over Python collections. Performance-critical, loop-intensive mathematical routines—specifically RRT tree generation in `paths.pyx`—release the GIL (`nogil`) and execute entirely against contiguous C-allocated buffers.

##### Math: Geometry

* Address: `libs.core.math.geometry`

This module houses pure geometric evaluations, translating expensive Python float and distance calculations into C-level primitives.

* **`intersects`**: Calculates Axis-Aligned Bounding Box (AABB) intersections. Iterates through entity hitboxes, returning the overlapping tuple pair or `None`.
* **`onscreen`**: AABB camera culling check used by the renderer. Evaluates if an asset's absolute position intersects with the camera viewport.
* **`cone`**: A zero-allocation field-of-view check validating whether a target coordinate falls within a parameterized directional vision cone.
* **`nearby`**: Pure integer squared-distance check ($dx^2 + dy^2 < r^2$).
* **`punctures` / `c_punctures**`: A `noexcept nogil` implementation of the Liang-Barsky line clipping algorithm. Evaluates whether a line segment $(x_1, y_1) \to (x_2, y_2)$ penetrates the interior of an AABB obstacle with non-degenerate penetration depth ($u_1 < u_2 - \epsilon$).
* **`los`**: Raycasts a line-of-sight segment across a collection of primitive AABB tuples using `c_punctures`, returning `True` if clear and `False` if occluded.
* **`contours`**: Executes a two-pass Sweep-Line algorithm over primitive AABBs to dynamically generate map boundaries. Uses C-level interval merging and XOR symmetric differences to isolate exposed contour edges, returning boundary segments.
* **`bounded`**: Narrow-phase validation checking whether an asset's offset hitboxes intersect a raw mathematical boundary constraint.

##### Math: Paths

* Address: `libs.core.math.paths`

This module implements the Rapidly-exploring Random Tree (RRT) pathfinding algorithm in pure C memory.

* **Memory Management**: Ingests obstacle lists at function entry into a flat `RRTObstacle*` contiguous buffer and allocates an `RRTNode*` tree buffer sized to `max_iter + 2` via `malloc()`. Both buffers are freed synchronously via a `try...finally` block.
* **Tree Representation**: Nodes are represented as flat `RRTNode` structs containing coordinate values and an integer `parent_idx`, eliminating object pointer chasing and heap fragmentation.
* **Inner Loop (`nogil`)**: Releases the Python GIL during the exploratory phase. Executes 5% goal-biased continuous coordinate sampling, $O(N)$ nearest-neighbor distance minimization via `hypotf()`, fixed-distance trigonometric node steering via `atan2f()`, `cosf()`, and `sinf()`, and line-of-sight segment verification via `c_punctures`.
* **Path Reconstruction**: Re-acquires the GIL upon reaching the goal, traverses the `parent_idx` chain in reverse into an integer path buffer, and instantiates the final list of Python `Position` models. Returns an empty list if iterations expire without resolving a route.

##### Math: Space

* Address: `libs.core.math.space`

This module manages the broad-phase spatial partitioning grid.

* **Memory Management (`__init__`, `__dealloc__`)**: Manually allocates continuous blocks of system memory (`malloc`) for its `bucket_counts` and `bucket_data` arrays. Enforces safe teardown via `__dealloc__` calling `free()`, preventing memory leaks.
* **`clear`**: Resets the grid for the current frame by zeroing out the allocated memory block using C's `memset()`.
* **`insert` & `_hash**`: Maps 2D spatial coordinates to a 1D flat array. Assets intersecting cell boundaries are hashed into multiple buckets dynamically.
* **`query`**: Iterates through populated buckets and yields a list of unique `(id1, id2)` integer tuples, generating candidate pairs for narrow-phase evaluation.

##### Math: Physics

* Address: `libs.core.math.physics`

This module orchestrates the physical simulation, bridging the broad-phase grid with narrow-phase resolution, computing forces, and applying velocities to engine states.

* **`collisions`**: The collision pipeline. Ingests a flat list of primitive integer tuples to avoid Python object overhead:
    1. **Hash**: Inserts dynamic assets into the `Space` grid using physical dimensions.
    2. **Query**: Retrieves the reduced list of candidate pairs occupying the same spatial buckets.
    3. **Narrow Phase**: Pre-allocates dummy `Position` and `Dimensions` objects on the C-stack, unpacks candidate primitives, and evaluates overlaps via `geometry.intersects`. Returns verified colliding pairs.
* **`collide`**: Resolves confirmed physical overlaps, accounting for local `Hitbox` offsets:
    1. **Spatial Resolution**: Shifts overlapping entities apart based on inverse mass ratios (e.g., an $m=0$ wall absorbs 0% of the shift, forcing dynamic bodies out).
    2. **Momentum Transfer**: Evaluates 1D elastic collision formulas, updating the `.vx` and `.vy` attributes of participating `Velocity` objects. Kinematic assets bypass momentum transfer to retain immediate vector control.
* **`integrate`**: Executes Symplectic Euler Integration ($x_{n+1} = x_n + v_n \Delta t$). Maintains sub-pixel accumulators (`rx`, `ry`) to update discrete integer positions without drift.
* **`friction`**: Decays the magnitude of a `Velocity` vector over time using an environmental friction coefficient, clamping to $0.0$ to prevent negative overshoot.
* **`kinematics`**: Handles direct velocity assignment. Snaps non-input axes to zero and normalizes the resulting vector to the specified `speed`.
* **`dynamics`**: Calculates acceleration vectors towards a target coordinate (`tx`, `ty`) based on a given `impulse`. Clamps the resulting velocity to `speed` and snaps directly to the target velocity if within the arrival threshold to prevent oscillation.
* **`boundaries`**: Evaluates broad-phase and narrow-phase candidate collisions between dynamic assets and static environmental boundary hulls.
* **`constrain`**: Resolves spatial overlap and inverts velocity vectors for assets colliding with infinitely massive boundary hulls.

#### Library: Graphics

* Address: `libs.core.graphics`

The engine relies on a Cythonized bridge to C-level SDL2 bindings. To mitigate the overhead of crossing the Python-to-C boundary, the rendering pipeline does not pass heavy Python objects (like `SpriteState` or `Dimensions`) to the renderer. Instead, it extracts raw integers on the Python side and unpacks them cleanly onto the C-stack.

* **Context Initialization (`init`):** Sets up the SDL environment, including video, images, and typography (`SDL2_ttf`). If `headless`, a SDL software rendering context (`_renderer`) is bound to a master memory surface (`SDL_Surface`), bypassing window creation.
* **Asset & Font Allocation (`_load_image`, `_load_font`):** Loads physical image (`.png`) and font (`.ttf`) assets from disk into system memory, returning Cython wrappers (`TexturePtr` and `TTFFont`). To prevent styling overhead in the inner loop, fonts are pre-styled (bold, italics, RGBA color, margins) natively via SDL during ingestion using the YAML configuration properties.
* **Typography (`measure`, `write`):** The `measure` function queries the pixel dimensions of a string without allocating a rendering surface. The `write` function calculates wrapping bounds and alignment, rendering UTF-8 characters as a blended surface that is stamped  onto a target `TexturePtr`. This zero-allocation technique ensures typography does not generate memory garbage during the main game loop.
* **Background Compilation (`canvas` & `construct`):** A blank texture (`SDL_TEXTUREACCESS_TARGET`) is created in memory to match the full size of the Board. Python passes a single list of flattened integer tuples representing the source/destination coordinates and grid multipliers. Cython unpacks these primitives and executes`SDL_RenderCopy` calls natively via the C-level software rasterizer. This caches a unified map texture, eliminating the need to instantiate and re-render tiles every frame.
* **Buffer Management (`clear` & `present`):** `clear()` wipes the current VRAM buffer at the start of the frame, and `present()` finalizes the buffer (`SDL_RenderPresent`) while pumping SDL events at the end of the frame.
* **World Rendering (`render`):** During the main game loop, `Screen.draw()` performs lightweight integer-based AABB camera culling natively in Python. The visible world assets are flattened into primitive integer tuples and passed across the C-boundary in a single list. `render()` copies the cropped background texture and then maps world-coordinates to camera-relative coordinates on the fly, stamping the active primitives onto the back buffer.
* **Overlays (`superimpose`):** After the world is rendered, `Screen.interface()` passes a flattened list of active Menu and Widget primitives. `superimpose()` bypasses the camera offset logic, rendering these textures via strict absolute screen coordinates (`SDL_RenderCopy`) directly on top of the world view, ensuring Menus remain statically positioned.

**Memory Management**

The engine uses Cython extension types (`cdef class`) to bridge Python's garbage collector with SDL's manual memory management.

* **`TexturePtr`**: Wraps a raw `SDL_Texture*` pointer alongside its integer dimensions (`w`, `l`).
* **`TTFFont`**: Wraps a raw `TTF_Font*` pointer alongside its pre-configured styling metadata.

Both classes implement the Cython `__dealloc__` method. When the Python interpreter garbage-collects these objects out of scope, they automatically invoke `SDL_DestroyTexture` and `TTF_CloseFont`. This architecture guarantees safe C-level memory cleanup for standard assets and prevents VRAM leaks without requiring explicit teardown commands in the Python application layer.

While `__dealloc__` is sufficient for standard asset garbage collection, relying on Python's non-deterministic GC timing for massive VRAM allocations (e.g., the `Screen` background and foreground canvases) during scene transitions risks Out-Of-Memory (OOM) GPU crashes. 

To mitigate this, the Cython layer exposes a `render.destroy()` interface. During a world transition, `Screen.rebake()` explicitly calls this method to force an immediate, synchronous `SDL_DestroyTexture` on the old `TexturePtr` canvases before allocating the new environment's memory footprint.