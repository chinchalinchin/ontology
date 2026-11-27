
##### Bug B073: `CognitionMechanics._project` Steers Escaping Sprites Into Attackers & Crashes on `None` Goal

**STATUS**: CLOSED
**SEVERITY**: HIGH

**Description**

In `src/app/game/logic/mechanics/intentional/cognition.py` (lines 503–510):
1. `if intention == Intentions.ESCAPE and sprite.state.mutators.triggers.vision:` dereferences `sprite.state.goal.position` without verifying `sprite.state.goal` is not `None`, raising `AttributeError`.
2. It extrapolates `sprite.state.goal.position` using `dx * 10` without clamping to Layer bounds (causing RRT stalls against perimeters) and without handling `dx == 0, dy == 0`.
3. It leaves `goal.name` set to the attacker's Asset name and does not set `goal.category = Goals.POSITION`. `NavigationMechanics._target()` prioritizes `board.asset(goal.name)` for same-layer Assets, silently discarding the flee coordinates and steering the escaping Sprite directly into its attacker.

**Steps to Replicate**

1. Place a Sprite in `Intentions.ESCAPE` with `triggers.vision = True` and `goal = Goal(name="attacker", category=Goals.TARGET, ...)`.
2. Run `CognitionMechanics.update()` followed by `NavigationMechanics.update()`.
3. Observe `sprite.state.trajectory.target` points to `"attacker"`'s live hitbox center instead of the extrapolated flee coordinate.

**Proposed Remeditation**

Emit a synthetic `Goals.POSITION` Goal (`name="escape"`) with `None` guards, zero-displacement fallback, and Layer-bounds clamping in `Projector.escape`, and bypass `board.asset(goal.name)` in `NavigationMechanics._target()` whenever `goal.category == Goals.POSITION`.
