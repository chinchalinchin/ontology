##### Bug B046: Procedural Shorelines & Projected Door Shadows Persisted in `Board.serialize`

**STATUS**: OPEN
**SEVERITY**: Medium

**Description**

In `src/app/game/board/core.py` (`Board.serialize`, lines 397–436), the serializer iterates over `self._assets` and excludes `WIDGETS`, non-persistent `TEMPORARY` effects, and `Equipment` sheets, but does not exclude:
1. Procedurally generated `GEOGRAPHY` assets (`AssetInstances.SHORELINES`), which are synthesized dynamically by `Cartographer` / `FluidMechanics`.
2. Reciprocal shadow footprints projected by `Doors` (`DoorState.projection == LayerProjections.OUT.value`), which are generated automatically during hydration.

Serializing a running board writes these runtime-synthesized entities into the state dump file, causing duplicate door projections and stale shoreline state entries upon reloading the saved slot.

**Steps to Replicate** 

1. Hydrate a board containing a `Door` (which projects a reciprocal `OUT` door onto `outlayer`) and `Fluids` (which synthesize `Shorelines`).
2. Call `board.serialize(world, slot)`.
3. Inspect the saved state YAML: both `geography.shorelines` and the reciprocal `OUT` door state are written to disk.

**Proposed Remeditation**

In `Board.serialize`, skip assets where `asset.category == AssetCategories.GEOGRAPHY.value` or where `asset.instance == AssetInstances.DOORS.value and getattr(asset.state, "projection", None) == LayerProjections.OUT.value`.