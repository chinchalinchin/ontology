### Bug B026: `Screen.export_map` Renders Auxiliary Channels to the Default Viewport Instead of `full_target`

**STATUS**: CLOSED
**SEVERITY**: LOW

**Description**

In `src/app/game/screen.py` (lines 369–384), `Screen.export_map` allocates a transient full-board texture `full_target` and passes `target=full_target` to `render.render(...)`. However, on line 381, it invokes `render.channel(active_channels, pov.x, pov.y)` without passing `target=full_target`. Any active `ChannelTypes.TINT` operations are drawn onto the default renderer backbuffer instead of `full_target` and are omitted from the exported image file.

**Steps to Replicate**

1. Call `screen.export_map(out_path, assets)` on a layer containing an asset that emits a `ChannelTypes.TINT` directive in `asset.frame.channels(...)`.
2. Inspect the call arguments to `render.channel` (or the exported image) and observe that `target=full_target` is not passed.

**Proposed Remeditation**

Pass `target=full_target` to `render.channel(active_channels, pov.x, pov.y, target=full_target)` in `Screen.export_map`.
