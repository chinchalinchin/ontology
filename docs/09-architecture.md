# Ontology: Architecture

This section contains an in-depth presentation of the game engine's programmatic architecture.

## Initialization

1. **Bootstrapping & Loading (`Orchestrator.__init__`)**
    * Loads YAML files from the `assets/`, `data/config/`, and `data/state/` directories using Pydantic `TypeAdapters`.
    * Instantiates the [Decomposer](./03-compositions.md#decomposer) early as a singleton to track unique name increments for macro-generated assets.
2. **Cython Context Initialization (`render.init`)**
    * Initializes the underlying C-level SDL2 video, image, and typography subsystems before any textures are processed.
3. **Board Migration (`Orchestrator.migrate`)**
    * Resolves [Actions](./01-assets.md#asset-concepts) globally within [Properties](./01-assets.md#asset-hierarchy) to prevent redundant dictionary lookups during runtime.
    * Intercepts [Compositions](./03-compositions.md) defined in the state YAML, passing them to the [Decomposer](./03-compositions.md#decomposer) to unpack into a flat list of absolute-positioned Assets.
    * Iterates over all remaining state fields, applying the Entity-Component-System (ECS) pattern. Assets are injected with Frame, Animation, Properties, and State components via Factory [recipes](./appendices/01-schemas.md#configuration-recipes), and mapped accurately (e.g., Players inherit [Sprite](./02-sprites.md) properties).
    * Instantiates the [Board](./00-overview.md#board) database.
4. **Board Injection (`Orchestrator.inject`)**
    * Hydrates the input mappings and injects the [Device](./02-sprites.md#devices) (e.g., Keyboard) into the [Board](./00-overview.md#board).
    * Creates the SpawnableGroup and instantiates the Cradle, injecting both into the [Board](./00-overview.md#board) to allow Mechanics to generate temporary effects, projectiles, and struts at runtime.
5. **Registry Initialization (`Registry`)**
    * Recursively unboxes all Python `Enum` values into primitive strings/integers (`Orchestrator._unbox_enums`). Cython cannot natively parse Pydantic/Python Enums without significant GIL overhead.
    * Caches `.png` and `.ttf` files into GPU memory (`TexturePtr` and `TTFFont`).
    * Resolves Asset Stacks and generates strict index crop-maps for $O(1)$ frame lookups.
6. **Screen Allocation (`Screen`)**
    * Dynamically calculates the maximum width and length across all Board layers.
    * Instantiates a distinct [Screen](./00-overview.md#screen) object for *each* layer, generating independent background and foreground Cython canvases for the Painter's Algorithm.
7. **Mechanics & Menus (`Provider`)**
    * Instantiates [Mechanics](./05-mechanics.md) into two distinct lists: `core` and `world`.
    * Instantiates the [Provider](./06-widgets.md#provider) to handle runtime Widget unpacking.
    * Automatically generates the non-blocking Heads-Up Display (HUD) via the `view` Menu Configuration and mounts it to `board.overlays`.
8. **Ignition (`Engine.start`)**
    * Injects the fully hydrated Board, Screens, Mechanics, and Provider into the [Engine](./00-overview.md#engine) and initiates the fixed-timestep loop.

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

## Rendering

### Depth & Height

To accurately render perspective, the Screen `draw()` loop relies on a tuple-based sorting mechanism applied to all active Assets before they are passed across the Cython boundary. This system resolves the classic "Painter's Algorithm" dilemma where architectural decals (like Doors) need to render *on top of* their parent structures (like Strut), but *behind* dynamic entities (like Players) that walk in front of the building.

The rendering pipeline sorts Assets using a two-part tuple: `(Primary Key, Secondary Key)`

* **Primary Key: Height**: By default, an Asset's height is calculated dynamically using its Y-coordinate plus its physical length (`state.position.y + dimensions.l`). This ensures entities closer to the bottom of the screen are drawn last, appearing "in front" of objects higher up. 
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
* **Frame Rendering (`render`):** During the main game loop, `Screen.draw()` performs lightweight integer-based AABB camera culling natively in Python. This intentionally avoids paying the micro-transaction overhead of calling a Cython function repeatedly inside a massive Python loop. The visible assets are flattened into primitive integer tuples and passed across the C-boundary in a single list. `render()` clears the canvas buffer, copies the cropped background texture, stamps the active primitives, and finalizes the buffer in memory (`SDL_RenderPresent`), ready for extraction to disk.

**Memory Management**

The engine uses Cython extension types (`cdef class`) to bridge Python's garbage collector with SDL's manual memory management.

* **`TexturePtr`**: Wraps a raw `SDL_Texture*` pointer alongside its integer dimensions (`w`, `l`).
* **`TTFFont`**: Wraps a raw `TTF_Font*` pointer alongside its pre-configured styling metadata (`color`, `margins`, `align_str`).

Both classes implement the Cython `__dealloc__` method. When the Python interpreter garbage-collects these objects out of scope, they automatically invoke `SDL_DestroyTexture` and `TTF_CloseFont`. This architecture guarantees safe C-level memory cleanup and prevents VRAM leaks without requiring explicit teardown commands in the Python application layer.