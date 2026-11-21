##### Bug 0602-02: Cross-Layer Door Subsumption Deadlocks Sprites in `hunt`

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

When a Sprite in `Intentions.HUNT` pursues a `Goals.TARGET` residing on a different Layer, cross-layer door subsumption replaces `sprite.state.goal` with a `Goals.DOOR` (or `Goals.OBJECT`). In `src/data/config/intentions/main.yaml`, `hunt` only transitions to `attack` (requiring `goal.category == TARGET`) or `idle` (requiring `not sprite.goal`). The Sprite walks to the door in `hunt`, never enters `interact`, and stalls indefinitely.

**Steps to Replicate**

1. Place a Sprite in `hunt` on `layer_1` with a `Goals.TARGET` on `layer_2` and a mapped Door on `layer_1`.
2. Let `CognitionMechanics` substitute the prerequisite Door Goal.
3. Advance ticks; the Sprite arrives at the Door while remaining stuck in `hunt`.

**Proposed Remediation**

Add a category-mismatch Exitpoint to `hunt` (`sprite.goal` and `sprite.goal.category != constants.Goals.TARGET` $\to$ `idle`) and analogous mismatch Exitpoints to `attack` and `follow` so substituted `Goals.DOOR` goals route through `idle` $\to$ `find` $\to$ `interact`.
