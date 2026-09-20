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

* [x] Subtask: Implement `Actuator.pump(fluid, board)` using `geometry.raycast()`.
* [x] Subtask: Implement annular perimeter partitioning around struck obstacles using the `flow` radius.
* [x] Subtask: Generate compound `Hitbox` objects covering the active stream and pool rectangles.

**3. Task: Multi-Axis FluidFrame Implementation**

*Objective*: Implement `FluidFrame` in `app/assets/frames/core.py` to handle dynamic key generation without polluting state.

* [x] Subtask: Implement `FluidFrame.index()` generating forward and reverse slices along width and length across all animation frames.
* [x] Subtask: Implement `FluidFrame.keys()` calculating tile coordinates dynamically from `state.length` and `state.pool`.
* [x] Subtask: Register `FluidFrame` in `app/services/generators/game/factory.py`.

**4. Task: Migrator Bootstrap Hydration**

*Objective*: Integrate `Actuator` into `Migrator.step()` to ensure fluids are fully calculated before the first frame renders.

* [x] Subtask: Instantiate `Actuator` during Step 3 of `Migrator._build_generator()`.
* [x] Subtask: Execute an initial flow pass for all `fluids` in `board`, populating `length`, `pool`, and `hitboxes`.

**5. Task: FluidMechanics Engine System**

*Objective*: Implement `FluidMechanics` in `app/game/logic/mechanics/world/fluid.py` to handle dynamic obstacle invalidation.

* [x] Subtask: Implement change detection monitoring crate velocities and gate switch state transitions.
* [x] Subtask: Re-invoke `Actuator` for invalidated fluids to update state and hitboxes.
* [x] Subtask: Register `FluidMechanics` in `src/data/config/mechanics/main.yaml` directly following `CollisionMechanics`.

#### Live Test

Changes accepted with revisisions. `flow` and `source` should be attributes of FluidState (otherwise all flows will be the same direction!)

```python
@dataclass(slots=True)
class FluidState(EffectState):
    # Overrides
    height: Optional[int] = 0
    depth: int = -1
    # Fluid Fields
    length: int = 0
    pool: Optional[Pool] = None
    hitboxes: List[Hitbox] = field(default_factory=list) # type: ignore
    dirty: bool = True
    flow: int = 1
    source: Directions = Directions.DOWN.value
```

Actuator pump method was updated to accomodate:

```python
def pump(self, fluid: Asset, board: Board) -> Tuple[int, Optional[Pool], List[Hitbox]]:
        """
        Executes directional raycast propagation, sets stream length, builds annular
        pooling bounds for internal obstacles, and assigns active compound hitboxes.
        """
        direction = fluid.state.source.value
        flow = fluid.state.flow
        fw = fluid.properties.dimensions.w
        fl = fluid.properties.dimensions.l
        fx = fluid.state.position.x
        fy = fluid.state.position.y

        obstacle_tuples = self._collect_obstacles(fluid, board)
        max_dist = self._calculate_max_distance(fluid, board, direction)

        stream_length, struck_obstacle = geometry.raycast(
            fx,
            fy,
            fw,
            fl,
            direction,
            obstacle_tuples,
            max_dist
        )

        hitboxes: List[Hitbox] = []
        stream_hb = self._build_stream_hitbox(direction, stream_length, fw, fl)
        if stream_hb:
            hitboxes.append(stream_hb)

        # Internal obstacles generate a 4-flank annular pool; map borders do not pool
        pool_bounds: Optional[Pool] = None
        if isinstance(struck_obstacle, Asset) and flow > 0:
            pool_bounds, pool_hitboxes = self._partition_pool(struck_obstacle, fluid, flow)
            hitboxes.extend(pool_hitboxes)

        # Synchronize physical state and property containers
        fluid.state.length = stream_length
        fluid.state.pool = pool_bounds
        fluid.state.hitboxes = hitboxes
        fluid.state.dirty = False
        fluid.properties.hitboxes = hitboxes

        return stream_length, pool_bounds, hitboxes
```

##### Initial Conditions

**Properties**

```yaml
effects:
  fluids:
    waterflow:
      dimensions:
        w: 32
        l: 32
      lifecycle: continuous
      count: 3
      hitboxes: null
      mass: -1
      flow: 2
      source: down
```

**State**

```yaml
effects:
  fluids:
    - id: waterflow
      name: jasilynns-tears
      position:
        x: 70
        y: 0
      flow: 2
      source: down
```

**Shell Checks**

```bash
(.venv) grant@skynet:~/Projects/ontology$ file src/assets/effects/fluids/continuous/*
src/assets/effects/fluids/continuous/waterflow.png: PNG image data, 96 x 32, 8-bit/color RGBA, non-interlaced
```

##### Results

**State Dump**

```markdown

## the-steppe

- **Taxonomy:**
  - Category: `tiles`
  - Instance: `back`
  - ID: `grass`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SingleFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Friction: 100.0
- **State:**
  - Layer: `0`
  - Depth: 0
  - Position: (0, 0)
  - Multiple:
    - nx: 100
    - ny: 100

... elided for brevity

## jasilynns-tears

- **Taxonomy:**
  - Category: `effects`
  - Instance: `fluids`
  - ID: `waterflow`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.LifecycleAnimation'>`
  - Frame: `<class 'app.assets.frames.core.FluidFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: -1
  - Lifecycle: Lifecycle(type=<Lifecycles.CONTINUOUS: 'continuous'>, delay=60, frequency=0, cooldown=60, persist=False)
  - Count: 3
- **State:**
  - Layer: `0`
  - Depth: -1
  - Height: 0
  - Position: (70, 0)
  - Active: `True`
  - Animation:
    - Action: `walk`
    - Direction: `down`
    - Frame: 0
    - Tick: 51
```

!!! note
    New fields are not yet part of the state dump.

State Dump Template:

```jinja2
# Ontology: State Dump

- **Board:** {{ board_key }}
- **Timestamp:** {{ timestamp }}
{% for asset in assets %}

## {{ asset.name | default(asset.state.name if (asset.state is defined and asset.state.name is defined) else none, true) | default(asset.id, true) }}

- **Taxonomy:**
  - Category: `{{ asset.category }}`
  - Instance: `{{ asset.instance }}`
  - ID: `{{ asset.id }}`
- **Components:**
  - Animation: `{{ asset.animation.__class__ }}`
  - Frame: `{{ asset.frame.__class__ }}`
{%- set props = asset.properties if (asset.properties is defined and asset.properties is not none) else asset %}
{%- set dims = props.dimensions if (props.dimensions is defined and props.dimensions is not none) else (asset.dimensions if (asset.dimensions is defined and asset.dimensions is not none) else none) %}
{%- if dims or (props.mass is defined and props.mass is not none) or (props.count is defined and props.count is not none) or (props.friction is defined and props.friction is not none) or (props.cost is defined and props.cost) or (props.stack is defined and props.stack) or (props.hitboxes is defined and props.hitboxes) or (props.actions is defined and props.actions) or (props.frames is defined and props.frames) or (props.alignment is defined and props.alignment is not none) or (props.color is defined and props.color is not none) or (props.bold is defined and props.bold is not none) or (props.italics is defined and props.italics is not none) or (props.margins is defined and props.margins is not none) or (props.size is defined and props.size is not none) or (props.font is defined and props.font is not none) %}
- **Properties:**
{%- if dims %}
  - Dimensions:
    - Width: {{ dims.w }}
    - Length: {{ dims.l }}
{%- endif %}
{%- if props.mass is defined and props.mass is not none %}
  - Mass: {{ props.mass }}
{%- endif %}
{%- if props.lifecycle is defined and props.lifecycle is not none %}
  - Lifecycle: {{ props.lifecycle }}
{%- endif %}
{%- if props.count is defined and props.count is not none %}
  - Count: {{ props.count }}
{%- endif %}
{%- if props.friction is defined and props.friction is not none %}
  - Friction: {{ props.friction }}
{%- endif %}
{%- if props.cost is defined and props.cost %}
  - Cost:
{%- for c in props.cost %}
    - `{{ c.item }}`: {{ c.quantity }}
{%- endfor %}
{%- endif %}
{%- if props.stack is defined and props.stack %}
  - Stack:
{%- for item in props.stack %}
    - `{{ item }}`
{%- endfor %}
{%- endif %}
{%- if props.hitboxes is defined and props.hitboxes %}
  - Hitboxes:
{%- for hb in props.hitboxes %}
{%- if hb.position is defined and hb.dimensions is defined %}
    - Position: ({{ hb.position.x }}, {{ hb.position.y }}) | Dimensions: w: {{ hb.dimensions.w }}, l: {{ hb.dimensions.l }}
{%- elif hb.x is defined and hb.y is defined %}
    - Position: ({{ hb.x }}, {{ hb.y }}) | Dimensions: w: {{ hb.w | default(hb.width, true) }}, l: {{ hb.l | default(hb.length, true) }}
{%- else %}
    - {{ hb }}
{%- endif %}
{%- endfor %}
{%- endif %}
{%- if props.actions is defined and props.actions %}
{%- if props.actions is string %}
  - Actions: `{{ props.actions }}`
{%- else %}
  - Actions:
{%- for act_key, act_val in props.actions.items() %}
{%- if act_val.count is defined %}
    - `{{ act_key }}`:
      - Count: {{ act_val.count }}
      - Delay: {{ act_val.delay }}
{%- if act_val.directions %}
      - Directions:
{%- for dir_key, dir_val in act_val.directions.items() %}
        - `{{ dir_key }}`: row {{ dir_val.row if dir_val.row is defined else dir_val }}
{%- endfor %}
{%- endif %}
{%- else %}
    - `{{ act_key }}`: `{{ act_val }}`
{%- endif %}
{%- endfor %}
{%- endif %}
{%- endif %}
{%- if props.frames is defined and props.frames %}
  - Frames:
{%- for f in props.frames %}
    - `{{ f }}`
{%- endfor %}
{%- endif %}
{%- set font_obj = props.font if (props.font is defined and props.font is not none) else (props if (props.alignment is defined or props.color is defined or props.size is defined) else none) %}
{%- if font_obj %}
  - Font:
{%- if font_obj.alignment is defined and font_obj.alignment is not none %}
    - Alignment: `{{ font_obj.alignment.value if font_obj.alignment.value is defined else font_obj.alignment }}`
{%- endif %}
{%- if font_obj.size is defined and font_obj.size is not none %}
    - Size: {{ font_obj.size }}
{%- endif %}
{%- if font_obj.color is defined and font_obj.color is not none %}
    - Color: rgba({{ font_obj.color.r }}, {{ font_obj.color.g }}, {{ font_obj.color.b }}, {{ font_obj.color.a }})
{%- endif %}
{%- if font_obj.bold is defined and font_obj.bold is not none %}
    - Bold: {{ font_obj.bold }}
{%- endif %}
{%- if font_obj.italics is defined and font_obj.italics is not none %}
    - Italics: {{ font_obj.italics }}
{%- endif %}
{%- if font_obj.margins is defined and font_obj.margins is not none %}
    - Margins: {{ font_obj.margins }}
{%- endif %}
{%- endif %}
{%- endif %}
{%- if asset.state is defined and asset.state is not none %}
- **State:**
{%- if asset.state.layer is defined and asset.state.layer is not none %}
  - Layer: `{{ asset.state.layer }}`
{%- endif %}
{%- if asset.state.depth is defined and asset.state.depth is not none %}
  - Depth: {{ asset.state.depth }}
{%- endif %}
{%- if asset.state.height is defined and asset.state.height is not none %}
  - Height: {{ asset.state.height }}
{%- endif %}
{%- if asset.state.position is defined and asset.state.position is not none %}
  - Position: ({{ asset.state.position.x }}, {{ asset.state.position.y }})
{%- endif %}
{%- if asset.state.initial is defined and asset.state.initial is not none %}
  - Initial Position: ({{ asset.state.initial.x }}, {{ asset.state.initial.y }})
{%- endif %}
{%- if asset.state.velocity is defined and asset.state.velocity is not none %}
  - Velocity: ({{ asset.state.velocity.vx }}, {{ asset.state.velocity.vy }})
{%- endif %}
{%- if asset.state.speed is defined and asset.state.speed is not none %}
  - Speed: {{ asset.state.speed }}
{%- endif %}
{%- if asset.state.direction is defined and asset.state.direction is not none %}
  - Direction: `{{ asset.state.direction }}`
{%- endif %}
{%- if asset.state.multiple is defined and asset.state.multiple is not none %}
  - Multiple:
    - nx: {{ asset.state.multiple.nx }}
    - ny: {{ asset.state.multiple.ny }}
{%- endif %}
{%- if asset.state.active is defined and asset.state.active is not none %}
  - Active: `{{ asset.state.active }}`
{%- endif %}
{%- if asset.state.animation is defined and asset.state.animation is not none %}
  - Animation:
    - Action: `{{ asset.state.animation.action }}`
    - Direction: `{{ asset.state.animation.direction }}`
    - Frame: {{ asset.state.animation.frame }}
    - Tick: {{ asset.state.animation.tick }}
{%- endif %}
{%- if asset.state.plot is defined and asset.state.plot is not none %}
  - Plot:
{%- if asset.state.plot.current is defined and asset.state.plot.current is not none %}
    - Current: `{{ asset.state.plot.current }}`
{%- endif %}
{%- if asset.state.plot.previous is defined and asset.state.plot.previous %}
    - Previous:
{%- for prev_plot in asset.state.plot.previous %}
      - `{{ prev_plot }}`
{%- endfor %}
{%- endif %}
{%- endif %}
{%- if asset.state.switch is defined and asset.state.switch is not none %}
  - Switch: {{ asset.state.switch }}
{%- endif %}
{%- if asset.state.content is defined and asset.state.content is not none %}
  - Content:
{%- if asset.state.content is iterable and asset.state.content is not string %}
{%- for item in asset.state.content %}
    - `{{ item }}`
{%- endfor %}
{%- else %}
    - `{{ asset.state.content }}`
{%- endif %}
{%- endif %}
{%- if asset.state.link is defined and asset.state.link is not none %}
  - Link: `{{ asset.state.link }}`
{%- endif %}
{%- if (asset.state.outlayer is defined and asset.state.outlayer is not none) or (asset.state.out is defined and asset.state.out is not none) %}
  - Door Out:
{%- if asset.state.outlayer is not none %}
    - Layer: `{{ asset.state.outlayer }}`
{%- endif %}
{%- if asset.state.out is not none %}
    - Position: ({{ asset.state.out.x }}, {{ asset.state.out.y }})
{%- endif %}
{%- endif %}
{%- if asset.state.owner is defined and asset.state.owner is not none %}
  - Owner: `{{ asset.state.owner }}`
{%- endif %}
{%- if asset.state.persona is defined and asset.state.persona is not none %}
  - Persona: `{{ asset.state.persona }}`
{%- endif %}
{%- if asset.state.lexicon is defined and asset.state.lexicon is not none %}
  - Lexicon: `{{ asset.state.lexicon }}`
{%- endif %}
{%- if (asset.state.icon is defined and asset.state.icon is not none) or (asset.state.ttl is defined and asset.state.ttl is not none) or (asset.state.offset is defined and asset.state.offset is not none) %}
  - Attachment:
{%- if asset.state.icon is defined and asset.state.icon is not none %}
    - Icon: `{{ asset.state.icon }}`
{%- endif %}
{%- if asset.state.ttl is defined and asset.state.ttl is not none %}
    - TTL: {{ asset.state.ttl }}
{%- endif %}
{%- if asset.state.offset is defined and asset.state.offset is not none %}
    - Offset: ({{ asset.state.offset.x }}, {{ asset.state.offset.y }})
{%- endif %}
{%- endif %}
{%- if asset.state.character is defined and asset.state.character is not none %}
  - Character:
    - Strength: {{ asset.state.character.strength }}
    - Defense: {{ asset.state.character.defense }}
    - Speed: {{ asset.state.character.speed }}
    - Impulse: {{ asset.state.character.impulse }}
{%- endif %}
{%- if asset.state.meters is defined and asset.state.meters is not none %}
  - Meters:
    - Health: {{ asset.state.meters.health.current }} / {{ asset.state.meters.health.maximum }}
    - Magic: {{ asset.state.meters.magic.current }} / {{ asset.state.meters.magic.maximum }}
{%- endif %}
{%- if asset.state.inventory is defined and asset.state.inventory is not none %}
  - Inventory:
    - Wallet: {{ asset.state.inventory.wallet }}
{%- if asset.state.inventory.loot %}
    - Loot:
{%- for item_id, qty in asset.state.inventory.loot.items() %}
      - `{{ item_id }}`: {{ qty }}
{%- endfor %}
{%- endif %}
{%- if asset.state.inventory.equipment is defined and asset.state.inventory.equipment is not none %}
    - Equipment:
{%- if asset.state.inventory.equipment.armor is not none %}
      - Armor: `{{ asset.state.inventory.equipment.armor }}`
{%- endif %}
{%- if asset.state.inventory.equipment.weapon is not none %}
      - Weapon: `{{ asset.state.inventory.equipment.weapon }}`
{%- endif %}
{%- if asset.state.inventory.equipment.tool is not none %}
      - Tool: `{{ asset.state.inventory.equipment.tool }}`
{%- endif %}
{%- if asset.state.inventory.equipment.utility is not none %}
      - Utility: `{{ asset.state.inventory.equipment.utility }}`
{%- endif %}
{%- if asset.state.inventory.equipment.shield is not none %}
      - Shield: `{{ asset.state.inventory.equipment.shield }}`
{%- endif %}
{%- endif %}
{%- endif %}
{%- if asset.state.goal is defined and asset.state.goal is not none %}
  - Goal:
{%- if asset.state.goal.name is not none %}
    - Name: `{{ asset.state.goal.name }}`
{%- endif %}
{%- if asset.state.goal.category is not none %}
    - Category: `{{ asset.state.goal.category }}`
{%- endif %}
{%- if asset.state.goal.layer is not none %}
    - Layer: `{{ asset.state.goal.layer }}`
{%- endif %}
{%- if asset.state.goal.position is not none %}
    - Position: ({{ asset.state.goal.position.x }}, {{ asset.state.goal.position.y }})
{%- endif %}
{%- endif %}
{%- if asset.state.mutators is defined and asset.state.mutators is not none %}
  - Mutators:
{%- if asset.state.mutators.triggers is defined and asset.state.mutators.triggers is not none %}
    - Triggers:
      - Animated: {{ asset.state.mutators.triggers.animated }}
      - Frightened: {{ asset.state.mutators.triggers.frightened }}
      - Dead: {{ asset.state.mutators.triggers.dead }}
      - Vision: {{ asset.state.mutators.triggers.vision }}
{%- endif %}
{%- if asset.state.mutators.parameters is defined and asset.state.mutators.parameters is not none %}
    - Parameters:
{%- if asset.state.mutators.parameters.fear is defined and asset.state.mutators.parameters.fear is not none %}
      - Fear:
        - Radius: {{ asset.state.mutators.parameters.fear.radius }}
        - Limit: {{ asset.state.mutators.parameters.fear.limit }}
        - Enemy: {{ asset.state.mutators.parameters.fear.enemy }}
{%- endif %}
{%- if asset.state.mutators.parameters.vision is defined and asset.state.mutators.parameters.vision is not none %}
      - Vision:
        - Radius: {{ asset.state.mutators.parameters.vision.radius }}
{%- endif %}
{%- if asset.state.mutators.parameters.action is defined and asset.state.mutators.parameters.action is not none %}
      - Action:
        - Radius: {{ asset.state.mutators.parameters.action.radius }}
{%- endif %}
{%- endif %}
{%- endif %}
{%- if asset.state.memory is defined and asset.state.memory is not none %}
  - Memory:
{%- if asset.state.memory.goals %}
    - Goals:
{%- for g_key, goal in asset.state.memory.goals.items() %}
      - `{{ g_key }}`:
{%- if goal.name is defined and goal.name is not none %}
        - Name: `{{ goal.name }}`
{%- endif %}
{%- if goal.category is defined and goal.category is not none %}
        - Category: `{{ goal.category }}`
{%- endif %}
{%- if goal.layer is defined and goal.layer is not none %}
        - Layer: `{{ goal.layer }}`
{%- endif %}
{%- if goal.position is defined and goal.position is not none %}
        - Position: ({{ goal.position.x }}, {{ goal.position.y }})
{%- endif %}
{%- endfor %}
{%- endif %}
{%- if asset.state.memory.sprites %}
    - Sprites:
{%- for name, pos in asset.state.memory.sprites.items() %}
      - `{{ name }}`: ({{ pos.x }}, {{ pos.y }})
{%- endfor %}
{%- endif %}
{%- if asset.state.memory.property %}
    - Property:
{%- for name, pos in asset.state.memory.property.items() %}
      - `{{ name }}`: ({{ pos.x }}, {{ pos.y }})
{%- endfor %}
{%- endif %}
{%- if asset.state.memory.doors %}
    - Doors:
{%- for door_key, dest in asset.state.memory.doors.items() %}
      - `{{ door_key }}`: `{{ dest }}`
{%- endfor %}
{%- endif %}
{%- if asset.state.memory.relationships %}
    - Relationships:
{%- for entity, rel in asset.state.memory.relationships.items() %}
      - `{{ entity }}`: `{{ rel.value if rel.value is defined else rel }}`
{%- endfor %}
{%- endif %}
{%- if asset.state.memory.rumors %}
    - Rumors:
{%- for rumor in asset.state.memory.rumors %}
      - `{{ rumor }}`
{%- endfor %}
{%- endif %}
{%- if asset.state.memory.prices %}
    - Prices:
{%- for item, price in asset.state.memory.prices.items() %}
      - `{{ item }}`: {{ price }}
{%- endfor %}
{%- endif %}
{%- endif %}
{%- if asset.state.psyche is defined and asset.state.psyche is not none %}
  - Psyche:
{%- if asset.state.psyche.persona is not none %}
    - Persona: `{{ asset.state.psyche.persona }}`
{%- endif %}
{%- if asset.state.psyche.motivation is not none %}
    - Motivation: `{{ asset.state.psyche.motivation }}`
{%- endif %}
{%- if asset.state.psyche.dialogue is not none %}
    - Dialogue: `{{ asset.state.psyche.dialogue }}`
{%- endif %}
{%- if asset.state.psyche.expression is defined and asset.state.psyche.expression is not none %}
    - Expression:
{%- if asset.state.psyche.expression.icon is not none %}
      - Icon: `{{ asset.state.psyche.expression.icon }}`
{%- endif %}
{%- if asset.state.psyche.expression.ttl is not none %}
      - TTL: {{ asset.state.psyche.expression.ttl }}
{%- endif %}
{%- if asset.state.psyche.expression.offset is not none %}
      - Offset: ({{ asset.state.psyche.expression.offset.x }}, {{ asset.state.psyche.expression.offset.y }})
{%- endif %}
{%- endif %}
{%- endif %}
{%- if asset.state.intention is defined and asset.state.intention is not none %}
  - Intention: `{{ asset.state.intention.value if asset.state.intention.value is defined else asset.state.intention }}`
{%- endif %}
{%- endif %}
{% endfor %}
{%- if perimeters %}

---

# Perimeters

{% for layer, bounds in perimeters.items() %}

## Layer: {{ layer }}

{%- if bounds %}
{% for b in bounds %}

* Position: ({{ b.position.x }}, {{ b.position.y }}) | Dimensions: w: {{ b.dimensions.w }}, l: {{ b.dimensions.l }}
{%- endfor %}
{%- else %}
* *No boundaries derived for this layer.*
{%- endif %}
{% endfor %}
{%- endif %}
```

!!! todo
    Update state dump template to include new fields so we can determine what is going on.

**Registry Dump**

```markdown
## 2. Mapped Frame Coordinates

*Dynamic frame keys mapped to target asset IDs and their crop coordinates:*

| Frame Key | Target Asset ID | Crop X | Crop Y | Crop W | Crop L |
| :--- | :--- | :--- | :--- | :--- | :--- |
... elided for brevity
| `waterflow-0` | `waterflow` | 0 | 0 | 32 | 32 |
| `waterflow-0-down-1` | `waterflow` | 0 | 0 | 32 | 1 |
| `waterflow-0-down-10` | `waterflow` | 0 | 0 | 32 | 10 |
| `waterflow-0-down-11` | `waterflow` | 0 | 0 | 32 | 11 |
| `waterflow-0-down-12` | `waterflow` | 0 | 0 | 32 | 12 |
| `waterflow-0-down-13` | `waterflow` | 0 | 0 | 32 | 13 |
| `waterflow-0-down-14` | `waterflow` | 0 | 0 | 32 | 14 |
| `waterflow-0-down-15` | `waterflow` | 0 | 0 | 32 | 15 |
| `waterflow-0-down-16` | `waterflow` | 0 | 0 | 32 | 16 |
| `waterflow-0-down-17` | `waterflow` | 0 | 0 | 32 | 17 |
| `waterflow-0-down-18` | `waterflow` | 0 | 0 | 32 | 18 |
| `waterflow-0-down-19` | `waterflow` | 0 | 0 | 32 | 19 |
| `waterflow-0-down-2` | `waterflow` | 0 | 0 | 32 | 2 |
| `waterflow-0-down-20` | `waterflow` | 0 | 0 | 32 | 20 |
| `waterflow-0-down-21` | `waterflow` | 0 | 0 | 32 | 21 |
| `waterflow-0-down-22` | `waterflow` | 0 | 0 | 32 | 22 |
| `waterflow-0-down-23` | `waterflow` | 0 | 0 | 32 | 23 |
| `waterflow-0-down-24` | `waterflow` | 0 | 0 | 32 | 24 |
| `waterflow-0-down-25` | `waterflow` | 0 | 0 | 32 | 25 |
| `waterflow-0-down-26` | `waterflow` | 0 | 0 | 32 | 26 |
| `waterflow-0-down-27` | `waterflow` | 0 | 0 | 32 | 27 |
| `waterflow-0-down-28` | `waterflow` | 0 | 0 | 32 | 28 |
| `waterflow-0-down-29` | `waterflow` | 0 | 0 | 32 | 29 |
| `waterflow-0-down-3` | `waterflow` | 0 | 0 | 32 | 3 |
| `waterflow-0-down-30` | `waterflow` | 0 | 0 | 32 | 30 |
| `waterflow-0-down-31` | `waterflow` | 0 | 0 | 32 | 31 |
| `waterflow-0-down-4` | `waterflow` | 0 | 0 | 32 | 4 |
| `waterflow-0-down-5` | `waterflow` | 0 | 0 | 32 | 5 |
| `waterflow-0-down-6` | `waterflow` | 0 | 0 | 32 | 6 |
| `waterflow-0-down-7` | `waterflow` | 0 | 0 | 32 | 7 |
| `waterflow-0-down-8` | `waterflow` | 0 | 0 | 32 | 8 |
| `waterflow-0-down-9` | `waterflow` | 0 | 0 | 32 | 9 |
| `waterflow-0-down-slice-1` | `waterflow` | 0 | 0 | 32 | 1 |
| `waterflow-0-down-slice-10` | `waterflow` | 0 | 0 | 32 | 10 |
| `waterflow-0-down-slice-11` | `waterflow` | 0 | 0 | 32 | 11 |
| `waterflow-0-down-slice-12` | `waterflow` | 0 | 0 | 32 | 12 |
| `waterflow-0-down-slice-13` | `waterflow` | 0 | 0 | 32 | 13 |
| `waterflow-0-down-slice-14` | `waterflow` | 0 | 0 | 32 | 14 |
| `waterflow-0-down-slice-15` | `waterflow` | 0 | 0 | 32 | 15 |
| `waterflow-0-down-slice-16` | `waterflow` | 0 | 0 | 32 | 16 |
| `waterflow-0-down-slice-17` | `waterflow` | 0 | 0 | 32 | 17 |
| `waterflow-0-down-slice-18` | `waterflow` | 0 | 0 | 32 | 18 |
| `waterflow-0-down-slice-19` | `waterflow` | 0 | 0 | 32 | 19 |
| `waterflow-0-down-slice-2` | `waterflow` | 0 | 0 | 32 | 2 |
| `waterflow-0-down-slice-20` | `waterflow` | 0 | 0 | 32 | 20 |
| `waterflow-0-down-slice-21` | `waterflow` | 0 | 0 | 32 | 21 |
| `waterflow-0-down-slice-22` | `waterflow` | 0 | 0 | 32 | 22 |
| `waterflow-0-down-slice-23` | `waterflow` | 0 | 0 | 32 | 23 |
| `waterflow-0-down-slice-24` | `waterflow` | 0 | 0 | 32 | 24 |
| `waterflow-0-down-slice-25` | `waterflow` | 0 | 0 | 32 | 25 |
| `waterflow-0-down-slice-26` | `waterflow` | 0 | 0 | 32 | 26 |
| `waterflow-0-down-slice-27` | `waterflow` | 0 | 0 | 32 | 27 |
| `waterflow-0-down-slice-28` | `waterflow` | 0 | 0 | 32 | 28 |
| `waterflow-0-down-slice-29` | `waterflow` | 0 | 0 | 32 | 29 |
| `waterflow-0-down-slice-3` | `waterflow` | 0 | 0 | 32 | 3 |
| `waterflow-0-down-slice-30` | `waterflow` | 0 | 0 | 32 | 30 |
| `waterflow-0-down-slice-31` | `waterflow` | 0 | 0 | 32 | 31 |
| `waterflow-0-down-slice-4` | `waterflow` | 0 | 0 | 32 | 4 |
| `waterflow-0-down-slice-5` | `waterflow` | 0 | 0 | 32 | 5 |
| `waterflow-0-down-slice-6` | `waterflow` | 0 | 0 | 32 | 6 |
| `waterflow-0-down-slice-7` | `waterflow` | 0 | 0 | 32 | 7 |
| `waterflow-0-down-slice-8` | `waterflow` | 0 | 0 | 32 | 8 |
| `waterflow-0-down-slice-9` | `waterflow` | 0 | 0 | 32 | 9 |
| `waterflow-0-left-1` | `waterflow` | 31 | 0 | 1 | 32 |
| `waterflow-0-left-10` | `waterflow` | 22 | 0 | 10 | 32 |
| `waterflow-0-left-11` | `waterflow` | 21 | 0 | 11 | 32 |
| `waterflow-0-left-12` | `waterflow` | 20 | 0 | 12 | 32 |
| `waterflow-0-left-13` | `waterflow` | 19 | 0 | 13 | 32 |
| `waterflow-0-left-14` | `waterflow` | 18 | 0 | 14 | 32 |
| `waterflow-0-left-15` | `waterflow` | 17 | 0 | 15 | 32 |
| `waterflow-0-left-16` | `waterflow` | 16 | 0 | 16 | 32 |
| `waterflow-0-left-17` | `waterflow` | 15 | 0 | 17 | 32 |
| `waterflow-0-left-18` | `waterflow` | 14 | 0 | 18 | 32 |
| `waterflow-0-left-19` | `waterflow` | 13 | 0 | 19 | 32 |
| `waterflow-0-left-2` | `waterflow` | 30 | 0 | 2 | 32 |
| `waterflow-0-left-20` | `waterflow` | 12 | 0 | 20 | 32 |
| `waterflow-0-left-21` | `waterflow` | 11 | 0 | 21 | 32 |
| `waterflow-0-left-22` | `waterflow` | 10 | 0 | 22 | 32 |
| `waterflow-0-left-23` | `waterflow` | 9 | 0 | 23 | 32 |
| `waterflow-0-left-24` | `waterflow` | 8 | 0 | 24 | 32 |
| `waterflow-0-left-25` | `waterflow` | 7 | 0 | 25 | 32 |
| `waterflow-0-left-26` | `waterflow` | 6 | 0 | 26 | 32 |
| `waterflow-0-left-27` | `waterflow` | 5 | 0 | 27 | 32 |
| `waterflow-0-left-28` | `waterflow` | 4 | 0 | 28 | 32 |
| `waterflow-0-left-29` | `waterflow` | 3 | 0 | 29 | 32 |
| `waterflow-0-left-3` | `waterflow` | 29 | 0 | 3 | 32 |
| `waterflow-0-left-30` | `waterflow` | 2 | 0 | 30 | 32 |
| `waterflow-0-left-31` | `waterflow` | 1 | 0 | 31 | 32 |
| `waterflow-0-left-4` | `waterflow` | 28 | 0 | 4 | 32 |
| `waterflow-0-left-5` | `waterflow` | 27 | 0 | 5 | 32 |
| `waterflow-0-left-6` | `waterflow` | 26 | 0 | 6 | 32 |
| `waterflow-0-left-7` | `waterflow` | 25 | 0 | 7 | 32 |
| `waterflow-0-left-8` | `waterflow` | 24 | 0 | 8 | 32 |
| `waterflow-0-left-9` | `waterflow` | 23 | 0 | 9 | 32 |
| `waterflow-0-left-slice-1` | `waterflow` | 31 | 0 | 1 | 32 |
| `waterflow-0-left-slice-10` | `waterflow` | 22 | 0 | 10 | 32 |
| `waterflow-0-left-slice-11` | `waterflow` | 21 | 0 | 11 | 32 |
| `waterflow-0-left-slice-12` | `waterflow` | 20 | 0 | 12 | 32 |
| `waterflow-0-left-slice-13` | `waterflow` | 19 | 0 | 13 | 32 |
| `waterflow-0-left-slice-14` | `waterflow` | 18 | 0 | 14 | 32 |
| `waterflow-0-left-slice-15` | `waterflow` | 17 | 0 | 15 | 32 |
| `waterflow-0-left-slice-16` | `waterflow` | 16 | 0 | 16 | 32 |
| `waterflow-0-left-slice-17` | `waterflow` | 15 | 0 | 17 | 32 |
| `waterflow-0-left-slice-18` | `waterflow` | 14 | 0 | 18 | 32 |
| `waterflow-0-left-slice-19` | `waterflow` | 13 | 0 | 19 | 32 |
| `waterflow-0-left-slice-2` | `waterflow` | 30 | 0 | 2 | 32 |
| `waterflow-0-left-slice-20` | `waterflow` | 12 | 0 | 20 | 32 |
| `waterflow-0-left-slice-21` | `waterflow` | 11 | 0 | 21 | 32 |
| `waterflow-0-left-slice-22` | `waterflow` | 10 | 0 | 22 | 32 |
| `waterflow-0-left-slice-23` | `waterflow` | 9 | 0 | 23 | 32 |
| `waterflow-0-left-slice-24` | `waterflow` | 8 | 0 | 24 | 32 |
| `waterflow-0-left-slice-25` | `waterflow` | 7 | 0 | 25 | 32 |
| `waterflow-0-left-slice-26` | `waterflow` | 6 | 0 | 26 | 32 |
| `waterflow-0-left-slice-27` | `waterflow` | 5 | 0 | 27 | 32 |
| `waterflow-0-left-slice-28` | `waterflow` | 4 | 0 | 28 | 32 |
| `waterflow-0-left-slice-29` | `waterflow` | 3 | 0 | 29 | 32 |
| `waterflow-0-left-slice-3` | `waterflow` | 29 | 0 | 3 | 32 |
| `waterflow-0-left-slice-30` | `waterflow` | 2 | 0 | 30 | 32 |
| `waterflow-0-left-slice-31` | `waterflow` | 1 | 0 | 31 | 32 |
| `waterflow-0-left-slice-4` | `waterflow` | 28 | 0 | 4 | 32 |
| `waterflow-0-left-slice-5` | `waterflow` | 27 | 0 | 5 | 32 |
| `waterflow-0-left-slice-6` | `waterflow` | 26 | 0 | 6 | 32 |
| `waterflow-0-left-slice-7` | `waterflow` | 25 | 0 | 7 | 32 |
| `waterflow-0-left-slice-8` | `waterflow` | 24 | 0 | 8 | 32 |
| `waterflow-0-left-slice-9` | `waterflow` | 23 | 0 | 9 | 32 |
... elided for brevity
```

##### Review

- `waterflow` appears to be indexed correctly by the registry.
- Fluid Effect is successfully injected into Board.
- **No Fluid Frames are rendering**

Is there an interaction going on between the Tile height/depth versus Fluid height/depth?

Here is the Screen, for review,

```python
"""
# Ontology: app.game.screen

Package for the Screen, an abstraction over the Cython SDL rendering interface and image registries.
"""

# Standard Libraries
import logging
from typing import (
    List, 
    Union
)

# Application Libraries
from app.assets.base import Asset
from app.config.enums import (
    AssetInstances, 
    AssetCategories
)
from app.models.state.widgets import (
    DisplayState,
    PaneState
)
from app.models.state.sprites import (
    SpriteState,
    PlayerState
)
from app.game.menus.core import Menu

# Cython Libraries
import libs.graphics.render as render

from libs.core.models import (
    Position, 
    Dimensions
)
from libs.graphics.registry import (
    Registry, 
    TexturePtr
)

logger = logging.getLogger(__name__)

class Screen:
    """
    Manages the rendering layer and camera calculations.
    """
    screensize: Dimensions
    boardsize: Dimensions
    bg_canvas: TexturePtr
    fg_canvas: TexturePtr
    registry: Registry


    def __init__(self, 
        screensize: Dimensions,
        boardsize: Dimensions,
        tiles: List[Asset],
        registry: Registry
    ):
        self.screensize = screensize
        
        # Hardware Minimum Clamp: Guarantee rendering bounds never drop below viewport size
        self.boardsize = Dimensions(
            w=max(boardsize.w, screensize.w),
            l=max(boardsize.l, screensize.l)
        )
        
        logger.info(
            f"Initializing Screen (Viewport: {self.screensize.w}x{self.screensize.l} |" 
            f"Board: {self.boardsize.w}x{self.boardsize.l})"
        )
        
        self.registry = registry

        # Canvas Opacity Flag: If layer has no tiles, initialize to opaque black
        is_opaque = len(tiles) == 0

        # Instantiate Painter's Algorithm Targets
        self.bg_canvas = render.canvas(
            self.boardsize.w, 
            self.boardsize.l, 
            opaque=is_opaque
        )
        self.fg_canvas = render.canvas(
            self.boardsize.w, 
            self.boardsize.l
        ) # Foreground stays transparent
        
        back_tiles, fore_tiles = self._prerender(tiles)
        
        render.construct(self.bg_canvas, back_tiles)
        render.construct(self.fg_canvas, fore_tiles)


    def _prerender(self, 
        tiles: List[Asset]
    ) -> tuple[list, list]:
        """
        Prerender Tile Assets.
        """
        back_tiles, fore_tiles = [], []
        
        logger.debug(f"Constructing {len(tiles)} total tiles...")

        for tile in tiles:
            frame_keys = tile.frame.keys(tile.id, tile.state)
            for frame_key, ox, oy in frame_keys:
                tex_data = self.registry.image(frame_key)

                if not tex_data: continue

                tex, sx, sy, sw, sl = tex_data
                tile_tuple = (
                    tex, sx, sy, sw, sl,
                    tile.state.position.x + ox, 
                    tile.state.position.y + oy,
                    tile.dimensions.w, tile.dimensions.l,
                    tile.state.multiple.nx, tile.state.multiple.ny
                )
                # Route properties
                if tile.taxonomy.instance == AssetInstances.BACK:
                    back_tiles.append(tile_tuple)
                elif tile.taxonomy.instance == AssetInstances.FORE:
                    fore_tiles.append(tile_tuple)
                    
        return back_tiles, fore_tiles


    def _widgets(self, menus: List[Menu]) -> None:
        """Helper to collect and superimpose widget primitives for a set of menus."""
        widgets = []
        for menu in menus:
            if menu.widgets:
                widgets.extend(menu.widgets.values())

        primitives = []
        for widget in widgets:
            if isinstance(widget.state, DisplayState):
                tex = widget.state.canvas
                primitives.append((
                    tex, 0, 0, tex.w, tex.l,
                    widget.state.position.x, widget.state.position.y,
                    widget.dimensions.w, widget.dimensions.l
                ))
                continue

            frame_keys = widget.frame.keys(widget.id, widget.state)
            for key, ox, oy in frame_keys:
                if key:
                    tex_data = self.registry.image(key)

                    if not tex_data:
                        if not (
                            isinstance(widget.state, DisplayState) or
                            isinstance(widget.state, PaneState)
                        ):
                            logger.warning(f"Registry MISS: Frame key not found: '{key}'")
                        continue

                    tex, sx, sy, sw, sl = tex_data
                    primitives.append((
                        tex, sx, sy, sw, sl,
                        widget.state.position.x + ox, widget.state.position.y + oy,
                        sw, sl
                    ))

        if primitives:
            render.superimpose(primitives)


    def _flatten(self, 
        menus: List[Menu], 
        overlays: List[Menu]
    ) -> List[Asset]:
        """
        """
        widgets = []
        for menu in overlays:
            if menu.widgets:
                widgets.extend(menu.widgets.values())
        for menu in menus:
            if menu.widgets:
                widgets.extend(menu.widgets.values())
        return widgets

    
    def camera(self, 
        focus: Position, 
        dim: Dimensions
    ) -> Position:
        """
        Calculates the camera's top-left coordinates, centered on the focus target,
        and clamps it to the boundaries of the board.
        """
        # Center the camera on the target
        cam_x = focus.x + (dim.w // 2) - (self.screensize.w // 2)
        cam_y = focus.y + (dim.l // 2) - (self.screensize.l // 2)

        # Clamp to board edges
        max_x = max(0, self.boardsize.w - self.screensize.w)
        max_y = max(0, self.boardsize.l - self.screensize.l)

        cam_x = max(0, min(cam_x, max_x))
        cam_y = max(0, min(cam_y, max_y))

        return Position(x=cam_x, y=cam_y)


    def clear(self) -> None: render.clear()


    def present(self) -> None: render.present()


    def destroy(self) -> None:
        """
        Explicitly destroys hardware canvas textures held by this screen.
        """
        if self.bg_canvas:
            render.destroy(self.bg_canvas)
            self.bg_canvas = None
        if self.fg_canvas:
            render.destroy(self.fg_canvas)
            self.fg_canvas = None
            
    # ------------------------------------------------ CANVAS METHODS

    def draw(self, 
        assets: List[Asset], 
        focus: Position,
        dim: Dimensions
    ) -> None:
        """
        Calculates viewport positioning, culls non-visible items, and routes data to the renderer.
        """
        pov = self.camera(focus, dim)
        active_assets = []
        
        # Height-sort the assets directly prior to querying asset.frame.keys()
        #   Primary Sort: Explicit Height OR (Y + Length)
        #   Secondary Sort: Depth-index tie-breaker for overlapping entities
        assets.sort(key=lambda a: (
            a.state.height if a.state.height is not None else (
                (a.state.position.y + (a.dimensions.l if a.dimensions else 0))
            ),
            a.state.depth
        ))

        for asset in assets:
            if asset.category == AssetCategories.TILES: continue

            frame_keys = asset.frame.keys(asset.id, asset.state)
            for frame_key, ox, oy in frame_keys:
                tex_data = self.registry.image(frame_key)

                if not tex_data: 
                    if not (
                        isinstance(asset.state, SpriteState) or 
                        isinstance(asset.state, PlayerState)
                    ):
                        logger.warning(f"Registry MISS: Frame key not found: '{frame_key}'")
                    continue 

                # Flatten mapping to C-level PRIMITIVE INTEGERS for destination logic
                tex, sx, sy, sw, sl = tex_data
                dx, dy = asset.state.position.x + ox, asset.state.position.y + oy
                dw, dl = sw, sl

                # Strict Camera Culling: Only pass geometry if intersecting the camera frame 
                if (dx + dw >= pov.x and dx <= pov.x + self.screensize.w and
                    dy + dl >= pov.y and dy <= pov.y + self.screensize.l):
                    active_assets.append((tex, sx, sy, sw, sl, dx, dy, dw, dl))

        logger.debug(f"Render Payload: Camera({pov.x}, {pov.y}) | Total Assets: {len(active_assets)}")

        # Pass purely native integers to bypass heavy object allocation
        render.render(
            self.bg_canvas, 
            self.fg_canvas,
            active_assets, 
            pov.x, 
            pov.y, 
            self.screensize.w, 
            self.screensize.l
        )


    def stamp(self, widget: Asset, content: Union[str, List[str]]) -> None:
        """
        Dynamically restamps background and bakes updated text for O(N) runtime rendering. 
        """
        if not isinstance(widget.state, DisplayState):
            return
            
        tex = widget.state.canvas
        base_keys = widget.frame.keys(widget.id, widget.state)
        base_key, ox, oy = base_keys[0]  # Just unpack the first element

        tex_data = self.registry.image(base_key)
        if not tex_data:
            logger.warning(f"Registry MISS: Frame key not found: '{base_key}'")
            return

        base_ptr, sx, sy, sw, sl = tex_data
        
        # 1. Fetch and stamp clean background
        render.construct(tex, [(base_ptr, sx, sy, sw, sl, 0, 0, sw, sl, 1, 1)])
        
        # 2. Re-write the font over the cleared canvas
        if isinstance(content, str) and content:
            font_key = widget.state.font
            font = self.registry.font(font_key)
            if not font:
                logger.warning(
                    f"Registry MISS: Font '{font_key}' not found for widget '{widget.name}'."
                )
                return
            render.write((tex, 0, 0, sw, sl, 0, 0, sw, sl), content, font)
               

    def interface(self, menus: List[Menu], overlays: List[Menu]) -> None:
        """       
        Renders HUD overlays, dims the background if modal menus exist, 
        and renders modal menus on top.
        """
        # 1. Render HUD / Overlays over the raw world
        if overlays:
            self._widgets(overlays)

        # 2. Dim background and render modal menus
        if menus:
            # Alpha: 140-180 provides good contrast for UI panes
            for menu in menus:
                render.dim(r=0, g=0, b=0, a=120)
                self._widgets([menu])

    def rebake(self, 
        tiles: List[Asset], 
        boardsize: Dimensions,
        screensize: Dimensions = None
    ) -> None:
        """
        Dynamically reallocates Cython VRAM canvases for a new world state.
        Safely destroys old textures immediately to prevent VRAM OOM crashes.
        """
        logger.info("Rebaking Screen canvases for new world state...")

        # 1. Explicitly free GPU memory immediately (bypassing Python GC)
        if self.bg_canvas:
            render.destroy(self.bg_canvas)
        if self.fg_canvas:
            render.destroy(self.fg_canvas)

        # 2. Update dimensions
        if screensize:
            self.screensize = screensize

        # Hardware Minimum Clamp: Guarantee rendering bounds never drop below viewport size
        self.boardsize = Dimensions(
            w=max(boardsize.w, self.screensize.w),
            l=max(boardsize.l, self.screensize.l)
        )
        
        logger.debug(f"New Canvas Bounds: {self.boardsize.w}x{self.boardsize.l}")

        # 3. Canvas Opacity Flag: If layer has no tiles, initialize to opaque black
        is_opaque = len(tiles) == 0

        # 4. Reallocate VRAM
        self.bg_canvas = render.canvas(
            self.boardsize.w, 
            self.boardsize.l, 
            opaque=is_opaque
        )
        self.fg_canvas = render.canvas(
            self.boardsize.w, 
            self.boardsize.l
        )

        # 5. Prerender and Construct
        back_tiles, fore_tiles = self._prerender(tiles)

        render.construct(self.bg_canvas, back_tiles)
        render.construct(self.fg_canvas, fore_tiles)

    # ------------------------------------------------ EXPORT METHODS

    def export_background(self, out_path: str) -> None:
        """
        Exports the raw generated background canvas mapping to disk.
        """
        logger.info(f"Dumping pre-constructed map textures (bg_canvas) to file system -> {out_path}")
        render.save(
            out_path, 
            self.boardsize.w, 
            self.boardsize.l, 
            target=self.bg_canvas
        )


    def export_render(self, 
        out_path: str, 
        assets: List[Asset], 
        focus: Position, 
        fdim: Dimensions
    ) -> None:
        """
        Draws a composited snapshot of the frame and extracts the VRAM buffer to disk.
        """
        logger.info(f"Extracting VRAM view buffer representing full composition to file system -> {out_path}")
        self.draw(assets, focus, fdim)
        render.save(
            out_path, 
            self.screensize.w, 
            self.screensize.l
        )


    def export_map(self, out_path: str, assets: List[Asset]) -> None:
        """
        Draws a composited snapshot of the entire board and extracts the full VRAM buffer to disk,
        bypassing the viewport camera culling.
        """
        logger.info(f"Extracting full board VRAM view buffer to file system -> {out_path}")
        active_assets = []
        
        assets.sort(key=lambda a: (
            a.state.height if a.state.height is not None else (
                (a.state.position.y + (a.dimensions.l if a.dimensions else 0))
            ),
            a.state.depth
        ))

        for asset in assets:
            if asset.category == AssetCategories.TILES: continue

            frame_keys = asset.frame.keys(asset.id, asset.state)
            for frame_key, ox, oy in frame_keys:
                tex_data = self.registry.image(frame_key)
                if not tex_data: continue 

                tex, sx, sy, sw, sl = tex_data
                dx, dy = asset.state.position.x + ox, asset.state.position.y + oy
                dw, dl = sw, sl

                if (dx + dw >= 0 and dx <= self.boardsize.w and
                    dy + dl >= 0 and dy <= self.boardsize.l):
                    active_assets.append((tex, sx, sy, sw, sl, dx, dy, dw, dl))
        
        # 1. Allocate a temporary canvas matching the absolute board dimensions
        full_target = render.canvas(
            self.boardsize.w, 
            self.boardsize.l, 
            opaque=True
        )

        # 2. Render directly onto the transient target instead of the default viewport
        render.render(
            self.bg_canvas, 
            self.fg_canvas,
            active_assets, 
            0, 
            0, 
            self.boardsize.w, 
            self.boardsize.l,
            target=full_target # Invokes the Cython update
        )
        
        # 3. Read the pixels strictly from the custom target
        render.save(out_path, self.boardsize.w, self.boardsize.l, target=full_target)
        
        # 4. Explicitly free the GPU memory to prevent memory leaks
        render.destroy(full_target)
```

##### Task: Debug

- Debug the test results.
- Update the state dump template to include new fields.
- Add telemetry logs during the Fluid workflow at critical junctions to capture information that will provide insight into what is going on.

#### Implement: Phase 09.02 - {{ title }}

TODO