##### Bug B053: Collision Inefficiencies

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

1. **All-Layer Physics Execution vs. Single-Layer Rendering**:
   * In `CollisionMechanics.update`, the outer loop iterates over `for layer in board.layers():`, running stair traversal, elevation partitioning, perimeter constraints, and broad/narrow-phase collision resolution across **every layer in the Board** on every tick.
   * Because `81,896` calls to `SpatialMechanic.collisions` occur across `5,447` world ticks, `CollisionMechanics` is executing an average of **15.04 elevation-tier collision passes per tick** across all layers.
2. **Static-vs-Static Broad/Narrow-Phase Evaluation in `CollisionMechanics`**:
   * `board.weights(layer)` returns all assets with $m \ge 0$, which includes both dynamic bodies ($m > 0$) and all static bodies ($m = 0$: walls, buildings, obstacle struts, resources, chests, etc.).
   * In Phase 2 of `CollisionMechanics.update`, all `tier_weights` (dominated by static $m = 0$ assets) are passed to `self.collisions(tier_weights, elevation=elevation)`.
   * `physics.collisions` inserts all static and dynamic hitboxes into `Space`, queries all overlapping cell pairs (including **static-vs-static** pairs), and runs `geometry.intersects` on them.
   * For every intersecting pair, `_resolve` re-fetches hitboxes and calls `geometry.intersects` a **second time**, only for `physics.collide` to compute `inv_m1 = 0.0`, `inv_m2 = 0.0`, `inv_total = 0.0` and no-op on static-vs-static pairs.
   * Additionally, `geometry.intersects` returns only the **first** intersecting `(hb1, hb2)` tuple (`return (hb1, hb2)`). If a dynamic entity simultaneously overlaps two hitboxes of a compound asset (e.g., an L-shaped enclosure or multi-hitbox fluid/shoreline), only the first hitbox is resolved per tick.
3. **Perimeter Union Collapse in `Perimeter.extract` (`src/app/services/generators/game/perimeter.py`)**:
   * `Perimeter.extract` collects rectangles for Tier 0 `ENVIRON` and `CANOPY` tiles (Step 1) and then appends static `OBJECTS` and `CRAFTS` rectangles (Step 3) into the same `rects` list passed to `geometry.contours(rects)`.
   * Because `geometry.contours` computes the outer boundary of the **union** $\bigcup_i R_i$ via interval merging (`merge()`), any static object or craft situated *inside* the bounding footprint of the background `ENVIRON` tiles is completely absorbed into the tile interval and produces zero contour edges. Conversely, including `CANOPY` tiles in Step 1 expands the walkable Tier 0 perimeter out to overhead tree/roof canopies.
   * Furthermore, `Perimeter.generate` computes `perimeters_by_tier` for all elevations $E > 0$ (including Step 2 for elevated stairs), but `CollisionMechanics.update` restricts Phase 1 to `if elevation == 0:`, leaving elevated perimeters unused by collision constraints.
