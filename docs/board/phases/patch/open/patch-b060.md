##### Bug B060: `attack` Intention Softlock, Unreachable `attack -> scavenge`, and Unsafe Attribute Dereference

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

In `src/data/config/intentions/main.yaml` (lines 3–22):
1. `CognitionMechanics` runs before `TransitionMechanics` and clears `sprite.state.goal = None` as soon as `target.mutators.triggers.dead` becomes `True`. Consequently, `attack -> scavenge` (which requires `sprite.goal` and `target.dead`) is unreachable.
2. `attack` has no exitpoint to `idle` when `not sprite.goal` and no other `TARGET` exists in `memory.goals`, violating the Intention Loop hub invariant and leaving the Sprite permanently stuck in `attack`.
3. `attack -> attack` accesses `sprites.get(sprite.goal.name).mutators.triggers.dead` without an existential `sprites.get(sprite.goal.name)` check, and does not check `is_near(..., action.radius)` to transition back to `hunt` when a Target retreats out of attack range.

**Steps to Replicate**

1. Put an autonomous Sprite in `Intentions.ATTACK` targeting an enemy with `memory.goals = {}`.
2. Set the target's `mutators.triggers.dead = True`.
3. Run `CognitionMechanics.update()` then `TransitionMechanics.update()`.
4. Observe `sprite.state.goal` becomes `None`, `attack -> scavenge` does not trigger, and `sprite.state.intention` stays `Intentions.ATTACK` indefinitely.

**Proposed Remediation**

Add a terminal `- next: idle` rule (`conditions: [not sprite.goal]`) to `attack`, guard `sprites.get(sprite.goal.name)` before dereferencing `.mutators`, add a range-loss transition back to `hunt` when the live Target leaves `action.radius`, and decouple `scavenge` acquisition cleanly via `idle` rather than relying on a cleared `TARGET` goal.
