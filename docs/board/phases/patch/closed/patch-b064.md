##### Bug B064: `CognitionMechanics._track` Blocks Cross-Layer Door Subsumption for Static Goals

**STATUS**: CLOSED
**SEVERITY**: MEDIUM

**Description**

In `src/app/game/logic/mechanics/intentional/cognition.py` (lines 454–465), `_track` returns early for `Goals.POSITION`, `Goals.OBJECT`, and `Goals.PROPERTY` prior to reaching the cross-layer door subsumption block (lines 470–492). If a Sprite holds a static Goal located on another Layer, it never subsumes the Goal into a Door while `NavigationMechanics` (`navigation.py`, line 210) clears its trajectory whenever `goal.layer != sprite.layer`, freezing the Sprite indefinitely.

**Steps to Replicate**

1. Assign a Sprite on `layer-1` a Goal with `category=Goals.OBJECT` (or `POSITION`) and `layer="layer-2"`.
2. Run `CognitionMechanics.update()` and `NavigationMechanics.update()`.
3. Observe no Door goal is assigned and `sprite.state.trajectory.target` remains `None`.

**Proposed Remediation**

Move cross-layer subsumption out of `_track` into `GoalResolver`'s declarative `layered` outcome, enabling uniform Door routing across all non-`DOOR` Goal categories (`TARGET`, `SUBJECT`, `OBJECT`, `POSITION`, `PROPERTY`, `RESOURCE`).

##### Bug B064 (Duplicate): Cross-Layer Door Subsumption Deadlocks Sprites in `hunt`

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
