##### Bug B066: `SheetState.goal` Default Factory Instantiates a Truthy Empty `Goal()`

**STATUS**: CLOSED
**SEVERITY**: LOW

**Description**

`SheetState` (`src/app/models/state/assets/sheets.py`, line 143) declares `goal: Optional[Goal] = field(default_factory=Goal)`. Any Sprite hydrated without an explicit `goal: null` receives a non-`None`, truthy `Goal(name=None, category=None, layer=None, position=Position(0, 0))`, causing `not sprite.goal` guards across `CognitionMechanics` and `TransitionMechanics` (`idle -> wander`, `_remember`, `_motivate`) to evaluate to `False`.

**Steps to Replicate**

1. Instantiate `SpriteState(id="archaxes", name="npc-1", layer="layer-1")` without specifying `goal`.
2. Evaluate `bool(state.goal)` and observe `True` with `state.goal.category is None`.

**Proposed Remediation**

Default `CharacterState.goal` to `Optional[Goal] = None` (and validate `Goal.category` as `Optional[Enumerated[Goals]]`), auditing `MotionMechanics` and `PlayerMechanics` to confirm `None` safety.