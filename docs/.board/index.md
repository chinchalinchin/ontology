### Phase 1: Rendering

**1. Cython SDL2 Interface (`libs/render.pyx`)**

Construct a native Cython wrapper around the SDL2 C library to handle hardware-accelerated GPU rendering, strictly avoiding Python-side memory buffers.

* **Dependencies:** Link against `SDL2` and `SDL2_image` in `setup.py`.
  * **Method - `init_sdl()`:** Initialize the SDL video and image subsystems and instantiate the hidden window and hardware-accelerated `SDL_Renderer`.
  * **Method - `load_texture(filepath)`:** Load a `.png` file directly into GPU memory and return an `SDL_Texture` C-pointer.
  * **Method - `create_render_target(width, height)`:** Instantiate a blank `SDL_Texture` configured with `SDL_TEXTUREACCESS_TARGET` to act as a cached background canvas entirely on the GPU.
  * **Method - `draw_to_target(target_ptr, source_ptr, src_rect, dst_rect)`:** Bind the target texture, copy the specifically cropped `source_ptr` rectangle to the target coordinate, and unbind.
  * **Method - `render_scene(background_ptr, active_assets)`:** Clear the active renderer, copy the cached background pointer, iterate over active assets to overlay their respective textures, and call `SDL_RenderPresent`.
  * **Method - `save_to_png(filename)`:** Read the active renderer's pixels into an `SDL_Surface` and export it to the disk for debugging.

**2. Asset Registry (`src/app/game/registry.py`)**

Create a centralized class to ingest YAML files, cache GPU textures, and map dynamic string keys to C-struct crop coordinates.

* **YAML Ingestion:** Recursively parse the `/src/assets/**` directories using Pydantic DTO models strictly to validate schema integrity at startup.
* **Texture Caching:** Invoke the SDL2 interface to load each physical `.png` file, storing the resulting C-pointers in a flat dictionary keyed by the base `<asset-key>`.
* **Persona Assembly:** For composite sprites, leverage `create_render_target()` and `draw_to_target()` to stack the `base` and `feature` textures directly on the GPU, caching the flattened result as a new distinct texture pointer.
* **Frame Indexing:** Construct a flat lookup table mapping every possible `FrameKey` (e.g., `<asset-key>-walk-left-3`) to its exact `SDL_Rect` crop coordinates `(x, y, w, h)` based on the loaded Pydantic Properties.
* **Query Interface:** Expose `get_render_data(frame_key)` to return the exact `(TexturePtr, SDL_Rect)` needed by the rendering pipeline in $O(1)$ time.

**3. Command Line Interface (`src/cli.py`)**

Implement the debugging commands required to test configurations, schemas, and rendering output without booting the full physics loop.

* **Command Definition:** `construct <board-key> --out <directory> --layer <layer>`
  * **Construct Step 1:** Parse the immutable configuration (`/src/data/boards/<board-key>/immutable/inanimate.yaml`) using Pydantic validation.
  * **Construct Step 2:** Initialize the `Registry` to load required tilesheets and boot the Cython SDL2 Interface.
  * **Construct Step 3:** Use `create_render_target()` to allocate the layer's background canvas on the GPU.
  * **Construct Step 4:** Iterate through the deployed Tiles, query their pointers/rects from the `Registry`, and use `draw_to_target()` to paint them directly onto the canvas.
  * **Construct Step 5:** Execute `save_to_png()` to export the resulting static background.
* **Command Definition:** `render <board-key> --out <directory> --layer <layer>`
  * **Render Step 1:** Execute the previous `construct` steps to generate the cached background texture pointer.
  * **Render Step 2:** Parse the mutable and animate YAML configurations for `<board-key>` via Pydantic.
  * **Render Step 3:** Instantiate the composite `Asset` POPOs, mapping the validated YAML data into their respective `State` and `Properties` models alongside their stateless `GraphicsBehavior` component.
  * **Render Step 4:** Iterate over the mutable assets, invoking their `GraphicsBehavior.frame()` method to evaluate their current `FrameKey` based on their state variables.
  * **Render Step 5:** Pass the background pointer and the evaluated assets to `render_scene()`, followed by `save_to_png()` to snapshot the full composite scene.

## Phase 2: Editor

TODO