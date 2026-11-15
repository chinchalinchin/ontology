### Bug B028: `NavigationMechanics` Performs 1D Point-Ray LOS and RRT Planning Without Inflating Obstacles by Sprite Hitbox Half-Extents or `squeeze.radius`

**STATUS**: CLOSED
**SEVERITY**: HIGH

**Description**

In `src/app/game/logic/mechanics/intentional/navigation.py` (`NavigationMechanics.obstacles`, lines 68–103) and `src/libs/core/math/paths.pyx` (`rrt`), obstacles are extracted as raw AABBs `(x, y, w, l)` without Minkowski inflation by the navigating sprite's hitbox half-dimensions `(hb.w / 2, hb.l / 2)` or `sprite.state.mutators.parameters.squeeze.radius`. Both `geometry.los()` and `paths.rrt()` (`_is_segment_clear` and `_prune_path`) validate a zero-width 1D ray between `anchor` and `target`. Because `_prune_path()` string-pulls waypoints tight against raw obstacle corners, steering the sprite's center anchor along the resulting ray causes its physical hitbox to collide with obstacle corners.

**Steps to Replicate**

1. Position a `sprite` (`18x15` hitbox at offset `(23, 34)`, `anchor = (132, 541)`) at `Position(100, 500)` and a `32x32` `crate` at `Position(180, 542)` (top edge at `y = 542`, `1px` below the `y = 541` anchor ray).
2. Set `sprite.state.intention = Intentions.FIND.value` and `sprite.state.goal` to `Position(260, 500)` (`target = (292, 541)`).
3. Call `mechanic._navigate(sprite, mock_board)` and observe `geometry.los` returns `True` (setting a direct trajectory through `y = 541`), even though the sprite's physical hitbox spans `y in [534, 549]` and collides directly with the crate (`y in [542, 574]`).

**Proposed Remeditation**

Inflate each candidate obstacle AABB `(ox, oy, ow, ol)` by the navigating sprite's hitbox half-extents `(half_w + squeeze, half_l + squeeze)`—i.e., `(ox - pad_x, oy - pad_y, ow + 2 * pad_x, ol + 2 * pad_y)`—before evaluating `geometry.los()` and `Planner.plan()`.