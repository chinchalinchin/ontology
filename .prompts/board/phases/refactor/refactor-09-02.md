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
  This set of Tasks has been cancelled due to the subsequent Architectural Analyses. See Next Section.

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

#### Refactor: Phase 09.02 v2 - Shores & Geography (CANCELLED: See v3 below)

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
  This set of Tasks has been cancelled due to the subsequent Architectural Analyses. See Next Section.

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

#### Refactor: Phase 09.02 v3 - Shorelines & Geography (CANCELLED: See v4 below)

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

!!! warning
  This set of Tasks has been cancelled due to the subsequent Architectural Analyses. See Next Section.

##### User Review

Okay, bugs logged and documentation updated. Backlog mostly accepted. I think the task list is basically finalized, but two further points I want to drill down into before proceeding to the implementation of the refactor. 

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

##### Architectural Analysis

**Secondary Indexing: Location & Lifecycle**

The relationship between `Tile`, `Fluid`, and `Shoreline` is static metadata declared in YAML:

```yaml
# src/assets/geography/main.yaml
geography:
  shorelines:
    shoreline-grass-water:
      tile: tile-grass-meadow
      fluid: fluid-water-clean      # Optional constraint
      dimensions: { w: 32, l: 32 }
      thickness: 8
      mass: -1

```

**Where the Index Lives**

Neither the `Registry`, `Screen`, nor `Board` needs to know that `tile-grass-meadow` maps to `shoreline-grass-water`.

* The **`Registry`** only cares about rasterizing image files into `TexturePtr` crop maps.
* The **`Board`** is a database of deployed entities.
* The **`Screen`** only reads resolved frame keys.

The only component that performs this relational translation is the **`Actuator`**. Therefore, the lookup table belongs directly in the `Actuator` domain as a `ShorelineIndex`:

```python
class ShorelineIndex:
    """
    Relational lookup table mapping (tile_id, fluid_id) tuples to shoreline asset IDs.
    """
    def __init__(self, entries: Dict[Tuple[str, Optional[str]], str]):
        self._entries = entries

    def resolve(self, tile_id: str, fluid_id: Optional[str] = None) -> Optional[str]:
        # 1. Exact match: (tile, fluid)
        if fluid_id and (tile_id, fluid_id) in self._entries:
            return self._entries[(tile_id, fluid_id)]
        # 2. Substrate fallback: (tile, None)
        return self._entries.get((tile_id, None))

```

**Compilation Timing**

The `ShorelineIndex` is built during the **Bootstrapping Phase** (in `Orchestrator.__init__`) immediately after `PropertiesSchema` is parsed by Pydantic:

1. `Orchestrator` iterates over `properties.geography.shorelines`.
2. It compiles `ShorelineIndex({(p.tile, p.fluid): asset_id, ...})`.
3. It passes `ShorelineIndex` into the `Actuator` during construction.

**Actuator Lifecycle & Mechanic Dependency Injection**

Currently, `Actuator` is instantiated ad-hoc inside `Migrator` and `FluidMechanics`:

* In `Migrator._build_generator()`: `actuator = Actuator()`
* In `FluidMechanics.__init__()`: `self.actuator = Actuator()`

If `Actuator` requires injected properties or a `ShorelineIndex`, ad-hoc instantiation becomes untenable. Furthermore, inspecting mechanic class names in the Builder (`if isinstance(m, TransitionMechanics): ...`) is a brittle anti-pattern.

**Evaluating the Mechanic Interface**

```python
class Mechanic(ABC):
    @abstractmethod 
    def update(self, 
        board: Board, 
        delta: float,
        bus: collections.deque, 
        payload: DevicePayload
    ) -> None:
        pass

```

The runtime interface `Mechanic.update(...)` is **not** where static dependencies belong. Polluting `update()` with `actuator`, `isl_matrix`, or `plot_engine` would bloat the game loop signature and violate Interface Segregation. Static dependencies belong in the **constructor (`__init__`)**.

**Recommended Solution: Mechanics Factory with Constructor Injection**

Replace generic `cls()` instantiation with an explicit `MechanicsFactory` (or provider registry) inside the orchestration pipeline.

```
Orchestrator Bootstrapping
┌─────────────────────────┐
│     PropertiesSchema    │ ───> ShorelineIndex ───> Actuator
└─────────────────────────┘                              │
                                                         ▼
┌─────────────────────────┐                     ┌──────────────────┐
│ Configuration (YAML)    │ ──────────────────> │ MechanicsFactory │
└─────────────────────────┘                     └────────┬─────────┘
                                                         │
                         ┌───────────────────────────────┴───────────────────────────────┐
                         ▼                                                               ▼
             FluidMechanics(actuator)                                        TransitionMechanics(matrix)

```

```python
class MechanicsFactory:
    """
    Instantiates mechanics with explicit constructor dependency injection,
    eliminating runtime class-name inspection.
    """
    def __init__(self, 
        actuator: Actuator, 
        isl_matrix: Any, 
        plot_engine: Any
    ):
        self._builders = {
            "fluid": lambda: FluidMechanics(actuator=actuator),
            "transition": lambda: TransitionMechanics(matrix=isl_matrix),
            "plot": lambda: PlotMechanics(engine=plot_engine),
            "motion": lambda: MotionMechanics(),
            "animation": lambda: AnimationMechanics(),
            "menu": lambda: MenuMechanics(),
            "remove": lambda: RemoveMechanics(),
            "combat": lambda: CombatMechanics(),
            "interaction": lambda: InteractionMechanics(),
            "cognition": lambda: CognitionMechanics(),
            "navigation": lambda: NavigationMechanics(),
            "player": lambda: PlayerMechanics(),
            "social": lambda: SpeechMechanics(),
            "switch": lambda: SwitchMechanics(),
            "projectile": lambda: ProjectileMechanics(),
            "collision": lambda: CollisionMechanics(),
        }

    def build(self, key: str) -> Mechanic:
        builder = self._builders.get(key)
        if not builder:
            raise KeyError(f"No mechanic factory registered for key: '{key}'")
        return builder()

```

**Why This Cleanly Resolves Both Problems**

1. **Eliminates Ad-Hoc Instantiation**:

`Actuator` is constructed once during bootstrap:

```python
shoreline_index = ShorelineIndex.from_properties(properties.geography.shorelines)
actuator = Actuator(shorelines=shoreline_index)
```

2. **Unified Migrator & FluidMechanics Dependency**:

* `Migrator` receives `actuator` directly in its constructor: `Migrator(board, properties, configurations, actuator=actuator)`.
* `FluidMechanics` receives the exact same `actuator` via `MechanicsFactory`.

3. **Strict Immutability**:

Mechanics never exist in an unconfigured, half-initialized state. No secondary `configure()` calls or class-name checks are required.

4. **Preserves the Core Engine Loop**:

The `Mechanic.update()` interface remains strictly focused on per-frame game state (`board`, `delta`, `bus`, `payload`).

##### Grooming: Finalization

Consolidate the preceding discussion into a finalized task list. Integrate the Factory recommendation into the existing framework.

##### Architectural Analysis

Phase 09.02 introduces static topographical boundaries into a simulation loop that previously modeled water as an open, uniform vector field. Bridging fluid corridors and terrain requires resolving three systemic challenges:

```
Bootstrap Pipeline
┌──────────────────────────┐
│ PropertiesSchema         │ ───> ShorelineIndex ───> Actuator ──┐
│ (geography.shorelines)   │                                      │
└──────────────────────────┘                                      │
                                                                  ▼
┌──────────────────────────┐                              ┌──────────────────┐
│ ISL / Plot Configurations│ ───────────────────────────> │ Factory          │
└──────────────────────────┘                              └────────┬─────────┘
                                                                   │
                                 ┌─────────────────────────────────┴──────────────────┐
                                 ▼                                                    ▼
                 FluidMechanics(actuator)                             TransitionMechanics(executor)
                                 │
                                 ▼
                     Runtime Execution Loop
        ┌────────────────────────────────────────────────────────┐
        │ Actuator.pump()                                        │
        │  ├── Purge dirty fluid.state.shorelines                │
        │  ├── Discretize unoccluded corridor & pool flanks      │
        │  ├── Query board.tile(layer, pos) & resolve asset      │
        │  ├── Coalesce runs -> Instantiate Shorelines           │
        │  └── Register on Board & link to FluidState            │
        │ fields.update()                                        │
        │  ├── Intersect Shoreline sensor (t = 8px)              │
        │  ├── Inward normal dot product (v · n_water)           │
        │  ├── Apply step-down shift & toggle submerged          │
        │  └── Enforce one-way constraint on sheer ledges        │
        └────────────────────────────────────────────────────────┘

```

**1. Inversion of Ownership: The Terrain-Coupled Secondary Key**

In the initial proposals, `FluidProperties` owned the shoreline asset key. This proved untenable: a single river corridor traversing stone caverns, meadows, and sandy riverbeds would force the entire stream to render identical bank foam.

Moving shorelines to `AssetCategories.GEOGRAPHY` establishes the correct ontology:

* **`GeographyProperties`** declares a secondary relational key: `tile: str` (with an optional `fluid: str` constraint).
* **`ShorelineIndex`** compiles these relations during bootstrapping into an $O(1)$ composite map:

$$\text{Index}[(tile\_id, fluid\_id)] \to shoreline\_id$$

* **`Actuator`** queries `board.tile(layer, adjacent_coord)` along unoccluded margins, resolving the correct bank asset dynamically based on the substrate the water borders.

**2. Lifecycle Unification & Dependency Injection**

Currently, `Actuator` is instantiated ad-hoc inside `FluidMechanics.__init__()` and `Migrator._build_generator()`. If `Actuator` requires injected properties and a compiled `ShorelineIndex`, ad-hoc instantiation fractures the engine state. Furthermore, `Builder.build_pipeline()` inspects string class names (`type(m).__name__ == 'TransitionMechanics'`) to inject executors post-construction.

The resolution preserves the game loop interface (`Mechanic.update(board, delta, bus, payload)`):

1. Construct `ShorelineIndex` during bootstrap inside `Builder.load_data()`.
2. Construct a single `Actuator(shorelines=shoreline_index)`.
3. Pass `actuator` directly into `Migrator(board, properties, configurations, actuator=actuator)`.
4. Refactor `Factory` to accepts constructor dependencies (`actuator`, `intention_executor`, `plot_executor`), replacing post-instantiation monkey-patching in `Builder.build_pipeline()`.

**3. Flank Discretization & Occlusion Logic**

Corridors cannot be bounded by monolithic rectangles:

* **Occlusion**: When a stream flows along a solid stone perimeter wall ($m = 0$) or strikes an immovable crate, water abuts an obstacle face. No shoreline sensor is placed along occluded cells.
* **Sampling**: Flanks are stepped in increments of `TILE_HASH_SIZE` (32px).
* **Run-Length Coalescence**: Contiguous unoccluded cells sharing the same `shoreline_id` are merged into single spans. Fractional terminal lengths (`length % 32 != 0`) are passed to the distal segment, delegating edge cropping to `ShorelineFrame`.

**4. Virtual Edge Transitions in `fields.py`**

Shorelines are sensor assets ($m = -1$) with a physical transition strip ($t = 8\text{px}$). When an entity's footprint intersects a shoreline:

* We evaluate the velocity dot product against the inward water normal: $\vec{v} \cdot \hat{n}_{\text{water}}$.
* **Entry ($\vec{v} \cdot \hat{n} > 0$)**: Apply an instantaneous spatial drop displacement ($\vec{\delta} = \hat{n} \cdot t$), toggle `mutators.triggers.submerged = True`, and spawn a splash particle via `cradle.spawn_passive()`.
* **Exit ($\vec{v} \cdot \hat{n} < 0$)**: If `bidirectional == True`, exit clears `submerged`. If `bidirectional == False` (sheer cliff/ledge), the velocity component directed against the bank is nullified, enforcing a one-way physical drop.

#### Refactor: Phase 09.02 v4 - Shorelines & Geography

**Overview**

Codifies `AssetCategories.GEOGRAPHY` to model macroscopic topographical landforms and procedural water margins. Implements the `ShorelineIndex` secondary relational lookup mapping `(tile, fluid) -> shoreline`. Establishes `MechanicsFactory` to unify constructor dependency injection across `Migrator` and `FluidMechanics`. Expands `Actuator.pump()` to discretize unoccluded fluid flanks against `board.tile()`, coalesce homogenous terrain runs, and manage child shoreline entity lifecycles. Implements `ShorelineFrame` for cardinal row atlas indexing and fractional distal slicing, and extends `fields.py` with virtual edge drop displacement, submersion gating, and one-way ledge constraints.

##### Goal: Geography Taxonomy, Properties & State Schemas

Integrate `GEOGRAPHY` and `SHORELINES` into engine enums. Define `GeographyProperties` with foreign keys (`tile`, `fluid`) and `ShorelineState` to track cardinal orientation, length, thickness, and parent fluid emitter links. Add `shorelines: List[str]` to `FluidState` to track managed child entities.

```python
@dataclass(slots=True)
class GeographyProperties(AssetProperties):
    dimensions: Dimensions
    hitboxes: Optional[List[Hitbox]] = field(default_factory=list)
    tile: str
    fluid: Optional[str] = None
    thickness: int = 8
    mass: int = -1

@dataclass(slots=True)
class ShorelineState(AssetState):
    position: Optional[Position] = None
    orientation: str = Directions.DOWN.value
    length: int = 0
    thickness: int = 8
    bidirectional: bool = True
    parent_fluid: Optional[str] = None
    hitboxes: List[Hitbox] = field(default_factory=list)

```

##### Goal: Relational Secondary Index & MechanicsFactory Dependency Injection

Compile `ShorelineIndex` during bootstrap from `properties.geography.shorelines`. Inject a single unified `Actuator(shorelines=shoreline_index)` into both `Migrator` and `MechanicsFactory`. Replace class-name inspection in `Builder.build_pipeline()` with explicit constructor injection across all mechanics.

```python
class MechanicsFactory:
    def __init__(self, actuator: Actuator, intention_executor: Any, plot_executor: Any):
        self._builders = {
            Mechanics.FLUID.value: lambda: FluidMechanics(actuator=actuator),
            Mechanics.TRANSITION.value: lambda: TransitionMechanics(executor=intention_executor),
            Mechanics.PLOT.value: lambda: PlotMechanics(executor=plot_executor),
            Mechanics.MOTION.value: lambda: MotionMechanics(),
            Mechanics.ANIMATION.value: lambda: AnimationMechanics(),
            Mechanics.MENU.value: lambda: MenuMechanics(),
            Mechanics.REMOVE.value: lambda: RemoveMechanics(),
            Mechanics.COMBAT.value: lambda: CombatMechanics(),
            Mechanics.COLLISION.value: lambda: CollisionMechanics(),
            Mechanics.INTERACTION.value: lambda: InteractionMechanics(),
            Mechanics.COGNITION.value: lambda: CognitionMechanics(),
            Mechanics.NAVIGATION.value: lambda: NavigationMechanics(),
            Mechanics.PLAYER.value: lambda: PlayerMechanics(),
            Mechanics.SOCIAL.value: lambda: SpeechMechanics(),
            Mechanics.SWITCH.value: lambda: SwitchMechanics(),
            Mechanics.PROJECTILE.value: lambda: ProjectileMechanics(),
        }

    def build(self, key: str) -> Mechanic:
        builder = self._builders.get(key)
        if not builder:
            raise KeyError(f"No mechanic factory registered for key: '{key}'")
        return builder()

```

##### Goal: Cardinal Shoreline Frame Indexing & Fractional Slicing

Implement `ShorelineFrame` to index 4 cardinal profile rows (`north`, `west`, `south`, `east`) from the asset atlas. Emit repeating full-tile keys along `state.length` with fractional distal slices for truncations.

```python
class ShorelineFrame(Frame):
    CARDINAL_ROWS = {
        Directions.UP.value: 0,     # NORTH (Land North, Water South)
        Directions.LEFT.value: 1,   # WEST  (Land West, Water East)
        Directions.DOWN.value: 2,   # SOUTH (Land South, Water North)
        Directions.RIGHT.value: 3   # EAST  (Land East, Water West)
    }

    def keys(self, id: str, state: ShorelineState) -> List[Tuple[str, int, int]]:
        # Emit repeated full tiles and distal fractional remainder slice
        pass

```

##### Goal: Transform Fluid State shorelines Into Renderable Assets

* **Atlas Indexing**: During bootstrap, the `Registry` calls `ShorelineFrame.index(id, properties)`.
* This slices the asset atlas into crop coordinates across the 4 cardinal rows (`north`, `west`, `south`, `east`) plus any fractional terminal crops, storing them under composite keys in the `Registry`'s texture map.
* When `Actuator.pump(fluid, board)` executes (either at hydration in `Migrator` or dynamically in `FluidMechanics`):
  1. **Purge**: It queries `fluid.state.shorelines` and calls `board.remove()` on existing child shoreline assets to prevent duplicate or orphaned entities.
  2. **Discretize & Resolve**: It samples unoccluded corridor and pool flanks, queries `board.tile()`, resolves the matching `shoreline_id` via `ShorelineIndex`, and coalesces contiguous cells.
  3. **Spawn**: It constructs child `ShorelineState` instances and instantiates them via `cradle.spawn_shoreline(...)`.
  4. **Inject**: It calls `board.add(new_shorelines)` and tracks the new asset names on `fluid.state.shorelines`.`

Because `Shoreline` belongs to `AssetCategories.GEOGRAPHY` (`category != AssetCategories.TILES.value`):

```python
if asset.category != AssetCategories.TILES.value:
    self._cached_renderables[layer].append(asset)

```

`board.add()` immediately appends the shoreline assets into `board._cached_renderables[layer]`.

Every frame, `Engine._render()` fetches active renderables:

```python
screen.draw(
    self.board.renderables(player.state.layer), 
    player.state.position, 
    player.dimensions
)

```

Inside `Screen.draw()`:

1. **Z-Order Sorting**: Assets are sorted via `(state.height, state.depth)`:
  * **Fluid**: `height = 0`, `depth = -1` $\to (0, -1)$
  * **Shoreline**: `height = 0`, `depth = 0` $\to (0, 0)$
  * **Dynamic Entities (Characters/Crates)**: `height = Y + L`, `depth = 0` $\to (>0, 0)$

Because $(0, -1) < (0, 0) < (Y + L, 0)$, the engine draws the fluid water canvas first, paints the foam/shoreline directly on top of the water margin, and renders characters and obstacles on top of both.

2. **Key Emission**: `Screen.draw()` calls `shoreline.frame.keys(shoreline.id, shoreline.state)`.

3. **Texture Stamping**: `Screen` queries the `Registry` for the emitted keys, applies camera culling, and passes the primitive coordinate tuples across the Cython boundary to `render.render()`.

##### Goal: Procedural Flank Discretization & Child Management in Actuator

Enhance `Actuator.pump()` to sweep active fluid corridors and annular pools. Discretize perimeter margins into 32px intervals, filter cells occluded by static solids or boundaries, query adjacent substrate tiles via `board.tile()`, resolve matching shoreline assets, coalesce contiguous spans, and register new shoreline entities on the `Board` while purging obsolete child assets.

```python
def _generate_flank_shorelines(
    self, 
    flank_coords: List[Tuple[int, int, str]], 
    fluid: Asset, 
    board: Board
) -> List[Asset]:
    # 1. Discretize and query substrate tile at each flank cell
    # 2. Map tile.id -> shoreline_id via self.shorelines.resolve()
    # 3. Coalesce contiguous cells into run-length spans
    # 4. Instantiate Shoreline assets and return for board registration
    pass

```

##### Goal: Virtual Edge Mechanics & Immersion Gating in fields.py

Integrate virtual edge crossing into `fields.py`. Calculate velocity dot products against inward shoreline normals. Apply instantaneous orthogonal step-down displacement, gate character submersion transitions, trigger splash particles, and enforce directional ledge traversal constraints.

##### Task

!!! warning
  This set of Tasks has been cancelled due to the subsequent Architectural Analyses. See Next Section.

##### User Review

Hmm. So the decision to split MechanicsFactory and Factory into separate classes is a result of the form of the dependencies they are constructing. Mechanics add a "layer" of dependencies to the dependency tree; Mechanics now needs to be injected with an executor class. And the executors require configuration and/or properties. And future Mechanics could possibly require multiple executors. So your suggestion is essentially equivalent to: formalize the relationships between executors and config/props in a dedicated class. 

Instead, my counter proposal: the mechanics have their dependencies declared in configuration:

1. Update to Mechanics interface to include a `executor` field and a `set_executor` method.
2. Register executors in the Mechanics configuration.

```yaml
mechanics:
  core:
    - menu
    - animation
    - remove
  world:
    - player
    - cognition
    - transition:
        executors:
          - intention
    - navigation
    - motion
    - interaction
    - social
    - collision
    - fluid:
        executors:
          - actuator
    - combat
    - switch
    - projectile
    - plot:
        executors:
          - plot
```

There can be a step in the Builder that initiailizes the executors. That is where the "bespokeness" resides. Each executor has a specific set of instructions for its instantiation: Translators compile configuration, Actuators ingest properties, etc. They get stored in a dictionary keyed to their type, e.g. `actuator`, `intention`, `plot`, etc.

Then, the existing Factory mechanics() method is refactored to ingest the mechanics key, the mechanics configuration and dictionary of executors. 

Evaluate this approach.

##### Architectural Analysis

1. **Keeps `Factory` Completely Stateless**: `Factory` remains a pure namespace of `@staticmethod` factory methods. No hybrid state, no lifecycle ordering constraints on `Factory` itself, and no need to pass factory instances around to `Cradle` or `Migrator`.
2. **Eliminates Post-Hoc Monkey-Patching & String Checks**: The brittle `type(m).__name__ == 'TransitionMechanics'` checks currently residing in `Builder.build_pipeline()` are completely eliminated. Instantiation and wiring happen in one step.
3. **Data-Driven & Extensible**: If a future mechanic requires multiple executors (e.g. `CommerceMechanics` requiring both a `pricing` and `reputation` executor, or `CognitionMechanics` requiring a `utility` and `path` executor), no factory code needs to be modified. You simply register the executor in the YAML configuration.
4. **Boot-Time Fail-Fast Verification**: If a mechanic configuration specifies an executor key that was not registered in the `Builder`'s executor map, the engine immediately raises a descriptive error at boot time rather than failing silently or crashing during the main game loop.


**Singular vs. Multiple Executors on the `Mechanic` Base Class**

Because the YAML schema defines `executors` as a **list**, a mechanic can hold more than one executor:

```yaml
transition:
  executors:
    - intention

```

The `Mechanic` interface should store a dictionary of executors, with a convenience property for the common single-executor case:

```python
class Mechanic(ABC):
    executors: Dict[str, Any]

    def __init__(self):
        self.executors = {}

    def set_executor(self, key: str, executor: Any) -> None:
        self.executors[key] = executor

    @property
    def executor(self) -> Any:
        """Convenience accessor for mechanics that rely on a single primary executor."""
        if not self.executors:
            return None
        return next(iter(self.executors.values()))

    @abstractmethod 
    def update(self, 
        board: Board, 
        delta: float,
        bus: collections.deque, 
        payload: DevicePayload
    ) -> None:
        pass

```

For specialized mechanics like `FluidMechanics`, you can either expose a typed property or wire it cleanly:

```python
class FluidMechanics(Mechanic):
    @property
    def actuator(self) -> Actuator:
        return self.executors["actuator"]

```

This avoids redundant internal references while keeping access strongly typed.

**Configuration Schema Normalization (Pydantic / Dataclasses)**

In `mechanics/main.yaml`, entries are polymorphic: simple mechanics are strings (e.g., `- player`), while configured mechanics are mappings (e.g., `- transition: { executors: [intention] }`).

To avoid messy `isinstance(m, dict)` branching in `Factory.mechanics()`, normalize the items in the Pydantic / Dataclass configuration schema:

```python
@dataclass(slots=True)
class MechanicConfig:
    key: str
    executors: List[str] = field(default_factory=list)

@dataclass(slots=True)
class MechanicsConfiguration:
    core: List[MechanicConfig] = field(default_factory=list)
    world: List[MechanicConfig] = field(default_factory=list)

```

The configuration loader converts bare strings into `MechanicConfig(key="player", executors=[])` and mappings into `MechanicConfig(key="transition", executors=["intention"])`. As a result, `Factory.mechanics()` receives a clean, typed model every time.

**Execution Lifecycle Timing in `Builder`**

Notice how cleanly this resolves the `Migrator` dependency on `Actuator`.

In `Builder`:

1. `load_data()` loads configuration and properties.
2. `build_executors()` runs immediately after `load_data()`:
  * Compiles ISL intention rules $\to$ `executors["intention"]`
  * Compiles ISL plot rules $\to$ `executors["plot"]`
  * Compiles `ShorelineIndex` and builds `Actuator` $\to$ `executors["actuator"]`
3. `build_board()` runs:
  * `Migrator` receives `self.executors["actuator"]` directly.
4. `build_pipeline()` runs:
  * `self.world = [Factory.mechanics(cfg, self.executors) for cfg in world_cfg]`

Both `Migrator` and `FluidMechanics` share the exact same `Actuator` instance without circular dependencies or ad-hoc instantiations.

**`Factory.mechanics()` in `app/services/generators/game/factory.py`**

```python
@staticmethod
def mechanics(config: MechanicConfig, executors: Dict[str, Any]) -> Mechanic:
    target_cls = Factory.MECHANICS_MAP.get(config.key)
    if not target_cls:
        raise KeyError(f"No mechanic class registered for key: '{config.key}'")
    
    mechanic_instance = target_cls()
    
    for executor_key in config.executors:
        executor = executors.get(executor_key)
        if executor is None:
            raise KeyError(
                f"Mechanic '{config.key}' requested executor '{executor_key}', "
                f"but it is not registered in the active executor map."
            )
        mechanic_instance.set_executor(executor_key, executor)
        
    return mechanic_instance

```

##### FINALIZED AND GROOMED: Tasks

**1. Task: Schemas, Models & Configuration Registry**

*Objective*: Codify `GEOGRAPHY` category and `SHORELINES` instances across data schemas, properties, and engine models.

* [x] Subtask: Add `GEOGRAPHY = "geography"` to `AssetCategories` in `app/config/enums.py`.
* [x] Subtask: Add `SHORELINES = "shorelines"` to `AssetInstances` in `app/config/enums.py`.
* [x] Subtask: Add `SHORELINE = "shoreline"` to `FrameRecipe` in `app/config/enums.py`.
* [x] Subtask: Implement `GeographyProperties` and `GeographyPropertyInstances` in `app/models/properties.py` and register on `PropertiesSchema`.
* [x] Subtask: Implement `ShorelineState` in `app/models/state/objects.py`.
* [x] Subtask: Add `shorelines: List[str] = field(default_factory=list)` to `FluidState` in `app/models/state/objects.py`.
* [x] Subtask: Register `shorelines` recipes under `recipes/main.yaml` mapping `frame: shoreline` and `animation: none`.

**2. Task: Config-Driven Mechanic Executors & Dependency Injection**

*Objective*: Codify mechanic executor declarations in configuration and formalize executor injection through the Mechanic base interface.

- [x] Subtask: Add `executors: Dict[str, Any]`, `set_executor(key, executor)`, and `executor` property to `Mechanic` in `app/game/logic/mechanics/base.py`.
- [x] Subtask: Update `MechanicsConfiguration` schema in `app/models/config.py` to support `MechanicInstance(key, executors)` normalization for string and dict YAML entries.
- [x] Subtask: Update `src/data/config/mechanics/main.yaml` declaring executors for `transition` (intention), `plot` (plot), and `fluid` (actuator).
- [x] Subtask: Implement `ShorelineIndex.from_properties()` in `app/game/logic/relations/shorelines.py`.
- [x] Subtask: Update `Actuator.__init__()` to accept `shorelines: Optional[ShorelineIndex] = None`.
- [x] Subtask: Add `Builder.build_executors()` compiling the master executor registry (`intention`, `plot`, `actuator`).
- [x] Subtask: Update `Builder.build_board()` to inject `self.executors["actuator"]` into `Migrator`.
- [x] Subtask: Refactor `Factory.mechanics(config, executors)` to wire declared executors, eliminating all `type(m).__name__` checks in `Builder.build_pipeline()`.
- [x] Subtask: Refactor `FluidMechanics` to query `self.actuator` via its registered executor instead of ad-hoc instantiation.

**3. Task: ShorelineFrame Indexing & Rendering**

*Objective*: Provide cardinal row atlas indexing and distal fractional slicing for variable corridor lengths.

* [~] Subtask: Implement `ShorelineFrame` in `app/assets/frames/core.py`.
* [x] Subtask: Index 4 cardinal rows (Row 0: North, Row 1: West, Row 2: South, Row 3: East) in `ShorelineFrame.index()`.
* [x] Subtask: Generate fractional crop keys for remainder slices in `ShorelineFrame.index()`.
* [x] Subtask: Implement `ShorelineFrame.keys()` emitting tile repetition offsets along `state.length` with terminal slice remainders.
* [x] Subtask: Register `FrameRecipe.SHORELINE` to `ShorelineFrame` in `Factory.FRAME_MAP`.
* [x] Subtask: Verify default Z-ordering sorts shorelines above fluid surfaces (`depth = 0, height = 0`).

**4. Task: Flank Discretization & Procedural Generation in Actuator**

*Objective*: Dynamically extract unoccluded perimeters, resolve terrain tiles, and manage child shoreline lifecycles.

* [x] Subtask: Implement flank boundary extraction for linear stream corridors (left, right, distal) based on emitter `source` and `length`.
* [x] Subtask: Implement outer flank perimeter extraction for annular pools based on `pool` bounds.
* [x] Subtask: Implement `_detect_flank_occlusions()` querying `board.perimeters` and static solid obstacles ($m \ge 0$).
* [x] Subtask: Discretize unoccluded flanks into 32px cells, query `board.tile(layer, coord)`, and resolve `shoreline_id` via `ShorelineIndex`.
* [x] Subtask: Coalesce contiguous cells sharing the same `shoreline_id` and orientation into unified `ShorelineState` entities.
* [x] Subtask: Implement child shoreline purging in `Actuator.pump()`: remove entities listed in `fluid.state.shorelines` from `Board` before re-allocating.
* [x] Subtask: Add `cradle.spawn_shoreline()` helper in `app/services/generators/game/cradle.py`.

**5. Task: Virtual Edge Traversals in Motion Pipeline**

*Objective*: Resolve sensory shoreline crossings, spatial drop displacement, immersion gating, and one-way ledges in `fields.py`.

* [x] Subtask: Add shoreline sensor query pass in `app/game/logic/modules/motion/fields.py`.
* [x] Subtask: Compute velocity dot products against shoreline inward normals to differentiate entry ($\vec{v} \cdot \hat{n} > 0$) versus exit ($\vec{v} \cdot \hat{n} < 0$).
* [x] Subtask: Apply orthogonal spatial nudge $\vec{\delta}_{\text{shore}} = \hat{n}_{\text{water}} \cdot t_{\text{shore}}$ upon water entry.
* [x] Subtask: Transition `asset.state.mutators.triggers.submerged = True` and emit splash passive particles upon crossing the shoreline sensor.
* [x] Subtask: Enforce one-way constraint on non-bidirectional shorelines by cancelling velocity vectors directed against the bank.

##### Live Test

**Tile Properties**

```yaml
tiles:
  back:
    grass:
      dimensions:
        w: 32
        l: 32
      friction: 100
```

**Fluid Properties**

```yaml
effects:
  fluids:
    waterflow-00:
      dimensions:
        w: 32
        l: 32
      lifecycle: 
        type: continuous
        delay: 60
      count: 3
      hitboxes: null
      mass: 0
```

**Geography Properties**

```yaml
geography:
  shorelines:
    grassy-shore:
      tile: grass
      fluid: waterflow-00
      dimensions: 
        w: 32
        l: 32
      thickness: 10
      mass: -1
      hitboxes: null
```

**Fluid Initial State**

```yaml
effects:
  fluids:
    - id: waterflow-00
      name: jasilynns-tears-00
      layer: '0'
      position:
        x: 70
        y: 0
      flow: 2
      source: down
    - id: waterflow-00
      name: jasilynns-tears-01
      layer: '0'
      position:
        x: 600
        y: 600
      source: left
    - id: waterflow-00
      name: jasilynns-tears-02
      layer: '0'
      flow: 4
      position:
        x: 632
        y: 0
      source: down
```

**Results**

Shorelines are successfully indexed and sliced. They are definitely rendering, but position placement is not correct. State dump included below.

**Relevant Sections of State Dump**

*Omitted after bug identified for brevity*

!!! note
  Any model updates from this phase are not yet reflected in the state dump.

**State Dump Template**

*Omitted after update for brevity*

**Priorities**

- Determine why the placement is off.
- Add Geography and updated Fluid fields to the state dump template so all available information is dumped.


##### Analysis

**1. Off-by-32px Outer Displacement (Land Tile vs. Water Canvas)**

In the state dump:

* `jasilynns-tears-00` corridor runs down at $x = 70..102$ ($w = 32$).
  * West shoreline (`spawn-152d68e1`) was anchored at $x = 38$ ($70 - 32$).
  * East shoreline (`spawn-2a59bb68`) was anchored at $x = 102$ ($70 + 32$).
* `jasilynns-tears-00.pool` runs from $y = 536..720$ ($l = 184$).
  * North shoreline (`spawn-5164d94e`) was anchored at $y = 504$ ($536 - 32$).
  * South shoreline (`spawn-6af427ab`) was anchored at $y = 720$ ($536 + 184$).

Every shoreline was anchored **completely outside the water on the dry land tile**, rather than **directly on top of the water margin**.

Because `ShorelineFrame` texture cells are drawn with transparent backdrops and foam positioned along the bank edge:

* **UP (North bank)**: Foam along $(0, 0) \to (w, 0)$ (top edge). It must sit at $y = y_{\text{water}}$ so the foam paints on the northern margin of the water canvas.
* **DOWN (South bank)**: Foam along $(0, l) \to (w, l)$ (bottom edge). It must sit at $y = y_{\text{water}} - 32$ so the bottom edge paints on the southern margin of the water canvas.
* **LEFT (West bank)**: Foam along $(0, 0) \to (0, l)$ (left edge). It must sit at $x = x_{\text{water}}$ so the foam paints on the western margin of the water canvas.
* **RIGHT (East bank)**: Foam along $(w, 0) \to (w, l)$ (right edge). It must sit at $x = x_{\text{water}} - 32$ so the right edge paints on the eastern margin of the water canvas.

Anchoring on the adjacent land tile caused the textures and sensor hitboxes to float 32px away in the grass.

**2. Corridor-to-Pool Junction Overrun & 24px Quantization Gaps**

* For `jasilynns-tears-00`, the corridor descriptor ran from $y = 1$ to $y = 601$, ignoring the fact that the pool begins at $y = 536$.
* When the flank sampling loop reached $c = 512$, the 32px step ($512..544$) crossed into the pool at $y = 536$. Because `_is_inside_fluid` tested the entire 32px bounding box, it rejected the whole block.
* This dropped the remaining unoccluded 24px ($512..536$), creating an artificial gap before the pool.
* **Fix**: When an annular pool exists, corridor flanks must terminate exactly where they meet the pool (`end = pool.y` for `DOWN`, `start = pool.y + pool.l` for `UP`, `end = pool.x` for `RIGHT`, `start = pool.x + pool.w` for `LEFT`). The distal flank must also be suppressed since the stream flows into the pool.

**3. Duplicate Overlapping Shorelines at Pool Inflow**

* `jasilynns-tears-01` had multiple shorelines at $(156, 568)$ (`spawn-bf6a9697` and `spawn-62dcfa9b`).
* Because the stream corridor flanks overlapped the outer pool bounds, both the corridor North flank and the pool East flank generated shorelines at the junction.
* Terminating the corridor at the pool boundary eliminates these collisions.

##### Live Test

*Note*: Same initial conditions.

**State Dump**

*Omitted after bug identified for brevity.*

**Notes:**

Placement is much cleaner now, however some bugs remain:

- When the down and left waterflows meet, they form overlapping pools. Because they have different flow rates, their pools are different areas, so both shorelines get rendered, with the smaller area shorelines visible over the Fluid assets.
- When crossing a shore from the north, i.e. player travelling in south direction, the first shoreline is initially rendered on top of the sprite, until the Sprite's lower bound crosses the lower bound of the shore frame, i.e. painter's algorithm. Shorelines need hardcoded depth and height to render underneath everything except the Fluid.
- South and east banks are rendering slightly askew and not contiguous with the terrain tiles, i.e. the fluid frame is visible along the edges. This only seems to happen with pools, as the actual streams render as expected, i.e. blending in with the terrain tiles.  

Here is the diagnosis and remediation for the three issues identified in the live test.

##### Analysis

1. **Bug 1: Overlapping Pool Shorelines (Smaller Pools Rendering Inside Larger Pools)**
  * **Cause**: `_generate_shorelines` only evaluated `_is_inside_fluid` against the *current* fluid being pumped. When querying the adjacent substrate tile via `board.tile(layer, coord)`, it queried the static background tile map, which returned `grass` everywhere. It did not check whether that grass was actually submerged under water from *another* fluid on the board.
  * **Fix**: Introduce `_is_water(px, py, layer, board)` and `_is_water_excluding(...)`. If the probe point (where dry land is supposed to be) is covered by any fluid's stream or pool, water meets water—no shoreline is generated. Additionally, any previously generated shorelines submerged by an expanding fluid are pruned during `pump()`.
2. **Bug 2: Painter's Algorithm Depth/Height Sorting (Shoreline on top of Player)**
  * **Cause**: `ShorelineState` was instantiated without explicitly setting `height = 0`. It inherited `height = None` from `AssetState`. When `height is None`, `Screen.draw()` falls back to geometric height (`state.position.y + dimensions.l`). For a northern pool shoreline at $y = 536$, its height evaluated to $536 + 32 = 568$. When the player approached from the north at $y = 510$, the player's height was $510 + 48 = 558 < 568$, causing the engine to sort and draw the shoreline *on top of* the player.
  * **Fix**: Hardcode `height = 0` and `depth = 0` directly on `ShorelineState` and pass them explicitly in `cradle.spawn_shoreline()`. Because dynamic entities have geometric height $Y + L \ge 48 > 0$, the sort order is guaranteed: $\text{Fluid } (0, -1) < \text{Shoreline } (0, 0) < \text{Dynamic Entities } (>0, 0)$
3. **Bug 3: South and East Banks Rendering Askew / Fluid Exposed Along Edges**
  * **Cause**: In `_partition_pool`, `pool_w = ow + 2 * flow * fw` ($56 + 128 = 184$) and `pool_l = 184`. Because `ow = 56` is not a multiple of 32, the pool dimension was 184. `FluidFrame` renders pools by stepping in unit tiles (`range(0, 184, 32)`), which stamps full 32x32 tiles. The 6th tile at offset 160 rendered fluid out to $160 + 32 = 192$ px ($+8$ px overshoot). Meanwhile, `Actuator` placed the South and East shorelines at $184 - 32 = 152$, ending at 184. Consequently, $8$ pixels of raw fluid stuck out past the shorelines along the South and East edges.
  * **Fix**: In `_partition_pool`, snap the pool's outer bounding box to `TILE_HASH_SIZE = 32` grid multiples. The pool expands to an exact multiple of 32 (e.g., $192 \times 224$), perfectly matching `FluidFrame`'s full-tile rasterization and aligning the pool and shorelines to the background terrain grid with zero pixel bleed.


**1. `app/models/state/objects.py`**

Enforce `height = 0` and `depth = 0` on `ShorelineState`:

**2. `app/services/generators/game/cradle.py`**

Explicitly set `height = 0` and `depth = 0` in `spawn_shoreline()`:

**3. `app/services/generators/game/actuator.py`**

Update `Actuator` to:

1. Snap annular pool bounds to 32px tile grid multiples in `_partition_pool`.
2. Cross-reference all active fluids on the layer via `_is_water` and `_is_water_excluding`.
3. Check that the land-side probe point is not submerged before spawning a shoreline.
4. Prune submerged shorelines from the board during `pump()`.

##### User Review

Unit tests passing. Bugs remain in the implementation, but they are minor and non-application breaking. Everything is working enough to call the MVP for this phase attained. 

Before even getting to the bugs in the shoreline, the Actuator needs refactored. It is clear there is an entirely separate and logically contained service embedded in the Actuator for generating the Shoreline. There is no reason for the Shoreline generation to be embedded into the Actuator in such a manner.

- Task: Analyze the dependencies Shoreline generation has on Fluid generation, and what sort of interface the Actuator will need. Ideally, the Shoreline generation service will be static and stateless, so the Actuator can call it on as needed basis.

`is_water()` would seem a method that should belong to the Board, not the Actuator. Moreover, `is_water_excluding` is redundant; just overload `is_water` with an exclusion that defaults to None. 