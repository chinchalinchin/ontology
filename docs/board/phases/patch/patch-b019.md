##### Bug B019: Infinite Goal Ping-Pong Loop on Abandoned `TARGET` and `SUBJECT` Goals in `CognitionMechanics`

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

When a Sprite pursues a `TARGET` or `SUBJECT` whose sight has been lost (`not sprite.state.mutators.triggers.vision`) and reaches the target's last-known `goal.position`, `CognitionMechanics._resolve` shelves the goal into `sprite.state.memory.goals[goal.name] = goal` and sets `sprite.state.goal = None`.

In `CognitionMechanics._remember` (`src/app/game/logic/mechanics/intentional/cognition.py`, lines 341–351), the guard intended to keep the abandoned goal dormant is:

```python
if candidate.category in (
    Goals.TARGET.value, 
    Goals.SUBJECT.value
):
    if self.nearby(
        candidate.position, 
        sprite.state.position, 
        action_radius
    ) and not sprite.state.mutators.triggers.vision:
        continue

```

This guard fails for two independent reasons:

1. When the Sprite transitions `idle -> wander` and `CognitionMechanics._project` assigns a `wander` (`Goals.POSITION`) goal, `CognitionMechanics._track` (line 487) sets `sprite.state.mutators.triggers.vision = True` for all `POSITION` goals. When the wander goal resolves, `triggers.vision` remains `True`.
2. Once the Sprite moves outside `action_radius` of the empty `candidate.position` (e.g., after completing a single `wander` step), `self.nearby(candidate.position, sprite.state.position, action_radius)` evaluates to `False`. On the very next tick in `idle`, `_remember` pops `candidate` from `memory.goals` with the exact same stale `candidate.position`, forcing the Sprite to walk back to the empty coordinate in an infinite loop.

**Steps to Replicate**

1. Deploy a Sprite with a `TARGET` or `SUBJECT` goal whose target entity moves outside `vision_radius`.
2. Allow the Sprite to reach `goal.position`; `_resolve` abandons the goal into `memory.goals`.
3. The Sprite transitions `idle -> wander`, moves beyond `action_radius` of the abandoned coordinate, and resolves its `wander` goal (`wander -> idle`).
4. On the next tick, `_remember` pops the un-updated `candidate` goal from `memory.goals` and sends the Sprite back to the empty coordinate.

**Proposed Remeditation**

Add a `dormant: bool = False` attribute to `Goal` in `src/app/models/state/assets/sheets.py`. In `CognitionMechanics._resolve`, set `goal.dormant = True` when shelving an un-sighted target at its last-known position. In `CognitionMechanics._scan`, set `mem_goal.dormant = False` when `other_name` is spotted within `vision_radius`. In `CognitionMechanics._remember`, simply check `if candidate.dormant: continue`.