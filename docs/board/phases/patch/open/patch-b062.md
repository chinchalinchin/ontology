##### Bug 06-02-06: `CognitionMechanics.update` Dereferences `board.player().name` Without `None` Guard

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

`CognitionMechanics.update` (`src/app/game/logic/mechanics/intentional/cognition.py`, line 168) executes `if sprite.name == board.player().name:` on every Sprite iteration without verifying `board.player()` is not `None`. On any Board lacking a Player entity (such as headless NPC tests or simulations), this raises `AttributeError: 'NoneType' object has no attribute 'name'`.

**Steps to Replicate**

1. Instantiate a `Board` containing at least one `AssetInstances.SPRITES` entity and zero `AssetInstances.PLAYERS` entities.
2. Call `CognitionMechanics().update(board, delta, bus, payload)`.
3. Observe `AttributeError`.

**Proposed Remediation**

Hoist `player = board.player()` outside the Sprite loop and guard with `if player and sprite.name == player.name: continue` (matching `NavigationMechanics` and `TransitionMechanics`).
