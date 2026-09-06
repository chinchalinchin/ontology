##### Bug B004 - Friction Regression

**STATUS**: CLOSED
**SEVERITY**: MEDIUM

###### Report

Friction is no longer being applied to objects. The reason appears to be localized to the `board.tile()` method.

This line was been added to `app.game.logic.mechanics.motion.frictive`:

```python
logger.info('applying friction')
```

This log appears nowhere in the game logs.

**Context**

Recent refactors have touched how the board manages Tiles.

**Step to Reproduce**

Start game. Interact with Crate object. Momentum never decays due to friction.

##### Resolution

**Issue Summary**

Frictive assets (such as crates) were no longer experiencing velocity decay. The root cause was isolated to the `Board.tile()` method, which was returning `None` during environment queries in `frictive.update()`. Because the engine utilizes a time-sliced hydration architecture, the `Migrator` populates the world dynamically via `Board.add()`. However, the spatial hashing logic required to populate the `_cached_tilemap` was isolated to `Board._cache()`, meaning dynamically instantiated tiles were entirely missing from the spatial hash grid.

**Changes Made and Rationale**

The spatial hashing logic was added directly into `Board.add()` (and its inverse into `Board.remove()`).

* **Why:** Now, when `Board.add()` ingests an asset with the `TILES` category, it calculates the tile's spatial bounds, divides them by `TILE_HASH_SIZE`, and registers the tile in `_cached_tilemap` for every grid cell it intersects. This ensures the $O(1)$ spatial cache remains synchronized with the ECS pipeline during both initial world hydration and runtime asset generation.

**Lessons Learned**

* **Cache Parity:** When migrating from static bulk-initialization to dynamic time-sliced loading, all data structures populated during initialization (like spatial grids) must have exact functional counterparts in the dynamic injection methods.
* **Silent Failures in Physics Pipelines:** The spatial query failed silently by returning `None`, which `frictive.update()` gracefully bypassed. Implementing strict assertions or logging for expected environmental invariants—such as a `BACK` tile always existing beneath a terrestrial asset—would catch state desynchronization much earlier.