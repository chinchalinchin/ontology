

### Bug B032: `_steer` in `libs.core.math.paths.pyx` Steps a Fixed `step_size` Without Clamping to Sample Distance, Overshooting Near Targets Into Obstacles

**STATUS**: CLOSED
**SEVERITY**: MEDIUM

**Description**

In `src/libs/core/math/paths.pyx` (`_steer`, lines 76–86), new tree nodes are placed at a fixed distance `step_size` (`32.0`) from `(from_x, from_y)` toward `(to_x, to_y)`, even when the Euclidean distance between `(from_x, from_y)` and `(to_x, to_y)` is smaller than `step_size`. When a node is closer than `step_size` to `(tx, ty)` and an obstacle or boundary perimeter lies immediately behind `(tx, ty)`, goal-biased samples (`roll <= 0.05`) overshoot `(tx, ty)` into the obstacle behind it and fail `_is_segment_clear()`.

**Steps to Replicate**

1. Place an obstacle wall at `wall = (25.0, -50.0, 10.0, 100.0)` directly behind the target `(20.0, 0.0)`.
2. Call `rrt(0.0, 0.0, 20.0, 0.0, [wall], step_size=32.0, max_iter=300)`.
3. Every goal-biased step from `(0.0, 0.0)` toward `(20.0, 0.0)` steers to `(32.0, 0.0)`, puncturing `wall` at `x = 25.0`, even though the direct segment `(0.0, 0.0) -> (20.0, 0.0)` is unobstructed.

**Proposed Remeditation**

Clamp the step distance in `_steer()` (or check direct target connection before stepping when `hypotf(tx - from_x, ty - from_y) <= step_size`) via `cdef float dist = fminf(step_size, hypotf(to_x - from_x, to_y - from_y))`.
