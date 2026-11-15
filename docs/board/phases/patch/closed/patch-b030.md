
### Bug B030: `NavigationMechanics.obstacles` Queries `asset.hitboxes` at Base `asset.elevation` Instead of the Target `elevation` Tier

**STATUS**: CLOSED
**SEVERITY**: MEDIUM

**Description**

In `src/app/game/logic/mechanics/intentional/navigation.py` (lines 76–93), `NavigationMechanics.obstacles(layer, board, exclude, elevation=0)` iterates over `board.weights(layer, elevation=elevation)` and extracts `for hb in asset.hitboxes:`. However, `Asset.hitboxes` (`src/app/assets/base.py`, line 217) resolves `self.hitbox.get(self.properties, self.state, self.elevation)` at the asset's base `self.elevation` rather than the `elevation` argument passed to `NavigationMechanics.obstacles()`. For multi-tier assets using `ElevatedHitbox`, this extracts the wrong tier's hitboxes.

**Steps to Replicate**

1. Configure a craft asset with `ElevatedHitbox` at `state.elevation = 0` having `{0: [hb_tier0], 1: [hb_tier1]}`.
2. Call `NavigationMechanics.obstacles(layer="0", board=mock_board, exclude=[], elevation=1)`.
3. Observe that `hb_tier0` is returned in the obstacle list instead of `hb_tier1`.

**Proposed Remeditation**

Replace `for hb in asset.hitboxes:` in `NavigationMechanics.obstacles()` with `for hb in asset.hitbox.get(asset.properties, asset.state, elevation):`.
