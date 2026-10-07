#### Refactor: Phase 10.02 - Shoreline Seasonal Indexing

**Overview**

Integrate environmental Shorelines with temporal seasonality by extending atlas indexing across cardinal directions and calendar seasons. Decouple high-frequency ISL stage transition checks from the 60 Hz loop, eliminate transient heap allocation in hydrological probing, and ensure static screen reconstruction clears transparent fore canvases between season transitions.

##### Architectural Analysis I

###### Optimizations

1. Inner-Loop Heap Allocation in `SeasonMechanics._probes`

In `src/app/game/logic/mechanics/world/seasons.py`:

```python
@staticmethod
def _probes(resource: Asset) -> List[Position]:
    ...
    return [
        Position(mid_x, mid_y),
        Position(mid_x, pos.y - 1),
        Position(mid_x, pos.y + l),
        Position(pos.x - 1, mid_y),
        Position(pos.x + w, mid_y)
    ]

```

`SeasonMechanics.update()` executes at $60\text{ Hz}$. For every active `Resource` on the board, `_probes()` instantiates five heap-allocated Python `Position` objects each tick to query `board.fluid()`. For dense environments (such as an orchard or forest with 100+ trees), this generates $\sim 30{,}000$ transient Python allocations per second, violating the engine's driving principle of zero heap allocation in inner loops.

2. High-Frequency Evaluation of Declarative ISL Stage Transitions

In `SeasonMechanics.update()`:

```python
executor = self.executors.get(resource.properties.lifespan)
...
next_stage = executor.evaluate(resource.state.stage, locals)

```

Biological stage transitions are evaluated every frame ($16.6\text{ ms}$) across all resources. While moisture diffusion must integrate continuously with frame delta time ($\Delta t$), biological growth checks (which depend on macro seasons and discrete moisture thresholds) do not require $60\text{ Hz}$ AST/lambda evaluation. Throttling stage evaluation to period boundaries or a dedicated low-frequency accumulator (e.g., $1\text{ Hz}$) would eliminate unnecessary CPU overhead.

3. Texture Overdraw in `Screen.reconstruct()`

In `Screen.reconstruct()`:

```python
def reconstruct(self, tiles: List[Asset], calendar: CalendarState) -> None:
    back_tiles, fore_tiles = self._prerender(tiles, calendar)
    render.construct(self.bg_canvas, back_tiles)
    render.construct(self.fg_canvas, fore_tiles)

```

`render.construct()` executes `SDL_RenderCopy` calls directly onto the existing target texture. While opaque `back_tiles` overwrite underlying pixels cleanly, transparent foreground canopy tiles (`fg_canvas`) will overdraw new seasonal pixels directly on top of previous season textures without an intermediate clear pass.

##### User Review I 

###### Rendering

I do not believe `eras()` can support Shoreline Frame rendering. `eras()` is the projection of an external state onto the animation space of an Asset, i.e. SeasonalFrame accepts the Calendar state to retrieve from the frame key from Tile animation space; in this way the rendered Tile Frame is dependent on the Board state. 

However, the Shoreline Frame is dependent on its own state, with caveat that it caches its frame keys once computed and its state is procedurally generated in the Cartographer. 

Moreover, utilizing `eras()` would change the rendering process, as Shorelines are currently rendered through `keys()`. But, thinking upon that, this is incorrect, as Shorelines do not need to retrieve new keys every single frame. They are only recomputed when Fluid flow is altered. So, perhaps it does make sense to have Shorelines rendered through `eras()`. This will entail an analysis of what needs to change in the rendering workflow.

Also, tangentially related, the indexing for Shoreline frames will need to range over an enumeration of `app.config.enums.Seasons`.

###### Cythonization

The probing math in SeasonMechanics seems ripe for Cythonization, considering Bug B018.

##### Architectural Analysis II

###### 1. Rendering Lifecycle: `eras()` vs. `keys()` for Shorelines

In User Review I, the question arose whether `Shoreline` rendering should transition from `keys()` to `eras()`. A deeper inspection of the rendering pipeline reveals why **`eras()` cannot support Shorelines without breaking the engine's visual hierarchy**:

1. **Painter's Algorithm & Z-Ordering Invariant**:
    * `Screen._prerender()` bakes `eras()` outputs strictly onto static textures: `bg_canvas` (Back Tiles) and `fg_canvas` (Fore Tiles).
    * In the active draw loop (`Screen.draw()`), dynamic world entities sort by `(height, depth)`: $\text{Fluids} \, (\text{depth}: -1) < \text{Shorelines} \, (\text{depth}: 0) < \text{Bridges} \, (\text{depth}: 1)$
* Fluids are dynamic animated effects (`FluidState` cycles micro-frames and expands/contracts corridors). If Shorelines were baked into `bg_canvas`, they would be stamped **beneath** fluid streams. The opaque water bodies would overdraw and completely occlude the outer land fringe. Shoreline fringes must render on top of water (`depth: 0` over `depth: -1`).
2. **Interface Contract of `eras()**`:
    * `Frame.eras(id: str, calendar: CalendarState)` operates without entity `state`. Static tiles rely purely on their grid multiplier (`multiple.nx`, `multiple.ny`).
    * Procedural shorelines require `state.orientation` (to select cardinal rows) and `state.length` (to calculate full-tile intervals and fractional remainder slices). Stripping `state` from `eras()` makes computing slices impossible.
3. **Execution Cost**:
    * `CardinalFrame.keys()` already memoizes slice sequences onto `state._keys`. During standard 60 Hz execution, it performs an $O(1)$ reference check.
    * Shoreline keys only require invalidation when either:
    * Fluid geometry shifts (already handled via `Cartographer.purge()` and `generate()`).
    * A macro-temporal season advances (`SeasonEvent`).

**Conclusion**: Shorelines must remain dynamic renderables evaluated through `keys()`, with temporal invalidation driven by `SeasonEvent`.

###### 2. Shoreline Atlas Geometry & `ShorelineIndex`

Currently, `GeographyProperties` and `CardinalFrame` define a 1-column, 4-row atlas ($w \times 4l$, $32 \times 128$). To integrate seasonality:

1. **Atlas Grid**: Expand the atlas horizontally into 4 season columns: $\text{Columns} \in \{\text{spring}, \text{summer}, \text{autumn}, \text{winter}\}, \quad \text{Rows} \in \{\text{up}, \text{left}, \text{down}, \text{right}\}$, yielding a $4w \times 4l$ ($128 \times 128$) texture sheet.
2. **Keying Convention**:
    * Full tile: `{id}-{season}-{direction}` at $(col \cdot w, row \cdot l, w, l)$.
    * Fractional remainder ($s$): `{id}-{season}-{direction}-{s}` at $(col \cdot w, row \cdot l, s, l)$ (horizontal) or $(col \cdot w, row \cdot l, w, s)$ (vertical).
3. **Secondary Relation Resolution**:
    * If a multi-season shoreline atlas embeds all four seasons, `ShorelineIndex` only needs `(tile_id, fluid_id) \to shoreline_id`.
    * To support biomes where distinct seasons bind to entirely different asset atlases (e.g., standard fringe vs. standalone pack-ice shelf), `ShorelineIndex.resolve()` should accept an optional `season: Optional[str] = None`, querying `(tile, fluid, season)` with fallback to `(tile, fluid)`.

###### 3. Inner-Loop Optimizations

1. **Heap Allocation in `SeasonMechanics._probes` (Bug B018)**:
    * Generating 5 transient `Position` dataclass instances at 60 Hz per resource creates tens of thousands of heap objects per second.
    * Because `Resource` entities are static physical bodies ($m = 0$) whose positions and dimensions are invariant after hydration, their probe coordinates $(x + \Delta x, y + \Delta y)$ can be pre-calculated and cached on `ResourceState` during hydration, or evaluated via integer primitives using a new `board.fluid_at(layer, x, y)` lookup.
2. **ISL Stage Transition Throttling**:
    * Moisture diffusion requires continuous integration with frame $\Delta t$.
    * Declarative stage checks via `executor.evaluate(stage, locals)` do not need 60 Hz evaluation. Throttling execution to period changes (`period_changed == True`) or a 1.0-second accumulator removes ISL AST overhead from the hot loop.
3. **Canvas Bleed on Fore Tiles (Bug B013)**:
    * `Screen.reconstruct()` executes `render.construct()` directly on `fg_canvas` without clearing previous pixels. Because tree canopies contain alpha channels, new seasonal foliage draws on top of old textures. `fg_canvas` requires a clear pass prior to baking.

##### Bug Reports

###### Bug B013: Canvas Bleed on Fore Tiles

**STATUS**: OPEN
**SEVERITY**: Medium

**Description**

When `Screen.reconstruct()` updates seasonal tile frames, it invokes `render.construct(self.fg_canvas, fore_tiles)` directly on the existing `TexturePtr`. Unlike `bg_canvas` which is fully opaque and overwrites previous pixel values, `fg_canvas` contains transparent alpha channels (e.g., foliage overhangs and tree canopies). Successive season transitions will render new seasonal foliage textures over the existing pixels without clearing the target, causing ghosting and visual artifacts.

**Steps to Replicate**

1. Initialize a layer containing `fore` tiles with transparent backgrounds.
2. Advance `board.calendar` past a period boundary to fire `SeasonEvent`.
3. Inspect `screen.fg_canvas`; preceding seasonal canopy pixels remain visible beneath new seasonal pixels.

**Proposed Remediation**

Expose a clear-target routine in `libs.graphics.render` (or call `SDL_SetRenderTarget` followed by `SDL_RenderClear` on `fg_canvas`) within `Screen.reconstruct()` immediately before invoking `render.construct()`.

###### Bug B014: Transient Heap Allocation in SeasonMechanics._probes() Inner Loop

**STATUS**: OPEN
**SEVERITY**: Low

**Description**

In `SeasonMechanics._probes(resource)`, five discrete `Position` dataclass instances are constructed every frame for every active resource on the board. In dense maps, this creates tens of thousands of short-lived Python objects per second, contributing to garbage collection latency and violating the engine's zero-heap inner loop philosophy.

**Proposed Remediation**

Add `Board.fluid_at(layer: str, x: int, y: int) -> bool` accepting raw integer coordinates, and cache local probe offsets $(dx, dy)$ on `ResourceState` during hydration.

##### Goals

###### Goal: Multi-Season Shoreline Atlas & Frame Keying

Expand `CardinalFrame` to map 2D atlas grids partitioned by Cardinal directions (rows) and Calendar seasons (columns). Update `ShorelineState` to track active seasons, enabling lazy cache invalidation via `SeasonEvent` without rebuilding underlying geometric boundaries.

```python
# Atlas index schema: (col * w, row * l, w, l)
col = [s.value for s in Seasons].index(season)
row = CARDINAL_ROWS[direction]

```

###### Goal: Zero-Allocation Hydrological Probing & ISL Throttling

Decouple resource moisture diffusion from declarative stage transitions. Continue integrating soil moisture per tick at 60 Hz, but restrict `executor.evaluate()` calls to a 1.0-second accumulator or macro-temporal boundary triggers (`period_changed`). Refactor spatial water probing to utilize raw integer coordinates without instantiating `Position` models.

##### Tasks

**1. Task: Multi-Season Shoreline Atlas Keying**

*Objective*: Map shoreline atlas textures across cardinal rows and seasonal columns.

* [ ] Subtask: Update `GeographyProperties` to validate multi-season shoreline dimensions ($4w \times 4l$).
* [ ] Subtask: Extend `CardinalFrame.index()` to iterate over `Seasons` columns and `Directions` rows, generating crop entries for `{id}-{season}-{direction}` and fractional slices `{id}-{season}-{direction}-{rem}`.
* [ ] Subtask: Define `ShorelineState` in `app.models.state.assets.geography` with fields `season: str` and `_keys: Optional[List[Tuple[str, int, int]]]`.
* [ ] Subtask: Update `CardinalFrame.keys()` to emit `{id}-{state.season}-{direction}` and memoize on `state._keys`.
* [ ] Subtask: Update `SeasonEventHandler` to iterate over `board.shorelines()`, updating `state.season = event.season` and invalidating `state._keys = None`.

**2. Task: ShorelineIndex Relational Fallback**

*Objective*: Support compound relation lookups with temporal fallback.

* [ ] Subtask: Update `ShorelineIndex.resolve(tile_id, fluid_id, season=None)` to query `(tile_id, fluid_id, season)` before falling back to `(tile_id, fluid_id)`.
* [ ] Subtask: Update `Cartographer._coalesce_segments()` to pass `board.calendar.season` into `index.resolve()`.

**3. Task: SeasonMechanics Execution Throttling & Probing Optimization**

*Objective*: Eliminate inner-loop heap allocations and throttle AST evaluations.

* [ ] Subtask: Implement `Board.fluid_at(layer: str, x: int, y: int, exclude: Optional[str] = None) -> bool` to perform $O(1)$ spatial lookups with raw integers.
* [ ] Subtask: Refactor `SeasonMechanics._probes()` to query integer offsets using `board.fluid_at()` without allocating `Position` objects.
* [ ] Subtask: Add `_transition_tick: float` accumulator to `SeasonMechanics` and throttle `executor.evaluate()` to run only once per second or when `period_changed == True`.

**4. Task: Canvas Clear Pass in Screen.reconstruct()**

*Objective*: Resolve Bug B013 by eliminating texture bleed on foreground tiles.

* [ ] Subtask: Add texture wipe or clear invocation for `fg_canvas` in `Screen.reconstruct()` before executing `render.construct(self.fg_canvas, fore_tiles)`.


Treating fluid networks as potential field sources obeying linear superposition transforms soil hydrology from an ad-hoc geometric collision query into a continuous, physical state space.

This architecture cleanly decouples `SeasonMechanics` from fluid geometries and reduces per-frame environmental queries to zero.

---






No. Refactoring the entire call stack down through `Board`, `predicates`, and Cython is unnecessary churn and misdiagnoses the bottleneck.

Here is why that approach is flawed, what the actual bottleneck in `predicates.py` is, and the clean way to solve it.

---

### The Hidden Bottleneck in `predicates.py`

Even if `_probes()` were rewritten to pass raw integer primitives `(x, y)`:

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

`in_stream()` dynamically allocates a new `list` and multiple `tuple` objects **on every single call**.

For 100 resources probed 5 times per frame at 60 Hz, passing integer coordinates to `board.fluid()` would save 30,000 `Position` allocations per second while `predicates.in_stream()` continues generating **30,000+ lists and 60,000+ tuples per second** on the heap.

Ripping up the `Position` interface across the stack solves only a fraction of the allocations while breaking existing call sites like `Cartographer.is_step_fluid()`.

---

### Pragmatic Remediation

#### 1. Cache Probe Instances on `ResourceState` (Zero API Changes)

Resources (trees, crops, ore) are static bodies ($m = 0$). Their coordinates and dimensions never change after world hydration.

Pre-calculate the five `Position` objects **once** during entity hydration or spawning and store them on `ResourceState`:

```python
# During hydration in Migrator / Cradle:
resource.state.probes = [
    Position(mid_x, mid_y),
    Position(mid_x, pos.y - 1),
    Position(mid_x, pos.y + l),
    Position(pos.x - 1, mid_y),
    Position(pos.x + w, mid_y),
]

```

In `SeasonMechanics.update()`:

```python
is_near_water = any(
    board.fluid(resource.state.layer, probe_pos)
    for probe_pos in resource.state.probes
)

```

* **Inner loop heap allocations**: 0.
* **Changes to `Board.fluid()**`: 0.
* **Changes to `predicates.py**`: 0.
* **Changes to Cython**: 0.

#### 2. Cache Water AABBs on `FluidState`

To eliminate the real heap pressure inside `predicates.in_stream()`, compile the AABBs once when the fluid propagates rather than recomputing them per query.

`Actuator.propagate()` already calculates stream lengths, pools, and branches when fluid geometry changes. Store the pre-compiled AABB bounding boxes on `FluidState` (e.g., `fluid.state._aabbs: List[Tuple[int, int, int, int]]`).

`predicates.in_stream()` then simplifies to:

```python
def in_stream(position: Position, fluid: Asset) -> bool:
    if not fluid.state._aabbs:
        return False
    return geometry.inside(int(position.x), int(position.y), fluid.state._aabbs)

```

This reduces `in_stream()` from an allocation-heavy layout routine to a direct pass-through into Cython's `geometry.inside()`.

#### 3. Throttle Probing Frequency

Because resources are stationary and water geometry only shifts when gates open/close or during initial load, running 5 spatial queries per resource at 60 Hz is wasted work.

Evaluate `is_near_water` inside the throttled stage accumulator (e.g., at 1 Hz or on `period_changed`), caching a boolean `resource.state.irrigated` flag for the per-frame moisture diffusion formula.

---

### Task Backlog Adjustment

Replace the proposed `Board.fluid_at` refactor in Phase 10.02 with targeted caching:

* **Subtask**: Add pre-calculated `probes: List[Position]` field to `ResourceState`, populated during hydration.
* **Subtask**: Pre-compile stream and branch AABBs onto `FluidState._aabbs` in `Actuator.propagate()`.
* **Subtask**: Update `predicates.in_stream()` to pass `fluid.state._aabbs` directly to `geometry.inside()`.



---

Okay, here is a wild idea. The process bottlenecks because it is trying to determine its moisture level by examining its surrounding terrain. the engine then hardcodes a diffusion rate and applies it if the probes are successful. However, this isn't really how the whole process occurs in reality. In actuality, it's more like bodies of waters are sources in a field that obeys superposition. So, what if after the actuator pumps fluid, a field is calculated across the entire Board layer perimeter according to the following rules:

- every source fluid asset contributes to a moisture field
- field is calculated by summing individual contributions and then cached on Board. An approximation can be generated to turn it into a closed form function, if necessary. Fluid in the game is essentially equivalent to the classical mechanical problem of a bar of infinite length and the fields it creates. it has a nice closed form, as I recall.
- SeasonMechanics doesn't care about Fluids. it queries a Resource's location in the moisture field.

---


### 1. Mathematical Formulation: Superposition of Linear and Disk Sources

In continuous 2D soil hydrology with uniform transmissivity $D$ and surface evaporation/sink rate $\gamma$, the steady-state moisture concentration $\Phi(\mathbf{x})$ outside active bodies satisfies the screened Poisson equation:

$$\nabla^2 \Phi(\mathbf{x}) - \kappa^2 \Phi(\mathbf{x}) = -S(\mathbf{x})$$

where $\kappa = \sqrt{\gamma / D}$ is the inverse diffusion length and $S(\mathbf{x})$ represents fluid injection sources.

```
       Linear Stream Source (S_i)           Annular Pool Source (P_j)
      [============================]                 /-----\
                     \                             |   Q_j   |
                      \ d(x, segment)               \-----/
                       \                               /
                        \                             / d(x, pool)
                         v                           v
                     Resource Coordinate x: Phi(x) = Sum Phi_i(x)

```

#### A. Linear Stream Corridors (Finite Line Segments)

A fluid stream or branch corridor with source direction $\hat{u}$, width $w$, flow intensity $f$, and length $L$ acts as a uniform line source segment between endpoints $\mathbf{a}$ and $\mathbf{b} = \mathbf{a} + L\hat{u}$ with linear flux density $\lambda = \lambda_0 \cdot f$.

In classical potential theory, the field generated by a finite uniform line segment at target point $\mathbf{x} = (x, y)$ can be evaluated either via exact line integration or via orthogonal distance to the segment:

1. **Exact 3D Potential Projection (Finite Bar)**:
Mapping the corridor to a bar spanning $z \in [0, L]$ with transverse offset $r = d_{\perp}(\mathbf{x}, \text{axis})$:

$$\Phi_{\text{bar}}(\mathbf{x}) = \lambda \int_0^L \frac{dz'}{\sqrt{r^2 + (z - z')^2}} = \lambda \ln \left( \frac{(L - z) + \sqrt{r^2 + (L - z)^2}}{-z + \sqrt{r^2 + z^2}} \right)$$


2. **Screened Euclidean Distance Approximation (Piecewise or Exponential Decay)**:
For 2D terrain diffusion with a maximum hydrological cutoff radius $R_{\max} = \sigma \cdot f$, the field contribution simplifies to a function of the minimum Euclidean distance $d_i(\mathbf{x})$ from $\mathbf{x}$ to segment $[\mathbf{a}_i, \mathbf{b}_i]$:

$$\Phi_i(\mathbf{x}) = \Phi_0 \cdot f_i \cdot \exp\left( -\frac{d_i(\mathbf{x})}{\sigma} \right) \quad \text{for } d_i(\mathbf{x}) \le R_{\max}$$



where the distance $d_i(\mathbf{x})$ to the segment is computed without square roots outside the radius:

$$t = \text{clamp}\left( \frac{(\mathbf{x} - \mathbf{a}_i) \cdot (\mathbf{b}_i - \mathbf{a}_i)}{\Vert{}\mathbf{b}_i - \mathbf{a}_i\Vert{}^2}, 0, 1 \right), \quad d_i(\mathbf{x}) = \Vert{}\mathbf{x} - (\mathbf{a}_i + t(\mathbf{b}_i - \mathbf{a}_i))\Vert{}$$



#### B. Annular Pools (Disk Sources)

A pool centered at $\mathbf{c}_j$ with effective radius $R_j = \frac{1}{2}\sqrt{w_{\text{pool}}^2 + l_{\text{pool}}^2}$ acts as an isotropic source of intensity $Q_j \propto f$:

$$\Phi_j(\mathbf{x}) = Q_j \cdot \exp\left( -\frac{\max(0, \Vert{}\mathbf{x} - \mathbf{c}_j\Vert{} - R_j)}{\sigma} \right)$$

#### C. Superposition Field

By the principle of superposition, the total soil moisture potential at any point $\mathbf{x}$ on layer $L$ is:

$$\Phi(\mathbf{x}) = \sum_{i \in \text{Streams}} \Phi_i(\mathbf{x}) + \sum_{j \in \text{Pools}} \Phi_j(\mathbf{x})$$

---

### 2. Architectural Division of Labor

```
+-------------------------------------------------------------------------+
| FluidMechanics / Actuator (Event-Driven: Runs only when water shifts)   |
|                                                                         |
|  1. Truncate streams, expand pools, trace branches                     |
|  2. If geometry shifted: Compute MoistureField for layer                |
|  3. Assign Field to Board: board.set_moisture_field(layer, field)       |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| Board (Data Store)                                                      |
|                                                                         |
|  Exposes: board.moisture(layer, x, y) -> float                          |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| SeasonMechanics (60 Hz Engine Loop)                                     |
|                                                                         |
|  Iterates Resources:                                                    |
|    flux = board.moisture(resource.layer, resource.pos.x, resource.pos.y) |
|    if flux > 0:                                                         |
|        resource.state.retention += flux * delta                         |
|    else:                                                                |
|        resource.state.retention -= evap * delta                         |
+-------------------------------------------------------------------------+

```

1. **`Actuator.propagate()` / `FluidMechanics**`:
* Maintains exclusive ownership of source generation.
* When fluid invalidation flags a layer as dirty, it updates stream lengths and pools.
* Once propagation concludes, it constructs a `MoistureField` instance from the active stream segments and pools.
* Pushes the compiled `MoistureField` to `Board`.


2. **`Board` Representation**:
Two valid concrete implementations exist for caching:
* **Analytic Evaluator (`AnalyticMoistureField`)**: Stores the list of segment tuples `(x1, y1, x2, y2, flow)` and pool circles `(cx, cy, radius, flow)`. Evaluates closed-form distance attenuation on demand.
* **Discrete Raster Grid (`RasterMoistureGrid`)**: A flat 2D scalar array matching the board size divided into coarse spatial buckets (e.g., $16 \times 16$ or $32 \times 32$ grid cells). During `FluidMechanics` pass 2, it rasterizes the sources into the grid. Sampling is an $O(1)$ array index lookup:

$$\text{cell\_x} = x \gg 5, \quad \text{cell\_y} = y \gg 5, \quad \Phi = \text{grid}[\text{cell\_y} \cdot W_{\text{cells}} + \text{cell\_x}]$$




3. **`SeasonMechanics`**:
* Completely decoupled from `predicates.in_fluid`, hitboxes, branch arrays, and `Position` allocations.
* Queries a single coordinate scalar: `flux = board.moisture(layer, pos.x, pos.y)`.
* Modulates absorption continuously: $\text{retention} \mathrel{+}= \kappa_{\text{diffusion}} \cdot \text{flux} \cdot \Delta t$.


4. **Zero-Work Optimization for Static Resources**:
* Because resources are static ($m = 0$), their positions are constant.
* When `board.set_moisture_field(layer, field)` is invoked, the board can update a scalar `resource.state.moisture_flux: float` directly on each resource on that layer.
* Under this pattern, `SeasonMechanics` executes **zero spatial lookups** per tick. It integrates `resource.state.retention += resource.state.moisture_flux * delta` directly in a flat scalar loop.



---

### 3. Comparison of Alternatives

| Dimension | Point Probing (`_probes()`) | Raster Moisture Grid ($32 \times 32$) | Analytic Continuous Field |
| --- | --- | --- | --- |
| **Complexity per Resource** | $O(K \cdot N_{\text{fluids}})$ per frame | $O(1)$ scalar array lookup | $O(N_{\text{segments}} + N_{\text{pools}})$ |
| **Inner Loop Allocations** | High (5 `Position` + lists) | **Zero** | **Zero** |
| **Hydrological Fidelity** | Binary step function (in/out) | Smooth gradient | Infinite continuous gradient |
| **Sensitivity to Board Scale** | Degrades with resource density | Fixed rasterization on shift | Independent of board size |
| **Cache Invalidation** | Every tick | Event-driven (only when gates mutate) | Event-driven (only when gates mutate) |

---

### 4. Backlog Task Modification for Phase 10.02

Replace Bug B018 remediation and Task 2 Subtasks with the Moisture Field model:

#### Task: Hydrological Superposition Field (Phase 10.02)

*Objective*: Replace iterative point-probing with an event-driven scalar potential field.

* [ ] **Subtask: Define MoistureField Model**
Implement `app.game.board.fields.MoistureField` supporting segment and pool source registration with exponential attenuation.
* [ ] **Subtask: Field Compilation in Actuator**
Update `Actuator.propagate()` to compile active stream branches and annular pools into a `MoistureField` upon completing fluid propagation.
* [ ] **Subtask: Field Caching on Board**
Add `board._moisture_fields: Dict[str, MoistureField]` and lookup method `board.moisture(layer, x, y) -> float`.
* [ ] **Subtask: Refactor SeasonMechanics Hydrology**
Remove `SeasonMechanics._probes()`. Update `SeasonMechanics.update()` to query `board.moisture()` or bind `resource.state.moisture_flux` upon field updates.