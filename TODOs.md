##### Review: Navigation Workflow & Logical Predicates

###### Overview

The navigation workflow (`NavigationMechanics`, `Planner`, and `libs.core.math.paths`) and the logical predicates module (`app.game.logic.predicates`) form the bridge between high-level strategic goal selection (`CognitionMechanics`), physical obstacle geometry (`CollisionMechanics`), and local steering (`MotionMechanics`). While the Cython RRT implementation (`paths.pyx`) cleanly manages manual C-buffer allocations and `nogil` tree exploration, several geometric, stateful, and architectural discrepancies exist at the boundary between `NavigationMechanics`, `paths.pyx`, and `predicates.py`—most notably zero-radius 1D point-ray planning, premature corner waypoint popping, and inconsistent obstacle qualification.

###### Review: Implementation

* **1D Point-Ray Pathfinding vs. Physical Hitbox Footprints (`NavigationMechanics` & `paths.pyx`)**:
* `SpriteState` defines `mutators.parameters.squeeze.radius` specifically as the buffer radius for avoiding obstacles during pathfinding, and each Sprite carries physical `hitboxes` (e.g., `18x15` for LPC sprites).
* Neither `NavigationMechanics.obstacles()` nor `paths.rrt()` inflates obstacle AABBs by the sprite's hitbox half-extents `(hb.w / 2, hb.l / 2)` or `squeeze.radius`. Because `_prune_path()` in `paths.pyx` uses greedy string-pulling to pull 1D rays tight against raw obstacle corners, any sprite steering along the pruned path will clip obstacle corners with its physical hitbox and stall against `CollisionMechanics`.


* **Fixed-Step Overshoot in `paths.pyx` (`_steer`)**:
* `_steer()` unconditionally steps a full `step_size` (`32.0`) along $\theta = \text{atan2}(y_{\text{to}} - y_{\text{from}}, x_{\text{to}} - x_{\text{from}})$, even when the sampled coordinate `(to_x, to_y)` is closer than `step_size`. When the 5% goal bias samples `(tx, ty)` from a node within `32px` of a target standing near a wall or boundary perimeter, `_steer()` overshoots the target into the wall behind it, causing `_is_segment_clear()` to reject valid goal connections.


* **Collinear Search-Box Starvation in `paths.pyx` (`rrt`)**:
* `rrt()` computes its sampling window padding as `pad_w = fabsf(tx - sx) * 0.2 + step_size * 2.0` (`64px` when `sx == tx`). If a sprite and its target are aligned vertically (`sx == tx`) on opposite sides of an obstacle wider than `128px` (such as a multi-strut building or river barrier), the obstacle completely bisects `[min_x, max_x]`. Because `_sample_point()` is restricted to `[min_x, max_x]`, RRT cannot sample around the obstacle's outer edges.


* **Float-to-Int Truncation Drift Between `_prune_path` and `geometry.los**`:
* `_prune_path()` verifies segment clearance using `float` coordinates `(nodes[idx].x, nodes[idx].y)`, pulling rays to within $\epsilon = 10^{-5}$ of obstacle corners. Line 284 then truncates waypoints via `Position(int(nodes[idx].x), int(nodes[idx].y))`. Truncating by up to `0.999px` can shift the segment ray into the obstacle interior on the very next frame when `NavigationMechanics._navigate()` validates `geometry.los()` using the truncated integer waypoint.


* **Missing Null Guard on `board.player()` in `NavigationMechanics.update**`:
* `if sprite.name == board.player().name:` assumes `board.player()` is never `None` (unlike `Engine._render()`, which guards `if not self.board.loaded or not player:`).



###### Review: Quality

* **Deprecated Backward-Compatibility Scaffolding (`plan.py`)**:
* `src/app/game/logic/modules/paths/plan.py` retains a deprecated `Node` class (`"Deprecated: Retained for backward compatibility"`). This directly violates the project constraint against retaining dead structures for backward compatibility.




* **Return Type Annotation Violations (`navigation.py`)**:
* `NavigationMechanics._plan()` is annotated as `-> None` (line 156) but returns `bool` (`True` at line 175, `False` at line 183).


* `NavigationMechanics._navigate()` is annotated as `-> None` (line 186) and returns `None` everywhere except line 275, where it executes `return False`.




* **Duck-Typing and Defensive Attribute Checks (`predicates.py`)**:
* `predicates.is_weight()` wraps `asset.properties.mass` in a `try ... except AttributeError` block rather than relying on validated model structure or category predicates.
* `predicates.in_stream()` repeatedly evaluates `direction.value if hasattr(direction, "value") else str(direction)` (lines 91 and 115) instead of enforcing normalized semantic string/enum types at hydration.


* **Duplicate Cython Compiler Directive (`paths.pyx`)**:
* `# cython: language_level=3` is declared twice at the top of `src/libs/core/math/paths.pyx` (lines 1 and 10).



###### Review: Logic

* **Premature Corner Waypoint Popping (`NavigationMechanics._navigate`)**:
* In Step 5 of `_navigate()`, arrival at an intermediate waypoint `vertices[0]` is evaluated using `arrival_radius = sprite.state.mutators.parameters.action.radius` (`25px`).
* Because `_prune_path()` collapses all collinear and unobstructed intermediate nodes, every surviving intermediate waypoint in `trajectory.vertices` is a **corner vertex** where direct line-of-sight to the *next* waypoint (`vertices[1]`) is obstructed until the corner is reached.
* Popping `vertices[0]` when the sprite is still `24px` away from the corner causes the next tick's `geometry.los(anchor, wp2_anchor, obstacles)` check (line 258) to puncture the corner obstacle, clearing `vertices` and triggering a full RRT replan before the sprite can round the corner.




* **Target Anchor vs. `goal.position` Mismatch (`NavigationMechanics._target` vs. `_navigate`)**:
* When `goal.name` references a same-layer asset, `_target()` resolves `self.anchor(target_asset)` (the live footprint center of the target asset).


* However, when `geometry.los()` is clear (line 231) or when the final waypoint is popped (line 298), `_navigate()` assigns `sprite.state.trajectory.target = sprite.state.goal.position`. If `goal.position` is `None` (default on `Goal` when initialized by target name) or stale relative to the moving target's live position, `trajectory.target` either becomes `None` or steers the sprite's canvas origin `(x, y)` to a raw coordinate without subtracting `(offset_x, offset_y)`.




* **Multi-Tier Hitbox Resolution Mismatch (`NavigationMechanics.obstacles`)**:
* `NavigationMechanics.obstacles()` filters candidates via `board.weights(layer, elevation=elevation)` but then iterates over `for hb in asset.hitboxes:`. Because `asset.hitboxes` evaluates `self.hitbox.get(self.properties, self.state, self.elevation)` at the asset's base elevation rather than the queried `elevation` tier, multi-tier crafts (`ElevatedHitbox`) emit their base-tier hitboxes instead of the hitboxes for the requested `elevation`.


* **Zero-Length Parent Stream Short-Circuits Active Branches (`predicates.in_fluid`)**:
* `in_fluid()` guards `in_stream()` behind `if fluid.state.length > 0 and in_stream(position, fluid):`. If a fluid source is obstructed at `length == 0` into an annular pool that spawns active downstream `branches` (`branch.length > 0`), `in_fluid()` short-circuits and returns `False` for coordinates inside the child branches.



###### Review: Architecture

* **Unused `board.obstacles()` Interface & Dynamic Agent Thrashing**:
* `Board.obstacles(layer, elevation)` and `predicates.is_obstacle()` exist specifically to query navigational obstructions, yet `NavigationMechanics.obstacles()` queries `board.weights(layer, elevation=elevation)` instead.
* Because `board.weights()` includes all dynamic `SPRITES` and `PLAYERS` ($m > 0$), `NavigationMechanics` treats moving NPCs as static walls during 60 Hz `geometry.los()` checks and RRT planning. Whenever another moving sprite crosses a navigating sprite's line of sight, `_navigate()` discards its trajectory and replans via RRT, duplicating and fighting the local RVO steering already performed by `MotionMechanics` (`physics.avoid`).




* **Inaccurate Qualification in `predicates.is_obstacle**`:
* `predicates.is_obstacle()` checks only `asset.instance in (...)`. Consequently, calling `board.obstacles(layer)` (with `elevation=None`) returns passable `STRUTS` (e.g., `floors`, `flats`, `paths`, `corridors`, `roofs`, `decor`), open `GATES` (`switch == True`), and sensor `SIGNS` (`mass = -1`). `is_obstacle()` should verify that the asset actually projects active obstacle hitboxes (or `mass >= 0` with non-empty `elevations`).



###### Review: Optimization

* **Per-Tick Obstacle Tuple Reconstruction (`NavigationMechanics._navigate`)**:
* `NavigationMechanics.obstacles()` rebuilds a fresh Python `list` of `float` 4-tuples for every navigating sprite on every tick (60 Hz), even though static weights and layer `perimeters` are invariant between gate/fluid state changes. Caching static obstacle tuples per `(layer, elevation)` on `Board` (or computing them once per `(layer, elevation)` per frame in `NavigationMechanics.update()`) eliminates $O(N_{\text{sprites}} \times N_{\text{weights}})$ tuple allocations per frame.


* **Five Heap `malloc`/`free` Calls Per `rrt()` Invocation (`paths.pyx`)**:
* Every call to `rrt()` executes up to five separate `malloc()` and `free()` calls (`c_obstacles`, `nodes`, `path_buf`, `forward_buf`, `pruned_buf`). Allocating a single contiguous arena block (or holding reusable pre-allocated C buffers on a Cython extension class, analogous to `Space`) removes per-plan heap allocation overhead.


* **Per-Call List and Tuple Allocations in `predicates.in_pool` and `predicates.in_stream**`:
* `in_pool()` allocates a single-element list `[(pool.x, pool.y, pool.x + pool.w, pool.y + pool.l)]` on every call just to invoke `geometry.inside()` for a 4-integer comparison.
* `in_stream()` rebuilds `aabbs: List[Tuple[int, int, int, int]]` from `fluid.state.source` and `fluid.state.branches` on every `Board.fluid()` lookup (`60 Hz` per moving entity), even though `Actuator.propagate()` already compiles the active stream and pool geometry onto `fluid.state.hitboxes`.



---

##### Bug B028: `NavigationMechanics` Performs 1D Point-Ray LOS and RRT Planning Without Inflating Obstacles by Sprite Hitbox Half-Extents or `squeeze.radius`

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

In `src/app/game/logic/mechanics/intentional/navigation.py` (`NavigationMechanics.obstacles`, lines 68–103) and `src/libs/core/math/paths.pyx` (`rrt`), obstacles are extracted as raw AABBs `(x, y, w, l)` without Minkowski inflation by the navigating sprite's hitbox half-dimensions `(hb.w / 2, hb.l / 2)` or `sprite.state.mutators.parameters.squeeze.radius`. Both `geometry.los()` and `paths.rrt()` (`_is_segment_clear` and `_prune_path`) validate a zero-width 1D ray between `anchor` and `target`. Because `_prune_path()` string-pulls waypoints tight against raw obstacle corners, steering the sprite's center anchor along the resulting ray causes its physical hitbox to collide with obstacle corners.

**Steps to Replicate**

1. Position a `sprite` (`18x15` hitbox at offset `(23, 34)`, `anchor = (132, 541)`) at `Position(100, 500)` and a `32x32` `crate` at `Position(180, 542)` (top edge at `y = 542`, `1px` below the `y = 541` anchor ray).
2. Set `sprite.state.intention = Intentions.FIND.value` and `sprite.state.goal` to `Position(260, 500)` (`target = (292, 541)`).
3. Call `mechanic._navigate(sprite, mock_board)` and observe `geometry.los` returns `True` (setting a direct trajectory through `y = 541`), even though the sprite's physical hitbox spans `y in [534, 549]` and collides directly with the crate (`y in [542, 574]`).

**Proposed Remeditation**

Inflate each candidate obstacle AABB `(ox, oy, ow, ol)` by the navigating sprite's hitbox half-extents `(half_w + squeeze, half_l + squeeze)`—i.e., `(ox - pad_x, oy - pad_y, ow + 2 * pad_x, ol + 2 * pad_y)`—before evaluating `geometry.los()` and `Planner.plan()`.

##### Bug B029: Early Waypoint Popping at `action.radius` (`25px`) Before Corner Clearance Triggers Next-Frame LOS Occlusion and Replan Thrashing

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

##### Bug B030: `NavigationMechanics.obstacles` Queries `asset.hitboxes` at Base `asset.elevation` Instead of the Target `elevation` Tier

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/game/logic/mechanics/intentional/navigation.py` (lines 76–93), `NavigationMechanics.obstacles(layer, board, exclude, elevation=0)` iterates over `board.weights(layer, elevation=elevation)` and extracts `for hb in asset.hitboxes:`. However, `Asset.hitboxes` (`src/app/assets/base.py`, line 217) resolves `self.hitbox.get(self.properties, self.state, self.elevation)` at the asset's base `self.elevation` rather than the `elevation` argument passed to `NavigationMechanics.obstacles()`. For multi-tier assets using `ElevatedHitbox`, this extracts the wrong tier's hitboxes.

**Steps to Replicate**

1. Configure a craft asset with `ElevatedHitbox` at `state.elevation = 0` having `{0: [hb_tier0], 1: [hb_tier1]}`.
2. Call `NavigationMechanics.obstacles(layer="0", board=mock_board, exclude=[], elevation=1)`.
3. Observe that `hb_tier0` is returned in the obstacle list instead of `hb_tier1`.

**Proposed Remeditation**

Replace `for hb in asset.hitboxes:` in `NavigationMechanics.obstacles()` with `for hb in asset.hitbox.get(asset.properties, asset.state, elevation):`.

##### Bug B031: `NavigationMechanics._navigate` Assigns Raw `goal.position` Instead of Offset-Adjusted `_target` Coordinate on Clear LOS and Final Waypoint Arrival

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/game/logic/mechanics/intentional/navigation.py`, `_target(sprite, board)` (lines 125–147) resolves a same-layer target asset's live `anchor(target_asset)`, or offsets `goal.position` by the sprite's footprint displacement `(offset_x, offset_y)`. However, when `geometry.los()` is `True` (line 231) or when the final waypoint in `trajectory.vertices` is popped (line 298), `_navigate()` sets `sprite.state.trajectory.target = sprite.state.goal.position`. If `goal.name` is a moving same-layer asset whose live position has diverged from `goal.position`, or if `goal.position` is `None` (default on `Goal(name=...)`), `trajectory.target` is set to a stale coordinate or `None`.

**Steps to Replicate**

1. Instantiate a sprite on layer `'0'` with `sprite.state.intention = Intentions.FOLLOW.value` and `sprite.state.goal = Goal(name=player.name, category=Goals.TARGET.value, layer="0", position=None)`.
2. Position `player` and `sprite` in open space with clear line of sight and call `mechanic._navigate(sprite, mock_board)`.
3. Observe that `_target()` returns the player's `Position` anchor and `geometry.los()` returns `True`, but `sprite.state.trajectory.target` is set to `None` (`sprite.state.goal.position`).

**Proposed Remeditation**

Set `sprite.state.trajectory.target = Position(x=int(target.x - offset_x), y=int(target.y - offset_y))` at lines 231 and 298 so direct tracking and final waypoint handoff consistently steer the sprite's anchor to the resolved `target` anchor, and guard `if goal.position is None: return None` in `_target()`.

##### Bug B032: `_steer` in `libs.core.math.paths.pyx` Steps a Fixed `step_size` Without Clamping to Sample Distance, Overshooting Near Targets Into Obstacles

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/libs/core/math/paths.pyx` (`_steer`, lines 76–86), new tree nodes are placed at a fixed distance `step_size` (`32.0`) from `(from_x, from_y)` toward `(to_x, to_y)`, even when the Euclidean distance between `(from_x, from_y)` and `(to_x, to_y)` is smaller than `step_size`. When a node is closer than `step_size` to `(tx, ty)` and an obstacle or boundary perimeter lies immediately behind `(tx, ty)`, goal-biased samples (`roll <= 0.05`) overshoot `(tx, ty)` into the obstacle behind it and fail `_is_segment_clear()`.

**Steps to Replicate**

1. Place an obstacle wall at `wall = (25.0, -50.0, 10.0, 100.0)` directly behind the target `(20.0, 0.0)`.
2. Call `rrt(0.0, 0.0, 20.0, 0.0, [wall], step_size=32.0, max_iter=300)`.
3. Every goal-biased step from `(0.0, 0.0)` toward `(20.0, 0.0)` steers to `(32.0, 0.0)`, puncturing `wall` at `x = 25.0`, even though the direct segment `(0.0, 0.0) -> (20.0, 0.0)` is unobstructed.

**Proposed Remeditation**

Clamp the step distance in `_steer()` (or check direct target connection before stepping when `hypotf(tx - from_x, ty - from_y) <= step_size`) via `cdef float dist = fminf(step_size, hypotf(to_x - from_x, to_y - from_y))`.

##### Bug B033: `predicates.in_fluid` Short-Circuits Active Child Branches When Parent `fluid.state.length == 0`

**STATUS**: OPEN
**SEVERITY**: LOW

**Description**

In `src/app/game/logic/predicates.py` (lines 134–142), `in_fluid(position, fluid)` checks `if fluid.state.length > 0 and in_stream(position, fluid):`. Inside `in_stream()`, parent corridor evaluation is already guarded by `if slen > 0:` (line 95), while child `fluid.state.branches` are evaluated independently (lines 107–125). If a fluid emitter's parent stream is immediately obstructed at `fluid.state.length == 0` while spawning active child branches (`branch.length > 0`), `in_fluid()` short-circuits before calling `in_stream()` and erroneously returns `False` for positions inside active branches.

**Steps to Replicate**

1. Instantiate a `fluid` asset at `Position(64, 64)` with `fluid.state.length = 0`, `fluid.state.pool = None`, and an active branch `Branch(position=Position(96, 64), source=Directions.DOWN.value, flow=1, length=64)`.
2. Observe that `predicates.in_stream(Position(100, 96), fluid)` returns `True`, whereas `predicates.in_fluid(Position(100, 96), fluid)` returns `False`.

**Proposed Remeditation**

Remove the redundant `fluid.state.length > 0` guard in `predicates.in_fluid()` and delegate directly to `if in_stream(position, fluid): return True`.