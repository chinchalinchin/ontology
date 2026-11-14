##### Bug 020: Broad-Phase `Space` Grid Inserts Unpadded Asset Dimensions Instead of Active Hitbox Bounds

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

In `src/libs/core/math/physics.pyx`, `physics.collisions()`, `physics.boundaries()`, and `physics.environment()` insert entities into the `Space` hash grid using `data[1..4]` (`asset.state.position.x`, `asset.state.position.y`, `asset.dimensions.w`, `asset.dimensions.l`), ignoring the actual bounding extent of `data[5]` (`hitboxes`). In `SpatialMechanic.proximities()`, virtual hitboxes are padded outward by `radius` (`position = (-radius, -radius)`, `dimensions = (w + 2*radius, l + 2*radius)`). When two entities are separated across a `64px` grid cell boundary such that their base dimensions fall in disjoint cells (e.g., cell `1` and cell `2`) while their padded action-radius hitboxes overlap across the cell boundary, `Space.query()` fails to pair them and `proximities()` returns `[]`.

**Steps to Replicate**

1. Instantiate two `64x64` `sprites` (`action.radius = 25`) at `sprite_a.state.position = Position(50, 10)` (occupying `Space` cells `cx in {0, 1}`) and `sprite_b.state.position = Position(130, 10)` (occupying `Space` cells `cx in {2, 3}`).
2. Their padded action hitboxes span `[25, 139]` and `[105, 219]` (overlapping by `34px`).
3. Call `mechanics.proximities([sprite_a, sprite_b])` and observe `[]` is returned instead of `[(sprite_a, sprite_b)]`.

**Proposed Remeditation**

Compute the broad-phase insertion bounding box in `physics.collisions()` and `physics.environment()` from the union of the entity's active `hitboxes` (`data[5]`) when present, or pass the padded bounding coordinates `(x - radius, y - radius, w + 2 * radius, l + 2 * radius)` directly in the primitive tuple constructed by `SpatialMechanic.proximities()` and `SpatialMechanic.intersections()`.
