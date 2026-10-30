### Bug Reports

##### Bug B016: Non-Recursive Flank Bifurcation in `Actuator.propagate`

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

According to the Ecological Principles specification (`Principle: Fluid Dynamics` and `World Mechanic: FluidMechanics`), a Fluid may bifurcate a number of times equal to its `flow` (`flow = 3` allows three consecutive bifurcations, decrementing `flow` by `1` at each obstacle). However, `Actuator.propagate` (`src/app/services/generators/game/actuator.py`, lines 324–384) only executes a single level of bifurcation. When raycasting child branches (`b_len, _ = geometry.raycast(...)` at line 344), `struck_obstacle` is discarded and child branches with `child_flow` greater than `1` neither form secondary pools nor recursively bifurcate upon striking downstream obstacles.

**Steps to Replicate**

1. Configure a Fluid with `flow = 3` flowing `down`.
2. Place an initial static obstacle (`mass = 0`) in the parent corridor, and place a second static obstacle in the path of one of the discharged child branches (`child_flow = 2`).
3. Call `Actuator.propagate(fluid, board)`.
4. Observe that the child branch truncates flatly against the second obstacle without generating an annular pool or discharging `flow = 1` sub-branches.

**Proposed Remeditation**

Extract corridor raycasting, pool partitioning, and flank discharge into a recursive helper method `_propagate_corridor(fluid, board, origin_pos, direction, flow)` that accumulates `pools`, `branches`, and relative `hitboxes` until `flow == 0` or no obstacle is struck.

---

##### Bug B017: Unclamped Negative Pool Coordinates and Off-Map Branch Spawning in `Actuator._partition_pool`

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `Actuator._partition_pool` (`src/app/services/generators/game/actuator.py`, lines 191–201), `raw_min_x = ox - flow * fw` and `raw_min_y = oy - flow * fl` are snapped to multiples of `(fw, fl)` without clamping to layer bounds `[0, layer_size.w]` and `[0, layer_size.l]`. In `world-testbed`, `test-fluid-00` (`fw = 96, flow = 2`) strikes `test-obstacle-00` at `ox = 68`, producing `pool.x = -192` and spawning the left child branch at `Position(-192, 736)` completely outside the western boundary of the board.

**Steps to Replicate**

1. Load `world-testbed` where `test-fluid-00` (`position = (60, 0), flow = 2, fw = 96`) strikes `test-obstacle-00` (`position = (68, 600)`).
2. Execute `Actuator.propagate(fluid, board)`.
3. Inspect `fluid.state.pool.x` (`-192`) and `fluid.state.branches[0].position.x` (`-192`).

**Proposed Remeditation**

Clamp `pool_x` and `pool_y` to `max(0, ...)` and `pool_end_x` / `pool_end_y` to the active layer dimensions returned by `board.size(layer)` (or suppress branch discharges whose origin coordinates fall outside `[0, layer_size.w)` and `[0, layer_size.l)`).

---

##### Bug B018: Hardcoded `32px` Tile Offsets in `Cartographer` Mismatch `temperate-banks` (`41x41`) Dimensions and Miss Narrow Streams

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

`Cartographer` hardcodes `32` in four places despite `temperate-banks` declaring `dimensions: { w: 41, l: 41 }` and `thickness: 22` in `src/assets/geography/main.yaml`:

1. `Cartographer.generate` (lines 397, 415) sets `margin_coord = y - 32` for `DOWN` and `margin_coord = x - 32` for `RIGHT`.
2. `Cartographer._build_shoreline_hitbox` (lines 161, 165) positions `DOWN` and `RIGHT` hitboxes at `32 - thickness` (`10`) instead of `shore_props.dimensions.l - thickness` (`19`) and `shore_props.dimensions.w - thickness` (`19`).
3. `Cartographer._resolve_fluid_id` (line 135) probes `water_fixed = margin_coord + 16`, which overshoots any stream or branch corridor narrower or shorter than `16` pixels (such as an `8px` truncated corridor) and also omits checking `fluid.state.branches`.

**Steps to Replicate**

1. Truncate a fluid stream to `length = 8` (for instance, upstream of an annular pool).
2. Call `Cartographer.generate("0", board, index)`.
3. Observe that `_resolve_fluid_id` probes `margin_coord + 16`, missing the `8px` stream corridor and failing to resolve `fluid_id` along that segment.

**Proposed Remeditation**

Query the resolved shoreline asset's `dimensions.w` and `dimensions.l` from `board.cradle.spawnables.shorelines[shoreline_id]` when computing `margin_coord` and hitbox offsets, and probe `water_fixed` 1 pixel inside the water boundary (`y + 1` for `UP`, `y - 1` for `DOWN`, `x + 1` for `LEFT`, `x - 1` for `RIGHT`) using `board.fluid(layer, water_pos)` or checking `fluid.hitboxes` so pools, parent streams, and branches of any positive length are resolved uniformly.

---

##### Bug B019: Redundant $O(N^2)$ `MoistureField` Recompilations in `Actuator.propagate`

**STATUS**: OPEN
**SEVERITY**: LOW

**Description**

`Actuator.propagate` (`src/app/services/generators/game/actuator.py`, lines 399–400) calls `cls.compile_moisture_field(layer, board)` and `board.set_moisture_field(layer, moisture_field)` at the end of propagating a single fluid. Because `FluidMechanics.update` (`src/app/game/logic/mechanics/world/fluid.py`, lines 181–188) iterates over every `f` in `layer_fluids` and calls `Actuator.propagate(f, board)`, a layer with $N$ fluids recompiles the entire layer's `MoistureField` $N$ times per invalidation pass, with the first $N - 1$ compilations reading stale geometry from the not-yet-propagated fluids on that layer.

**Proposed Remeditation**

Move `Actuator.compile_moisture_field(layer, board)` and `board.set_moisture_field(layer, moisture_field)` out of `Actuator.propagate` so it executes once per invalidated layer in `FluidMechanics.update` (immediately alongside `board.update_fluid_cache(layer)`) after all fluids on that layer have finished propagating.