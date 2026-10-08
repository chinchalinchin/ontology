#### Refactor: Phase 10.01 - Stage Hitboxes & Optimizations

**Overview**

Presently, `Resource` entities maintain static hitboxes declared on immutable `ResourceProperties` (`properties.hitboxes`). When `SeasonMechanics` transitions a resource across biological stages (e.g., from `sapling` to `adult` to `stump`, or `sprout` to `bloom`), physical hitboxes remain invariant. An adult oak tree retains the physical footprint of a sapling, and a harvested crop or stump blocks navigation identically to a mature plant.

This phase integrates dynamic, stage-indexed hitbox evaluation into the ECS pipeline, ensuring physical collision boundaries reflect biological lifecycle progression without violating static property caching.

##### Architectural Analysis

###### 1. The Conflict with Static Hitbox Architecture

In `src/app/assets/base.py`, hitbox resolution evaluates as follows:

```python
@property
def hitboxes(self) -> List[Hitbox]:
    state_hbs = getattr(self.state, "hitboxes", None)
    if state_hbs is not None:
        return state_hbs
    hbs = self.properties.hitboxes
    if not hbs and self.dimensions:
        hbs = [Hitbox(Position(0, 0), self.dimensions)]
    return hbs

```

When `hitboxes: null` is configured on `ResourceProperties`:

1. `hbs` resolves to `None`.
2. `if not hbs and self.dimensions` assigns a fallback hitbox covering the entire entity bounding box (`(0, 0, 94, 137)` for a deciduous tree).
3. This creates two simulation bugs:
  * **Full-Canopy Obstruction**: In top-down 2.5D perspective, characters must walk behind the tree canopy (depth sorted by $y + l$). Obstructing the full $94 \times 137$ box makes the entire air canopy impassable.
  * **Juvenile Collision Imbalance**: A `sapling` (a 12px plant) shares the identical physical obstacle footprint as a mature $94 \times 137$ `adult` tree.

###### 2. Constraints

* **Immutability of Properties**: `AssetProperties` are static and must never mutate at runtime.
* **Zero Allocation in the Inner Loop**: Reconstructing `Hitbox` objects or allocating lists on each collision frame degrades performance.
* **Uniform Sprite Atlas Bounds**: In `StageFrame`, each stage cell occupies an identical $(w, l)$ slice ($94 \times 137$) along the horizontal strip. The coordinate space for hitboxes across all stages remains normalized relative to the cell's top-left origin $(0, 0)$.

###### 3. Resolution: Stage-Indexed Hitbox Mapping

Mirror the existing `SheetProperties.attackboxes` pattern:

* Allow `ResourceProperties.hitboxes` to accept either:
* A static `List[Hitbox]` (for uniform entities like boulders or ores).
* A stage dictionary `Dict[str, List[Hitbox]]` mapping biological stages (`sapling`, `bush`, `adult`, `stump`) to localized collision boxes.


* Update `Asset.hitboxes` to evaluate:
```python
if isinstance(hbs, dict):
    stage = getattr(self.state, "stage", None)
    if stage and stage in hbs:
        return hbs[stage]
    return hbs.get("default", [])

```

* Because `ResourceProperties` is pre-instantiated at boot, indexing `hbs[stage]` returns a cached `List[Hitbox]` in $O(1)$ time with zero heap allocation. When `SeasonMechanics` mutates `resource.state.stage`, the active collision footprint updates on the following frame.

###### 4. Cythonization Candidates

| Target Subsystem | Current Implementation | Bottleneck / Friction | Proposed Cython Architecture |
| --- | --- | --- | --- |
| **`MoistureField.evaluate`** | `app.game.board.fields.MoistureField` (Pure Python) | Iterates Python `StreamSegment` and `PoolSource` dataclasses, executing `math.hypot` and `math.exp`. Fine for static resources, but bottlenecks dynamic raster grids or moving entities. | Implement `cdef class MoistureField` in `libs/core/math/fields.pyx`. Store flat C structs (`CStreamSegment`, `CPoolSource`) in contiguous buffers; evaluate distance attenuation with `hypotf` and `expf` under `nogil`. |
| **Contour Sweeps & Margin Descriptors** | `Cartographer._collect_water_rectangles` & `_coalesce_segments` (Python) | Unpacks fluid states into Python lists of integer tuples; performs boundary step probes with Python dataclasses. | Ingest raw `FluidState` AABB buffers directly in Cython `geometry.contours()`, emitting coalesced shoreline descriptors as flat C structs directly to Python. |

##### Specifications

###### Hitbox Mapping Schema

In `/src/assets/resources/main.yaml`, `hitboxes` accepts stage-keyed dictionary mappings:

```yaml
resources:
  trees:
    deciduous:
      dimensions:
        w: 94
        l: 137
      lifespan: perennial
      loot: wood
      mass: 0
      hitboxes:
        sapling:
          - position: { x: 42, y: 122 }
            dimensions: { w: 10, l: 12 }
        bush:
          - position: { x: 36, y: 114 }
            dimensions: { w: 22, l: 20 }
        branch:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        adult:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        vibrant:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        healthy:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        abscise:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        snowcapt:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        dying:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        dead:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        stump:
          - position: { x: 30, y: 115 }
            dimensions: { w: 34, l: 18 }

```

###### Fallback Correction

In `Asset.hitboxes`, the condition `if not hbs and self.dimensions:` erroneously converts intentional empty hitboxes (`hitboxes: []` or `hitboxes: { sapling: [] }`) into full-dimension obstacles. The fallback must only trigger when `hbs is None`.

###### Zero-Allocation Resolution in Inner Loops

`CollisionMechanics` and `NavigationMechanics` query `asset.hitboxes` and `asset.primitive()` at 60 Hz.

By compiling the stage dictionary into static Pydantic/Cython `Hitbox` model instances during boot-time YAML loading, querying `hbs[resource.state.stage]` is an $O(1)$ reference lookup returning an existing immutable list.

```
Frame Loop (60 Hz)
  │
  ├─► CollisionMechanics / NavigationMechanics:
  │     Query asset.hitboxes
  │       │
  │       ├─► 1. Check state.hitboxes (Dynamic overrides: fluids, shorelines)
  │       │
  │       ├─► 2. Check properties.hitboxes:
  │       │     ├─► Is dict: Return properties.hitboxes.get(state.stage, default)
  │       │     └─► Is list: Return properties.hitboxes
  │       │
  │       └─► 3. Fallback: If hbs is None, return [Hitbox(0, 0, dimensions)]

```

###### Decoupling from SeasonMechanics

Because `Asset.hitboxes` references `state.stage` directly, `SeasonMechanics` does not need to synchronize hitboxes or dispatch collision invalidation events upon stage transitions. Updating `resource.state.stage` instantly changes the spatial boundary seen by all spatial queries on the subsequent frame.

##### Goals

##### Goal: Declarative Stage Hitbox Indexing & Dynamic State Resolution

Allow `ResourceProperties` to declare hitboxes partitioned by stage key. Resolve active physical boundaries dynamically in `Asset.hitboxes` via `state.stage`.

```python
# Schema design for ResourceProperties:
@dataclass(slots=True)
class ResourceProperties(AssetProperties):
    dimensions: Dimensions
    loot: str
    lifespan: Lifespans
    mass: int = 0
    hitboxes: Optional[Dict[str, List[Hitbox]]] = field(default_factory=dict)

```

In `Asset.hitboxes`:

```python
@property
def hitboxes(self) -> List[Hitbox]:
    state_hbs = getattr(self.state, "hitboxes", None)
    if state_hbs is not None:
        return state_hbs

    if isinstance(self.properties.hitboxes, dict):
        stage = getattr(self.state, "stage", None)
        if stage and stage in self.properties.hitboxes:
            return self.properties.hitboxes[stage]

    return self.properties.hitboxes or [Hitbox(Position(0, 0), self.dimensions)]

```

##### Tasks

**1. Task: Resource Hitbox Schema & Model Extension**

*Objective*: Support stage-indexed hitbox dictionaries across data models and YAML schemas.

* [ ] Subtask: Update `ResourceProperties` in `app.models.properties` to type `hitboxes: Optional[Union[List[Hitbox], Dict[str, List[Hitbox]]]]`.
* [ ] Subtask: Verify Pydantic adapter validation in `app.models.adapters` for stage-keyed dictionary structures.
* [ ] Subtask: Configure stage hitboxes for `trees.deciduous` in `/src/assets/resources/main.yaml` constraining adult collision to trunk bounds (`(36, 110, 22, 24)`).
* [ ] Subtask: Configure passable hitboxes (`null` or `[]`) for juvenile stages and crops in `/src/assets/resources/main.yaml`.

**2. Task: Asset Hitbox Retrieval Refactoring**

*Objective*: Update `Asset.hitboxes` to dynamically resolve stage hitboxes with zero allocations.

* [ ] Subtask: Update `Asset.hitboxes` in `app.assets.base` to check `isinstance(self.properties.hitboxes, dict)` and return `self.properties.hitboxes.get(self.state.stage, [])`.
* [ ] Subtask: Replace `if not hbs and self.dimensions` with `if hbs is None and self.dimensions` to prevent converting empty lists into full bounding boxes.
* [ ] Subtask: Ensure `Asset.primitive()` cleanly passes the resolved stage hitboxes into Cython spatial collision arrays.

**3. Task: State Dump Serialization & Verification**

*Objective*: Support stage hitbox dictionaries in diagnostic dumping tools and test suites.

* [ ] Subtask: Update `/src/data/templates/state.md` to handle `props.hitboxes` when structured as a stage dictionary.
* [ ] Subtask: Write unit tests verifying that `tree.hitboxes` reflects trunk dimensions when `stage = "adult"` and stump dimensions when `stage = "stump"`.
* [ ] Subtask: Execute live verification via `python src/cli.py --dump-state start` ensuring character navigation walks behind tree canopies without collision stalls.








# Architectural Review & Synthesis: Post-Phase 10.02

## 2. Code Review & Systemic Refactoring Candidates

### A. Leaky Orchestration in `Actuator.propagate()` vs. `FluidMechanics`

In `src/app/services/generators/game/actuator.py`:

```python
# Actuator.propagate():
# 4. Compile and assign continuous hydrological superposition field to Board
moisture_field = self.compile_moisture_field(layer, board)
board.set_moisture_field(layer, moisture_field)

```

`Actuator` is architecturally defined as a **stateless geometry generator** operating on an individual `Fluid` asset. However, `propagate()` currently takes ownership of layer-wide field compilation:

1. **Redundant Layer Sweeps**: When a layer contains $K$ fluid emitters (e.g., multiple mountain springs), `FluidMechanics.update()` calls `self.actuator.propagate(f, board)` in a loop. Consequently, `compile_moisture_field()` and `board.set_moisture_field()` are invoked $K$ times in the same tick.
2. **Intermediate Stale States**: For emitter $i < K$, emitters $i+1 \dots K$ have not yet updated their truncated lengths, annular pools, or child branches. The field compiled on iteration $i$ is calculated using a mix of updated and stale geometry, causing intermediate inaccurate flux values to be assigned to resources until emitter $K$ concludes.

**Remediation**: Hoist `compile_moisture_field()` and `board.set_moisture_field()` out of `Actuator.propagate()` and place them exclusively in `FluidMechanics.update()`, executing once per invalidated layer after all layer fluids have finished propagating.

### B. Persistent Heap Allocations in `predicates.in_stream()`

In `src/app/game/board/predicates.py`:

```python
def in_stream(position: Position, fluid: Asset) -> bool:
    ...
    aabbs: List[Tuple[int, int, int, int]] = []
    if slen > 0:
        ...
        aabbs.append((...))
    if fluid.state.branches:
        for branch in fluid.state.branches:
            ...
            aabbs.append((...))
    return geometry.inside(px, py, aabbs)

```

Although `SeasonMechanics` no longer calls `predicates.in_stream()`, other systems—such as `board.fluid()`, character locomotion checks, and `Cartographer._resolve_fluid_id()`—still route through it. Instantiating a `list` and multiple 4-tuples on every call remains a hotspot when characters traverse waterways.
Pre-compiling these bounding boxes onto `FluidState._aabbs: List[Tuple[int, int, int, int]]` during `Actuator.propagate()` will reduce `in_stream()` to a zero-allocation pass-through into Cython `geometry.inside()`.

### C. State Coupling in Biome Shoreline Replacement

In `src/app/game/menus/handlers.py`, `SeasonEventHandler.handle()` synchronizes shoreline seasons:

```python
for shore in context.board.shorelines():
    shore.state.season = event.season
    shore.state._keys = None

```

For standard multi-season atlases ($4w \times 4l$), this $O(N)$ cache wipe is optimal. However, if a biome defines distinct asset substitutions across seasons (e.g., substituting `grassy-shore` with `frozen-shelf-shore`), `SeasonEventHandler` cannot evaluate `ShorelineIndex.resolve(tile_id, fluid_id, season)` because `ShorelineState` does not persist the underlying `tile_id` or `fluid_id` that birthed it. To support asset-level biome substitutions without full cartographic contour re-sweeps, `ShorelineState` must record its relational origin keys.

---



---

## 5. Bug Reports

##### Bug B016: Premature Layer MoistureField Compilation in Actuator.propagate()

**STATUS**: OPEN
**SEVERITY**: Medium

**Description**

`Actuator.propagate()` currently invokes `self.compile_moisture_field(layer, board)` and `board.set_moisture_field(layer, moisture_field)` at the end of each individual fluid's propagation pass. In a multi-fluid layer, this causes redundant recalculations ($K$ field compilations for $K$ fluids). More critically, on intermediate iterations, the field is compiled using unpropagated geometry from subsequent fluids, resulting in premature and inaccurate resource moisture fluxes until the final fluid finishes propagating.

**Steps to Replicate**

1. Set up a layer with two fluid emitters (`fluid_1` and `fluid_2`) positioned near separate crops.
2. Trigger gate invalidation affecting both fluids simultaneously.
3. Observe that after `fluid_1` propagates, `board.set_moisture_field()` is called immediately while `fluid_2` still holds pre-invalidation stream lengths and pool dimensions.

**Proposed Remediation**

Remove field compilation from `Actuator.propagate()`. Move `compile_moisture_field()` and `board.set_moisture_field()` into `FluidMechanics.update()`, invoking it once per dirty layer after all layer fluids have completed propagation.

---

##### Bug B017: Ephemeral AABB Allocation in predicates.in_stream()

**STATUS**: OPEN
**SEVERITY**: Low

**Description**

`predicates.in_stream()` dynamically instantiates a new Python `list` and multiple 4-tuples on every call to construct corridor bounding boxes for `geometry.inside()`. While `SeasonMechanics` no longer calls `in_stream()`, queries from `board.fluid()`, entity locomotion, and `Cartographer._resolve_fluid_id()` continue to incur transient heap allocations during high-frequency execution.

**Steps to Replicate**

1. Query `board.fluid(layer, pos)` repeatedly at 60 Hz over an active branched fluid corridor.
2. Profile Python heap allocations; observe ephemeral lists and tuples generated by `in_stream()`.

**Proposed Remediation**

Pre-compile stream and branch AABBs onto `FluidState._aabbs` in `Actuator.propagate()`. Update `predicates.in_stream()` to pass `fluid.state._aabbs` directly to `geometry.inside()`.

---



##### Tasks

**1. Task: Schema Migration for Stage Hitboxes**

*Objective*: Extend resource property schema and Pydantic adapters to support stage-keyed hitbox dictionaries.

* [ ] Subtask: Update `ResourceProperties` in `app.models.properties` to support `hitboxes: Union[List[Hitbox], Dict[str, List[Hitbox]]]`.
* [ ] Subtask: Update `src/assets/resources/main.yaml` to configure distinct hitboxes for `sapling`, `adult`, and `stump` stages.

**2. Task: Dynamic Asset Hitbox Stage Resolution**

*Objective*: Update `Asset.hitboxes` property to extract stage-specific hitboxes when present.

* [ ] Subtask: Refactor `Asset.hitboxes` in `app.assets.base` to inspect `state.stage` against `properties.hitboxes`.
* [ ] Subtask: Update `BoardCaches.rebuild_weights()` and `BoardCaches.rebuild_obstacles()` to invalidate spatial caches when a resource stage changes.

---

#### Backlog: Cython Acceleration of Environmental Potential Fields

**Overview**

While static resources ($m = 0$) evaluate environmental moisture fields once during fluid invalidation, future mechanics—such as dynamic crop planting, entity wading resistance, and fluid-to-tile moisture percolation—require high-frequency sampling across dynamic coordinates. Migrating `MoistureField` and distance attenuation math to a Cython extension type will eliminate Python interpreter overhead and allow non-blocking evaluation across the GIL boundary.

##### Goal: C-Level Potential Field Evaluator

Implement `libs/core/math/fields.pyx` providing contiguous C memory buffers for linear and disk potential sources with `nogil` sampling.

```cython
cdef struct CStreamSegment:
    float x1, y1, x2, y2
    int flow

cdef struct CPoolSource:
    float cx, cy, radius
    int flow

cdef class CMoistureField:
    cdef CStreamSegment* streams
    cdef int stream_count
    cdef CPoolSource* pools
    cdef int pool_count
    cdef float sigma, phi_0

    cpdef float evaluate(self, float x, float y) noexcept nogil:
        # Vectorized Euclidean line segment projection and exponential decay
        ...

```

##### Tasks

**1. Task: Cython MoistureField Implementation**

*Objective*: Create `libs/core/math/fields.pyx` and register with `setup.py`.

* [ ] Subtask: Implement `CStreamSegment` and `CPoolSource` structs with dynamic memory allocation in `__cinit__` and `__dealloc__`.
* [ ] Subtask: Implement `evaluate(x, y)` in pure C with `noexcept nogil`.
* [ ] Subtask: Bind Python-accessible wrapper methods in `libs.core.math.fields`.

---

## 7. Synthesis & Next Horizons

With Phase 10.02 closed, the simulation achieves a decoupled equilibrium across spatial and temporal dimensions:

* **Geometry**: Procedural shoreline generation is isolated to geometric shift events (`pre_sig != post_sig`).
* **Macro-Temporal Cycles**: Calendar progression and seasonal palette swaps invalidate frame keys via `SeasonEvent` without touching geometric contour boundaries.
* **Hydrology**: Fluid networks inject into a continuous potential field, eliminating per-frame spatial broad-phase lookups and GC allocations.

The immediate priorities on the horizon are:

1. **Closing Patch B013**: Implementing the target clear pass in `Screen.reconstruct()` to prevent transparency bleed on foreground seasonal canopies.
2. **Phase 10.01 (Stage Hitboxes)**: Aligning physical obstacle geometry with biological growth stages.
3. **Hydrodynamic Immersion (Goal 09)**: Unifying character current drift, buoyancy, and submerged split shaders.