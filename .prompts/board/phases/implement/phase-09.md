#### Implement: Phase 09 - Hydrodynamics

**Overview** 

Establish an autonomous fluid flow and obstacle occlusion system. Introduces a dedicated `fluids` effect instance and an `obstacles` object instance. Fluid assets propagate along their source direction vector, truncate at obstacle boundaries using pre-indexed partial frames, and pool radially around non-character solid bodies.

**Principles**

1. (**Source**) A Fluid Effect has a `source`. A `source` is a Direction. Fluid flows in the Direction of its `source`.
    - In game, this means Fluid Effect assets are multiplied in the downward direction until they meet an Obstacle. 
    - **NOTE**: This means a Fluid Effect with  `source = down` may be truncated into a fraction of its dimensions. For example, if a Fluid Effect of 32px x 32px is 48px away (measured from its top left corner) from an Obstacle, the Fluid Effect will be multiplied 1.5 times (32 + 16 = 48) in the `down` direction to achieve a resulting dimension of 32px x 48px.
2. (**Obstruction**) Fluid is obstructed by Board boundaries or non-Sheet weights: $\text{Fluid Obstacles} = \text{Boundaries} \cup \{ a \in \text{Weights} \mid a.\text{category} \neq \text{SHEETS} \land (a.m > 0 \lor (a.m = 0 \land a.\text{instance} \in \text{SOLID\_OBJECTS})) \}$
3. (**Flow**) A Fluid Effect has a `flow`.A `flow` is a radial parameter that determines the boundaries of the resultant body of water that is formed *around* the Obstacle. 
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

##### Architectural Analysis

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

##### Goal: Fluid & Obstacle Data Architecture

Extend property and state schemas to support directional fluid propagation, flow radii, and explicit static fluid obstacles.

```python
# Pseudo-schema additions for models/properties.py and models/state/objects.py

@dataclass(slots=True)
class FluidProperties(EffectProperties):
    source: str = Directions.DOWN.value
    flow: int = 1
    mass: int = -1

@dataclass(slots=True)
class FluidState(EffectState):
    source: Optional[str] = None
    flow: Optional[int] = None
    stream_length: int = 0
    pool_rects: List[Tuple[int, int, int, int]] = field(default_factory=list)
    dirty: bool = True

@dataclass(slots=True)
class ObstacleProperties(ObjectProperties):
    mass: int = 0

```

##### Goal: Sliced Frame Ingestion (`FluidFrame`)

Implement `FluidFrame` to pre-crop fractional slices in `index()` and yield compound stream and pool texture offsets in `keys()`.

```python
class FluidFrame(Frame):
    def index(self, id: str, properties: dict) -> dict[str, tuple[int, int, int, int]]:
        w, l = safe_dim(properties)
        crops = {id: (0, 0, w, l)}
        # Pre-index longitudinal slices for fractional edge truncation
        for slice_len in range(1, l):
            crops[f"{id}-slice-{slice_len}"] = (0, 0, w, slice_len)
        return crops

    def keys(self, id: str, state: AssetState) -> List[Tuple[str, int, int]]:
        # Emit full tiles along stream + fractional slice + annular pool tiles
        ...
```

##### Goal: Reactive Flow Propagation (`FluidMechanics`)

Implement `FluidMechanics` in the `world` mechanics pipeline, executing raycasts against boundaries and non-sheet weights. Recalculations are triggered strictly on dirty flags set when dynamic obstacles shift position.

```python
class FluidMechanics(Mechanic):
    def update(self, board: Board, delta: float, bus: deque, payload: DevicePayload) -> None:
        # 1. Broad-phase invalidation: check if any crates/gates moved on this layer
        # 2. Narrow-phase raycast for dirty fluids
        # 3. Partition pool annulus into 4 bounding boxes
        # 4. Synchronize fluid hitboxes on board
        ...
```

##### Tasks

**1. Task: Schemas & Taxonomy Registration**

*Objective*: Register `fluids` under `AssetCategories.EFFECTS` and `obstacles` under `AssetCategories.OBJECTS` across enums, properties, state, and recipe configurations.

* [ ] Subtask: Add `FLUIDS` to `AssetInstances` enum and `EffectPropertyInstances` schema.
* [ ] Subtask: Add `OBSTACLES` to `AssetInstances` enum and `ObjectPropertyInstances` schema.
* [ ] Subtask: Define `FluidProperties` and `FluidState` dataclasses with slots in `models/properties.py` and `models/state/objects.py`.
* [ ] Subtask: Add default recipes for `fluids` and `obstacles` in `src/data/config/recipes/main.yaml`.

**2. Task: FluidFrame Component Implementation**

*Objective*: Implement `FluidFrame` in `app/assets/frames/core.py` to support multi-tile linear extension and fractional border cropping.

* [ ] Subtask: Implement `FluidFrame.index()` to generate crop maps for full tiles and 1-pixel granular slices along the flow direction.
* [ ] Subtask: Implement `FluidFrame.keys()` to assemble compound render tuples `(frame_key, offset_x, offset_y)` for the stream corridor and the radial pool.
* [ ] Subtask: Register `FluidFrame` factory mapping in `app/services/generators/game/factory.py`.

**3. Task: Spatial Occlusion & Raycast Math**

*Objective*: Build directional 1D raycast clipping to determine obstacle impact coordinates and compute the 4-quadrant pooling perimeter.

* [ ] Subtask: Implement `geometry.raycast_obstacle(origin, direction, obstacles, boundaries)` returning collision distance $D$ and target obstacle.
* [ ] Subtask: Implement annular decomposition function calculating the 4 non-overlapping bounding rectangles for radial pool flow around the obstacle.
* [ ] Subtask: Unit test raycast clipping against static bounds, closed gates, and movable crates.

**4. Task: FluidMechanics Engine System**

*Objective*: Implement `FluidMechanics` in `app/game/logic/mechanics/world/fluid.py` and integrate it into the engine pipeline.

* [ ] Subtask: Implement dynamic obstacle motion detection to flag intersecting fluids as dirty.
* [ ] Subtask: Compute stream length, fractional end slices, and pool bounding boxes during dirty updates.
* [ ] Subtask: Synchronize compound `Hitbox` models onto the `Fluid` asset to support sensor detection and hazard overlaps.
* [ ] Subtask: Register `FluidMechanics` in `src/data/config/mechanics/main.yaml` directly following `MotionMechanics` and `CollisionMechanics`.

---

### Documentation Updates

#### Draft: Fluid and Obstacle Asset Specifications

* **Page**: `docs/01-assets.md`
* **Heading**: `## Effects`

##### Drift

Phase 09 introduces `fluids` under the `Effects` category and `obstacles` under the `Objects` category. The current documentation only accounts for `passive`, `hazard`, `collectable`, and `reactable` effects.

##### Update

```markdown
### Fluids

Fluids are directional Effects that project along a designated source vector until obstructed by environmental boundaries or physical weights.

**Properties: FluidProperties**

* `dimensions: Dimensions`
* `count: int`
* `source: str` (`up`, `down`, `left`, `right`)
* `flow: int` (radial perimeter expansion multiplier)
* `lifecycle: LifecycleProperties`
* `mass: int = -1`

**Frame: FluidFrame**

* `keys(id, state)`: Returns compound list of `(frame_key, offset_x, offset_y)` spanning the stream corridor, terminal truncated slice, and radial pool rectangles.
* `index(id, properties)`: Indexes base animation frames alongside longitudinal fractional slices from $1\text{ px}$ to $\text{dimension} - 1\text{ px}$.

**State: FluidState**

* `position: Position`
* `source: Optional[str]`
* `flow: Optional[int]`
* `stream_length: int`
* `pool_rects: List[Tuple[int, int, int, int]]`
* `dirty: bool`

```

---

#### Draft: Hydrodynamics Mechanics Pipeline

* **Page**: `docs/05-mechanics.md`
* **Heading**: `### Spatial`

##### Drift

Missing documentation for `FluidMechanics` and the separation of concerns regarding static vs. dynamic obstacle invalidation.

##### Update

```markdown
- `fluid: FluidMechanics`: Resolves directional fluid propagation, obstacle impact truncation, and radial pool perimeter calculation.

**FluidMechanics**

FluidMechanics governs fluid emission across active layers. It executes after physical momentum updates (`MotionMechanics` and `CollisionMechanics`) and uses reactive dirty-checking:

1. **Change Detection**: Inspects active crates ($\vert{}v\vert{} > 0$) and switch-linked gates. If any dynamic obstacle within a fluid's influence zone mutates, `fluid.state.dirty` is set to `True`.
2. **Raycast Truncation**: Raycasts along `properties.source` against board boundaries and non-sheet solid assets ($m \ge 0$). Calculates distance $D$ to the nearest occluder.
3. **Annular Pooling**: If the occluder is an internal obstacle rather than a perimeter boundary, expands a radial pool of radius `flow` around the obstacle perimeter, partitioned into four rectangular bounding boxes.
4. **Hitbox Update**: Injects composite hitboxes for the stream path and pool boundaries into the broad-phase spatial hash.

```

---

### Bug Reports

##### Bug B008: Open Gates Included in Board Obstacles Query

**STATUS**: OPEN

**SEVERITY**: Medium

**Description**

`Board.obstacles()` retrieves all gates via `self._cached_instances.get(layer, {}).get(AssetInstances.GATES.value, [])` without checking their `state.switch` value. In the engine specification, an open gate (`switch == True`) has no physical hitboxes and allows entities to pass freely. Including open gates in `Board.obstacles()` causes pathfinding algorithms (`NavigationMechanics`) and line-of-sight checks to treat open passages as solid barriers.

**Steps to Replicate**

1. Deploy a gate linked to a pressure plate on Layer `0`.
2. Trigger the plate so `gate.state.switch = True`.
3. Call `board.obstacles('0')`.
4. Observe that the open gate is still returned in the obstacle list.

**Proposed Remediation**

Filter gates in `Board.obstacles()` by switch state:

```python
gates = [
    g for g in self._cached_instances.get(layer, {}).get(AssetInstances.GATES.value, [])
    if not getattr(g.state, "switch", False)
]

```

---

### Verification and Sanity Check

1. **State Independence:** CognitionMechanics remains the sole mutator of `Goal`, and TransitionMechanics remains the sole mutator of `Intention`. Fluid flow mechanics strictly mutate `FluidState` and spatial hitboxes.
2. **Performance Safety:** By representing fluids as single compound assets using pre-indexed `FluidFrame` slices and gating re-calculations behind obstacle velocity/switch checks, Board list removal and cache invalidation thrash are avoided.
3. **Engine Alignment:** The proposed design adheres strictly to the existing ECS frame-indexing architecture (`safe_dim`, `Registry`, `Frame.keys()`).