##### Bug B063: `CognitionMechanics.door` Can Target Non-Interactive `LayerProjections.OUT` Shadow Doors

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

`CognitionMechanics.door` (`src/app/game/logic/mechanics/intentional/cognition.py`, lines 139–151) scans `board.instances(AssetInstances.DOORS, sprite.state.layer)` without filtering by `DoorState.projection`. Because Board hydration deploys reciprocal `LayerProjections.OUT` shadow doors onto destination layers (with empty `LayeredHitbox.elevations()`), a Sprite exploring unmapped doors can select an `OUT` projection that it can never physically intersect or traverse.

**Steps to Replicate**

1. Deploy a Door on `layer-1` projecting an `OUT` shadow footprint onto `layer-2`.
2. Give a Sprite on `layer-2` (within vision radius of the `OUT` shadow, with empty `memory.doors`) a Goal located on `layer-1`.
3. Call `CognitionMechanics.door(sprite, board)`.
4. Observe the `OUT` shadow door may be returned as `target_door`.

**Proposed Remediation**

Filter candidate doors in `GoalResolver.door()` to strictly require `d.state.projection == LayerProjections.IN`.

**NOTE**

This is not a bug. How else would a Sprite get to the other layer? The reciprocal shadow of a Door is *supposed* to be able to intersect and interact with a Door Shadow.