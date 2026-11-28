##### Bug B057: `NavigationMechanics._target` Overrides `ESCAPE` Goal Projection, Steering Fleeing Sprites Toward Their Attacker

**STATUS**: CLOSED
**SEVERITY**: HIGH

**Description**

When a Sprite enters `Intentions.ESCAPE`, `CognitionMechanics._project` (`src/app/game/logic/mechanics/intentional/cognition.py`, lines 512–518) extrapolates `sprite.state.goal.position` away from the threat while leaving `sprite.state.goal.name` set to the attacker's name. Immediately afterward, `NavigationMechanics._target` (`src/app/game/logic/mechanics/intentional/navigation.py`, lines 152–157) resolves `board.asset(goal.name, sprite.state.layer)` whenever `goal.name` matches a same-layer asset—completely ignoring `goal.position` and returning `self.anchor(attacker)`. As a result, fleeing Sprites path directly into their attacker. Additionally, `_project` dereferences `sprite.state.goal.position` without a `None` check and fails to clamp the extrapolated point to layer bounds.

**Steps to Replicate**

1. Deploy a Sprite at `(100, 100)` with `intention = Intentions.ESCAPE`, `triggers.vision = True`, and `goal = Goal(name=attacker.name, category=Goals.TARGET, layer=layer, position=Position(120, 100))`.
2. Run `CognitionMechanics.update()` followed by `NavigationMechanics.update()`.
3. Observe `sprite.state.goal.position.x == -100` (unclamped off-map), while `sprite.state.trajectory.target` is set to the attacker's position at `(120, 100)` instead of fleeing left.

**Proposed Remediation**

Respect `goal.position` in `NavigationMechanics._target()` when `sprite.state.intention == Intentions.ESCAPE` (or when `goal.category == Goals.POSITION`), guard `sprite.state.goal` for `None` in `Projector`, and clamp extrapolated escape coordinates to `[0, max_w - sprite_w] x [0, max_l - sprite_l]` matching `WANDER`.
