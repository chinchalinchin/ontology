#### Refactor: Phase 09.02 - Shorelines & Geography (CANCELLED: See v2 below)
**Overview**

Eliminates abrupt fluid boundary transitions and visual submersion-channel clipping by introducing procedural Shoreline assets along fluid perimeters. Implements virtual edge mechanics that simulate stepping down into water, applying an instantaneous positional shift, triggering waterline splash particles, and synchronizing character submersion states with environmental geometry.

##### Goal: Shoreline Taxonomy, Schemas & Recipes

Register `shorelines` under `AssetCategories.EFFECTS`. Define `ShorelineState` to track orientation, length, and parent fluid emitter links. Configure asset recipes supporting 4-way cardinal shoreline profiles (`north`, `south`, `east`, `west`) with animated foam lifecycles.

```yaml
# Property Recipe Concept
effects:
  shorelines:
    shoreline-grass-water:
      dimensions:
        w: 32
        l: 16
      lifecycle:
        type: continuous
        delay: 30
      count: 3
      hitboxes: null
      mass: -1

```

##### Goal: Procedural Shoreline Generation in Actuator

Expand `Actuator` to generate shoreline perimeters around active fluid corridors and annular pools during `pump()`. Shorelines are dynamically generated on unoccluded fluid flanks, tracking fluid stream lengths and truncations.

```python
# Actuator Perimeter Flank Calculation
def _generate_shorelines(self, fluid: Asset, stream_length: int, pool: Optional[Pool], board: Board) -> List[Asset]:
    # Compute perimeter flank bounding boxes along East, West, North, and South unoccluded boundaries
    # Construct ShorelineState instances tied to parent fluid name
    pass

```

##### Goal: Virtual Edge Traversals & Ledge Drop Mechanics

Implement virtual edge traversal logic in `fields.py`. When an entity's sensory footprint crosses a shoreline sensor into open water, apply an orthogonal positional shift equal to the shoreline thickness, spawn splash particles, toggle `mutators.triggers.submerged = True`, and impart environmental current.

```python
# Virtual Edge Spatial Shift
if crossing_shoreline_into_water:
    asset.state.position.x += shore_delta_x
    asset.state.position.y += shore_delta_y
    asset.state.mutators.triggers.submerged = True
    board.cradle.spawn_passive("splash", layer, splash_pos)

```

##### Goal: Sliced Shoreline Frame Component

Implement `ShorelineFrame` (or adapt `FluidFrame`) to dynamically tile and slice shoreline assets across variable corridor lengths and pool perimeters using cardinal orientation schemas.

##### Tasks

!!! warning
  This set of Tasks has been cancelled due to the subsequent Architectural Analyses. They have been kept merely for record-keeping purposes, to demonstrate the thought process that led to the actual Task list.

**1. Task: Schemas, Models & Asset Recipes**

*Objective*: Integrate shoreline definitions into engine taxonomy and configuration registries.

* [!: Cancelled] Subtask: Add `SHORELINES` to `AssetInstances` enum in `app/config/enums.py`.
* [!: Cancelled] Subtask: Add `shorelines: Dict[str, EffectProperties]` to `EffectPropertyInstances` schema in `app/models/properties.py`.
* [!: Cancelled] Subtask: Implement `ShorelineState` with `orientation`, `length`, `bidirectional`, and `parent_fluid` fields in `app/models/state/objects.py`.
* [!: Cancelled] Subtask: Add recipes for cardinal shoreline assets in `recipes/main.yaml`.

**2. Task: Shoreline Frame Indexing & Slicing**

*Objective*: Render repeating and sliced shoreline segments along variable stream lengths.

* [!: Cancelled] Subtask: Implement `ShorelineFrame` in `app/assets/frames/core.py` supporting cardinal crop indexing (`north`, `south`, `east`, `west`).
* [!: Cancelled] Subtask: Add fractional distal slicing for shoreline edges meeting truncated boundaries.
* [!: Cancelled] Subtask: Verify shoreline Z-ordering defaults (`depth = 0`, `height = 0`) to layer foam over water tiles.

**3. Task: Procedural Shoreline Generation**

*Objective*: Automatically instantiate and synchronize shoreline entities with fluid geometry.

* [!: Cancelled] Subtask: Add `_calculate_shoreline_flanks()` to `Actuator` in `app/services/generators/game/actuator.py`.
* [!: Cancelled] Subtask: Generate flank bounds for linear stream corridors based on emitter `source` and `length`.
* [!: Cancelled] Subtask: Generate outer flank bounds for annular obstacle pools.
* [!: Cancelled] Subtask: Add `cradle.spawn_shoreline()` and manage child shoreline lifecycles during `Actuator.pump()`.

**4. Task: Virtual Edge Motion & Immersion Transitions**

*Objective*: Resolve edge crossing physics, positional shifting, and submersion gating.

* [!: Cancelled] Subtask: Add shoreline sensor intersection checks in `app/game/logic/modules/motion/fields.py`.
* [!: Cancelled] Subtask: Implement orthogonal positional shift $\vec{\delta}_{\text{shore}}$ upon water entry.
* [!: Cancelled] Subtask: Gate `mutators.triggers.submerged = True` strictly to entities past the shoreline edge.
* [!: Cancelled] Subtask: Dispatch `cradle.spawn_passive("splash", ...)` at the shoreline crossing coordinate.
* [!: Cancelled] Subtask: Configure reverse traversal logic for bi-directional banks vs. one-way ledges.

##### User Review

**Core Problem To Keep In Mind**: Fluids are deployed by the state. Shorelines are dependent on Fluid deployments.

- It seems as though Geography would be better served as an Object, not an Effect. Shorelines aren't animated; they are an inanimate Asset. 
- To head off future refactors, it might be better to define and layout the whole procedural generation pipeline now rather than later. Shorelines are implicitly connected to the Fluid generation so they should probably stay in the `app.services.generators.game.actuator`, although with the introduction of Geography, it seems likely there will eventually be an `app.services.generators.game.terraformer` to construct physical Geography. Right now there is an implicit pipeline in the Migrator, starting with Perimeter, now with the addition of the Actuator.
- If Geography is separated into an Object, keeping it as an attribute of the FluidState is still the correct move, I believe.
- Perhaps Geography should be a category unto itself? It is a question of where the "concreteness" of Geography resides. When Actuator pumps a Fluid, it needs to generate a concrete instance of something, with the instantiation referring to a physical Asset file. If Geography is treated as a Category, and a Shoreline as an Instance, say, then the Actuator still has a "degree of a freedom" in which shoreline asset to deploy. Which actually maps to the Assets which are available, i.e. there are grassy shorelines, rocky shorelines, icy shorelines, etc., ready to be codified and added to the engine.
  - This would require some sort of additional field to either Fluid properties or Fluid state to account for what type of shoreline it generates.
- With respect to shorelines there is an added complication of how to arrange the frames. I think frames arranged in horizontal rows of (w, l) that correspond to the cardinal directions (NORTH, WEST, SOUTH, EAST). So the NORTH frame contains a shoreline along (0, 0) to (w, 0), WEST from (0, 0) to (0, l), SOUTH from (0, l) to (w, l) and EAST from (w, 0) to (w, l). 
  - But then, what defines the width of the shorelines themselves? The dimensions of the frame don't map to these dimensions. This is what hitboxes are for, actually.
- **Aesthetic (Very Unimportant) Question**: Is Geography the correct term here? Shouldn't it be Geology? 

##### Architectural Analysis

**1.1 Taxonomy: Geography vs. Geology vs. Objects vs. Effects**

The user review poses a fundamental classification question: *Where does a shoreline reside in the engine’s ontology?*

```
Asset Hierarchy
└── AssetCategories.GEOGRAPHY
    └── AssetInstances.SHORELINES (Inanimate, Static Sensor, Mass = -1)

```

1. **Why Shorelines Cannot Be `Effects`**: In this engine, `Effects` (`passive`, `hazard`, `collectable`, `reactable`, `fluids`) are defined by `LifecycleProperties` and temporal frame cycling via `LifecycleAnimation`. A shoreline is not a transient particle or an oscillating hazard; it is a permanent topographical feature. Classifying it as an `Effect` forces dummy lifecycle schemas onto a static structural boundary.
2. **Geography vs. Geology**: *Geology* denotes subsurface mineralogy, petrology, and stratigraphy. *Geography* (specifically Physical Geography / Geomorphology) denotes macroscopic surface topography, water boundaries, coastlines, terraces, and relief profiles. Because this engine already models mineral deposits under `Resources` (`ore`), surface landforms and water margins belong strictly to **Geography**.
3. **Why `Geography` Should Be an Autonomous `AssetCategory`**: While shorelines share `ObjectProperties` (`dimensions`, `hitboxes`, `mass = -1`), grouping them under `Objects` causes structural confusion:
  * `Objects` (`chests`, `crates`, `doors`, `gates`, `plates`) represent discrete interactive entities placed manually on a board.
  * `Geography` represents continuous, macro-environmental terrain structures generated procedurally to define elevation thresholds and biome perimeters.
  * Establishing `AssetCategories.GEOGRAPHY` now lays the proper foundation for future terrain features—specifically cliffs, terraces, elevation ledges, and Phase 09.03 (`Bridges, Bifurcation & Buoyancy`).

**1.2 Coupling & The Procedural Pipeline**

Fluids are declared in board state; Shorelines are dependent on Fluid geometry.

```
State Hydration Pipeline (Migrator / Actuator)
┌──────────────┐      ┌───────────────┐      ┌──────────────┐      ┌─────────────────┐
│ World State  │ ───> │  Perimeters   │ ───> │ Fluid Raycast│ ───> │ Flank Detection │
│ (Emitters)   │      │ (Contour Map) │      │ & Pool Slices│      │   & Shorelines  │
└──────────────┘      └───────────────┘      └──────────────┘      └─────────────────┘

```

1. **Fluid Emitter Configuration**:

To eliminate hardcoded asset bindings, `FluidProperties` must specify the target shoreline recipe key:

```yaml
effects:
  fluids:
    water-clean:
      dimensions: { w: 32, l: 32 }
      shoreline: "shoreline-grass"  # Target Geography Recipe
```


2. **Flank Occlusion Logic in `Actuator`**:

Shorelines must not be blindly stamped on all 4 sides of a fluid corridor:

* If a stream flows along a solid perimeter wall ($m = 0$), no shoreline exists on that flank; water abuts stone.
* If the distal stream terminates against a closed gate or immovable crate, water terminates against an obstacle face.
* Shorelines are generated **only along unoccluded flanks** where fluid directly borders empty traversable terrain.

3. **Lifecycle Reconciliation on `Board`**:

When a crate moves, `FluidMechanics` flags `fluid.state.dirty = True` and triggers `actuator.pump()`. To prevent orphan assets, `FluidState` must track its child shoreline names:

```python
# Inside Actuator.pump()
# 1. Sweep previous children
if fluid.state.shorelines:
    board.remove([board.asset(name) for name in fluid.state.shorelines if board.asset(name)])
    fluid.state.shorelines.clear()

# 2. Re-compute unoccluded flanks and instantiate new Shoreline assets
new_shorelines = self._generate_shorelines(fluid, unoccluded_flanks, board)
board.add(new_shorelines)
fluid.state.shorelines = [s.name for s in new_shorelines]
```

**1.3 Frame Slicing & Cardinal Profiles**

A shoreline strip varies in length based on raycast distance and pool expansion.

1. **Texture Atlas Layout**: A shoreline asset file contains 4 cardinal profiles organized in contiguous horizontal cells of $(w, l)$:
  * **Row Index 0 (NORTH)**: Land to the North, water to the South.
  * **Row Index 1 (WEST)**: Land to the West, water to the East.
  * **Row Index 2 (SOUTH)**: Land to the South, water to the North.
  * **Row Index 3 (EAST)**: Land to the East, water to the West.
2. **`ShorelineFrame` Slicing**: Like `FluidFrame`, `ShorelineFrame` indices repeating full tiles of dimension $(w, l)$ and registers fractional terminal slices for remainders (`length % dim != 0`).
3. **Hitbox Sensor vs. Visual Bounds**: Visual assets require padding (e.g., $32 \times 32$ or $32 \times 16$) to render soft waterline foam. However, the physical step-down boundary is narrow. The `Hitbox` on `GeographyProperties` defines this sensor strip (e.g., thickness $t = 8\text{px}$ aligned along the water threshold), preventing premature drops while the character is still on dry land.

**1.4 Virtual Edge Mechanics in `fields.py`**

Virtual edge mechanics simulate dropping off an embankment into water:

$$\vec{x}_{\text{drop}} = \vec{x}_{\text{current}} + \hat{n}_{\text{shore}} \cdot t_{\text{shore}}$$

1. **Trigger Condition**:
Evaluated during `fields.update()`. When an entity intersects a `shoreline` sensor:
  * Calculate dot product of entity velocity with the inward shoreline normal $\vec{v} \cdot \hat{n}_{\text{water}}$.
  * If $\vec{v} \cdot \hat{n}_{\text{water}} > 0$ (moving into water):
  * Apply spatial displacement shift $\vec{\delta}$ equal to shoreline sensor thickness.
  * Toggle `entity.state.mutators.triggers.submerged = True`.
  * Dispatch `board.cradle.spawn_passive("splash", layer, crossing_pos)`.
  * Superimpose fluid current $\vec{v}_{\text{current}}$.
2. **Ledge Drop vs. Bi-directional Banks**:
  * `bidirectional == True`: Allows wading back onto land. Crossing back clears `submerged` and removes current velocity.
  * `bidirectional == False` (cliff/ledge): Treats the edge as a sheer drop. Reverse traversal is blocked by nullifying velocity components directed against $\hat{n}_{\text{water}}$.

#### Refactor: Phase 09.02 v2 - Shores & Geography (CANCELLED: See v2 below)

**Overview**

Introduces `AssetCategories.GEOGRAPHY` to model macroscopic surface landforms and procedural water boundaries. Expands `Actuator` to calculate unoccluded fluid corridor and pool flanks, spawning repeating and sliced `Shoreline` sensor assets. Implements virtual edge mechanics in `fields.py` to handle spatial drop shifts, immersion transitions, and one-way embankment constraints.

##### Goal: Geography Taxonomy, Schemas & Recipes

Codify `AssetCategories.GEOGRAPHY` in the asset taxonomy. Define `GeographyProperties` and `ShorelineState`. Add `shoreline` asset linkage to `FluidProperties` and establish recipe definitions for cardinal bank transitions.

```yaml
# Property Concept
geography:
  shorelines:
    shoreline-grass:
      dimensions: { w: 32, l: 32 }
      thickness: 8
      mass: -1
      hitboxes:
        - position: { x: 0, y: 24 }
          dimensions: { w: 32, l: 8 }

```

##### Goal: Shoreline Frame Indexing & Slicing Component

Implement `ShorelineFrame` to index cardinal profile rows (`north`, `west`, `south`, `east`) and support fractional distal slicing for irregular stream lengths and pool perimeters.

```python
# ShorelineFrame Key Emission Concept
class ShorelineFrame(Frame):
    def keys(self, id: str, state: ShorelineState) -> List[Tuple[str, int, int]]:
        # Emit repeating full tile keys along state.length
        # Emit terminal sliced key for remainder
        pass
```

##### Goal: Procedural Flank Generation & Lifecycle in Actuator

Enhance `Actuator` to inspect corridor raycast boundaries and annular pool perimeters against environmental obstacles, generating `Shoreline` assets strictly along unoccluded flanks and caching active IDs on `FluidState`.

```python
# Actuator Flank Extraction Concept
def _calculate_unoccluded_flanks(self, fluid: Asset, board: Board) -> List[FlankBounds]:
    # Extract left, right, and pool margins
    # Filter margins occluded by m=0 walls, boundaries, or crates
    pass
```

##### Goal: Virtual Edge Traversals & Ledge Drop Mechanics

Integrate sensor traversal resolution into `fields.py`. Apply instantaneous step-down displacement, gate `submerged` states, trigger splash particles, and enforce directional ledge traversal.

##### Tasks

!!! warning
  This set of Tasks has been cancelled due to the subsequent Architectural Analyses. They have been kept merely for record-keeping purposes, to demonstrate the thought process that led to the actual Task list.

**1. Task: Schemas, Taxonomy & Configuration**

*Objective*: Codify `GEOGRAPHY` category and `SHORELINES` instances across data schemas and engine models.

* [!: Cancelled] Subtask: Add `GEOGRAPHY = "geography"` to `AssetCategories` in `app/config/enums.py`.
* [!: Cancelled] Subtask: Add `SHORELINES = "shorelines"` to `AssetInstances` in `app/config/enums.py`.
* [!: Cancelled]Subtask: Implement `GeographyProperties` and update `PropertiesSchema` in `app/models/properties.py`.
* [!: Cancelled] Subtask: Add optional `shoreline: Optional[str] = None` field to `EffectProperties` (or fluid property schemas).
* [!: Cancelled] Subtask: Implement `ShorelineState` in `app/models/state/objects.py` with `orientation`, `length`, `thickness`, `bidirectional`, and `parent_fluid`.
* [!: Cancelled] Subtask: Add `shorelines: List[str]` to `FluidState` to track managed child entities.
* [!: Cancelled] Subtask: Register `shoreline-grass` recipe under `recipes/main.yaml`.

**2. Task: ShorelineFrame Indexing & Rendering**

*Objective*: Provide dynamic repeating and distal fractional slicing across cardinal orientations.

* [!: Cancelled] Subtask: Implement `ShorelineFrame` in `app/assets/frames/core.py`.
* [!: Cancelled] Subtask: Implement `ShorelineFrame.index()` mapping cardinal row offsets (0: North, 1: West, 2: South, 3: East) and distal fractional crops.
* [!: Cancelled] Subtask: Implement `ShorelineFrame.keys()` emitting tile repeat offsets and terminal slices based on `state.length`.
* [!: Cancelled] Subtask: Ensure default Z-ordering sorts shorelines above fluid surfaces (`depth = 0, height = 0`).

**3. Task: Procedural Flank Calculation in Actuator**

*Objective*: Calculate unoccluded fluid flanks and manage shoreline lifecycles.

* [!: Cancelled] Subtask: Implement `_detect_flank_occlusions()` in `app/services/generators/game/actuator.py` querying boundary contours and static solids.
* [!: Cancelled] Subtask: Add `_generate_stream_shorelines()` for linear stream boundaries.
* [!: Cancelled] Subtask: Add `_generate_pool_shorelines()` for annular obstacle flood perimeters.
* [!: Cancelled] Subtask: Implement child shoreline purging in `Actuator.pump()` using `fluid.state.shorelines` to prevent memory leaks during dirty state re-pumps.
* [!: Cancelled] Subtask: Add `spawn_shoreline()` helper to `Cradle` in `app/services/generators/game/cradle.py`.

**4. Task: Virtual Edge Traversals in Motion Pipeline**

*Objective*: Resolve shoreline sensor crossings and submersion transitions in `fields.py`.

* [!: Cancelled]Subtask: Add shoreline sensor query pass in `app/game/logic/modules/motion/fields.py`.
* [!: Cancelled] Subtask: Compute velocity dot products against shoreline inward normals to differentiate entry vs. exit vectors.
* [!: Cancelled] Subtask: Apply orthogonal spatial nudge $\vec{\delta}_{\text{shore}}$ upon water entry.
* [!: Cancelled] Subtask: Transition `asset.state.mutators.triggers.submerged = True` and emit splash passive particles strictly upon clearing the shoreline sensor.
* [!: Cancelled]Subtask: Enforce one-way constraint on non-bidirectional shorelines by cancelling velocity vectors directed against the bank.

##### User Review

This is better and closer to what I think needs implemented. However, I don't think shoreline should be a Fluid property. That would mean the Fluid deployment has to be specific to the terrain it is embedded in and has to be redefined for each type of terrain. Furthermore, what if fluid traverses different terrain Tiles over the course of its stream length? This would lead to confusing rendering results. 

The shoreline generation has to be aware of the Tile grid stored on the Board to be able to map the shoreline instances appropriately. Shorelines have to be configured in the asset directories in some way to make them map to tiles. 

- Essentially, extending the analogy of the Board as a database: Shorelines need a "secondary key" to map to the Tiles.

##### Architectural Analysis

**1.1 The Relational Inversion: Fluid-Centric vs. Terrain-Centric Shorelines**

Binding `shoreline` to `FluidProperties` violates the physical reality of the environment:

1. **Multi-Biome Corridors**: A single fluid emitter with a 300px stream length might originate in a rocky cavern, traverse a grass meadow, and terminate across a sand beach. If the fluid emitter dictates the shoreline asset globally, stone and sand banks render with grass foam.
2. **Terrain-Driven Geometry**: Shorelines are the physical margin where dry substrate meets water. Visually and physically, the bank is an attribute of the terrain being submerged, not of the water itself.

```text
Relational Model: Board as Database
┌─────────────────────────┐
│     Fluid Instance      │
│  (Emits corridor/pool)  │
└────────────┬────────────┘
             │ Intersects & Borders
             ▼
┌─────────────────────────┐         Foreign Key         ┌─────────────────────────┐
│       Board Tile        │ ◄─────────────────────────  │     Shoreline Asset     │
│   (Grid Position x, y)  │   (tile: "tile-grass-01")   │   (Category: Geography) │
└─────────────────────────┘                             └─────────────────────────┘
```

In relational terms:

* `Board._cached_tilemap` acts as the spatial table of terrain tiles.
* `GeographyProperties` on the Shoreline asset declares a **secondary key** (`tile: str`, optionally paired with `fluid: str`) pointing back to the `Tile` asset ID it encapsulates.
* The `Registry` or `Orchestrator` builds an inverted lookup index during bootstrap: $\text{Index}[(tile\_id, fluid\_id)] \to shoreline\_asset\_id$
* When `Actuator.pump()` resolves a fluid corridor or pool, it queries the `Board` for the adjacent background tiles along the unoccluded perimeter and resolves the exact shoreline asset dynamically.

**1.2 Flank Discretization & Run-Length Segmentation**

Because a stream flank can border multiple terrain types, flanks cannot be treated as a single continuous bounding box. Instead, the `Actuator` must discretize and group unoccluded perimeters:

```text
Stream Corridor (Flow Down)
Tile Grid:
[Grass Tile]  | [Water Stream] |  [Stone Tile]
[Grass Tile]  | [Water Stream] |  [Stone Tile]
[Dirt Tile]   | [Water Stream] |  [Stone Tile]

Flank Sampling Resolution:
Left Flank:
  - (y: 0 -> 64):  Tile = Grass -> Span = 64px -> Instantiate ShorelineGrass (WEST profile)
  - (y: 64 -> 96): Tile = Dirt  -> Span = 32px -> Instantiate ShorelineDirt  (WEST profile)
Right Flank:
  - (y: 0 -> 96):  Tile = Stone -> Span = 96px -> Instantiate ShorelineStone (EAST profile)
```

1. **Cell Discretization**: The unoccluded flank is sampled along the grid interval defined by `TILE_HASH_SIZE` (32px).
2. **Terrain Query**: For each flank step, `board.tile(layer, adjacent_coord, instance=AssetInstances.BACK.value)` retrieves the bordering terrain asset.
3. **Run-Length Grouping**: Contiguous cells sharing the same resolved `shoreline_id` are coalesced into a single segment of `length = N * 32px`.
4. **Distal Truncation**: If the fluid terminates mid-tile due to an obstacle collision (`length % 32 != 0`), the terminal shoreline segment receives the fractional length, delegating edge cropping to `ShorelineFrame`.

**Summary**

| Dimension | Previous Conception | Terrain-Coupled Geography Architecture |
| --- | --- | --- |
| **Category** | `Effects` (Animated lifecycle) | `Geography` (Inanimate structural terrain) |
| **Coupling** | Fluid $\to$ Shoreline (Global property on emitter) | Tile $\leftrightarrow$ Shoreline (Secondary key relational index) |
| **Flank Generation** | Monolithic corridor bounding box | Cell-discretized sampling with run-length encoding |
| **Multi-Biome Support** | Impossible (Entire stream used 1 bank texture) | Native (Stream changes bank graphics when crossing tile types) |
| **Lifecycle** | Orphan risks during crate/gate movement | Tracked via `fluid.state.shorelines` and pruned on dirty re-pumps |

#### Refactor: Phase 09.02 v3 - Shorelines & Geography

**Overview**

Introduces `AssetCategories.GEOGRAPHY` to model macroscopic surface topography. Implements terrain-coupled shoreline sensors where `Shoreline` assets reference `Tile` keys as secondary relational indexes. Enhances `Actuator` to discretize unoccluded fluid flanks against `board._cached_tilemap`, grouping contiguous terrain segments and spawning terrain-accurate shoreline assets. Implements virtual edge drop mechanics and directional ledge constraints in `fields.py`.

##### Goal: Geography Taxonomy & Secondary Index Registry

Define `AssetCategories.GEOGRAPHY` and `AssetInstances.SHORELINES`. Introduce `GeographyProperties` featuring `tile` and `fluid` foreign keys. Build a relational lookup cache in the `Registry` / `Loader` mapping `(tile_id, fluid_id) -> shoreline_id`.

```yaml
# Geography Asset Property Concept (assets/geography/main.yaml)
geography:
  shorelines:
    grassy-river-shore:
      tile: "grass"
      fluid: "waterflow"
      dimensions: 
        w: 32
        l: 32
      thickness: 8
      mass: -1
      hitboxes:
        - position:
            x: 0
            y: 24
          dimensions:
            w: 32
            l: 8
```

##### Goal: Terrain-Discretized Flank Extraction in Actuator

Expand `Actuator` to step along unoccluded stream flanks and annular pool perimeters at grid intervals. Query `board.tile()` for each adjacent cell, resolve the matching shoreline asset via the secondary index, coalesce homogenous runs, and manage child shoreline lifecycles on `FluidState`.

```python
# Discretized Flank Grouping Concept
def _segment_flank(self, flank_coords: List[Tuple[int, int]], fluid: Asset, board: Board) -> List[ShorelineSegment]:
    # 1. Query board.tile(layer, coord) for each grid cell along the flank
    # 2. Map tile.id -> shoreline_id via registry index
    # 3. Coalesce contiguous cells with identical shoreline_id into run-length spans
    pass

```

##### Goal: Cardinal Frame Indexing & Fractional Slicing

Implement `ShorelineFrame` to index the 4 cardinal rows (`north`, `west`, `south`, `east`) from the asset atlas and emit repeating full-tile keys with distal fractional slices.

##### Goal: Virtual Edge Mechanics & Immersion Transitions

Implement sensory edge crossing in `fields.py`. Detect when character footprints traverse the shoreline sensor into fluid, apply orthogonal positional nudge $\vec{\delta}_{\text{shore}}$, spawn splash passives, toggle `mutators.triggers.submerged = True`, and enforce one-way traversal for sheer ledges.

##### Tasks

**1. Task: Schemas, Taxonomy & Secondary Indexing**

*Objective*: Establish `GEOGRAPHY` data structures and the `(tile, fluid) -> shoreline` relational index.

* [ ] Subtask: Add `GEOGRAPHY = "geography"` to `AssetCategories` and `SHORELINES = "shorelines"` to `AssetInstances` in `app/config/enums.py`.
* [ ] Subtask: Implement `GeographyProperties` in `app/models/properties.py` containing `tile: str`, `fluid: Optional[str]`, `thickness: int = 8`, `dimensions: Dimensions`, `hitboxes: List[Hitbox]`, and `mass: int = -1`.
* [ ] Subtask: Add `geography: GeographyPropertyInstances` to `PropertiesSchema`.
* [ ] Subtask: Implement inverted lookup cache `_shoreline_index: Dict[Tuple[str, Optional[str]], str]` in `Registry` or `Loader` mapping `(tile_id, fluid_id)` to `shoreline_id`.
* [ ] Subtask: Implement `ShorelineState` in `app/models/state/objects.py` with `orientation`, `length`, `thickness`, `bidirectional`, and `parent_fluid`.
* [ ] Subtask: Add `shorelines: List[str]` to `FluidState` to track managed child entities.

**2. Task: ShorelineFrame Indexing & Slicing**

*Objective*: Render repeating and sliced shoreline segments along variable stream lengths.

* [ ] Subtask: Implement `ShorelineFrame` in `app/assets/frames/core.py`.
* [ ] Subtask: Index 4 cardinal rows (0: North, 1: West, 2: South, 3: East) in `ShorelineFrame.index()`.
* [ ] Subtask: Generate full-tile keys and fractional distal crop keys in `ShorelineFrame.index()`.
* [ ] Subtask: Implement `ShorelineFrame.keys()` emitting tile repetition offsets along `state.length` with terminal slice remainders.
* [ ] Subtask: Verify Z-order default (`depth = 0`, `height = 0`) to sort banks above water canvas.

**3. Task: Grid-Discretized Flank Extraction in Actuator**

*Objective*: Map adjacent board tiles to shoreline segments during fluid generation.

* [ ] Subtask: Implement `_sample_flank_cells()` in `app/services/generators/game/actuator.py` to step along linear stream and pool margins at `TILE_HASH_SIZE` increments.
* [ ] Subtask: Implement `_resolve_tile_shorelines()` querying `board.tile(layer, pos)` at each cell and mapping to `shoreline_id`.
* [ ] Subtask: Coalesce contiguous cells sharing the same `shoreline_id` into cohesive `ShorelineState` segments.
* [ ] Subtask: Add distal remainder slicing to handle fractional terminal stream lengths.
* [ ] Subtask: Implement child shoreline cleanup in `Actuator.pump()`: purge entities tracked in `fluid.state.shorelines` from `Board` before re-allocating.
* [ ] Subtask: Add `cradle.spawn_shoreline()` to `app/services/generators/game/cradle.py`.

**4. Task: Virtual Edge Motion & Immersion Transitions**

*Objective*: Handle spatial drop shifts, immersion gating, and ledge constraints.

* [ ] Subtask: Add shoreline sensor query pass in `app/game/logic/modules/motion/fields.py`.
* [ ] Subtask: Calculate velocity dot products against shoreline normals to verify direction of traversal (land $\to$ water vs water $\to$ land).
* [ ] Subtask: Apply orthogonal spatial nudge $\vec{\delta}_{\text{shore}}$ upon water entry.
* [ ] Subtask: Gate `mutators.triggers.submerged = True` strictly to entities clearing the shoreline sensor.
* [ ] Subtask: Dispatch `board.cradle.spawn_passive("splash", ...)` at the crossing coordinate.
* [ ] Subtask: Enforce one-way constraint on non-bidirectional banks by nullifying reverse velocities.

##### User Review

Okay, bugs logged and documentation updated. Backlog mostly accepted. I think the task list is basically finalized, but two further points I want to drill down into before proceeding to the implementation of the refactor. 

Starting with the simpler issue:

```markdown
* [ ] Subtask: Implement `ShorelineFrame` in `app/assets/frames/core.py`.
```

It seems like the ShorelineFrame is basically identical to the FluidFrame logic, is it not? Is there any reason the FluidFrame cannot be reused?

```markdown
- [ ] Subtask: Implement inverted lookup cache `_shoreline_index: Dict[Tuple[str, Optional[str]], str]` in `Registry` or `Loader` mapping `(tile_id, fluid_id)` to `shoreline_id`.
```

This is probably going to be the trickiest bit. It is not clear to me where the lookup occurs or where in the application it should live. It seems like it would only be needed during the Actuator phase. Once the Fluid ID is determined, the rendering shouldn't care where the Shoreline ID came from. 

The actual codified relationship will live in YAML in the Geography properties. YAML gets loaded by Loader during orchestration. Currently the Actuator is instantiated in two spots: FluidMechanics and the Migrator. Seems like it will need to be instantiated in the Builder so it can be injected with Asset properties. Then it will need injected into the Migrator and registered to the FluidMechanics in a similar manner to the transition executors for TransitionMechanics and PlotMechanics.

Which brings up the point that the Mechanic interface, 

```python
"""
# Ontology: app.game.logic.mechanics.base

Package for defining the Mechanic interface.
"""
from __future__ import annotations

# Standard Libraries
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import collections
import logging

if TYPE_CHECKING:
    from app.game.board import Board

# Application Libraries

from app.models.state import (
    DevicePayload
)

logger = logging.getLogger(__name__)

class Mechanic(ABC):
    """
    """

    @abstractmethod 
    def update(self, 
        board: Board, 
        delta: float,
        bus: collections.deque, 
        payload: DevicePayload
    ) -> None:
        pass
```

Might need modified. Currently the Builder checks the class name on the Mechanics to inject their dependencies. It might be better to setup a codified interface to accept the Mechanic dependencies.
