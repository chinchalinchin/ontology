##### Bug B059: `CognitionMechanics._remember` Uses Stale `triggers.vision` for Dormancy & Ignores Intention Affinity

**STATUS**: CLOSED
**SEVERITY**: HIGH

**Description**

In `src/app/game/logic/mechanics/intentional/cognition.py` (lines 352–363), `_remember` evaluates dormancy for memorized goals using `not sprite.state.mutators.triggers.vision` — a flag belonging to the Sprite's *previously active* Goal rather than the memorized candidate.
1. If a Sprite abandons a `TARGET` at `(100, 100)` (`triggers.vision = False`), and the `TARGET` later returns to `(105, 100)` (within `action.radius`), `_scan` updates `memory.goals[target].position` without setting `triggers.vision = True`. `_remember` then skips the `TARGET` as dormant even though it is standing directly next to the Sprite.
2. Conversely, after dropping a `WANDER` goal (`_track` sets `triggers.vision = True` for `POSITION`), a genuinely absent dormant `TARGET` is immediately popped back into `sprite.state.goal`.
3. `_remember` selects the first matching dict entry without considering `sprite.state.intention`, allowing a Sprite in `Intentions.HUNT` to pop a `SUBJECT` goal and deadlock in `hunt`.

**Steps to Replicate**

1. Place a Sprite at `(100, 100)` with `goal = None`, `triggers.vision = False`, and `memory.goals["target"] = Goal(name="target", category=Goals.TARGET, layer=L, position=Position(100, 100))`.
2. Move `"target"` to `(105, 100)` (within `action.radius`) on layer `L`.
3. Execute `CognitionMechanics._scan` and `CognitionMechanics._remember`.
4. Observe `sprite.state.goal` remains `None` despite `"target"` being visible and adjacent.

**Proposed Remediation**

Evaluate dormancy in `Recall` by checking live visibility against `board.character(candidate.name)` (same layer and within `vision.radius`), skipping only when the entity is currently *unseen* and the Sprite is already within `action.radius` of `candidate.position` on `candidate.layer`. Filter/prioritize candidates by intention affinity (`HUNT` $\to$ `TARGET`; `FIND` $\to$ `SUBJECT`, `OBJECT`, `DOOR`; `IDLE` $\to$ any eligible category).
