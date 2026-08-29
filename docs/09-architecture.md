# Ontology: Architecture

This section contains an in-depth presentation of the game engine's programmatic architecture.

## Initialization

1. Entrypoint: `Orchestrate`
    * Load data into memory
        - Load (Image) Asset Recipes YAML File from `/src/assets/main.yaml`
        - Load (Image and Font) Asset Category properties YAML files from `/src/assets/<category>/main.yaml`
        - Load (Image) Asset Instance state YAML files from the `/src/data/state/<board-key>` directory, where `<board-key>` is the selected board. There may be an arbitrary number of state files, with any filename, in the `<board-key>` directory.
        - Validate all data models against Pydantic TypeAdapters and convert into Plain-Old-Python-Objects (POPOs) and Cython `cdef classes` for runtime use.
        - Initialize list of (Image) Asset, injecting (Frame, Animation, Properties, State) components using Asset Recipes in concert with Asset Taxonomy (Category, Instance, ID).
        - Initialize Font Assets with configured Styles. 
    * Construct application components and manage dependency-injections (Cradle, Decomposer, etc.)
2. Init: `Registry`
    * Load Assets into memory
        - Recursively load `/src/assets/**/*.png`, `/src/assets/**/*.tff`
            - For image Assets, create a map using the key-values `<registry-key>: <frame>`, where `<registry-key>` is calculated according to the Frame schema.
            - For font Assets, create a map using the key-value `<registry-key>: <font>`, where `<registry-key>` is the font name.
3. Init: `Board`
    * Initialize and register the Mechanics (e.g., `CollisionMechanics`, `AnimationMechanics`, etc.).
    * Initialize and register Device (e.g. `Keyboard`, `Controller`)
4. Init: `Screen`
    * Initialize background and foreground tile canvases. 
    
## Mechanics

The `Engine.start()` method never changes when new game features are added. It simply iterates through the registered Mechanics:

```python
def start(self) -> None:
    # ... 
    for mechanic in mechanics:
        mechanic.update(self.board, delta_time)
```

Mechanics act as filters. Rather than the Engine passing arguments to a system, a Mechanic is responsible for querying the Board for the exact data it cares about.

For example, the `SwitchMechanics` system strictly queries `board.plates`, `board.gates`, and any heavy entities (like `crates` and `sprites`) to resolve trigger logic, leaving the rest of the Board untouched. This keeps execution tight and game loops strictly separated by behavior.

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