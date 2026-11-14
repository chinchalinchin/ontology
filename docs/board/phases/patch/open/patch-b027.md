##### Bug B027: `Engine._drain` Returns Early on Unregistered Event Types, Stranding Remaining Events in `self.bus`

**STATUS**: OPEN
**SEVERITY**: LOW

**Description**

In `src/app/game/engine.py` (lines 102–116), `Engine._drain` iterates over `while self.bus:`. If an event is popped whose type is not in `self.handlers`, line 113 logs a warning and executes `return` instead of `continue`, halting the drain loop and leaving all subsequent events queued in `self.bus` unprocessed for the current tick.

**Steps to Replicate**

1. Append an unregistered event object followed by a valid `MenuEvent` to `engine.bus`.
2. Call `engine._drain()`.
3. Observe that `MenuEvent` remains stranded in `engine.bus` without being handled.

**Proposed Remeditation**

Replace `return` with `continue` on line 113 of `src/app/game/engine.py`.