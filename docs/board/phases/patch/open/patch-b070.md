##### Bug 0602-04: `any_memories_visible` Matches Dead Targets

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/services/translators/environ.py`, `any_memories_visible` checks whether a remembered goal's `name` is in `sprites` on the same layer within `vision.radius`, without checking `not target.mutators.triggers.dead`. A wandering Sprite passing near a remembered target that died while dormant triggers `wander -> hunt` repeatedly until the target is garbage-collected.

**Steps to Replicate**

1. Place a `Goals.TARGET` into `sprite.memory.goals` and set `target.mutators.triggers.dead = True` while retaining the entity on the board.
2. Move the Sprite in `Intentions.WANDER` within `vision.radius` of the dead target.
3. Observe `any_memories_visible` returning `True` and triggering `wander -> hunt`.

**Proposed Remediation**

Guard `any_memories_visible` with `if target.mutators.triggers.dead: continue` for `Goals.TARGET` / `Goals.SUBJECT` candidates.
