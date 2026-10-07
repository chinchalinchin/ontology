##### Bug B017: Canvas Bleed on Fore Tiles

**STATUS**: OPEN
**SEVERITY**: Medium

**Description**

When `Screen.reconstruct()` updates seasonal tile frames, it invokes `render.construct(self.fg_canvas, fore_tiles)` directly on the existing `TexturePtr`. Unlike `bg_canvas` which is fully opaque and overwrites previous pixel values, `fg_canvas` contains transparent alpha channels (e.g., foliage overhangs and tree canopies). Successive season transitions will render new seasonal foliage textures over the existing pixels without clearing the target, causing ghosting and visual artifacts.

**Steps to Replicate**

1. Initialize a layer containing `fore` tiles with transparent backgrounds.
2. Advance `board.calendar` past a period boundary to fire `SeasonEvent`.
3. Inspect `screen.fg_canvas`; preceding seasonal canopy pixels remain visible beneath new seasonal pixels.

**Proposed Remediation**

Expose a clear-target routine in `libs.graphics.render` (or call `SDL_SetRenderTarget` followed by `SDL_RenderClear` on `fg_canvas`) within `Screen.reconstruct()` immediately before invoking `render.construct()`.
