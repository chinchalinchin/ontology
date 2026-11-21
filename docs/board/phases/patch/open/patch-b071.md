##### Bug 0602-05: `CognitionMechanics.update` Dereferences `board.player()` Without `None` Guard

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/game/logic/mechanics/intentional/cognition.py`, `CognitionMechanics.update` evaluates `if sprite.name == board.player().name:` on every sprite iteration without checking whether `board.player()` is `None` (unlike `TransitionMechanics` and `NavigationMechanics`), causing an `AttributeError` on boards without a deployed Player (such as headless or unit-test simulations).

**Steps to Replicate**

1. Instantiate a `Board` containing at least one `Sprite` and zero `Player` assets.
2. Invoke `CognitionMechanics().update(board, delta, bus, payload)`.
3. Observe `AttributeError: 'NoneType' object has no attribute 'name'`.

**Proposed Remediation**

Hoist `player = board.player()` outside the sprite loop and guard with `if player and sprite.name == player.name: continue`.
