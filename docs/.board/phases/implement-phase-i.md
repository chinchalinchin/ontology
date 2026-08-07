
#### Phase I: Render

1. **Cython SDL2 Interface** (`libs/render.pyx`)

Construct a native Cython wrapper around the SDL2 C library to handle hardware-accelerated GPU rendering, strictly avoiding Python-side memory buffers.

- [x] **Dependencies** - Link against `SDL2` and `SDL2_image` in `setup.py`.
- [x] **Method** - `init()`: Initialize the SDL video and image subsystems and instantiate the hidden window and hardware-accelerated `SDL_Renderer`.
- [x] **Method** - `load(filepath)`: Load a `.png` file directly into GPU memory and return an `SDL_Texture` C-pointer.
- [x] **Method** - `canvas(width, height)`: Instantiate a blank `SDL_Texture` configured with `SDL_TEXTUREACCESS_TARGET` to act as a cached background canvas entirely on the GPU.
- [x] **Method** - `draw(target_ptr, source_ptr, src_rect, dst_rect)`: Bind the target texture, copy the specifically cropped `source_ptr` rectangle to the target coordinate, and unbind.
- [x] **Method** - `compose(base_ptr, feature_ptrs)` Bind a blank `TEXTUREACCESS_TARGET`, stamps the base and features onto it, unbinds, and returns the new flattened TexturePtr. Used for assembling Sprite's base and features into a "virtual" Asset.
- [x] **Method** - `render(background_ptr, assets)`:** Clear the active renderer, copy the cached background pointer, iterate over active Assets to overlay their respective textures, and call `SDL_RenderPresent`.
- [x] **Method** - `save(filename)`:** Read the active renderer's pixels into an `SDL_Surface` and export it to the disk for debugging.
- [x] **Optimize Render Signatures**: Refactor `render()` and `construct()` to accept flat tuples of primitive integers rather than Position/Dimensions POPOs to enforce zero-allocation C-stack unpacking.

2. **Asset Registry** (`libs/registry.pyx` & `libs/registry.pxd`)

Create a centralized Cython Extension Type to ingest the parsed data structures from the YAML configuration, cache GPU textures, and map dynamic string keys to C-struct crop coordinates.

- [x] **Data Structures** (`libs/registry.pxd`): Define the cdef class TexturePtr wrapper here so both the Registry and Renderer can strongly type it in their arguments.
- [x] **Method** - `load(filepath)`: `cimport` the `_rendere`r from `render`.pxd. Load `.png` files directly into GPU memory via `IMG_LoadTexture` and return a safe `TexturePtr` wrapper. Implement` __dealloc__` to call `SDL_DestroyTexture` to prevent memory leaks.
- [~] **YAML Ingestion**: Recursively parse the `/src/assets/**` directories using Pydantic DTO models on the Python side strictly to validate schema integrity at startup.
- [x] **Texture Caching**: Invoke `load()` for each physical .png file, storing the resulting TexturePtr in a flat C-level dictionary/map keyed by the base `<asset-key>`.
- [x] **Persona Assembly**: For composite sprites, leverage render.`compile_texture()` to stack the base and feature textures directly on the GPU, caching the flattened result as a new distinct texture pointer in the dictionary.
- [x] **Frame Indexing**: Construct a flat lookup table mapping every possible FrameKey (e.g., `<asset-key>-walk-left-3`) to its exact crop coordinates as primitive integers `(src_x, src_y, src_w, src_h)`.
- [x] **Query Interface**: Expose `data(frame_key)` to return a Python tuple containing `(TexturePtr, src_x, src_y, src_w, src_h)`. This allows `screen.py` to append destination coordinates without instantiating heavy POPOs.

**Application Orchestration** (`src/app/orchestration.py`, `src/app/models/*`, `src/app/game/*`)

- [x] Initialize `libs.render`.
- [x] Instantiate Registry to validate `/src/assets/**` and cache GPU textures.
- [x] Parse `/src/data/boards/<board-key>/**.yaml`.
- [x] Convert Pydantic models by invoking Factory to hydrate runtime Asset POPOs from the parsed configuration.
- [x] Query Registry for the calculated TexturePtr frames and bind them to the Assets.
- [x] Intialize Board and inject the hydrated Assets into the Board. This logic belongs inside `Screen.draw()`, requiring the Registry to be injected into the Screen component at startup.
- [x] Camera Culling: Implement integer-based boundary checks inside Screen.draw() to cull assets falling outside the camera's viewport before passing them to the Cython rendering interface.

**4. Command Line Interface** (`src/cli.py`)

Implement the debugging commands required to test configurations, schemas, and rendering output without booting the full physics loop.

* [x]**Command Definition:** `construct <board-key> --out <directory> --layer <layer>`
  * [x] **Construct Step 1:** Parse the state configuration (`/src/data/boards/<board-key>/*.yaml`) using Pydantic validation. 
  * [x] **Construct Step 2:** Initialize the `Registry` to load required tilesheets and boot the Cython SDL2 Interface.
  * [x] **Construct Step 3:** Use `canvas()` to allocate the layer's background canvas on the GPU.
  * [x] **Construct Step 4:** Iterate through the deployed Tiles, query their pointers/rects from the `Registry`, and use `draw()` to paint them directly onto the canvas.
  * [x] **Construct Step 5:** Execute `save()` to export the resulting static background.
* [x] **Command Definition:** `render <board-key> --out <directory> --layer <layer>`
  * [x] **Render Step 1:** Execute the previous `construct` steps to generate the cached background texture pointer.
  * [x] **Render Step 2:** Parse the mutable and animate YAML configurations for `<board-key>` via Pydantic.
  * [x] **Render Step 3:** Instantiate the composite `Asset` POPOs, mapping the validated YAML data into their respective `State` and `Properties` models alongside their stateless `Frame` and `Animation` component. Will need to default these when initializing. Should probably make this part of the Factory initialization as well.
  * [x] **Render Step 4:** Iterate over the mutable assets, invoking their `Frame.key()` method to evaluate their current `FrameKey` based on their state variables.
  * [x] **Render Step 5:** Pass the background pointer and the evaluated assets to `render()`, followed by `save()` to snapshot the full composite scene.

##### Refactors

- [x] **Shape**: The Asset properties `hitboxes` and `dimensions` were previously nested under a `shape` object. This object has been removed to flatten out the objects and align the application with a data-oriented design perspective. Ensure the application has not been broken during this refactor.