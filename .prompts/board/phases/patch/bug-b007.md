##### Bug B007: Cradle Spawning

**STATUS**: OPEN

**SEVERITY**: HIGH

**Description**

`Cradle.spawn_temporary()` in `src/app/services/generators/cradle.py` instantiates the spawned asset with `PositionalState`. `PositionalState` only provides `position` and `velocity`; it does not contain the `animation: AnimationState` field. When `AnimationMechanics.update()` iterates over Effect assets and invokes `animate()`, `TemporaryAnimation` attempts to access `state.animation.frame`, triggering an unhandled `AttributeError`. Additionally, `RemoveMechanics` crashes when attempting to read `effect.state.animation.frame`.

**Steps to Replicate**

1. Invoke `board.cradle.spawn_temporary("dust-puff", "0", Position(10, 10))` during runtime.
2. Advance the engine tick into `AnimationMechanics.update()`.
3. Observe `AttributeError: 'PositionalState' object has no attribute 'animation'`.

**Proposed Remediation**

Modify `Cradle.spawn_temporary()` to instantiate `AnimatorState` (or its functional derivative) initialized with a valid `AnimationState` instance.