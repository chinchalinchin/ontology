#### Refactor: Phase 09.03 - Bifurcation, Bridges & Buoyancy

**Overview**

Transition the fluid subsystem from single linear raycasts to dynamic field propagation. Introduces multi-branch obstacle bifurcation, bridge layer elevation masks, and kinetic momentum transfer to floating physical bodies ($m > 0$).

##### Goal: Obstacle Bifurcation & Downstream Continuation

When an obstacle occludes a fluid stream, the annular pool should not form a dead end. Fluid that pools laterally around the obstacle should check for downstream clearance along the original source vector, propagating two secondary branch streams past the obstacle flanks until blocked.

##### Goal: Bridge Hitbox Masking & Elevation Layering

Introduce `bridges` under `AssetCategories.CRAFTS`. Bridges declare `elevation: int = 1` and contain hitboxes that override underlying fluid sensor hitboxes during `SpatialMechanics` broad-phase evaluation, permitting characters and crates to cross fluid streams without triggering environmental hazard checks.

##### Goal: Buoyancy & Current Displacement

In `FluidMechanics`, iterate over dynamic weights ($m > 0$, such as crates) intersecting fluid stream or pool hitboxes. Apply a directional impulse proportional to `flow` along the stream vector, simulating buoyancy and flotsam drift without requiring explicit scripting.

##### Tasks

**1. Task: Multi-Branch Fluid Stream Propagation**

*Objective*: Implement recursive branch raycasting in `Actuator` to project secondary flows past obstacle flanks.

* [] Subtask: Refactor `Actuator.pump()` to evaluate left and right flank discharge points after annular pool partitioning.
* [] Subtask: Emit secondary `Hitbox` corridors for active downstream branches.
* [] Subtask: Update `FluidFrame.keys()` to render multi-branch offset manifests.

**2. Task: Bridge Taxonomy & Hitbox Masking**

*Objective*: Implement bridges that dynamically suppress fluid hazard hitboxes.

* [] Subtask: Register `bridges` in `crafts` property schemas with an `elevation: 1` attribute.
* [] Subtask: In `SpatialMechanics`, filter out overlapping `mass: -1` fluid hitboxes when an entity intersects an active bridge hitbox.

**3. Task: Fluid Current Dynamics**

*Objective*: Apply passive velocity vectors to dynamic bodies in fluid corridors.

* [] Subtask: Add `current: Velocity` vector calculation to `Actuator` based on `stream.source`.
* [] Subtask: In `FluidMechanics`, accelerate floating bodies ($m > 0$) along the current vector, clamping to terminal stream speed.

##### Bug B010: Stream and Annular Pool Texture Overdraw

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

When a fluid stream encounters an obstacle and generates an annular pool, `Actuator._partition_pool` creates a top flank hitbox extending from $y = o_y - \text{flow} \cdot f_l$ to $y = o_y$. Concurrently, `Actuator.pump` sets `stream_length = oy - fy`, projecting stream corridor tiles all the way to $o_y$.

In `FluidFrame.keys`, full-tile keys are emitted along the stream corridor from $f_y$ to $o_y$, and the pool iteration subsequently emits full-tile keys across the top flank from $o_y - \text{flow} \cdot f_l$ to $o_y$. The stream corridor column within this band receives two identical overlapping texture blits on the same frame, doubling alpha-blended opacity and causing visual stuttering.

**Proposed Remediation**

In `Actuator.pump`, truncate the active stream length at the outer edge of the annular pool boundary rather than the obstacle face:

```python
if pool_bounds and flow > 0:
    if direction == Directions.DOWN.value:
        stream_length = max(0, pool_bounds.y - fy)
    elif direction == Directions.UP.value:
        stream_length = max(0, fy - (pool_bounds.y + pool_bounds.l))
    elif direction == Directions.RIGHT.value:
        stream_length = max(0, pool_bounds.x - fx)
    elif direction == Directions.LEFT.value:
        stream_length = max(0, fx - (pool_bounds.x + pool_bounds.w))
```
