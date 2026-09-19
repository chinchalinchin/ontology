#### Implement: Phase 09 - Hydrodynamics

**Overview** 

Establish an autonomous fluid flow and obstacle occlusion system. Introduces a dedicated `fluids` effect instance and an `obstacles` object instance. Fluid assets propagate along their source direction vector, truncate at obstacle boundaries using pre-indexed partial frames, and pool radially around non-character solid bodies.

**Principles**

1. (**Source**) A Fluid Effect has a `source`. A `source` is a Direction. Fluid flows in the Direction of its `source`.
    - In game, this means Fluid Effect assets are multiplied in the indicated direction until they meet an Obstacle. 
    - **NOTE**: This means a Fluid Effect may be truncated into a fraction of its dimensions. For example, if a Fluid Effect of 32px x 32px with a `source = down` is 48px away (measured from its top left corner) from an Obstacle, the Fluid Effect will be multiplied 1.5 times (32 + 16 = 48) in the `down` direction to achieve a resulting dimension of 32px x 48px.
2. (**Obstruction**) Fluid is obstructed by Board boundaries or non-Sheet weights: $\text{Fluid Obstacles} = \text{Boundaries} \cup \{ a \in \text{Weights} \mid a.\text{category} \neq \text{SHEETS} \land (a.m > 0 \lor (a.m = 0 \land a.\text{instance} \in \text{SOLID\_OBJECTS})) \}$
3. (**Flow**) A Fluid Effect has a `flow`.A `flow` is a radial-esque (rectangular, not circular) parameter that determines the boundaries of the resultant body of water that is formed *around* the Obstacle. 
    - **Example**: Suppose an Obstacle with dimensions 10px x 10px at (100, 100) is met by a Fluid Effect with dimensions 10px x 10px travelling in the `down` direction with  `flow = 3`. The Fluid will thus multiply *around* the Obstacle to form a perimeter with vertices (70, 70), (70, 140), (140, 70), (140, 140) and a hole of dimensions 10px by 10px at (100, 100), where the Obstacle is rendered. In this example, `top_left_vertex = (obstacle.position.x - flow * effect.dimensions.w, obstacle.position.y - flow * effect.dimensions.l` and `bottom_right_vertex = (obstacle.position.x + obstacle.dimensions.w + flow * effect.dimensions.w, obstacle.position.y + obstacle.dimensions.l + flow * effect.dimensions.l)`

**Corollaries**

* Sensors ($m = -1$, like plates and collectible effects) and character sheets are explicitly ignored by fluid raycasts.
* `Fluid` itself is instantiated with `mass: int = -1` (Sensor) so it does not participate in physical momentum transfer, while retaining hitboxes for environmental hazard checks and bridge masking

**Core Questions**

- Where does the Fluid flow get calculated? Initial thought is it should be part of the World hydration, i.e. when the Migrator is creating the state, it should delegate Fluid generation to a generator service. However, the moveable nature of obstacles makes this untenable. 
- Sprites need to be treated with care, as they should not be considered Obstacles, otherwise player and sprite movement will alter the Fluid flow. However, this can be mitigated by required all Fluid have a mass of 0, i.e. treating Fluid as an immovable object.
- It seems like there will need to be a FluidMechanics to calculate dynamic changes to the flow due to Obstacles. However, this needs to be done smartly to prevent excessive calculations.
- The Fluid frame logic is very similar to Meter frames, i.e. fractions of a frame. Can the existing Meter frame logic be leveraged in any capacity?

**Refactors**

- After Fluid Flow is established, Bridges will need introduced to allow movement over the Fluid's hitboxes. This will require an Object whose hitboxes override the hitboxes of the Fluid over which it is superimposed. Not a pressing concern right now, but something to keep in mind.

##### Architectural Analysis I

```
+-----------------------------------------------------------------------------------+
|                               BOARD (World State)                                 |
|                                                                                   |
|  [Fluid Asset]                                     [Dynamic Obstacle (Crate)]     |
|   - Origin: (x, y)                                  - Position: (x_obs, y_obs)    |
|   - Source: DOWN                                    - State: velocity > 0         |
|   - State: dirty=False                                                            |
+-----------------------------------------------------------------------------------+
                                         |
                                         | 1. Obstacle shifts / switch toggles
                                         v
+-----------------------------------------------------------------------------------+
|                        FLUID MECHANICS (World Pipeline)                           |
|                                                                                   |
|  - Reactive Invalidation: Checks if obstacles in layer moved                      |
|  - Raycast: Origin -> First colliding obstacle (or board boundary)                |
|  - Stream Truncation: N full tiles + 1 fractional slice                           |
|  - Pooling Perimeter: 4-quadrant annulus surrounding obstacle                     |
|  - Hitbox Sync: Updates compound hitboxes on FluidState                           |
+-----------------------------------------------------------------------------------+
                                         |
                                         | 2. Frame key extraction
                                         v
+-----------------------------------------------------------------------------------+
|                          FLUID FRAME (Renderer Bridge)                            |
|                                                                                   |
|  - Pre-indexed slices in Registry (similar to MeterFrame)                         |
|  - Returns List[(frame_key, offset_x, offset_y)]                                  |
|  - Screen paints compound texture slices in a single pass                         |
+-----------------------------------------------------------------------------------+

```

**1. Calculation Lifecycle: Hydration vs. Runtime Mechanics**

* **The Dilemma:** Pre-computing water bodies during `Migrator` bootstrap creates high runtime efficiency, but fails when crates slide or gates toggle. Running linear raycasts and polygon bounds every tick for every fluid source wastes CPU cycles and thrashes the board.
* **The Solution:** A **Reactive Invalidation (Dirty-Flag) Pattern**.
    * **Bootstrap:** During `Migrator` hydration, an initial fluid flow pass computes the steady-state stream length and pool boundary against static geometry.
    * **Tick Update:** `FluidMechanics` does not recalculate flow every frame. Instead, it checks whether any dynamic obstacle ($m > 0$ crates with $\vert{}v\vert{} > 0$ or gates with flipped switches) intersects the fluid's active stream or pool bounds.
    * Only when an obstacle mutates within the fluid's influence zone is the fluid marked `dirty = True`, triggering a re-raycast. Otherwise, `FluidMechanics` yields in $O(1)$ time.

**2. Entity Representation: Single Compound Asset vs. Spawned Tiles**

* **The Problem:** If a fluid source spawns dozens of individual `Asset` instances into `Board._assets`, every obstacle movement forces `board.remove()` and `board.add()` calls. In `Board`, removal performs linear traversals across `_assets`, `_cached_layers`, `_cached_categories`, `_cached_instances`, and `_cached_renderables`. Doing this continuously introduces severe GC overhead and cache thrashing.
* **The Solution:** Treat each fluid stream as a **Single Compound Asset** (`instance = 'fluids'`).
* Like `SpriteFrame` (which yields multiple tuples for body, armor, tools, and expressions) and `MultiplierState` for tiles, a `Fluid` asset uses a dedicated `FluidFrame`.
* `FluidState` stores the computed length and pooling perimeter. When the Screen queries `asset.frame.keys(id, state)`, `FluidFrame` produces the list of `(frame_key, offset_x, offset_y)` tuples covering the entire stream and pool.
* The `Board` database only tracks **one asset** per fluid emitter.

**3. Fractional Truncation & The MeterFrame Analogy**

* **The Parallel:** `MeterFrame.index()` solves partial rendering by pre-indexing 100 percentage crops of a sprite (`int(w * res / 100.0)`) into the Cython `Registry` at boot.
* **Applying to Fluid:**
* A fluid stream running `down` hits an obstacle at arbitrary sub-tile distances (e.g., 48px from a 32px tile yields $1.5$ tiles).
* Rather than generating runtime texture buffers, `FluidFrame.index()` pre-crops fractional slices of the fluid tile along the flow axis (from $1\text{ px}$ to $\text{dimension} - 1\text{ px}$) during registry initialization:

$$
\text{key} = \text{id} \text{ + separator + slice + separator + } h
$$


* When rendering, `FluidFrame.keys()` emits $N$ full-tile keys followed by one fractional slice key at the obstacle boundary.

**4. Radial Pooling Geometry (Principle 3)**

For an obstacle of dimensions $(w_{\text{obs}}, l_{\text{obs}})$ at $(x_{\text{obs}}, y_{\text{obs}})$ met by a fluid tile $(w_{\text{eff}}, l_{\text{eff}})$ with flow parameter $F$:

* Outer perimeter bounds:

$$
\text{top\_left} = (x_{\text{obs}} - F \cdot w_{\text{eff}},\, y_{\text{obs}} - F \cdot l_{\text{eff}})
$$

$$
\text{bottom\_right} = (x_{\text{obs}} + w_{\text{obs}} + F \cdot w_{\text{eff}},\, y_{\text{obs}} + l_{\text{obs}} + F \cdot l_{\text{eff}})
$$

* The resulting annular pool surrounds the obstacle. To render and assign hitboxes without overlapping the obstacle body, the geometry is partitioned into four bounding rectangles:

1. **Top Bar:** Width $= w_{\text{obs}} + 2F w_{\text{eff}}$, Height $= F l_{\text{eff}}$
2. **Bottom Bar:** Width $= w_{\text{obs}} + 2F w_{\text{eff}}$, Height $= F l_{\text{eff}}$
3. **Left Flank:** Width $= F w_{\text{eff}}$, Height $= l_{\text{obs}}$
4. **Right Flank:** Width $= F w_{\text{eff}}$, Height $= l_{\text{obs}}$

**Overview**

Establish an autonomous fluid flow and obstacle occlusion system. Extends effect and object taxonomies to support directional fluid propagation, multi-axis fractional frame cropping, reactive obstacle occlusion, and annular pooling. Aligns fluid frame keys and Z-index state with `Registry` indexing and `Screen.draw` sorting rules.

##### Architectural Analysis II

The underlying Cython rendering pipeline (`libs.graphics.render`), the asset registry (`libs.graphics.registry`), and the `Screen` abstraction (`app.game.screen`) require specific updates to the Phase 09 backlog.

**Graphics & Pipeline Findings**

1. **Painter's Algorithm Inversion in `Screen.draw`**: `Screen.draw` height-sorts assets using `asset.state.height if asset.state.height is not None else (asset.state.position.y + asset.dimensions.l)`. Because a fluid stream is a spatially distributed compound entity rather than a localized bounding box, an upward (`up`) or lateral (`left`) stream anchored at `position.y = 400` flowing to an obstacle at `y = 100` receives an implicit sort key of `432`. It sorts *after* the obstacle at `y = 100` (sort key `132`) and characters at `y = 250` (sort key `314`), drawing fluid directly over the obstacle that blocked it.
    - *Resolution*: `FluidState` must enforce `height = 0` and `depth = -1` by default. This forces the entire compound fluid body to sort immediately above `bg_canvas` (terrain tiles) and underneath all dynamic bodies, obstacles, and bridges.
2. **Crop Invariance in `Screen.draw` and `render.pyx`**: `Screen.draw` flattens texture tuples as `tex, sx, sy, sw, sl = tex_data` and sets `dw, dl = sw, sl` before passing them across the Cython boundary to `render.render()`. `render.render()` blits slices 1:1 using `c_src = (sx, sy, sw, sl)` and `c_dst = (dx - cam_x, dy - cam_y, dw, dl)`. The Cython rendering loop natively supports variable sub-tile slices without requiring scaling, new SDL bindings, or texture allocations.
3. **Multi-Axis & Reverse Slicing in `FluidFrame`**: The initial Phase 09 design assumed vertical length slicing `(0, 0, w, slice_len)`. Slicing must support:
    * **Lateral Flow (`left`, `right`)**: Slices varying width $1 \le \text{slice\_w} < w$.
    * **Vector Anchoring**: For `down` and `right`, the truncated edge anchors at texture origin $(0, 0)$. For `up` and `left`, the truncated edge anchors at the distal edge: `(0, l - slice_l, w, slice_l)` or `(w - slice_w, 0, slice_w, l)`.
4. **Animation Lifecycle Collision**: In `AnimationMechanics`, all entities under `AssetCategories.EFFECTS` advance their animation frame every tick via `asset.animation.animate()`. If `FluidFrame.index()` only indexes static slice keys (`f"{id}-slice-{len}"`), every animated frame tick ($f > 0$) causes `self.registry.image(frame_key)` to fail and triggers `Registry MISS` warnings in `Screen.draw`. Slices must be indexed per animation frame: `f"{id}-{f}-{direction}-slice-{len}"`.
5. **Inner-Loop Allocation Overhead**: `Screen.draw()` calls `asset.frame.keys()` every render frame (60 FPS). Dynamically computing raycasts, assembling 40–80 coordinate offsets, and allocating string keys each render frame introduces Python heap fragmentation. `FluidMechanics` must cache the computed offset manifest on `FluidState` during the game tick; `FluidFrame.keys()` merely applies the current `state.animation.frame` to pre-calculated offsets.

##### Architectural Analysis III

**1. The Fluid Generator & Hydration Lifecycle**

Introducing a dedicated generator service—let's call it `Actuator` in `src/app/services/generators/game/fluid.py`—is architecturally sound and aligns with how the engine handles procedural geometry elsewhere.

In `Migrator.step()`, procedural boundaries are handled immediately after ECS entity injection:

```python
# 3. Post-Hydration Phase: Procedural Boundaries
perimeter_gen = Perimeter()
for layer in self.board.layers():
    self.board.perimeters[layer] = perimeter_gen.generate(self.board, layer)

```

If fluid propagation is left entirely to `FluidMechanics.update()`, the engine enters a race condition on boot:

1. `Migrator` finishes hydration and emits a `TerminalEvent`.
2. `Engine._render()` executes before the unpaused `world` mechanics have ticked.
3. The fluid asset renders with uninitialized stream dimensions (zero length, no pool).
4. `FluidMechanics` runs on the next logic tick, snapping the river into existence one frame late.

**2. The Division of Responsibilities**

Separating the geometric math from the runtime orchestration creates clean boundaries:

```
+--------------------------------------------------------------------------------+
|                        src/app/services/generators/game                        |
|                                                                                |
|  Actuator                                                                |
|    - Inputs: Fluid Asset, Board, Layer                                         |
|    - Logic:                                                                    |
|        1. Queries board obstacles & layer boundaries                           |
|        2. Executes geometry.raycast_obstacle()                                 |
|        3. Computes stream length & truncated edge slice                        |
|        4. Partitions annular pool into 4 bounding rects                        |
|        5. Returns: (stream_length, pool_rects, hitboxes)                       |
+--------------------------------------------------------------------------------+
                               ▲                                ▲
                  Called at    │                                │ Called on
                  Bootstrap    │                                │ Dirty Flag
                               │                                │
+------------------------------┴---------+    +-----------------┴----------------+
|               MIGRATOR                 |    |         FLUID MECHANICS          |
|                                        |    |                                  |
| - Runs post-hydration pass             |    | - Runs in world mechanics loop   |
| - Hydrates static steady-state flow    |    | - Monitors dynamic obstacles     |
|   before the first frame renders       |    | - Sets dirty = True on movement  |
| - Pre-warms initial hitboxes           |    | - Re-invokes Actuator      |
+----------------------------------------+    +----------------------------------+
```

* **`Actuator` (Stateless Service)**: Pure math and spatial queries. Ingests the fluid emitter and the board state, runs the Cython `raycast`, calculates the stream truncation distance, calculates the 4-quadrant annular pool geometry around the struck obstacle, and constructs the composite `Hitbox` list.
* **`Migrator` (Bootstrapping)**: Instantiates `Actuator` during Step 3 of `_build_generator()` and computes initial steady-state dimensions for all `fluids` in the world state.
* **`FluidMechanics` (Runtime System)**: Monitors dynamic obstacle mutations (e.g., crates with $\vert{}v\vert{} > 0$ or gates toggling switches). When an obstacle within a fluid's zone moves, it flags the fluid as `dirty = True` and delegates re-calculation to `Actuator`.

**2. Deconstructing `FluidState`: What Is Actually Needed?**

The previous formulation of `FluidState` had:

```python
stream_length: int = 0
pool_offsets: List[Tuple[str, int, int]] = field(default_factory=list)
stream_offsets: List[Tuple[str, int, int]] = field(default_factory=list)

```

The reason for this verbosity stemmed from a **premature optimization around rendering throughput**.

*The Original Rationale*

In `Screen.draw()`, the engine iterates through all visible assets and calls `asset.frame.keys(asset.id, asset.state)` at 60 FPS. If `FluidFrame.keys()` had to recalculate tile multiples, division remainders, and annular rectangle offsets on every single frame, it was doing redundant arithmetic.

By pre-calculating the exact rendering manifest—the string suffix for the crop key and the pixel offsets `(key_suffix, ox, oy)`—and storing them in `stream_offsets` and `pool_offsets`, `FluidFrame.keys()` became a single lookup that appended the asset ID and animation frame index. `stream_length` was kept separately as a scalar pixel value for hitbox generation.

*Why This Design Is Flawed*

It breaks the core architectural boundary of the engine: **Simulation State should not know about Texture Frame Keys.**

1. **State Pollution**: `stream_offsets` and `pool_offsets` stored rendering instructions (`key_suffix`) inside `app.models.state`. A state model should describe the physical reality in the simulation, not cache texture keys for SDL.
2. **Unnecessary Caching**: A 256px fluid stream composed of 32px tiles is 8 tiles long. Looping 8 times to emit 8 tuples in Python takes roughly **$0.4$ microseconds**. Doing that 60 times a second for a handful of fluid emitters uses a negligible fraction of the frame budget. Caching those tuples in `State` introduced object bloat to solve a performance bottleneck that does not exist.

*The Leaner, Principled Replacement*

`FluidState` only needs to represent the **physical result of hydrodynamics in the game world**, leaving texture decomposition entirely to `FluidFrame`:

```python
@dataclass(slots=True)
class PoolBounds:
    x: int
    y: int
    w: int
    l: int

@dataclass(slots=True)
class FluidState(EffectState):
    length: int = 0
    pool: Optional[PoolBounds] = None
    hitboxes: List[Hitbox] = field(default_factory=list)
    dirty: bool = True
    height: Optional[Union[int, str]] = 0
    depth: int = -1

```

Here is why each field is present:

* **`length: int`**: The scalar distance (in pixels) the stream travels from `position` along its `source` vector before hitting an obstacle or map perimeter.
* **`pool: Optional[PoolBounds]`**: If the stream strikes an internal obstacle rather than a boundary, `pool` stores the outer bounding box of the flooded area surrounding the obstacle. If it hits a boundary wall, `pool` is `None`.
* **`hitboxes: List[Hitbox]`**: Because a fluid's physical footprint changes dynamically as crates move, the active sensor hitboxes (one for the stream corridor and four for the annular pool flanks) are cached directly on the state so `SpatialMechanic` and broad-phase collision checks don't recompute them.
* **`dirty: bool`**: Invalidation flag for `FluidMechanics`.
* **`height: 0` / `depth: -1**`: Forces `Screen.draw()` to sort fluid directly above background tiles and below dynamic entities.

*How `FluidFrame` Consumes This Lean State*

`FluidFrame` does its proper job: translating pure state into texture keys on demand:

```python
class FluidFrame(Frame):
    def keys(self, id: str, state: FluidState) -> List[Tuple[str, int, int]]:
        keys = []
        frame_idx = str(state.animation.frame)
        w, l = self.tile_w, self.tile_l  # Emitter dimensions (e.g., 32x32)
        
        # 1. Emit stream corridor tiles
        full_tiles = state.length // l
        rem = state.length % l
        
        for i in range(full_tiles):
            keys.append((f"{id}-{frame_idx}", 0, i * l))
            
        # 2. Emit terminal truncated slice (if length is not an exact tile multiple)
        if rem > 0:
            slice_key = f"{id}-{frame_idx}-{state.source}-{rem}"
            keys.append((slice_key, 0, full_tiles * l))
            
        # 3. Emit pool tiles (if an annular pool exists)
        if state.pool:
            # Trivial grid iteration over the 4 rectangular flanks
            ...
            
        return keys

```

This keeps `FluidState` clean, eliminates leaked rendering keys, and maintains strict separation between the simulation and graphics subsystems.

##### Goal: Fluid & Obstacle Data Architecture

Extend property and state schemas to represent directional fluid streams, flow parameters, and obstacle bounding boxes with ground-plane Z-indexing.

```python
@dataclass(slots=True)
class Pool:
    x: int
    y: int
    w: int
    l: int

@dataclass(slots=True)
class FluidProperties(EffectProperties):
    source: str = Directions.DOWN.value
    flow: int = 1
    mass: int = -1

@dataclass(slots=True)
class FluidState(EffectState):
    length: int = 0
    pool: Optional[Pool] = None
    hitboxes: List[Hitbox] = field(default_factory=list)
    dirty: bool = True
    height: Optional[int] = 0
    depth: int = -1

```

##### Goal: Procedural Fluid Generator Service

Implement `Actuator` in `src/app/services/generators/game/fluid.py` to encapsulate raycasting, stream truncation, annular pool geometry, and composite hitbox generation.

```python
class Actuator:
    def pump(self, fluid: Asset, board: Board) -> Tuple[int, Optional[PoolBounds], List[Hitbox]]:
        # 1. Query board obstacles (crates, closed gates, struts) & boundaries
        # 2. Call geometry.raycast_obstacle() along fluid.properties.source
        # 3. Calculate distance, remainder slice, and annular pool bounds
        # 4. Construct composite Hitbox list (stream box + pool flank boxes)
        # Returns: (stream_length, pool_bounds, hitboxes)
        ...

```

##### Goal: Multi-Axis Sliced Frame Ingestion (`FluidFrame`)

Implement `FluidFrame` to index full and fractional crops across all animation frames and directional vectors in `Registry`, and emit pre-cached offset manifests in `Screen.draw`.

```python
class FluidFrame(Frame):
    def index(self, id: str, properties: dict) -> dict[str, tuple[int, int, int, int]]:
        # Index full tiles and forward/reverse slices along w and l per animation frame
        ...

    def keys(self, id: str, state: AssetState) -> List[Tuple[str, int, int]]:
        # Emit N full-tile keys + 1 fractional slice key + annular pool grid keys
        ...

```

##### Goal: Reactive Flow Propagation & Offset Caching (`FluidMechanics`)

Implement `FluidMechanics` in the `world` mechanics pipeline to handle spatial raycasts, annular pool partitioning, composite hitbox synchronizations, and dirty-flag invalidation.

```python
class FluidMechanics(Mechanic):
    def update(self, board: Board, delta: float, bus: deque, payload: DevicePayload) -> None:
        # 1. Invalidation: mark fluids dirty if layer obstacles/crates moved
        # 2. Narrow-phase raycast: source -> nearest boundary or non-sheet weight
        # 3. Partition stream: N full tiles + 1 directional truncated slice
        # 4. Partition pool: 4 rectangular flanks surrounding obstacle
        # 5. Cache relative (key_suffix, ox, oy) offsets on state
        # 6. Update broad-phase hitboxes
        ...

```

##### Tasks 09.01

**1. Task: Schemas & Taxonomy Registration**

*Objective*: Register `fluids` under `AssetCategories.EFFECTS` and `obstacles` under `AssetCategories.OBJECTS` across enums, properties, state, and recipe configurations.

* [x] Subtask: Add `FLUIDS` to `AssetInstances` enum and `EffectPropertyInstances` schema.
* [x] Subtask: Add `OBSTACLES` to `AssetInstances` enum and `ObjectPropertyInstances` schema.
* [x] Subtask: Define `FluidProperties` and `FluidState` dataclasses with slots in `models/properties.py` and `models/state/objects.py`.
* [x] Subtask: Add default recipes for `fluids` and `obstacles` in `src/data/config/recipes/main.yaml`.

**2. Task: Actuator Service Implementation**

*Objective*: Create `Actuator` in `app/services/generators/game/fluid.py` to calculate flow extents and hitboxes.

* [ ] Subtask: Implement `Actuator.pump(fluid, board)` using `geometry.raycast()`.
* [ ] Subtask: Implement annular perimeter partitioning around struck obstacles using the `flow` radius.
* [ ] Subtask: Generate compound `Hitbox` objects covering the active stream and pool rectangles.

**3. Task: Multi-Axis FluidFrame Implementation**

*Objective*: Implement `FluidFrame` in `app/assets/frames/core.py` to handle dynamic key generation without polluting state.

* [ ] Subtask: Implement `FluidFrame.index()` generating forward and reverse slices along width and length across all animation frames.
* [ ] Subtask: Implement `FluidFrame.keys()` calculating tile coordinates dynamically from `state.length` and `state.pool`.
* [x] Subtask: Register `FluidFrame` in `app/services/generators/game/factory.py`.


**4. Task: Migrator Bootstrap Hydration**

*Objective*: Integrate `Actuator` into `Migrator.step()` to ensure fluids are fully calculated before the first frame renders.

* [ ] Subtask: Instantiate `Actuator` during Step 3 of `Migrator._build_generator()`.
* [ ] Subtask: Execute an initial flow pass for all `fluids` in `board`, populating `length`, `pool`, and `hitboxes`.

**5. Task: FluidMechanics Engine System**

*Objective*: Implement `FluidMechanics` in `app/game/logic/mechanics/world/fluid.py` to handle dynamic obstacle invalidation.

* [ ] Subtask: Implement change detection monitoring crate velocities and gate switch state transitions.
* [ ] Subtask: Re-invoke `Actuator` for invalidated fluids to update state and hitboxes.
* [x] Subtask: Register `FluidMechanics` in `src/data/config/mechanics/main.yaml` directly following `CollisionMechanics`.