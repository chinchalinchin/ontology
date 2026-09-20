

### Documentation Divergences

#### Draft: Fluid Taxonomy & State Model Synchronization

* **Page**: `docs/01-assets.md`
* **Heading**: `Fluids`

##### Drift

The `docs/01-assets.md` specification still references the deprecated design where `source` and `flow` were properties under `FluidProperties`, and `FluidState` maintained explicit texture coordinate offset arrays (`stream` and `pool` lists of tuples). In the codebase, `source` and `flow` were migrated to `FluidState` to support dynamic per-instance stream orientation, fluids use `EffectProperties` directly, and `FluidState` stores only scalar physical dimensions (`length`, `pool: Optional[Pool]`, and compound `hitboxes`).

##### Update

```markdown
### Fluids

Fluids are directional Effects that project along a designated source vector until obstructed by environmental boundaries or physical weights. Because Fluid assets span multiple grid units, they bypass standard geometric height calculation (`pos.y + dim.l`).

**Z-Ordering & Sorting**

Fluids declare an explicit `height: 0` and `depth: -1`. This ensures the rendering pipeline (`Screen.draw`) sorts the compound stream directly above the pre-rendered terrain canvas (`bg_canvas`) while maintaining correct perspective beneath dynamic bodies, movable crates, bridges, and foreground overlays.

**Properties: EffectProperties**

* `dimensions: Dimensions`
* `count: int`
* `lifecycle: Lifecycle`
* `mass: int = -1`
* `hitboxes: Optional[List[Hitbox]]`

**Frame: FluidFrame**

* `keys(id, state)`: Dynamically calculates full tile keys and fractional slice keys across directional axes from `state.length` and `state.pool`.
* `index(id, properties)`: Indexes full frames and directional fractional slices (both forward and reverse across $w$ and $l$) for each animation frame index $0 \le f < \text{count}$.

**State: FluidState**

* `layer: Optional[str]`
* `position: Position`
* `source: Directions = Directions.DOWN.value`
* `flow: int = 1`
* `length: int = 0`
* `pool: Optional[Pool] = None`
* `hitboxes: List[Hitbox]`
* `dirty: bool = True`
* `height: Optional[int] = 0`
* `depth: int = -1`

```

---

#### Draft: IterableFrame Index Key Scheme

* **Page**: `docs/01-assets.md`
* **Heading**: `Chests`

##### Drift

The documentation specifies `IterableFrame.index` as returning `{ "{id}-{properties.count}": ... }`, implying only a single terminal crop key is registered. In `app/assets/frames/core.py`, `IterableFrame.index` iterates over `range(properties.count)` and generates keys for each individual index `"{id}-{i}"`.

##### Update

```markdown
**Frame: IterableFrame**

* `keys(id, state): returns [ ("{id}-{state.animation.frame}", 0, 0) ]`
* `index(id, properties): returns { "{id}-{i}": (i * w, 0, w, l) for i in range(properties.count) }`

```

---

#### Draft: FluidMechanics Execution & State Access

* **Page**: `docs/05-mechanics.md`
* **Heading**: `FluidMechanics`

##### Drift

The mechanics documentation states that raycasting reads `properties.source` to determine propagation orientation. Following the refactor in the task board, `source` is stored on `state.source`.

##### Update

```markdown
**FluidMechanics**

FluidMechanics governs fluid emission across active layers. It executes after physical momentum updates (`MotionMechanics` and `CollisionMechanics`) and uses reactive dirty-checking:

1. **Change Detection**: Inspects active crates ($\vert{}v\vert{} > 0$) and switch-linked gates. If any dynamic obstacle within a fluid's influence zone mutates, `fluid.state.dirty` is set to `True`.
2. **Raycast Truncation**: Raycasts along `state.source` against board boundaries and non-sheet solid assets ($m \ge 0$). Calculates distance $D$ to the nearest occluder.
3. **Annular Pooling**: If the occluder is an internal obstacle rather than a perimeter boundary, expands a radial pool of radius `state.flow` around the obstacle perimeter, partitioned into four rectangular bounding boxes.
4. **Hitbox Update**: Injects composite hitboxes for the stream path and pool boundaries into the broad-phase spatial hash.

```

---

### Bug Reports

##### Bug B009: Directional Up/Left Occlusion Blindspot in Raycast Candidate Collection

**STATUS**: OPEN

**SEVERITY**: HIGH

**Description**

In `Actuator._collect_obstacles`, candidate filtering for upward (`UP`) and leftward (`LEFT`) fluid propagation discards valid obstacles located immediately in front of or adjacent to the emitter origin.

For `direction == Directions.UP.value`, the filter executes:

```python
if (oy + ol) >= fy:
    continue

```

Because upward raycasts target decreasing Y-coordinates ($y < f_y$), an obstacle immediately adjacent or slightly overlapping the emitter top edge ($o_y + o_l = f_y$) evaluates to `True` and is excluded from the obstacle manifest. The raycast completely ignores the obstacle and extends past it to the map perimeter. The identical defect occurs on lateral leftward propagation (`ox + ow >= fx`).

**Steps to Replicate**

1. Place an obstacle Crate of dimensions `(32, 32)` at position `(100, 68)`.
2. Place a Fluid emitter of dimensions `(32, 32)` at position `(100, 100)` with `source = up`.
3. The Crate's bottom edge is at $y = 68 + 32 = 100 = f_y$.
4. Trigger `Actuator.pump()`. `_collect_obstacles` discards the crate because `(oy + ol) >= fy` is `True`.
5. The fluid raycasts through the crate to the map boundary.

**Proposed Remediation**

Filter candidate obstacles based on whether their entire body is strictly behind the emitter origin, taking the stream's cross-sectional axis into account:

```python
if direction == Directions.UP.value and oy >= fy:
    continue
elif direction == Directions.DOWN.value and (oy + ol) <= fy:
    continue
elif direction == Directions.LEFT.value and ox >= fx:
    continue
elif direction == Directions.RIGHT.value and (ox + ow) <= fx:
    continue

```

---

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

---

##### Bug B011: Missing Chests in Obstacle Catalogue

**STATUS**: OPEN

**SEVERITY**: LOW

**Description**

In `Board.obstacles(layer)`, the catalogue query gathers `crates`, `gates`, `struts`, and `signs`, but omits `chests`. While `Board.weights(layer)` includes chests (due to `mass: int = 0`), any subsystem querying `Board.obstacles()` directly will fail to treat chests as solid colliders or occluders.

**Proposed Remediation**

Update `Board.obstacles()` to include `AssetInstances.CHESTS.value`:

```python
chests = self._cached_instances.get(layer, {}).get(AssetInstances.CHESTS.value, [])
return crates + gates + struts + signs + chests

```

---

### Backlog Proposal

#### Backlog: Hydrodynamic Flow Bifurcation, Bridges & Buoyancy

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