#### Implement: Phase 10 - Seasons

**Overview** 

Implement seasonal progression mechanics across environmental terrain and dynamic biological resources. Establish temporal state tracking on the Board, deliver seasonal tile atlas decomposition with event-driven background canvas reconstruction, integrate the Resource ECS hierarchy (Properties, States, Frames), and construct SeasonMechanics to govern temporal progression and crop stage lifecycles.

##### Specifications

###### Tiles

Tile Assets will be arranged in rows according to the following schema,

- Tile Seasons: `spring`, `summer`, `autumn`, `winter` 
- Cycles per Season: `onset`, `peak`, `decline`
- Frames Per Cycle: 3

For a total of 12 frames per row and a total count of 36 tiles. For example, the first row will be,

- `spring-onset-0`, `spring-onset-1`, `spring-onset-2`, `spring-peak-0`, `spring-peak-1`, `spring-peak-2`, `spring-decline-0`, `spring-decline-1`, `spring-decline-2`

Each row will denote a Season.

###### Resources

Resources Assets will be arranged in horizontal rows according to Stages. Each Instance of Resource will have unique Stages.

- Crop Stages: `sprout`, `growth`, `stalk`, `bloom`, `stump`
- Tree Stages: `sapling`, `bush`, `branch`, `adult`, `vibrant`, `healthy`, `abscise`, `snowcapt`, `dying`, `dead`, `stump`
- Ore Stages: `trace`, `deposit`, `nugget`, `vein`, `crystal`, `alloy`
    - **Note**: Dependent on TBD geographical relations.

**Note**: Ore is not the principal target of this phase, but is included in the specification to ensure Resource properties are abstracted correctly for reuse.

###### Mechanics

**Seasonal Principles**

1. The Board accumulates the passage of time. 
2. A Season is approximately one hour in realtime. This can be adjusted in `app.config.settings`.
3. Seasons iterate continuously through `spring`, `summer`, `autumn` and `winter`. 
4. Each Season has a Cycle: `onset`, `peak`, `decline`.
5. Each Cycle has an Period. A Period is three frames.
6. The Tile frame that is rendered is dependent on the Season, Cycle and Period.

**Crop Stages**

- **Note**: Distributed over `spring`, `summer` and `autumn`. Hibernates over `winter`. Initializes during the onset of `spring`.

1. Crops begin the first Stage of their lifecycle in the first Period of `spring-onset`.
2. Crops end the last Stage of their lifecycle in last Period of `autumn-decline`.
3. Crops can only be harvested in `autumn`, i.e. the `bloom` Stage must occur in `autumn`.
4. Each stage of a Crop lifecycle requires preconditions to be met in order to pass into the next stage, where $\theta_{\text{season}}$ is a Resource property:
    * $\text{sprout} \to \text{growth}$: $\text{board.season} \in \{\text{spring}, \text{summer}\} \land \text{crop.state.retention} > \theta_{\text{growth}}$
    * $\text{growth} \to \text{stalk}$: $\text{board.season} \in \{\text{spring}, \text{summer}\} \land \text{crop.state.retention} > \theta_{\text{stalk}}$
    * $\text{stalk} \to \text{bloom}$: $\text{board.season} = \text{autumn} \land \text{crop.state.retention} > \theta_{\text{bloom}}$
    * $\text{bloom} \to \text{stump}$: $(\text{board.season} = \text{autumn} \land \text{crop.state.harvested}) \lor \text{board.season} = \text{winter}$

**Tree Stages**

Trees have an Epicycle in their Stages: Genesis, Homeostasis, Apotosis

- Genesis Stage Season Map: 
    - `board.season == spring and board.season.cycle == onset: tree.state.stage = sapling`
    - `board.season == spring and board.season.cycle == peak: tree.state.stage = bush`
    - `board.season == spring and board.season.cycle == decline: tree.state.stage = branch` 
    - `board.season == summer and board.season.cycle == onset: tree.state.stage = adult`
    - `board.season == summer and board.season.cycle == peak: tree.state.stage = healthy` (Enters Homoestasis)
- Homeostasis Stage Season Map: 
    - `board.season == spring and tree.state.hydrated: tree.state.stage = vibrant`
    - `board.season == summer and tree.state.hydrated: tree.state.stage = healthy`
    - `board.season == autumn and tree.state.hydrated: tree.state.stage = abscise`
    - `board.season == winter and tree.state.hydrated: tree.state.stage = snowcapt`
- Apotosis Stage Season: 
    - `not tree.state.hydrated: tree.state.stage = dying`
    - `tree.state.stage == dying and tree.state.hydrated: tree.state.stage = adult` (Re-enters Homoestasis)
    - `board.season == autumn and tree.state.stage == dying: tree.state.stage = dead` 
    - `board.season == winter and tree.state.stage == dead: tree.stage.stage = stump`

##### Architectural Analysis

###### VRAM Conflict

In the current rendering architecture (`app.game.screen.Screen`), static terrain is optimized via pre-baking:

* At hydration (`Screen.__init__` and `Screen.rebake`), all `back` and `fore` tiles are compiled into continuous GPU texture targets (`bg_canvas` and `fg_canvas`) via `render.construct`.
* During the frame loop (`Screen.draw`), tiles are completely excluded from per-frame draw arrays (`if asset.category == AssetCategories.TILES.value: continue`).

If seasonal tile variations were evaluated per frame in `Screen.draw`, this would dismantle the $O(1)$ background blit optimization.

**Resolution: Temporal Canvas Invalidation**

* A season represents approximately 1 hour in realtime ($3600\text{ s}$).
* With 3 cycles per season (`onset`, `peak`, `decline`) and 3 periods per cycle, there are 9 distinct temporal steps per season.
* A period transition occurs once every $400\text{ s}$ ($\approx 6.67\text{ minutes}$).
* Because seasonal transitions occur on a macro timescale, tiles do not animate on micro game ticks.
* **Design Rule**: Tiles remain static textures baked onto `bg_canvas`. When the `Board` calendar advances a temporal period, the engine triggers an asynchronous or slice-based canvas update (`Screen.reconstruct_tiles()` or dispatching a `SeasonEvent`), recompiling the background canvas with the new period's tile frame keys. This retains zero-allocation rendering in the inner loop.

###### Frames

A tile asset sheet containing seasonal variations requires an explicit frame strategy:

**Tile Frames**

* **Registry Atlas Mapping**: A $4 \times 9$ cell grid (4 seasons as rows, 9 periods per row as columns).
* Frame keys formatted canonically via `settings.SEPARATOR`: $\text{id}-\text{season}-\text{cycle}-\text{period}$
* `SeasonalFrame` indexes all 36 cells during engine bootstrap. At reconstruct time, it resolves the current key from the `Board`'s temporal state.

**Resource Frames**

- Note: Uses a categorical index, similar to IndexFrame. This Frame implementation can possibly be reused.

###### Data Models

* **`ResourceProperties` (Static / Immutable)**: Dimensions, base hitboxes, mass (typically $m = 0$ for static foliage/rock), harvested loot keys (`loot: str`), and valid stage enumerations.
* **`CropState` (Dynamic / Mutable)**: Position, layer, depth, height, current stage (`CropStages`), accumulated fluid retention (`fluid_retention: float`), and harvest flag (`harvested: bool`).
* **`OreState` (Dynamic / Mutable)**: Position, layer, depth, height, stage (`OreStages`), vein purity/type (`vein: str`).

###### Lifecycle Pipeline

Stage progression must be driven by environmental interaction rather than arbitrary tick counters:

* **`FluidMechanics`**: Populates and manages Fluid tiles.
    - In future phases, Climate and Weather will be introduced to formalize Rain.
    - In future phases, Watercan Equipment will be introduced for Sprites to allow user management of fluid retention.
**`SeasonMechanics`**
    * Crops adjacent to active fluid accumulate `fluid_retention`.
    * Accumulates delta time on the `Board`'s global calendar.
    * Ticks season, cycle, and period.
    * Dispatches `SeasonEvent` when a period boundary is crossed to trigger `Screen` canvas reconstruction.
    * Updates environmental resource stages (e.g. evaluating crop hydration and triggering stage transitions).
* **`TransitionMechanics`**:
    * Exclusively governs Sprite intentionality (e.g., transition to `mine` or `interact` when targeting a harvestable `bloom` crop).
* **`CognitionMechanics`**:
    * Exclusively governs Sprite goal commitments (e.g., committing to a `Goal(name="harvest", category=OBJECT)`).
* **`InteractionMechanics` / `CombatMechanics**`:
    * Resolves physical harvesting when a character interacts with or strikes a mature crop, dropping a `Collectable` effect containing the crop's loot key and toggling `crop.state.harvested = True`.

##### Goal: Temporal Board State & Season Configuration

Introduce core temporal enumeration classes in `app.config.enums` (`Seasons`, `SeasonCycles`, `CropStages`, `OreStages`). Extend `app.config.settings` with configurable seasonal durations and stage fluid thresholds. Establish `CalendarState` on the `Board` database to accumulate simulation delta time and track macro-temporal progression (`year`, `season`, `cycle`, `period`, `elapsed`).

##### Goal: Seasonal Tile Decomposition & Canvas Re-construction

Develop `SeasonalTileFrame` within `app.assets.frames` to index $4 \times 9$ tile atlas grids into canonical keys (`{id}-{season}-{cycle}-{period}`). Extend `Screen` with an event-driven `reconstruct()` method that updates `bg_canvas` and `fg_canvas` via `render.construct` without re-allocating GPU memory contexts or compromising $O(1)$ draw loop camera blitting.

##### Goal: Resource ECS Data Model Architecture

Define immutable `ResourceProperties` in `app.models.properties` and add `ResourcePropertyInstances` to `PropertiesSchema`. Implement mutable `CropState` and `OreState` in `app.models.state.assets.resources` and bind them to `ResourceStateInstances` within `StateSchema`. Implement `StageFrame` in `app.assets.frames` to dynamically map resource entity stages to horizontal sprite strips.

##### Goal: SeasonMechanics Execution Pipeline

Implement `SeasonMechanics` within the `world` mechanics pipeline (`app.game.logic.mechanics.world.season`). Evaluate macro-temporal increments, trigger `SeasonEvent` notifications on period transitions, calculate hydrological moisture diffusion from `board.fluid` into `crop.state.fluid_retention`, and enforce crop lifecycle state transitions across spring, summer, autumn, and winter.

##### Tasks

**1. Task: Temporal Schema & Enum Integration**

*Objective*: Establish data contracts and settings for temporal progression and resource types.

- [] Subtask: Add `Seasons`, `SeasonCycles`, `CropStages`, `OreStages`, `TreeStages`  to `app.config.enums`.
- [] Subtask: Configure `SEASON_DURATION_SECONDS`, `GROWTH_THRESHOLD`, `STALK_THRESHOLD`, and `BLOOM_THRESHOLD` in `app.config.settings`.
- [] Subtask: Create `CalendarState` dataclass in `app.models.state.core` and register it on `Board` and `StateSchema`.

**2. Task: Seasonal Tile Frame Indexing & Screen Integration**

*Objective*: Support multi-season tile sprite sheets and connect temporal invalidation to Screen canvas baking.

- [] Subtask: Implement `SeasonalTileFrame` in `app.assets.frames.tiles` supporting 36-frame atlases (4 seasons x 3 cycles x 3 periods).
- [] Subtask: Add `SeasonEvent` and `SeasonEventHandler` to `app.game.menus` to signal temporal transitions through the Engine bus.
- [] Subtask: Implement `Screen.reconstruct_tiles(board)` to execute `render.construct` on existing canvas pointers when `SeasonEvent` is handled.

**3. Task: Resource Hierarchy Models & Stage Framing**

*Objective*: Implement the Resource category across properties, states, recipes, and frames.

- [] Subtask: Add `ResourceProperties` to `app.models.properties` and integrate into `PropertiesSchema`.
- [] Subtask: Add `CropState` and `OreState` to `app.models.state.assets.resources` and integrate into `StateSchema`.
- [] Subtask: Implement `StageFrame` in `app.assets.frames.core` mapping `state.stage` to horizontal cell offsets.
- [] Subtask: Update `Orchestrator` recipes to bind `Resource` instances (`crops`, `ores`) to `StageFrame` and their respective property/state models.

**4. Task: SeasonMechanics Simulation Logic**

*Objective*: Execute time accumulation, hydrological crop absorption, and lifecycle stage transitions.

- [] Subtask: Implement `SeasonMechanics` inheriting from `Mechanic` in `app.game.logic.mechanics.world.season`.
- [] Subtask: Register `season: SeasonMechanics` in `/src/data/config/mechanics/main.yaml` within the `world` pipeline.
- [] Subtask: Implement delta time integration on `board.calendar`, emitting `SeasonEvent` when `period` shifts.
- [] Subtask: Implement moisture absorption for `Crop` entities based on proximity to active `board.fluid` buckets.
- [] Subtask: Implement stage precondition evaluation logic transitioning crops between `sprout`, `growth`, `stalk`, `bloom`, and `stump`.

##### User Review

Good basis for Crops and Seasons. Now need to incorporate separate tasks for Trees. 

Trees will likely require a Relation, similar to ShorelineIndex, for associating Board Seasons to Tree Asset frames. However, ShorelineIndex indexes Assets whose attributes are unknown until runtime, whereas Seasons are a hardcoded setting of the Mechanics.  

---

#### Draft: Tile Seasonal Atlas Specifications

- **Page**: docs/01-assets.md
- **Heading**: ## Tiles

##### Drift

The Phase 10 task board overview states: "Tile Seasons: spring, summer, autumn, winter; Cycles per Season: onset, peak, decline; Frames Per Cycle: 3. For a total of 12 frames per row and a total count of 36 tiles." This is mathematically contradictory: 3 cycles \(\times\) 3 frames \(= 9\) frames per season. Four seasons at 9 frames per row yields 36 tiles total. Stating 12 frames per row at 4 rows yields 48 tiles, or implies only 3 seasons at 12 frames. In addition, the naming example mixes 0-indexing and 1-indexing (`spring-onset-0`, `spring-onset-1`, `spring-onset-2`, `spring-peak-1`, `spring-peak-2`, `spring-peak-3`).

##### Update

### Tile Seasons & Temporal Atlases

Tile assets supporting seasonal variations organize their frames in a \(9 \times 4\) cell atlas (36 frames total). Each row represents an individual Season, containing 3 Cycles of 3 Periods each, consistently 0-indexed:

* Rows (\(Y\)-axis):
  * Row 0: `spring`
  * Row 1: `summer`
  * Row 2: `autumn`
  * Row 3: `winter`
* Columns (\(X\)-axis):
  * Cells 0–2: `onset-0`, `onset-1`, `onset-2`
  * Cells 3–5: `peak-0`, `peak-1`, `peak-2`
  * Cells 6–8: `decline-0`, `decline-1`, `decline-2`

**Frame: SeasonalTileFrame**

* `keys(id, state): returns [ (f"{id}-{board.calendar.season}-{board.calendar.cycle}-{board.calendar.period}", 0, 0) ]`
* `index(id, properties): returns { f"{id}-{s}-{c}-{p}": (col * w, row * l, w, l) }`


---

## Bug Reports

##### Bug B014: Mathematical & Indexing Inconsistency in Phase 10 Tile Specification

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

The specification for Phase 10 in the Task Board contains an internal arithmetic contradiction and mixed index conventions:

1. It defines 4 seasons (`spring`, `summer`, `autumn`, `winter`), 3 cycles per season (`onset`, `peak`, `decline`), and 3 frames per cycle. $3 \times 3 = 9$ frames per season. Four seasons $\times 9$ frames $= 36$ total tiles. However, the text explicitly specifies: "For a total of 12 frames per row and a total count of 36 tiles. Each row will denote a Season." If each row denotes a season, 4 rows $\times 12$ frames $= 48$ frames. If the atlas has 12 frames per row and 36 tiles total, it would only contain 3 rows (omitting one season).
2. The key schema switches from 0-indexed to 1-indexed midway through the definition: `spring-onset-0, spring-onset-1, spring-onset-2`, followed by `spring-peak-1, spring-peak-2, spring-peak-3`.

**Steps to Replicate**

1. Review Task Board documentation: `Implement: Phase 10 - Seasons` -> `Tile Specifications`.
2. Compare the product of cycles and frames ($3 \times 3 = 9$) against the stated row width ("12 frames per row").
3. Inspect the listed frame names for indexing divergence.

**Proposed Remeditation**

Update the Phase 10 specification to define a $9 \times 4$ grid (9 columns per row, 4 rows total $= 36$ tiles) and standardize strictly on 0-indexed notation (`{season}-{cycle}-{0..2}`).