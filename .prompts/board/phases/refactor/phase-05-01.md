#### Refactor: Phase 05.01 - Typography

**Goals**

- Integrate native `SDL2_ttf` typography rendering into the Cython graphics pipeline.
- Pre-load and pre-style `.ttf` assets in the Registry to ensure zero-allocation typography baking during the main game loop.

##### Tasks

**1. Task: Establish SDL2_ttf Cython Bindings**

*Objective*: Define the C-level headers and compilation directives required to interact with the SDL2 typography extension.

- [x] Subtask: Declare `TTF_Font` and `SDL_Color` C-structs in `registry.pxd`.
- [x] Subtask: Declare `TTF_Init`, `TTF_Quit`, `TTF_OpenFont`, `TTF_CloseFont`, `TTF_SizeUTF8`, `TTF_SetFontStyle`, and `TTF_RenderUTF8_Blended_Wrapped` in `registry.pyx` and `render.pyx`.
- [x] Subtask: Update `setup.py` Extension definitions to explicitly link the `SDL2_ttf` shared library alongside `SDL2` and `SDL2_image` to prevent `undefined symbol` runtime errors.

**2. Task: Extend Registry for Font Ingestion**

*Objective*: Modify the `Registry` class to discover, load, style, and manage the memory lifecycle of `.ttf` fonts natively.

- [x] Subtask: Create a `TTFFont` Cython extension class (`cdef class`) to wrap the `TTF_Font*` pointer, style properties, and implement `__dealloc__` for automated `TTF_CloseFont` garbage collection.
- [x] Subtask: Update `Registry._cache()` to recursively discover `.ttf` files in the static asset directory.
- [x] Subtask: Implement `Registry._load_font()` to instantiate fonts and apply configuration properties parsed from dictionaries (e.g., `bold`, `italics`, `alignment`, `margins`, and `color` RGBA channels).
- [x] Subtask: Apply SDL styles natively to the `TTF_Font*` pointer during initialization to avoid repeatedly setting styles in the active render loop.
- [x] Subtask: Provide a `font(font_key)` retrieval method for the application to pass styled fonts to the renderer.
- [ ] Subtask: Ensure Registry image indexing is unaffected by the addition of Font keys, i.e. separate the font and image properties at the Orchestrator level and ensure they are injected properly.

**3. Task: Implement Typography Rendering Pipeline**

*Objective*: Add headless string measurement and zero-allocation text rendering to the `render.pyx` hardware pipeline.

- [x] Subtask: Implement `measure(content, TTFFont)` utilizing `TTF_SizeUTF8` to calculate horizontal pixel width without allocating a rendering surface.
- [x] Subtask: Implement `write(asset, content, TTFFont)` to render UTF-8 strings natively using `TTF_RenderUTF8_Blended_Wrapped`.
- [x] Subtask: Implement manual X-coordinate bounding box math inside `write()` to handle `left`, `center`, and `right` alignments mapped against the configured margins, avoiding dependencies on newer `SDL2_ttf` alignment C-functions.
- [x] Subtask: Permanently stamp the generated text surface onto the asset's specific `TexturePtr` target (`SDL_SetRenderTarget`) to bake the text into VRAM, and immediately free the temporary surface and texture to prevent memory leaks.

**4. Task: Update Architecture Documentation**

*Objective*: Document the modified initialization and rendering procedures.

- [x] Subtask: Update the MkDocs architecture page to outline the `Registry` font ingestion process, the `TTFFont` wrapper, and the `measure`/`write` zero-allocation typography mechanics.

**5. Task: Update Unit Tests**

*Objective*: Ensure changes are captured by unit tests.

- [x] Subtask: Ensure unit tests for previous Registry implementation are passing.
- [x] Subtask: Add font fixtures.
- [x] Subtask: Ensure the `font()` method and font indexing are adequately covered by unit tests.