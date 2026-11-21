
##### Bug B003: Texture Blend Mode Corruption in `render.construct` & Un-cleared `bg_canvas` in `Screen.reconstruct`

**STATUS**: OPEN
**SEVERITY**: Medium

**Description**

1. In `src/libs/graphics/render.pyx` (`construct`, line 325), every tile/primitive iteration executes:
   ```cython
   SDL_SetTextureBlendMode(tex.ptr, SDL_BLENDMODE_NONE)
   ```
   `construct` is used not only for `bg_canvas` (`ENVIRON` tiles), but also for `fg_canvas` (`CANOPY` tiles) and UI `Pane` 9-slice canvases in `Screen.stamp(widget)`. Setting `SDL_BLENDMODE_NONE` disables alpha blending when stamping canopy tiles or 9-slice borders onto transparent target canvases (causing overlapping canopy tiles to overwrite adjacent foliage with transparent black `(0, 0, 0, 0)`), and permanently leaves the shared `TexturePtr` in `Registry._textures` with `SDL_BLENDMODE_NONE`.
2. In `src/app/game/screen.py` (`Screen.reconstruct`, lines 473–482), `render.clear(self.fg_canvas)` is called prior to `render.construct`, but `render.clear(self.bg_canvas)` is omitted, leaving stale pixels on `bg_canvas` if any area is not fully overwritten.

**Steps to Replicate** 

1. Deploy two overlapping `CANOPY` tiles on a layer, or render a texture in `construct` that is subsequently drawn with alpha modulation in `render.render`.
2. During `Screen.__init__` or `Screen.reconstruct`, `render.construct(self.fg_canvas, fore_tiles)` sets `SDL_BLENDMODE_NONE` on the canopy texture, causing the second canopy tile's transparent bounding box to erase the overlapping portion of the first canopy tile on `fg_canvas`.

**Proposed Remeditation**

1. In `Screen.reconstruct`, call `render.clear(self.bg_canvas)` alongside `render.clear(self.fg_canvas)` (and in `Screen.stamp`, call `render.clear(tex)` before `render.construct`).
2. In `render.construct`, preserve `SDL_BLENDMODE_BLEND` for foreground/UI composition (or restore `SDL_SetTextureBlendMode(tex.ptr, SDL_BLENDMODE_BLEND)` after copying).
