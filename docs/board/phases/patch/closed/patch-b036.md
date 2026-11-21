
##### Bug B036: `Screen._assemble` Applies `ChannelTypes.SUBMERGE` Slicing to Attached Expression Bubbles on Submerged Sprites

**STATUS**: CLOSED
**SEVERITY**: LOW

**Description**

In `src/app/game/screen.py` (`Screen._assemble`, lines 142–177), when an asset's `mutators.triggers.submerged` flag is `True`, `Frame.channels` emits a `ChannelTypes.SUBMERGE` directive with `split_y = properties.dimensions.l // 2` (e.g., `32` for a `64x64` LPC Sprite). `Screen._assemble` then applies this `split_y` slice unconditionally to every `(frame_key, ox, oy)` tuple returned by `asset.frame.keys(asset.id, asset.state)`. For an NPC `Sprite` with an active `state.psyche.expression` bubble (`SpriteFrame.keys`), the expression icon is appended to `frame_keys` with an overhead offset `(ox, oy)` and smaller dimensions (`sw, sl` of `16x16` or `32x32`). Slicing the expression texture at `split_y = 32` causes `rem_l = sl - split_y` to evaluate to `<= 0` and modulates/corrupts the overhead expression icon as if it were submerged.

**Steps to Replicate**

1. Instantiate an NPC `Sprite` (`id != "player"`) with `state.mutators.triggers.submerged = True` and an active `state.psyche.expression` (`AttachmentState`).
2. Call `screen._assemble([sprite], Position(0, 0), Dimensions(480, 480))`.
3. Inspect the generated `active_assets` tuples for the expression frame key: it is split into two slices using the parent Sprite's `split_y` (`32`), producing a lower slice with `rem_l = sl - 32 <= 0` and aquatic color modulation.

**Proposed Remeditation**

In `Screen._assemble`, only apply `submerge_channel` splitting when `(ox, oy) == (0, 0)` and `sl > split_y` (or compute slice bounds relative to the vertical offset `oy` and crop height `sl`).