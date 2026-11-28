##### Bug B056: `Screen.__init__` and `Screen.rebake` Negate `opaque=True` on Tileless `bg_canvas` via `render.construct`

**STATUS**: OPEN
**SEVERITY**: LOW

**Description**

In `src/app/game/screen.py` (`Screen.__init__`, lines 97–105, and `Screen.rebake`, lines 355–362), when a layer has no tiles (`len(tiles) == 0`), `is_opaque` is set to `True` and `self.bg_canvas` is allocated via `render.canvas(canvas_w, canvas_l, opaque=True)`, which clears the texture to opaque black `RGBA(0, 0, 0, 255)`. Immediately afterward, `render.construct(self.bg_canvas, back_tiles)` is invoked with its default `clear_target=True`, which calls `SDL_SetRenderDrawColor(_renderer, 0, 0, 0, 0)` and `SDL_RenderClear(_renderer)`, overwriting the opaque black canvas back to fully transparent `RGBA(0, 0, 0, 0)`.

**Steps to Replicate** 

1. Instantiate a `Screen` (or invoke `screen.rebake(...)`) with `tiles = []`.
2. Call `screen.export_background("empty_bg.png")`.
3. Inspect the exported image: all pixels have alpha `0` (transparent) instead of the intended opaque black `RGBA(0, 0, 0, 255)`.

**Proposed Remeditation**

Pass `clear_target=not is_opaque` to `render.construct(self.bg_canvas, back_tiles, clear_target=not is_opaque)` in both `Screen.__init__` and `Screen.rebake` (or invoke `render.construct` on `self.bg_canvas` only when `back_tiles` is non-empty, since `render.canvas` has already cleared the freshly allocated texture).