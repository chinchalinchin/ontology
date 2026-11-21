
##### Bug B047: Unclamped Camera Coordinates in `geometry.onscreen`

**STATUS**: OPEN
**SEVERITY**: Low

**Description**

In `src/libs/core/math/geometry.pyx` (`onscreen`, lines 60–71), camera coordinates are computed as:

```cython
cdef int cam_x = p_pos.x + (p_dim.w // 2) - (screen.w // 2)
cdef int cam_y = p_pos.y + (p_dim.l // 2) - (screen.l // 2)
```

Unlike `Screen.camera` in `src/app/game/screen.py` (lines 318–341), which clamps `cam_x` to `[0, boardsize.w - screensize.w]` and `cam_y` to `[0, boardsize.l - screensize.l]` (or centers layers smaller than the viewport), `geometry.onscreen` does not clamp to board boundaries. When the player (`p_pos`) is near any edge of the board (e.g., `p_pos.x = 0`), `Screen.camera` clamps `cam_x = 0` so the viewport displays `[0, screen.w]`, whereas `geometry.onscreen` evaluates `[ -screen.w // 2, screen.w // 2 ]`, falsely reporting visible entities in `[screen.w // 2, screen.w]` as offscreen.

**Steps to Replicate** 

1. Position the Player at `(0, 0)` on a board of size `1920x1080` with a `1280x720` screen viewport.
2. Place an Asset at `(800, 200)` (which is visible on screen since `Screen.camera` clamps `cam_x = 0`).
3. Call `geometry.onscreen(asset.pos, asset.dim, player.pos, player.dim, screen_dim)` — it returns `False` because `cam_x + screen.w` is computed as `-640 + 1280 = 640 < 800`.

**Proposed Remeditation**

Pass `board: Dimensions` (or the already-clamped camera `pov: Position` from `Screen.camera`) into `geometry.onscreen` so its viewport rectangle matches `Screen.camera`.
