##### Bug B023: `StageHitbox.get`, `OrientedHitbox.get`, and `DirectedHitbox.get` Raise `AttributeError` When `properties.hitboxes` Is `None`

**STATUS**: CLOSED
**SEVERITY**: MEDIUM

**Description**

In `src/app/assets/hitboxes/resources.py` (`StageHitbox.get`, line 41) and `src/app/assets/hitboxes/core.py` (`OrientedHitbox.get`, line 98; `DirectedHitbox.get`, line 118), `.get()` is invoked directly on `properties.hitboxes` without guarding against `properties.hitboxes is None`. Multiple assets in `src/assets/crafts/` (including `arch` and `suspension` in `bridges/main.yaml`, and `bed`, `chair`, `sofa`, and `throne` in `struts/main.yaml`) configure `hitboxes: null` (`None`). If any asset using `StageHitbox`, `OrientedHitbox`, or `DirectedHitbox` is configured with `hitboxes: null`, querying `asset.hitboxes` raises `AttributeError: 'NoneType' object has no attribute 'get'`.

**Steps to Replicate**

1. Instantiate a `Resource` or `Craft` asset bound to `StageHitbox`, `OrientedHitbox`, or `DirectedHitbox` where `asset.properties.hitboxes = None`.
2. Access `asset.hitboxes` (or call `asset.hitbox.get(asset.properties, asset.state, 0)`).
3. Observe `AttributeError: 'NoneType' object has no attribute 'get'`.

**Proposed Remeditation**

Add a `if not properties.hitboxes:` guard in `StageHitbox.get`, `OrientedHitbox.get`, and `DirectedHitbox.get` (consistent with `ElevatedHitbox.get` and `MaterialHitbox.get`), returning `[Hitbox(Position(0, 0), properties.dimensions)]` if `properties.dimensions` is present or `[]` otherwise.
