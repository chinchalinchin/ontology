
##### Bug B043: `SpatialMechanic.proximities` Index Misalignment Causes `IndexError` or Wrong-Entity Pairing When Assets Are Skipped (and Unguarded `parameters.action` Access)

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

In `src/app/game/logic/mechanics/spatial/base.py`, `SpatialMechanic.proximities` constructs `asset_map = dict(enumerate(assets))` and iterates `for i, asset in enumerate(assets):`. Whenever an asset fails the `if not asset.state.mutators or not asset.state.mutators.parameters:` check and executes `continue`, `primitive_data` has fewer elements than `assets`, yet subsequent assets still emit `asset.primitive(i, hitboxes=[pad_hb])` using the uncompacted index `i`.

Inside `libs.core.math.physics.collisions` (`src/libs/core/math/physics.pyx`), `data[0]` (`i`) is inserted into `Space`, and candidate pairs `(id_a, id_b)` returned by `grid.query()` are used to index `primitive_data[id_a]` and `primitive_data[id_b]`. If any skipped asset precedes colliding assets, `primitive_data[id_b]` either raises an unhandled `IndexError: list index out of range` or evaluates narrow-phase geometry against shifted, unrelated entries in `primitive_data`.

Additionally, `MutatorParameters.action` (`src/app/models/state/core.py`) is typed as `Optional[RadialParameters]`. Because `proximities` does not verify `asset.state.mutators.parameters.action is not None`, accessing `.action.radius` raises `AttributeError` when `action` is `None`.

**Steps to Replicate**

1. Instantiate three assets `[a0, a1, a2]` where `a0.state.mutators = None`, and `a1` and `a2` share the same position/elevation with valid `mutators.parameters.action`.
2. Call `mechanic.proximities([a0, a1, a2])`.
3. `a1` and `a2` are appended to `primitive_data` at indices `0` and `1` with entity IDs `1` and `2`, causing `physics.collisions` to index `primitive_data[2]` and raise `IndexError: list index out of range`.

**Proposed Remeditation**

Filter eligible assets (checking `mutators`, `mutators.parameters`, and `mutators.parameters.action`) into a contiguous list before enumerating indices into `asset_map` and `primitive_data` so that `data[0]` always matches its exact index in `primitive_data`.


##### Bug B043 (Duplicate Report): Index Desynchronization & Out-of-Bounds Access in `SpatialMechanic.proximities`

**STATUS**: OPEN
**SEVERITY**: High

**Description**

In `src/app/game/logic/mechanics/spatial/base.py`, `SpatialMechanic.proximities` constructs `asset_map = dict(enumerate(assets))` using the enumeration index `i` ($0 \le i < N$), and passes `i` as the first element (`entity_id`) of `asset.primitive(i, hitboxes=[pad_hb])` appended to `primitive_data`. However, if any asset in `assets` fails the guard condition (`if not asset.state.mutators or not asset.state.mutators.parameters: continue`), that iteration is skipped, making `len(primitive_data) < len(assets)` while `data[0]` still holds the original index `i`.

When `physics.collisions(primitive_data, self.grid)` executes in `src/libs/core/math/physics.pyx`, it inserts `data[0]` (`i`) into `self.grid`, and then indexes `primitive_data[id_a]` and `primitive_data[id_b]` using those `entity_id` values:
1. Any `entity_id >= len(primitive_data)` raises an `IndexError: list index out of range`.
2. Any `entity_id < len(primitive_data)` occurring after a skipped element accesses the wrong asset's tuple in `primitive_data`, evaluating narrow-phase intersections with mismatched coordinates before mapping the result back to `asset_map[id_a]`.
3. Additionally, if `asset.state.mutators.parameters.action` is `None`, accessing `.radius` raises an `AttributeError`.

**Steps to Replicate** 

1. Instantiate a list of 3 `Asset` instances `[asset_0, asset_1, asset_2]` where `asset_0` has `asset_0.state.mutators = None`, and `asset_1`, `asset_2` have valid `mutators.parameters.action.radius` and overlapping positions.
2. Call `SpatialMechanic().proximities([asset_0, asset_1, asset_2])`.
3. `primitive_data` has length 2, containing `entity_id` values `1` and `2`.
4. `physics.collisions` queries the grid, receives candidate pair `(1, 2)`, and attempts to access `primitive_data[2]`, raising `IndexError: list index out of range`.

**Proposed Remeditation**

Maintain a contiguous local index `idx = len(primitive_data)` for `primitive_data` and `asset_map` (and guard `asset.state.mutators.parameters.action`), ensuring a 1-to-1 correspondence between `entity_id` and `primitive_data` indices:
* Assign `idx = len(primitive_data)`, map `asset_map[idx] = asset`, and append `asset.primitive(idx, hitboxes=[pad_hb])`.
