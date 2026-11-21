##### Bug B050: Negative Crop Height & Corrupt Slicing on Submerged Composite Assets in `Screen._assemble`

**STATUS**: OPEN
**SEVERITY**: High

**Description**

In `src/app/game/screen.py` (`Screen._assemble`, lines 218–246), when an asset has `state.mutators.triggers.submerged == True`, `Frame.channels` emits a `ChannelTypes.SUBMERGE` directive with `split_y = properties.dimensions.l // 2` (e.g., `32` for a 64x64 `Sprite`). `Screen._assemble` then applies this `split_y` to **every** `(frame_key, ox, oy)` returned by `asset.frame.keys(asset.id, asset.state)`:
```python
rem_l = sl - split_y
active_assets.append((
    tex, sx, sy + split_y, sw, rem_l,
    dx, dy + split_y, dw, rem_l,
    r, g, b, a,
))
```
When a submerged `Sprite` has an active `Expression` cursor (which is superimposed via `SpriteFrame.keys` with a non-zero offset `(ox, oy)` and smaller dimensions, e.g., `16x16` where `sl < split_y`), `split_y` is neither offset by `oy` nor clamped to `[0, sl]`. Consequently, the upper slice crops out-of-bounds texture memory (`split_y > sl`) and stretches the expression icon to `split_y` pixels, while the lower slice computes a **negative** height (`rem_l = sl - split_y < 0`) passed to `SDL_RenderCopy`.

**Steps to Replicate** 

1. Place a `Sprite` (dimensions `64x64`, `split_y = 32`) in a `Fluid` stream so `state.mutators.triggers.submerged == True`.
2. Trigger an `Expression` bubble on the `Sprite` (e.g., `surprise` or `loquacity` with dimensions `16x16` or `32x32` at an overhead offset `oy < 0`).
3. Execute `Screen._assemble`: the expression frame is sliced using the Sprite's `split_y = 32`, producing corrupted rendering and `rem_l <= 0`.

**Proposed Remeditation**

Compute the local split offset relative to each frame's vertical offset `oy` (`local_split = split_y - oy`):
* If `local_split >= sl`: render the frame normally (entirely above the waterline).
* If `local_split <= 0`: render the entire frame with submerged RGBA modulation (entirely below the waterline).
* Otherwise (`0 < local_split < sl`): split into upper (`local_split`) and lower (`sl - local_split`) slices.