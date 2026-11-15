### Bug B024: `SpatialMechanic.intersections` Overrides Intentional Empty Hitboxes (`[]`) with Full Asset Dimensions and Ignores Elevation Tiers

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/game/logic/mechanics/spatial/base.py` (lines 90–92), `SpatialMechanic.intersections` executes:

```python
base_hbs = asset.hitboxes
if not base_hbs and asset.dimensions:
    base_hbs = [Hitbox(position=Position(x=0, y=0), dimensions=asset.dimensions)]

```

When an asset's `HitboxSchema` intentionally resolves to `[]`—such as an open `Gate` (`SwitchHitbox.get` returns `[]` when `state.switch is True`), a passable `Craft` floor/decor (`MaterialHitbox.get` returns `[]` when `not is_obstacle`), or a `NoHitbox` entity—`intersections()` overrides the empty list with a full-dimension hitbox `[Hitbox(Position(0, 0), asset.dimensions)]`. Furthermore, neither `intersections()` nor `proximities()` checks that candidate pairs share a common elevation tier, allowing entities at `elevation = 1` to intersect or interact with entities at `elevation = 0`.

**Steps to Replicate**

1. Instantiate a `Player` at `Position(60, 150)` with `elevation = 1` and an open `Gate` (`switch = True`) or `Chest` at `Position(60, 150)` with `elevation = 0`.
2. Call `mechanics.intersections([player, gate])`.
3. Observe that `(player, gate)` is returned even though the gate is open (`gate.hitboxes == []`) and the entities are on different elevation tiers (`1 != 0`).

**Proposed Remeditation**

Remove the `if not base_hbs and asset.dimensions:` fallback in `SpatialMechanic.intersections` (since `StaticHitbox.get` and `DynamicHitbox.get` already fall back to `properties.dimensions` when `properties.hitboxes is None`), and filter candidate pairs in `intersections` and `proximities` by shared elevation tiers.
