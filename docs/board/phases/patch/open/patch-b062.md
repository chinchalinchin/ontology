##### Bug B062: `CognitionMechanics.update` Dereferences `board.player().name` Without `None` Guard

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


##### Bug 0602-04: `any_memories_visible` Matches Dead Targets

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/services/translators/environ.py`, `any_memories_visible` checks whether a remembered goal's `name` is in `sprites` on the same layer within `vision.radius`, without checking `not target.mutators.triggers.dead`. A wandering Sprite passing near a remembered target that died while dormant triggers `wander -> hunt` repeatedly until the target is garbage-collected.

**Steps to Replicate**

1. Place a `Goals.TARGET` into `sprite.memory.goals` and set `target.mutators.triggers.dead = True` while retaining the entity on the board.
2. Move the Sprite in `Intentions.WANDER` within `vision.radius` of the dead target.
3. Observe `any_memories_visible` returning `True` and triggering `wander -> hunt`.

**Proposed Remediation**

Guard `any_memories_visible` with `if target.mutators.triggers.dead: continue` for `Goals.TARGET` / `Goals.SUBJECT` candidates.

---

##### Bug B062 (Duplicate): `CognitionMechanics.update` Dereferences `board.player()` Without `None` Guard

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