##### Bug B054: Heap Buffer Overflow in `render.save` When Exporting Targets Larger Than Requested Dimensions

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

In `src/libs/graphics/render.pyx` (`save`, lines 715–738), `SDL_CreateRGBSurfaceWithFormat` allocates an RGBA pixel buffer of dimensions `w x l` (`pitch = w * 4`), and then calls:

```cython
SDL_RenderReadPixels(
    _renderer, NULL, SDL_PIXELFORMAT_RGBA32, surface.pixels, surface.pitch
)
```

Passing `rect = NULL` instructs SDL2 to read the **entire** active render target into `surface.pixels`. However, in `src/app/game/screen.py` (`Screen.__init__` / `Screen.rebake`), `self.bg_canvas` is allocated with `canvas_w = max(boardsize.w, screensize.w)` and `canvas_l = max(boardsize.l, screensize.l)`, while `Screen.export_background` calls `render.save(out_path, self.boardsize.w, self.boardsize.l, target=self.bg_canvas)`. Whenever a layer is smaller than the screen viewport (`boardsize.w < screensize.w` or `boardsize.l < screensize.l`), `SDL_RenderReadPixels` reads `canvas_w x canvas_l` pixels into a smaller `boardsize.w x boardsize.l` surface buffer, causing an out-of-bounds heap write / memory corruption / segmentation fault.

**Steps to Replicate** 

1. Initialize a `Screen` with `screensize = Dimensions(1280, 720)` and a smaller layer `boardsize = Dimensions(400, 300)` (`bg_canvas` is allocated as `1280x720`).
2. Call `screen.export_background("bg.png")`.
3. `render.save` allocates a `400x300` `SDL_Surface` (`480,000` bytes) and invokes `SDL_RenderReadPixels` with `rect = NULL` against the `1280x720` target (`3,686,400` bytes), overflowing `surface.pixels`.

**Proposed Remeditation**

Construct a `cdef SDL_Rect read_rect` initialized to `(0, 0, w, l)` inside `render.save` and pass `&read_rect` to `SDL_RenderReadPixels` instead of `NULL`.