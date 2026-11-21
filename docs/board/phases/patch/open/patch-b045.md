##### Bug B045: Dead Attackers Can Still Spawn Projectiles and Deal Melee Damage in `CombatMechanics`

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/game/logic/mechanics/spatial/combat.py`, `CombatMechanics.update()` collects attacking entities solely by checking `asset.state.intention == Intentions.ATTACK`, without checking `asset.state.mutators.triggers.dead`:

```python
attackers = [
    asset
    for asset in (
        board.instances(AssetInstances.PLAYERS, layer) +
        board.instances(AssetInstances.SPRITES, layer)
    )
    if asset.state.intention == Intentions.ATTACK
]
```

Similarly, `CombatMechanics._melee()` checks `target.state.mutators.triggers.dead` before applying damage, but never checks `attacker.state.mutators.triggers.dead`. As a result, a dead entity whose `intention` remains `Intentions.ATTACK` (either prior to `TransitionMechanics` / `RemoveMechanics` cleanup or when killed by another attacker earlier in the same batched melee pass) will still emit projectiles via `_project()` and inflict melee damage via `_melee()`.

**Steps to Replicate**

1. Set a Sprite or Player on layer `"0"` to `state.intention = Intentions.ATTACK`, `state.mutators.triggers.dead = True`, equipped with `"longbow"` at `frame = 9, tick = 0` (or `"sword"` at `frame = 3` overlapping a live target).
2. Execute `CombatMechanics().update(board, 0.016, bus, payload)`.
3. Observe that the dead entity still spawns an `"arrow"` onto the Board (or decrements the live target's health).

**Proposed Remediation**

Filter out dead attackers in `CombatMechanics.update()` (`if asset.state.intention == Intentions.ATTACK and not asset.state.mutators.triggers.dead`) and guard against mid-batch attacker death in `CombatMechanics._melee()` (`or attacker.state.mutators.triggers.dead`).

