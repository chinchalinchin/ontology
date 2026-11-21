##### Bug B058: `SpriteAnimation.animate` Freezes Expression TTL Decay When `triggers.animated` Is `False`

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

`TransitionMechanics` (`src/app/game/logic/mechanics/intentional/transition.py`, lines 128–135) sets `sprite.state.mutators.triggers.animated = False` whenever a Sprite is stationary (`vx == 0, vy == 0`) in any `StaticIntention` (including `speak` and `idle`). `SpriteAnimation.animate` (`src/app/assets/animations/sheets.py`, lines 22–34) returns early when `not state.mutators.triggers.animated` before decrementing `state.psyche.expression.ttl`. Because `intentions/main.yaml` exits `speak -> idle` only when `not sprite.psyche.expression`, a stationary Sprite speaking to another Sprite (or displaying a `confusion` bubble while stationary in `idle`) never clears its Expression and permanently softlocks in `speak`.

**Steps to Replicate**

1. Place two non-player Sprites adjacent to each other with `velocity = (0, 0)`, `intention = Intentions.SPEAK`, and a `psyche.expression` with `ttl = 30`.
2. Tick `TransitionMechanics` followed by `AnimationMechanics` for 60 ticks.
3. Observe `triggers.animated == False`, `expression.ttl` remains `30`, and the Sprite never transitions back to `idle`.

**Proposed Remediation**

In the refactored `SpriteAnimation(CharacterAnimation)`, execute `super().animate(state, properties)` for body frames and decrement `state.psyche.expression.ttl` unconditionally afterward regardless of `mutators.triggers.animated`.
