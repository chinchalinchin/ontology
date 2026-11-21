##### Bug 06-02-09: Invalid Attribute/Enum References & Proximity Stalls in `intentions/main.yaml`

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

Multiple rules in `src/data/config/intentions/main.yaml` diverge from current State models or create deadlocks:
1. `barter -> threaten` (line 27) evaluates `sprite.inventory.wallet`, an attribute that does not exist on `Inventory` (`src/app/models/state/assets/sheets.py`).
2. `barter` and `mine` (lines 26, 147, 151) reference `constants.Goals.LOOT`, whereas Goal semantics specify `RESOURCE`.
3. `idle -> find` for `SUBJECT` and `OBJECT` (lines 95–116) requires `not functions.is_near(..., action.radius)`, yet `idle` defines no transition to `speak` or `interact` when already within `action.radius`—stalling idle Sprites positioned next to their target.
4. `CognitionMechanics._ideate` (lines 380–404) creates `Goals.SUBJECT` for any nearby character regardless of `memory.relationships`, while `find -> speak` (lines 58–62) requires `FRIEND` or `FAMILY`, causing a Sprite with dialogue near a stranger to pursue them and stall indefinitely in `find`.

**Steps to Replicate**

1. Place an `idle` Sprite with `psyche.dialogue = "hello"` directly adjacent (within `action.radius`) to a `FRIEND` character.
2. Run `CognitionMechanics` and `TransitionMechanics`.
3. Observe `_ideate` sets a `SUBJECT` Goal, `idle -> find` evaluates to `False` (already near), and the Sprite never transitions to `speak`.

**Proposed Remediation**

Align `barter`/`mine` with actual `Inventory` fields and `Goals.RESOURCE`; add proximity-ready transitions from `idle` (or remove the negated `is_near` guard on `idle -> find` so `find` immediately transitions to `speak`/`interact` on the following tick); and validate relationship admissibility inside `Ideation` before committing a `SUBJECT` Goal.
