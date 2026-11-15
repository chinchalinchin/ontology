##### Bug B034: `Screen._assemble` Appends Unculled `ChannelTypes.TINT` Payloads Inside the `frame_keys` Loop, Duplicating Channel Operations per Stacked Frame

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/game/screen.py` (`Screen._assemble`, lines 129–182), the `for c_type, payload in channels:` loop that appends `ChannelTypes.TINT` operations to `active_channels` is nested inside `for frame_key, ox, oy in frame_keys:` and placed outside the viewport AABB culling guard (`if dx + dw >= pov.x ...`). Consequently:

1. Any multi-frame stacked asset (e.g., a `Sprite` with equipped items and expressions) duplicates its `TINT` channel operations once per `frame_key`.
2. Off-screen assets outside the camera viewport still append `TINT` channel tuples to `active_channels` every frame.

**Steps to Replicate**

1. Instantiate an asset on layer `'0'` returning 3 `frame_keys` from `asset.frame.keys()` and 1 `ChannelTypes.TINT` directive from `asset.frame.channels()`.
2. Place the asset outside the camera viewport bounds (e.g., at `Position(2000, 2000)` with viewport `(0, 0, 480, 480)`) and call `screen._assemble([asset], Position(0, 0), Dimensions(480, 480))`.
3. Observe `active_assets` is empty (`[]`), whereas `active_channels` contains 3 duplicate `TINT` channel tuples.

**Proposed Remeditation**

Move the `for c_type, payload in channels:` block out of the `for frame_key, ox, oy in frame_keys:` loop in `Screen._assemble()` and guard `active_channels.append(...)` with a viewport AABB intersection check on `(asset.state.position.x + cx, asset.state.position.y + cy, cw, cl)`.