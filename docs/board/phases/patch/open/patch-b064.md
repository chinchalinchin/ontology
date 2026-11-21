
##### Bug B064: `CognitionMechanics._track` Blocks Cross-Layer Door Subsumption for Static Goals

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/game/logic/mechanics/intentional/cognition.py` (lines 454–465), `_track` returns early for `Goals.POSITION`, `Goals.OBJECT`, and `Goals.PROPERTY` prior to reaching the cross-layer door subsumption block (lines 470–492). If a Sprite holds a static Goal located on another Layer, it never subsumes the Goal into a Door while `NavigationMechanics` (`navigation.py`, line 210) clears its trajectory whenever `goal.layer != sprite.layer`, freezing the Sprite indefinitely.

**Steps to Replicate**

1. Assign a Sprite on `layer-1` a Goal with `category=Goals.OBJECT` (or `POSITION`) and `layer="layer-2"`.
2. Run `CognitionMechanics.update()` and `NavigationMechanics.update()`.
3. Observe no Door goal is assigned and `sprite.state.trajectory.target` remains `None`.

**Proposed Remediation**

Move cross-layer subsumption out of `_track` into `GoalResolver`'s declarative `layered` outcome, enabling uniform Door routing across all non-`DOOR` Goal categories (`TARGET`, `SUBJECT`, `OBJECT`, `POSITION`, `PROPERTY`, `RESOURCE`).
