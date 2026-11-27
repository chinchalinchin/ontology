##### Bug B067: `find -> interact` Radius Stops Sprites Outside `InteractionMechanics` Hitbox Overlap

**STATUS**: CLOSED
**SEVERITY**: HIGH

**Description**

`intentions/main.yaml` transitions `find -> interact` when `functions.is_near(sprite.position, sprite.goal.position, sprite.mutators.parameters.action.radius)` holds (default `30` px). Because `interact` belongs to `StationaryIntentions`, `NavigationMechanics` immediately clears the trajectory and halts locomotion. However, `InteractionMechanics` executes Door/Chest interactions on physical hitbox overlap (`self.intersections(assets)`). With Sprite hitboxes inset at `(x=23, y=34, w=18, l=15)` inside a `64x64` frame, the Sprite stops up to 30 px away without overlapping the target hitbox, deadlocking permanently in `interact`.

**Steps to Replicate**

1. Assign an autonomous Sprite a same-layer `Goals.OBJECT` (or `Goals.DOOR`) Goal with default `action.radius = 30`.
2. Advance ticks until the Sprite enters `action.radius` of the target's origin.
3. Observe `TransitionMechanics` switch `find -> interact` while `hitboxes` do not intersect; `InteractionMechanics` never fires and `interact -> idle` (`not sprite.goal`) is never satisfied.

**Proposed Remediation**

Align the initiation predicate and interaction geometry: either have `InteractionMechanics` evaluate `self.proximities` for Sprite-initiated `interact` transitions (matching `action.radius`), or tighten `find -> interact` / `NavigationMechanics` arrival so the Sprite overlaps the target's physical hitbox before halting.
