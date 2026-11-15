
### Bug B029: Early Waypoint Popping at `action.radius` (`25px`) Before Corner Clearance Triggers Next-Frame LOS Occlusion and Replan Thrashing

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

In `src/app/game/logic/mechanics/intentional/navigation.py` (lines 280–299), Step 5 pops the current waypoint `vertices[0]` as soon as `geometry.nearby(sprite.x, sprite.y, target.x, target.y, arrival_radius)` is `True`, using `arrival_radius = sprite.state.mutators.parameters.action.radius` (`25px`). Because `_prune_path()` in `paths.pyx` eliminates all intermediate vertices that have clear line-of-sight from the preceding vertex, every surviving intermediate vertex in `trajectory.vertices` is a corner waypoint where the ray to `vertices[1]` is blocked until the entity reaches `vertices[0]`. Popping `vertices[0]` `24px` early causes `geometry.los(anchor, wp2_anchor, obstacles)` (line 258) to fail against the corner on the very next frame, wiping `vertices` and forcing a redundant RRT replan.

**Steps to Replicate**

1. Place `sprite` at `Position(100, 500)` (`anchor = (132, 541)`, `action.radius = 25`) with `goal` at `Position(300, 500)` and an obstacle `Boundary(Position(150, 520), Dimensions(40, 100))`.
2. Populate `sprite.state.trajectory.vertices = [wp1, wp2]` where `wp1 = Position(118, 470)` (`wp1_anchor = (150, 511)`, distance $\sqrt{18^2 + 30^2}$ or within `25px` at `Position(115, 482)`) rounds the top-left corner of the obstacle and `wp2 = Position(200, 500)` (`wp2_anchor = (232, 541)`).
3. Execute `mechanic._navigate(sprite, mock_board)` on Tick 1: `wp1` is popped at distance `< 25px` and `trajectory.target` advances to `wp2`.
4. Execute `mechanic._navigate(sprite, mock_board)` on Tick 2: `geometry.los` from `(132, 541)` to `(232, 541)` punctures the obstacle at `x in [150, 190]`, discarding `wp2` and triggering a full replan.

**Proposed Remeditation**

Use a tight arrival threshold for intermediate navigational waypoints (e.g., `step_tolerance` based on `speed * delta` or requiring `geometry.los(anchor, next_wp_anchor, obstacles)` to be `True` before popping an intermediate corner vertex).