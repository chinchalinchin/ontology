
##### Bug B042: Secondary Bifurcation Pools Omitted from `Cache.cached_fluidmap` and `Actuator.compile_moisture_field()`

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

When a fluid with `flow >= 3` bifurcates (`Actuator._propagate_branches()`, `src/app/services/generators/game/actuator.py`, lines 259–306) and a child branch (`child_flow > 1`) strikes a downstream obstacle, `_partition_pool()` generates a secondary annular pool whose relative hitbox is appended only to `fluid.state.hitboxes` (not to `fluid.state.pool` or `Branch`). While `Cartographer._collect_water_rectangles()` explicitly iterates `fluid.state.hitboxes` to capture secondary pools, `Cache.map_fluid()` (`src/app/game/board/modules/cache.py`, lines 81–145) only indexes the primary corridor, primary `fluid.state.pool`, and `fluid.state.branches`. Consequently, spatial hash cells strictly inside secondary bifurcation pools are absent from `cached_fluidmap`, causing `Board.fluid(layer, pos)` to falsely return `False`. Likewise, `Actuator.compile_moisture_field()` (lines 310–362) omits secondary branch pools when emitting disk moisture sources.

**Steps to Replicate**

1. Deploy a `Fluid` with `flow = 3` flowing toward static Obstacle A, and place static Obstacle B downstream in the path of one of the resulting `child_flow = 2` flank branches.
2. Execute `Actuator.pump(fluid, board)` and `board.update_fluid_cache(layer)`.
3. Query `board.fluid(layer, pos)` for a coordinate inside Obstacle B's secondary pool (outside the truncated branch corridor); `Cache.get_fluid_bucket()` returns `None` and `board.fluid()` returns `False`.

**Proposed Remeditation**

Index `fluid.state.hitboxes` inside `Cache.map_fluid()` (mirroring `Cartographer._collect_water_rectangles()`), and attach an optional `pool: Optional[Pool] = None` field to `Branch` (`src/app/models/state/assets/effects.py`) so `Actuator.compile_moisture_field()` also registers secondary bifurcation pools as disk sources.