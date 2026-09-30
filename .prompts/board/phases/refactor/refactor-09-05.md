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


---

#### Backlog: Phase 09.05 - Bridges, Bifurcation & Buoyancy

**Overview**

Expand the environmental mechanics to support recursive stream bifurcation across orthogonal axes, elevate characters and frictive assets over fluids via static architectural bridges, and generalize buoyancy properties across dynamic bodies.

##### Goal: Generic Buoyancy Mechanics

Decouple floating velocity assignment in `fields.py` from `AssetInstances.CRATES.value` by introducing a `buoyant: bool` property on dynamic objects ($m > 0$).

```python
# app/models/properties.py
@dataclass(slots=True)
class ObjectProperties(AssetProperties):
    dimensions: Dimensions
    mass: int = 0
    count: int = 1
    hitboxes: Optional[List[Hitbox]] = field(default_factory=list)
    buoyant: bool = False

```

##### Goal: Architectural Bridges and Elevation Decks

Introduce static bridge assets that define elevated surface planes across fluid corridors, intercepting character entities to suppress fluid velocity impulses and shoreline ledge drops.

```python
# app/game/logic/modules/motion/fields.py
# Bridges act as static surface interceptors, similar to Rafts but immovable (m = 0)
for bridge in layer_bridges:
    if _intersects(asset, bridge):
        on_bridge = True
        asset.state.mutators.triggers.submerged = False
        break

```

##### Tasks

**1. Task: Generalize Dynamic Buoyancy**

*Objective*: Allow any dynamic object to float in fluid currents based on properties rather than instance whitelisting.

* [ ] Subtask: Add `buoyant: bool = False` to `ObjectProperties` in `src/app/models/properties.py`.
* [ ] Subtask: Refactor `fields.py` to check `asset.properties.buoyant` when applying stream velocity and suppressing tile friction.

**2. Task: Static Bridge Surface Interception**

*Objective*: Prevent fluid immersion and shoreline triggering when traversing fluid streams via bridges.

* [ ] Subtask: Create `Bridge` instance under `Objects` hierarchy with static mass ($m = 0$).
* [ ] Subtask: Update `fields.update()` to evaluate Bridge intersections prior to shoreline and fluid immersion checks.

**3. Task: Recursive Stream Bifurcation**

*Objective*: Enable fluids striking static obstacles to branch into secondary corridors when unobstructed.

* [ ] Subtask: Implement orthogonal branch raycasting in `Actuator` when an obstacle is struck and `flow > 1`.
* [ ] Subtask: Partition compound hitboxes across bifurcated child streams.
* [ ] Subtask: Verify layer water rectangle collection ingests bifurcated branches for seamless contour shoreline generation.