# Bug B000: Attacking

**Status:** CLOSED
**Resolution:** PATCHED

When pressing the Space Bar to attack, the player briefly (*very* briefly, less than a fraction of a second) enters into the appropriate Action, but immediately returns to the Walk Action.

**Initial Analysis**

It appears as though there needs to be a check in PlayerMechanics to prevent the Player intention from being overwritten when the Player is in a "blocking" Action.

Blocking Actions are: `cast`, `slash`, `thrust`, `shoot`

- Initial Proposed Solution: Add an `busy` mutator to the Sprite state. Add a check on the Player `update()` method to prevent Intention overwriting during blocked states. When Player enters these actions, set `busy` to `True`. Need to be careful to flip it off when action is concluded.

**Summary of Changes:**

1. **Intention Persistence:** Modified `PlayerMechanics` to respect blocking intentions (e.g., `ATTACK`, `MINE`). Replaced the unconditional `IDLE` fallback with a frame-aware check that only releases the player once the action's animation sequence completes (`frame == 0`).
2. **Registry Mapping Alignment:** Corrected the dimension properties for `shortsword` and other affected equipment in `sheets/main.yaml`. Equipment dimensions must match the parent sprite (e.g., `64x64`) to align with the `lpc-slash` coordinate mapping.

**Lessons Learned:**

* **Intrinsic State over Redundant Flags:** Avoid adding boolean flags (like `busy`) when the state is already mathematically represented by existing structures (`animation.frame > 0` during a blocking intention).
* **Cython/SDL Silent Failures:** C-level renderers inherently fail silently when fed mathematically impossible bounds. If a mapped coordinate asks SDL to crop a 64x64 square starting at Y=480 on a 32x32 image, the GPU yields an empty texture rather than a traceback. Telemetry and Registry introspection tools are mandatory for debugging the Python-to-C boundary.