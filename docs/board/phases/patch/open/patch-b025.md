##### Bug B025: `LayeredHitbox.elevations` Returns `[]` for `'out'`-Projected Doors, Omitting Them From Elevation-Filtered Queries

**STATUS**: CLOSED
**SEVERITY**: MEDIUM

**Description**

In `src/app/assets/hitboxes/objects.py` (lines 64–71), `LayeredHitbox.elevations` returns `[]` whenever `state.projection == LayerProjections.OUT.value`. However, `LayeredHitbox.get` (lines 73–104) resolves a valid `'out'` sensor hitbox at `target_e = max(0, state.elevation if state.elevation is not None else 0)`. Because `elevations()` returns `[]`, any query that filters by `hitbox.elevations(properties, state)`—such as `board.weights(layer, elevation=0)` or `board.obstacles(layer, elevation=0)`—excludes `'out'`-projected Doors on interior layers.

**Steps to Replicate**

1. Retrieve an `'out'`-projected `Door` asset on `'house-layer-1'` (where `door.state.projection == "out"` and `door.elevation == 0`).
2. Observe that `door.hitboxes` is non-empty, but `door.hitbox.elevations(door.properties, door.state)` returns `[]`.

**Proposed Remeditation**

Remove the `if state.projection == LayerProjections.OUT.value: return []` branch in `LayeredHitbox.elevations` so both `'in'` and `'out'` door projections report `[max(0, state.elevation if state.elevation is not None else 0)]`.
