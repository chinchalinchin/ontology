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