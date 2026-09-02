# Bug B001: Layering

**Status:** OPEN
**Resolution:** N/A

Layers can be instantiated on the fly through the `build` Intention and Struts/Compositons. Currently, Screens are initialized and keyed by layer. If a Layer is instantiated during the game, lookups for this key against the Screen will fail.

**Initial Analysis**

Need to identify what Intentions create new Layers. Right now, just: `build`. Layer is created during Mechanic and added to the board. Needs to bubble up back to the Engine so Engine can add Screen.

- Proposed Solutions:
    - Event prcoessing for "rescreening"
    - Return value for Mechanic `update()` to signal "rescreening"
    - Add "dirty" flag to Board to signal "rescreening".

**Summary of Changes:**

TODO

**Lessons Learned:**

TODO