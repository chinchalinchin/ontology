##### Bug B022: `CollisionMechanics._traverse_stairs` Raises `AttributeError` by Accessing `stairs.state.direction` Instead of `stairs.state.blueprint`

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

In `src/app/game/logic/mechanics/spatial/collision.py` (line 71), `CollisionMechanics._traverse_stairs` attempts to read the stair incline orientation via `direction = stairs.state.direction`. However, `StairState` inherits from `CraftState`, which stores its incline partition (`up`, `left`, `right`) on `stairs.state.blueprint` (as defined in `src/assets/crafts/stairs/main.yaml`, `src/data/state/world-testbed/stairs/main.yaml`, and the `Craft: Stairs` specification in `01-assets.md`). `StairState` has no `direction` attribute. Additionally, Phase 0 in `CollisionMechanics.update` (lines 206–218) checks `geometry.bounded` against `stair.dimensions.w` and `stair.dimensions.l` (`64x96`) rather than the active blueprint hitbox (`stair.hitboxes`, e.g., `32x96` for `up`).

**Steps to Replicate**

1. Hydrate `mock_board` and `mock_mechanic(Mechanics.COLLISION.value)`.
2. Position `player = mock_board.player()` at `Position(1000, 120)` with `Velocity(0.0, -20.0)` so the player's hitbox intersects `test-stairs` at `(1000, 100)` on layer `'0'`.
3. Call `mechanics.update(mock_board, 0.016, mock_bus, payload)` and observe an unhandled `AttributeError: 'StairState' object has no attribute 'direction'`.

**Proposed Remeditation**

Replace `direction = stairs.state.direction` with `direction = stairs.state.blueprint` in `CollisionMechanics._traverse_stairs`, and evaluate stair bounds using the stair's active `stair.hitboxes` (falling back to `stair.dimensions` only when `stair.hitboxes` is empty).
