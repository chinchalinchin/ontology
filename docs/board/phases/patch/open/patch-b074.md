##### Bug B074: `idle -> find` Proximity-Stall Deadlock, `follow -> speak` Missing Category Guard, & `Ideation` Relationship Mismatch

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

Three coupled defects exist in `src/data/configurations/automata/intentions/main.yaml` and `CognitionMechanics._ideate`:
1. `idle -> find` (lines 129–144) requires `not functions.is_near(...)` for `SUBJECT` and `OBJECT` Goals while `idle` has no direct `-> speak` or `-> interact` transitions. Any Sprite acquiring a `SUBJECT`, `OBJECT`, or `DOOR` Goal already within `action.radius` (such as an adjacent Player or an `OUT` Door it just exited) stalls permanently in `idle`.
2. `follow -> speak` (lines 99–111) omits `sprite.goal.category == constants.Goals.SUBJECT`. If cross-layer Door subsumption replaces a `SUBJECT` Goal with a `DOOR` while `psyche.dialogue` is set, the Sprite transitions `follow -> speak` toward a Door.
3. `CognitionMechanics._ideate` (lines 397–422) generates `SUBJECT` Goals for any character within `vision.radius`, whereas `find -> speak` requires `sprite.memory.relationships[sprite.goal.name]` to be `FRIEND` or `FAMILY`, causing Sprites to walk up to strangers and stall in `find`.

**Steps to Replicate**

1. Place a Sprite in `Intentions.IDLE` with `psyche.dialogue = "hello"` within `action.radius` (`< 30` px) of a `FRIEND` Sprite.
2. Run `CognitionMechanics.update()` followed by `TransitionMechanics.update()`.
3. Observe `sprite.state.goal` is assigned to the adjacent `SUBJECT`, `not is_near(...)` is `False`, and `sprite.state.intention` remains `Intentions.IDLE` indefinitely.

**Proposed Remeditation**

Remove `not functions.is_near(...)` from `idle -> find` (routing `SUBJECT`, `OBJECT`, and `DOOR` unconditionally through `find` using perceived `goal.position`), add `sprite.goal.category == constants.Goals.SUBJECT` and a category-mismatch `-> idle` exitpoint to `follow`, and filter `Ideation` candidates by the same `FRIEND`/`FAMILY` relationship predicate as `find -> speak`.
