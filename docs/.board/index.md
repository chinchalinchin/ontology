# Task Board

This is a backlog of open tasks.

## Phase 1: Rendering

### 1. [ ] Cython SDL2 Interface (`libs/render.pyx`)

Construct a native Cython wrapper around the SDL2 C library to handle hardware-accelerated image rendering without Python interpreter overhead.

- **Dependencies:** Link against `SDL2` and `SDL2_image` in `setup.py`.
- **Methods to Implement:**
  - `init()`: Initialize the SDL video and image subsystems and instantiate the window/renderer contexts.
  - `create_canvas(width, height)`: Instantiate an empty `SDL_Texture` serving as a static buffer for the background.
  - `draw_to_canvas(texture_ptr, src_rect, dst_rect)`: Accept an asset's texture pointer and copy a specific cropped rectangle (`src_rect`) onto the canvas at a specific coordinate (`dst_rect`).
  - `render_scene(stateful_assets)`: 
      1. Copy the static canvas buffer to the active renderer.
      2. Iterate over stateful assets, resolving their `FrameKey`.
      3. Use `SDL_RenderCopy` to overlay their respective textures onto the active renderer.
      4. Call `SDL_RenderPresent`.
  - `save_to_png(filename)`: Read the current renderer pixels into an `SDL_Surface` and save it to the disk for debugging.

### 2. [ ] Asset Registry (`src/app/game/registry.py`)

Create a centralized `Registry` class responsible for loading asset files into memory exactly once and mapping `FrameKey` strings to specific crop coordinates.

- **Initialization:** - Recursively parse the `/src/assets/**` directory.
  - Load all `main.yaml` property schemas to understand asset dimensions and animation counts.
- **Texture Management:** - Call the SDL2 interface to load each unique `.png` file into GPU memory using `IMG_LoadTexture`.
  - Store the resulting C-pointers in a dictionary keyed by the base `<asset-key>`.
- **Sprite Assembly**:** - Using the sprite property configuration for `base` and `feature`, assemble the Sprite Sheets and index them in the 
- **Frame Indexing:**
  - Build a lookup table mapping every possible calculated `FrameKey` (e.g., `<asset-key>-walk-left-3`) to its exact `SDL_Rect` crop coordinates (x, y, w, h) based on the asset's Property configurations (like row offsets and cell widths).
- **Lookup Method:** - `get_render_data(frame_key) -> Tuple[TexturePtr, SDL_Rect]`

### 3. [ ] Command Line Interface (`src/cli.py`)

Create a CLI tool to facilitate testing, debugging, and snapshotting board configurations without booting the full game loop.
- **Command: `construct`**
  - **Usage:** `python main.py construct <board-key> --out <directory>`
  - **Steps:**
      1. Load the immutable configuration (`/src/data/boards/<board-key>/immutable/inanimate.yaml`).
      2. Initialize the `Registry` to load required tilesheets.
      3. Initialize the SDL2 Interface and create a blank `Canvas`.
      4. Iterate over the Tile deployments, retrieving their textures/rects from the `Registry`, and paint them onto the `Canvas`.
      5. Call `save_to_png` to output the static background image to `<directory>`.
- **Command: `render`**
  - **Usage:** `python main.py render <board-key> --out <directory>`
  - **Steps:**
      1. Execute the `construct` steps to build the background canvas.
      2. Load the mutable and animate configurations for `<board-key>`.
      3. Instantiate the composite `Asset` objects and their respective `State` and `Properties` Pydantic models.
      4. Calculate the `FrameKey` for each stateful asset based on its default configuration.
      5. Pass the list of assets to the SDL2 `render_scene()` method to overlay them onto the background.
      6. Call `save_to_png` to output the full scene composite to `<directory>`.

## Phase 2: Editor

TODO

## Phase 3: Gameplay Loop

TODO

## Phase 4: Physics

TODO

## Phase 5: NPCs 

TODO

## Phase 6: Combat

TODO

## Phase 7: Cutscenes

TODO