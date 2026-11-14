
#### Backlog: Cythonization

**Overview**

While static resources ($m = 0$) evaluate environmental moisture fields once during fluid invalidation, future mechanics—such as dynamic crop planting, entity wading resistance, and fluid-to-tile moisture percolation—require high-frequency sampling across dynamic coordinates. Migrating `MoistureField` and distance attenuation math to a Cython extension type will eliminate Python interpreter overhead and allow non-blocking evaluation across the GIL boundary.

##### Architectural Analysis

###### Cythonization Candidates

| Target Subsystem | Current Implementation | Bottleneck / Friction | Proposed Cython Architecture |
| --- | --- | --- | --- |
| **`MoistureField.evaluate`** | `app.game.board.fields.MoistureField` (Pure Python) | Iterates Python `StreamSegment` and `PoolSource` dataclasses, executing `math.hypot` and `math.exp`. Fine for static resources, but bottlenecks dynamic raster grids or moving entities. | Implement `cdef class MoistureField` in `libs/core/math/fields.pyx`. Store flat C structs (`CStreamSegment`, `CPoolSource`) in contiguous buffers; evaluate distance attenuation with `hypotf` and `expf` under `nogil`. |
| **Contour Sweeps & Margin Descriptors** | `Cartographer._collect_water_rectangles` & `_coalesce_segments` (Python) | Unpacks fluid states into Python lists of integer tuples; performs boundary step probes with Python dataclasses. | Ingest raw `FluidState` AABB buffers directly in Cython `geometry.contours()`, emitting coalesced shoreline descriptors as flat C structs directly to Python. |

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

