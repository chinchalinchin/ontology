##### Bug 061: Per-Tick `logger.info` Logging in `PlayerMechanics` and Dead Statement in `StateFrame`

**STATUS**: OPEN
**SEVERITY**: LOW

**Description**

1. `src/app/game/logic/mechanics/intentional/player.py` emits two `logger.info` statements on every simulation tick while `player.state.intention == Intentions.ATTACK`, causing hot-loop log I/O overhead analogous to `SpriteFrame`.
2. `src/app/assets/frames/sheets.py` contains a stray no-op expression `properties.actions` in `StateFrame.index`.

**Steps to Replicate**

1. Hold or trigger `Intentions.ATTACK` on the Player with logging at `INFO` level.
2. Observe two `SheetState(...)` / `Equipment(...)` log entries emitted every tick for the full duration of the attack animation.

**Proposed Remediation**

Downgrade the per-tick `logger.info` calls in `PlayerMechanics` (and `SpriteFrame`) to `logger.debug`, and remove the dead `properties.actions` statement in `StateFrame.index`.