### Bug B031: `NavigationMechanics._navigate` Assigns Raw `goal.position` Instead of Offset-Adjusted `_target` Coordinate on Clear LOS and Final Waypoint Arrival

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/game/logic/mechanics/intentional/navigation.py`, `_target(sprite, board)` (lines 125–147) resolves a same-layer target asset's live `anchor(target_asset)`, or offsets `goal.position` by the sprite's footprint displacement `(offset_x, offset_y)`. However, when `geometry.los()` is `True` (line 231) or when the final waypoint in `trajectory.vertices` is popped (line 298), `_navigate()` sets `sprite.state.trajectory.target = sprite.state.goal.position`. If `goal.name` is a moving same-layer asset whose live position has diverged from `goal.position`, or if `goal.position` is `None` (default on `Goal(name=...)`), `trajectory.target` is set to a stale coordinate or `None`.

**Steps to Replicate**

1. Instantiate a sprite on layer `'0'` with `sprite.state.intention = Intentions.FOLLOW.value` and `sprite.state.goal = Goal(name=player.name, category=Goals.TARGET.value, layer="0", position=None)`.
2. Position `player` and `sprite` in open space with clear line of sight and call `mechanic._navigate(sprite, mock_board)`.
3. Observe that `_target()` returns the player's `Position` anchor and `geometry.los()` returns `True`, but `sprite.state.trajectory.target` is set to `None` (`sprite.state.goal.position`).

**Proposed Remeditation**

Set `sprite.state.trajectory.target = Position(x=int(target.x - offset_x), y=int(target.y - offset_y))` at lines 231 and 298 so direct tracking and final waypoint handoff consistently steer the sprite's anchor to the resolved `target` anchor, and guard `if goal.position is None: return None` in `_target()`.
