#### Implement: Phase 10 - Seasons

**Overview** 

Implement seasonal progression mechanics across environmental terrain and biological resources. Establish temporal calendar tracking on the `Board`, deliver seasonal tile atlas decomposition with event-driven canvas reconstruction, implement Resource ECS data models (`YieldState`, `RenewState`, `TectonicState`, `StageFrame`), compile declarative stage transition rules via `StageExecutor`, and construct `SeasonMechanics` to drive macro-temporal progression and soil moisture diffusion.

##### Specifications

###### Tiles

Tile Assets will be arranged in rows according to the following schema,

- Tile Seasons: `spring`, `summer`, `autumn`, `winter` 
- Cycles per Season: `onset`, `peak`, `decline`
- Frames Per Cycle: 3

For a total of 9 frames per row and, with 4 rows, each denoting a Season, a total count of 36 tiles. For example, the first row will be,

- `spring-onset-0`, `spring-onset-1`, `spring-onset-2`, `spring-peak-0`, `spring-peak-1`, `spring-peak-2`, `spring-decline-0`, `spring-decline-1`, `spring-decline-2`

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
4. Each stage of a Crop lifecycle requires preconditions to be met in order to pass into the next stage, where $\theta_{\text{season}}$ is a Resource property (not setting, i.e. unique to the Instance, but static):
    * $\text{sprout} \to \text{growth}$: $\text{board.season} \in \{\text{spring}, \text{summer}\} \land \text{crop.state.retention} > \theta_{\text{growth}}$
    * $\text{growth} \to \text{stalk}$: $\text{board.season} \in \{\text{spring}, \text{summer}\} \land \text{crop.state.retention} > \theta_{\text{stalk}}$
    * $\text{stalk} \to \text{bloom}$: $\text{board.season} = \text{autumn} \land \text{crop.state.retention} > \theta_{\text{bloom}}$
    * $\text{bloom} \to \text{stump}$: $(\text{board.season} = \text{autumn} \land \text{crop.state.harvested}) \lor \text{board.season} = \text{winter}$

**Tree Stages**

Trees have an Epicycle in their Stages: Genesis, Homeostasis, Apoptosis

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
- Apoptosis Stage Season Map: 
    - `not tree.state.hydrated: tree.state.stage = dying`
    - `tree.state.stage == dying and tree.state.hydrated: tree.state.stage = adult` (Re-enters Homoestasis)
    - `board.season == autumn and tree.state.stage == dying: tree.state.stage = dead` 
    - `board.season == winter and tree.state.stage == dead: tree.stage.stage = stump`

##### Architectural Analysis I

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

##### Architectural Analyis II

###### Animations vs Transitions

* **`Animation` components** (`BinaryAnimation`, `LifecycleAnimation`, `StateAnimation`, `SpriteAnimation`) are evaluated every tick in `core` mechanics via `AnimationMechanics`. They govern micro-temporal visual motion (e.g., ticking walking frames at $10\text{ Hz}$, cycling water ripples, or flashing cooldowns).
* **Biological Stages** (`SPROUT`, `GROWTH`, `STALK`, `BLOOM`, `STUMP`), by contrast, are discrete macro-environmental states. They do not advance via tick counters; they advance through environmental preconditions (season, cycle, hydrological fluid retention) evaluated by `SeasonMechanics`.

In other words, `StageFrame` maps `state.stage` directly to horizontal atlas cell offsets:

$$\text{StageFrame.keys}(id, state) \to [(\{id\}-\{state.stage\}, 0, 0)]$$

When `SeasonMechanics` transitions `crop.state.stage = CropStages.GROWTH.value`, the frame key dynamically resolves to `{id}-growth` on the very next render pass with zero heap allocation.

**Component Assignment**: Because resource foliage within a single biological stage is statically displayed on the board, resources should be assigned `NoAnimation` in their recipes.

**Stage Transitions Are Not Animations**: Animating *through* biological stages sequentially on tick intervals would violate the simulation philosophy—a crop must not grow merely because frames elapsed; it must grow because soil moisture and macro-seasons permitted it. If visual transition feedback is required (such as leaf burst or sparkle), the appropriate mechanism is spawning a transient `Effect` (`AssetCategories.EFFECTS`, `Lifecycles.TEMPORARY`) via `board.cradle.spawn()` at the resource's coordinate.

###### Persistent Epicycle Phase in `RenewState`

A Tree cannot be evaluated purely as a stateless function of $(season, cycle, hydrated)$:

* In `spring-onset`, a tree in **Genesis** is a `sapling`.
* In `spring-onset`, a tree in **Homeostasis** is `vibrant`.
* In `autumn`, an unhydrated tree in **Homeostasis** becomes `dying`, while an unhydrated tree already in **Apoptosis** transitions to `dead`.

If a tree did not store its current phase, a hundred-year-old forest would reset to saplings upon every Spring arrival. Therefore, `RenewState` must store:

* `stage: str` (`TreeStages`)
* `phase: str` (`EpicyclePhases`: `GENESIS`, `HOMEOSTASIS`, `APOPTOSIS`)
* `hydrated: bool` (or `retention: float`)

**Resolution: `EpicycleMap`**

Modeled directly after `AnimationMap` (`app.game.logic.modules.maps.animation`), an `EpicycleMap` module (`app.game.logic.modules.maps.epicycles`) encapsulates the pure transition rules:

```python
EpicycleMap.transition(
    stage: str, 
    phase: str, 
    season: str, 
    cycle: str, 
    hydrated: bool
) -> tuple[str, str]  # Returns (next_stage, next_phase)
```

`SeasonMechanics` iterates over `board.instances(AssetInstances.TREES.value)` during temporal ticks, evaluates local fluid proximity to update `tree.state.hydrated`, queries `EpicycleMap.transition()`, and applies the resulting stage and phase updates to `tree.state`.


##### User Review I

###### Tile Ambiguities

The distinction between Back and Fore Tiles exists and is codified, but has not yet been tested or leveraged in any capacity. Same with Grid Tiles. They were created to preempt future needs. With the implementation of this phase, the "speciation" of Tiles needs to be reanalyzed. Tiles are no longer "inanimate" nor are they "immutable". In addition, future phases will bring in "background" environment effects like Snow and Rain. While these entities could conceivably be managed by Effects, it may make more sense to make them Fore Tiles.

###### Resource Thresholds

`tree.state.hydrated` should be a threshold, similar to Crops, not a binary flag.

Moreover, thresholds should be part of the Resource properties, as they will be differ across Instances. 

It also may be beneficial to externalize the Stage transition conditions in Property or Configuration YAMLs, e.g.,

```yaml
resources:
    crops:
        lettuce:
            dimensions:
                w: 32
                l: 32
            hitboxes: null
            mass: 0
            loot: lettuce
            stages:
                - key: sprout
                  threshold: 10
                  season: spring
                - key: growth
                  threshold: 20
                  season: spring
                - key: stalk 
                  threshold: 25
                  season: summer
                - key: bloom
                  threshold: 30
                  season: autumn
                - key: stump
                  threshold: 10
                  season: winter
    trees:
        deciduous:
            dimensions:
                w: 94
                l: 137
            hitboxes: null
            mass: 0
            loot: wood
            stages:
                - key: sapling
                  threshold: 10
                  season: spring
                - key: bush
                  threshold: 15
                  season: spring
                - key: branch
                  threshold: 21
                  season: spring
                - key: adult
                  threshold: 30
                  season: summer
                - key: vibrant
                  threshold: 25
                  season: summer
                - key: healthy
                  threshold: 25
                  season: summer
                - key: abscise 
                  threshold: 20
                  season: autumn
                - key: snowcapt
                  threshold: 15
                  season: winter
                - key: dying
                  threshold: 5
                - key: dead
                  threshold: 0
```

The idea of Transitions actually exists in the engine already via Sprite Intention transitions and Plot Transitions. Here is the Plot Transition config as an example,

```yaml
plots:
  castle-dawn-locked:
    - next: castle-dawn-unlocked
      conditions:
        - sprites.get(constants.RequiredAssets.PLAYER.value)
        - sprites.get(constants.RequiredAssets.PLAYER.value).state.inventory.loot.get('writ-of-dawn') >= 1
    - next: town-unlocked
      conditions:
        - sprites.get('castle-dawn-guard')
        - sprites.get('castle-dawn-guard').mutators.triggers.dead
    - next: castle-dawn-unlocked
      conditions:
        - sprites.get('evil-empress-jasilynn')
        - sprites.get('evil-empress-jasiylnn').state.memory.relationships.get(constants.RequiredAssets.PLAYER.value)
        - sprites.get('evil-empress-jasilynn').state.memory.relationships.get(constants.RequiredAssets.PLAYER.value) == constants.Relationships.FRIEND
  castle-dawn-unlocked:
    - next: castle-dawn-hostile
      conditions:
        - sprites.get('evil-empress-jasilynn')
        - sprites.get('evil-empress-jasiylnn').state.memory.relationships.get(constants.RequiredAssets.PLAYER.value)
        - sprites.get('evil-empress-jasilynn').state.memory.relationships.get(constants.RequiredAssets.PLAYER.value) == constants.Relationships.FOE
  castle-dawn-hostile:
    - next: castle-dawn-unlocked
      conditions:
        - sprites.get('evil-empress-jasilynn')
        - sprites.get('evil-empress-jasiylnn').state.memory.relationships.get(constants.RequiredAssets.PLAYER.value)
        - sprites.get('evil-empress-jasilynn').state.memory.relationships.get(constants.RequiredAssets.PLAYER.value) != constants.Relationships.FOE
```

These are implemented as either anoynmous lambda functions or compiled AST objects, depending on `settings.ISL_TRANSLATOR`. Both have been tested and are known to function. Each transition is executed within an Environ:

This seems like an analogous situation, insofar there is an Asset whose internal state can transition through categorical fields (Intentions vs. Plots vs Stages) and those transitions are conditional on the world state.

Rather than codifying the Epicycles as Map, it seems more fitting to codify them as Executors and inject the EpicycleExecutor into SeasonMechanics. Both Plot and Intention transitions already utilize the same interface.

###### Fluid Retention

How is Fluid accumulated in a Tree or Crop? Fluid adjacency, climatic effects and user interference (Equipment: watercan) all must contribute. 

##### Architectural Analysis III

```
Frame Loop (60 Hz)
  │
  ├─► World Mechanics: SeasonMechanics.update(board, delta, bus, payload)
  │     │
  │     ├─► 1. Temporal Integration:
  │     │     board.calendar.elapsed += delta
  │     │     if elapsed >= PERIOD_DURATION_SECONDS (400.0s):
  │     │         advance period (0..2) -> cycle (onset, peak, decline) -> season -> year
  │     │         bus.append(SeasonEvent())
  │     │
  │     ├─► 2. Hydrological Diffusion:
  │     │     Iterate board.instances(CROPS) and board.instances(TREES)
  │     │     Query board.fluid(layer, adjacent_pos) via O(1) spatial buckets
  │     │     Apply delta integration: retention += diffusion * delta (or evaporate)
  │     │
  │     └─► 3. Stage Progression (StageExecutor):
  │           Evaluate declarative stage conditions for Crops and Trees
  │           Mutate crop.state.stage and tree.state.(phase, stage)
  │
  ├─► Event Drain: Engine._drain()
  │     └─► SeasonEventHandler.handle(SeasonEvent, context)
  │           ├─► SeasonalFrame.sync(context.board.calendar)
  │           └─► For screen in context.screens.values():
  │                 screen.reconstruct(board.categories(TILES, layer))
  │
  └─► Screen Rendering (60 Hz):
        Screen.draw() -> O(1) blit of bg_canvas / fg_canvas (Tiles culled from draw loop)
        Screen.draw() -> StageFrame resolves "{id}-{state.stage}" directly from atlas
```

###### Declarative `StageExecutor` vs. Hardcoded `EpicycleMap`

In the initial Phase 10 draft, tree life cycles were modeled via a hardcoded Python module (`EpicycleMap`). However, the engine already features an Intentional Scripting Language (ISL) transition engine utilized by both `TransitionMechanics` (Sprite intentionality) and `PlotMechanics` (world plot states).

* **The Problem**: Hardcoding `EpicycleMap.transition()` in Python violates the engine philosophy ("simulation and emergence... ingests a starting world state and evolves according to internal logic, without scripting"). Furthermore, it fragments biological lifecycles: Crops would use conditional threshold checks in `SeasonMechanics` while Trees would use a hardcoded lookup map.
* **The Solution**: Unify all biological state progression under the declarative `Executor` / `Translator` pipeline.
    * Externalize stage transitions into `/src/data/config/stages/main.yaml`.
    * Compile the rules into a `StageExecutor` implementing `Executor`.
    * Inject `StageExecutor` into `SeasonMechanics` via `set_executor("stage", stage_executor)`.
* **Compound State for Tree Epicycles**: A Tree's state cannot be evaluated solely on $(season, cycle, hydrated)$ without memory of its epicycle phase (`genesis`, `homeostasis`, `apoptosis`). By modeling the Tree's evaluated state as a compound token (`f"{tree.state.phase}:{tree.state.stage}"`, e.g., `genesis:sapling`, `homeostasis:healthy`, `apoptosis:dying`), `StageExecutor.evaluate()` deterministically resolves both the macro epicycle phase and micro visual stage atomically.

###### Hydrological Diffusion & Retention Dynamics

In the original specification, `crop.state.retention` was a floating-point accumulator while `tree.state.hydrated` was a binary boolean.

* **The Problem**: Binary hydration flags make environmental simulation brittle. A single missing fluid tile could toggle a 100-year-old tree directly into apoptosis. Furthermore, user interference (e.g., watering cans) and ambient weather cannot interact cleanly with a binary flag.
* **The Solution**:
    1. Standardize both `YieldState` (Crops) and `RenewState` (Trees) to maintain a continuous `retention: float` property.
    2. In `SeasonMechanics`, perform hydrological diffusion: check adjacent spatial buckets from `board.fluid()`. If adjacent to fluid, accumulate moisture (`retention += diffusion_rate * delta`). If unmoisturized, evaporate moisture (`retention -= evaporation_rate * delta`), modulated by seasonal temperature (faster decay in `summer`, lower in `winter`).
    3. Preconditions for stages evaluate against static `thresholds` defined on the `ResourceProperties` instance.


##### User Review II

###### Unnecessary Bloat

Adding the `{phase}:{stage}` semantics seems unnecessary, since all such constructions would reduce to a logical product of `tree.state.phase and tree.state.stage`. 

Although introducing an `app.services.translators.sugar` macro module for `app.services.translators.environ` might be a compromise.

However, Transitions are beginning to resemble a scripting language. Perhaps that is unavodiable.

###### Stage Transition Ambiguities

Stage Transition Executors needs more analysis. For example, what are the configuration nodes? While analogous to Plot and Intention transitions, they are not isomorphic, e.g. stages are unique to Resource Instances; Stage transition configuration will need to be nested as,

```yaml
stages:
    <resource>:
        <stage>:
            - next: <stage>
              conditions:
                - <condition>
```

###### Frame.sync

I am uneasy about altering a core interface, although it is not without precedent (see Frame.channels). I would like an in-depth justification for why the interface must be updated for Tile Seasonality. 

All of these seems like animation logic, it's just labeled `sync`. Seems like the same effect could be achieved by implementing a Tile animation and putting the timing logic in `AnimationMechanics`. Explain why this solution would not work and why altering a core interface is preferrable.

##### Architectural Analysis IV

###### Justification: Why `AnimationMechanics` Cannot Handle Tile Seasonality

The suggestion to treat seasonal tile shifts as standard animation within `AnimationMechanics` introduces critical architectural conflicts:

1. **The $O(1)$ Static Blit Invariant**: In `Screen.draw()`, terrain tiles are culled from every frame loop (`if asset.category == AssetCategories.TILES.value: continue`). All background and foreground tiles are pre-baked onto GPU textures (`bg_canvas` and `fg_canvas`) via `render.construct()`. If tiles were animated in `AnimationMechanics`, either:
  * Tile camera culling would have to be removed from `Screen.draw()`, forcing thousands of background tiles through sorting, camera-culling, and rendering every single frame at 60 Hz, breaking performance.
  * Or `AnimationMechanics` would have to trigger canvas rebaking. However, `Mechanic.update(board, delta, bus, payload)` has **no reference to `Screen**`. In the engine's unidirectional architecture, `Screen` is isolated in `Engine.screens` and exposed only to `EventHandler` implementations via `EventContext`. Mechanics cannot touch screens.


2. **Timescale Mismatch & Allocation Overhead**: `AnimationMechanics` executes at 60 Hz in the `core` pipeline to drive micro-temporal motions (walk cycles, water ripples) on 100 ms intervals. A seasonal period transition occurs once every $400\text{ s}$ ($\approx 6.67\text{ minutes}$). Ticking thousands of stationary tile entities 60 times a second to see if 400 seconds have elapsed creates unnecessary CPU overhead.
3. **Data Model Bloat**: `AnimationMechanics` requires `asset.state.animation: AnimationState`. Tiles intentionally use `MultiplierState(position, multiple)`. Forcing an `AnimationState` onto every tile on every layer would inflate memory footprint and state serialization dumps.

###### Resolving the `Frame` Interface Concern

The base `Frame` class in `app.assets.base` **does not need to be altered**.
`Frame.keys(id, state)` and `Frame.index(id, properties)` remain completely untouched:

* `SeasonalFrame.sync(calendar: CalendarState)` is a specialized method on `SeasonalFrame` in `app.assets.frames.tiles`.
* `SeasonalFrame` caches `_active_key = f"{calendar.season}{settings.SEPARATOR}{calendar.cycle}{settings.SEPARATOR}{calendar.period}"`.
* When `SeasonEventHandler` catches `SeasonEvent`, it executes `SeasonalFrame.sync(context.board.calendar)` once and calls `screen.reconstruct()`.
* During `screen.reconstruct()`, `tile.frame.keys(tile.id, tile.state)` returns `[(f"{tile.id}{settings.SEPARATOR}{SeasonalFrame._active_key}", 0, 0)]`.
* The core interface contract remains clean and closed for modification.

###### Tree Epicycles: Eliminating `{phase}:{stage}` String Hacks

Formatting tree state as compound string tokens (`f"{phase}:{stage}"`, e.g. `genesis:sapling`) violates typed schema design and forces runtime string splitting.

Instead, preserve typed fields on `RenewState`:

* `stage: str` (`TreeStages`)
* `phase: str` (`EpicyclePhases`)
* `retention: float`

In `/src/data/config/stages/main.yaml`, structure resource transitions under instance keys (`crops`, `trees`). For trees, allow transitions to evaluate `resource.phase` within condition expressions and declare an optional `phase` transition target:

```yaml
stages:
  trees:
    adult:
      - next: healthy
        phase: homeostasis
        conditions:
          - "resource.phase == EpicyclePhases.GENESIS.value"
          - "calendar.season == Seasons.SUMMER.value"
          - "calendar.cycle == SeasonCycles.PEAK.value"
          - "resource.retention >= 25.0"
      - next: dying
        phase: apoptosis
        conditions:
          - "resource.phase == EpicyclePhases.HOMEOSTASIS.value"
          - "resource.retention < 5.0"

```

The compiled `Transition` model encapsulates:

* `next: str` (target stage)
* `phase: Optional[str]` (target epicycle phase, if updated)
* `conditions: List[Callable]`

When evaluated:

```python
result = stage_executor.evaluate(AssetInstances.TREES.value, tree.state.stage, locals)
if result:
    tree.state.stage = result.next
    if result.phase:
        tree.state.phase = result.phase

```

This keeps `RenewState` clean and typed while letting ISL condition trees evaluate boolean products of `phase`, `season`, and `retention`.

##### Architectural Analysis V

###### 1. The State Contract Dependency Gap

An executor evaluates transition conditions against dynamic state fields:

* `ANNUAL` transitions inspect `resource.retention` and `resource.harvested`.
* `PERENNIAL` transitions inspect `resource.retention` and `resource.phase`.
* `CENTENNIAL` transitions inspect `resource.stage` (and potential future geological stress fields).

If `YieldState`, `RenewState`, and `TectonicState` remain rigidly segregated by instance (`crops -> YieldState`, `trees -> RenewState`), giving a `Crop` a `PERENNIAL` lifespan causes an immediate `AttributeError` when the ISL condition evaluates `resource.phase`.

*Resolution: Unified `ResourceState`*

Instead of partitioning states by arbitrary colloquial nouns (`YieldState`, `RenewState`, `TectonicState`), unify them under a single slotted state model:

```python
# src/app/models/state/assets/resources.py

@dataclass(slots=True)
class ResourceState(AssetState):
    position: Optional[Position] = None  # type: ignore
    stage: str = ""
    retention: float = 0.0
    phase: Optional[str] = None          # For Epicycles (genesis, homeostasis, apoptosis)
    harvested: bool = False              # For harvestable bloom states

```

Because `@dataclass(slots=True)` incurs zero dynamic dictionary overhead and all fields are typed with defaults, `ResourceState` can satisfy the state contract of **any** lifespan:

* An annual crop uses `stage`, `retention`, and `harvested` (`phase` remains `None`).
* A perennial tree uses `stage`, `retention`, and `phase` (`harvested` remains `False`).
* A perennial fruit tree (e.g., an apple orchard) can utilize **both** `phase` (cycling through homeostasis seasons) and `harvested` (clearing fruit in autumn without tree apoptosis).
* A centennial mineral uses `stage` (`retention`, `phase`, `harvested` remain idle).

This fully decouples the state contract from the asset instance and avoids runtime executor-state mismatches.

###### 2. The Atlas Indexing Gap in `StageFrame`

To allow `StageFrame.index()` to map horizontal atlas coordinates without hardcoded instance checks, create an explicit stage mapping table:

```python
# src/app/config/enums.py

class Lifespans(str, Enum):
    ANNUAL = "annual"
    PERENNIAL = "perennial"
    CENTENNIAL = "centennial"
```

Now, `StageFrame` in `app.assets.frames.resources` is completely generic:

```python
# src/app/assets/frames/resources.py

class StageFrame(Frame):
    """
    Indexes horizontal sprite strips based on the stage space 
    encoded by the asset's lifespan property.
    """

    @staticmethod
    def _stages(lifespan: str):
        if lifespan == Lifespans.ANNUAL.value:
            return AnnualStages
        if lifespan == Lifespans.PERENNIAL.value:
            return PerennialStages
        if lifespan == Lifespans.CENTENNIAL.value:
            return CentennialStages

    def index(self, id: str, properties: ResourceProperties) -> Dict[str, Tuple[int, int, int, int]]:
        w = properties.dimensions.w
        l = properties.dimensions.l
        stages = properties.lifespan
        

        return {
            settings.SEPARATOR.join([id, stage.value]): (i * w, 0, w, l)
            for i, stage in enumerate(stages)
        }

    def keys(self, id: str, state: AssetState) -> List[Tuple[str, int, int]]:
        return [(settings.SEPARATOR.join([id, state.stage]), 0, 0)]
```

---

###### 3. The Stage Configuration Schema Gap

In `/src/data/config/stages/main.yaml`, transitions are partitioned by `lifespan` rather than asset instance:

```yaml
stages:
  annual:
    sprout:
      - next: growth
        conditions:
          - "calendar.season in [Seasons.SPRING.value, Seasons.SUMMER.value]"
          - "resource.retention >= 20.0"
      - next: stump
        conditions:
          - "calendar.season == Seasons.WINTER.value"
    growth:
      - next: stalk
        conditions:
          - "calendar.season in [Seasons.SPRING.value, Seasons.SUMMER.value]"
          - "resource.retention >= 25.0"
      - next: stump
        conditions:
          - "calendar.season == Seasons.WINTER.value"
    stalk:
      - next: bloom
        conditions:
          - "calendar.season == Seasons.AUTUMN.value"
          - "resource.retention >= 30.0"
      - next: stump
        conditions:
          - "calendar.season == Seasons.WINTER.value"
    bloom:
      - next: stump
        conditions:
          - "calendar.season == Seasons.AUTUMN.value"
          - "resource.harvested"
      - next: stump
        conditions:
          - "calendar.season == Seasons.WINTER.value"
    stump:
      - next: sprout
        conditions:
          - "calendar.season == Seasons.SPRING.value"
          - "calendar.cycle == SeasonCycles.ONSET.value"
          - "calendar.period == 0"
          - "resource.retention >= 10.0"

  perennial:
    sapling:
      - next: bush
        phase: genesis
        conditions:
          - "resource.phase == EpicyclePhases.GENESIS.value"
          - "calendar.season == Seasons.SPRING.value"
          - "calendar.cycle == SeasonCycles.PEAK.value"
          - "resource.retention >= 15.0"
    # ... remaining perennial rules ...

  centennial:
    trace:
      - next: deposit
        conditions:
          - "calendar.year >= 5"
    # ... remaining centennial rules ...

```

###### 4. The Executor Evaluation Loop in `SeasonMechanics`

With `ResourceProperties.lifespan` and unified `ResourceState`, the inner loop of `SeasonMechanics` evaluates state changes without any conditional branching on instance types:

```python
# In SeasonMechanics.update():
for asset in board.categories(AssetCategories.RESOURCES.value):
    lifespan = asset.properties.lifespan
    current_stage = asset.state.stage
    
    locals_env = {
        "resource": asset.state,
        "properties": asset.properties,
        "calendar": board.calendar,
        "Seasons": Seasons,
        "Cycles": Cycles,
        "Phases": Phases,
    }
    
    transition = self.executor.evaluate(lifespan, current_stage, locals_env)
    if transition:
        asset.state.stage = transition.next
        if transition.phase:
            asset.state.phase = transition.phase

```

###### Tradeoff Analysis

| Dimension | Previous Instance-Bound Design | Proposed Lifespan Design |
| --- | --- | --- |
| **Ontological Rigor** | **Poor**: Possibility space assumed by hardcoded frame classes. | **Strict**: Properties define the space of possible stages; state exemplifies the active stage. |
| **Extensibility** | **Low**: Adding a perennial crop or biennial plant requires a new recipe, frame class, and mechanic branch. | **High**: Changing `lifespan: perennial` on a berry bush instantly enables tree epicycles and hydration retention without code changes. |
| **Code Duplication** | **High**: Separate frames (`CropStageFrame`, `TreeStageFrame`, `OreStageFrame`) doing identical offset math. | **Zero**: Single `StageFrame` parameterized by `properties.lifespan`. |
| **State Cohesion** | Fragmented (`YieldState`, `RenewState`, `TectonicState`). | Unified (`ResourceState`), eliminating cross-lifespan contract errors. |

##### User Review III

I do not fully agree. The problem comes down to `Screen.reconstruct()` and and `_prerender`, I believe. They do not currently have access to the Board calendar state. This appears to be the source of all design woes. The current tasking papers over this by ensuring Tile seasons have an initial value, but it ignores what happens if the Board being loaded already has a calendar state that has progressed beyond the initial state (loading a saved game), i.e. Tiles will initially be constructed with the default Seaons and will not sync until the first SeasonEvent is thrown. 

Tile rendering is using the same interface as Asset rendering, e.g. `keys()`, for Frame retrieval, when Tile rendering is not the type of rendering that occurs due to changes in its own state. `keys()` is a reflexive state based interface, whereas Tiles should be retrieving their keys from a different interface.

To extend the analogy, Seasons are not intrinsic to the Asset, but the Asset Frame is dependent on the Season state. While Dirt may be an independent phenomenon (debatable), it is not a mutually exclusive phenomenon with Seasonality. Dirt does not occur in a vacuumn where seasonality is null and void. Even dirt in the deep darkness of space orbits something and experiences variations in temperature, due to its instantiation in a physical universe where temperature is a thing that happens. In Heideggerian sense, Seasons inhabit Dirt as a mode of its being.  

`keys()` is akin to self animate locomotion, i.e. an entity that can produce its own changes. As you noted, it is a projection of its own state onto the animation space. We are, in a sense, projecting a different state onto the animation state. We need a `eras(calendar: CalendarState)` interface on Frames that provides a different lookup path along the Calendar state structure and simply goes unimplemented by the other Frames. Basically `sync`, except it's called by Screen, not EventHandlers or anywhere else. The prerendering process in Screen explicitly uses this interface. 

**Note**: This may have other uses, as aging and reproduction cycles are added to other Assets.

I believe Screen would have to be init'ed with the calendar state, the _prerender method would need to accept the calendar state and the reconstruct method would have to accept it. 

Evaluate this proposal, which is basically just an elaboration and relabeling of sync().

##### Architectural Analysis VI

The diagnosis of the hydration bug is spot-on, and separating reflexive intrinsic state projection (`keys`) from macro-temporal environmental resolution (`eras`) resolves the underlying category error.

###### 1. The Hydration Bug You Identified

In the existing code:

```python
# Screen.__init__ in src/app/game/screen.py
self.bg_canvas = render.canvas(canvas_w, canvas_l, opaque=is_opaque)
self.fg_canvas = render.canvas(canvas_w, canvas_l)

back_tiles, fore_tiles = self._prerender(tiles)
```

And in `Builder.build_pipeline`:

```python
self.screens[layer] = Screen(
    self.context.screensize, 
    Dimensions(layer_size.w, layer_size.l), 
    self.board.categories(AssetCategories.TILES.value, layer), 
    self.registry
)
```

Because `Screen` is instantiated without `board.calendar`, loading a saved game at Year 2, Autumn Peak bakes tiles using hardcoded default frames (`spring-onset-0`). The board would remain visually desynchronized until a `SeasonEvent` boundary was crossed 400 seconds later.

The root cause was not `SeasonalFrame` itself, but the fact that **canvas baking in `Screen` was divorced from ambient calendar state**.

###### 2. Ontological Grounding: `keys()` vs. `eras()`

The Heideggerian distinction between *self-movement* (an entity projecting its own intrinsic state) and *thrownness* (an entity existing within an ambient horizon or era) maps directly to the code:

* **`keys(id, state)`**: Reflexive, monadic projection. Used for entities that drive their own micro-temporal states (walk cycles, open/closed chests, velocities). Evaluated at 60 Hz in `Screen.draw()`.
* **`eras(id, calendar)`**: Environmental, dyadic projection. Used for entities whose visual presentation is determined by the macro-temporal epoch of the Board. Evaluated macro-temporally in `Screen._prerender()`.

Tiles do not "act"; they are acted upon by the macro-climate. Forcing tiles through `keys(id, state)` created the illusion that `tile.state` was responsible for seasonal appearance, which in turn spawned the awkward `sync()` side-channel.

###### 3. Evaluating the `eras` Interface: Setter vs. Direct Lookup

Rather than making `eras(calendar)` an imperative setter that stores hidden state on the frame instance, implement it as a **direct functional query**:

```python
# src/app/assets/base.py

class Frame(ABC):
    @abstractmethod
    def keys(self, 
        id: str, 
        state: AssetState
    ) -> List[Tuple[str, int, int]]:
        """Reflexive intrinsic state projection for dynamic 60 Hz draw passes."""
        pass

    def eras(self, 
        id: str, 
        calendar: CalendarState
    ) -> List[Tuple[str, int, int]]:
        """
        Macro-temporal epochal projection for static pre-rendered canvas baking.
        Default implementation falls back to static frame resolution.
        """
        return self.keys(id, None)

```

1. **Purity**: `eras(id, calendar)` is a pure projection $(ID \times Calendar \to FrameKey)$. It does not mutate the frame object.
2. **Instance-Agnostic**: It does not matter whether `SeasonalFrame` is a singleton or instantiated per tile in the recipe. No mutable state is shared across instances.
3. **No Redundant Calls**: `Screen` does not need to call `frame.eras(calendar)` before calling `keys()`. It simply dispatches `tile.frame.eras(tile.id, calendar)` during the prerender loop.

`SeasonalFrame` in `app.assets.frames.tiles` becomes:

```python
# src/app/assets/frames/tiles.py

class SeasonalFrame(Frame):
    def index(self, id: str, properties: TileProperties) -> Dict[str, Tuple[int, int, int, int]]:
        w = properties.dimensions.w
        l = properties.dimensions.l
        crops = {}
        for row, season in enumerate(Seasons):
            for col_cycle, cycle in enumerate(SeasonCycles):
                for period in range(3):
                    col = col_cycle * 3 + period
                    key = settings.SEPARATOR.join([
                        id, season.value, cycle.value, str(period)
                    ])
                    crops[key] = (col * w, row * l, w, l)
        return crops

    def eras(self, id: str, calendar: CalendarState) -> List[Tuple[str, int, int]]:
        key = settings.SEPARATOR.join([
            id, calendar.season, calendar.cycle, str(calendar.period)
        ])
        return [(key, 0, 0)]

    def keys(self, id: str, state: AssetState) -> List[Tuple[str, int, int]]:
        # Fallback if accessed outside of macro-temporal canvas baking
        return [(f"{id}-spring-onset-0", 0, 0)]
```

###### 4. Updating the `Screen` Canvas Pipeline

With `eras(id, calendar)`, the `Screen` class receives `calendar` across its three canvas compilation entry points:

```python
# src/app/game/screen.py

class Screen:
    def __init__(self, 
        screensize: Dimensions,
        boardsize: Dimensions,
        tiles: List[Asset],
        registry: Registry,
        calendar: CalendarState
    ):
        self.screensize = screensize
        self.boardsize = boardsize
        self.registry = registry

        canvas_w = max(boardsize.w, screensize.w)
        canvas_l = max(boardsize.l, screensize.l)

        is_opaque = len(tiles) == 0
        self.bg_canvas = render.canvas(canvas_w, canvas_l, opaque=is_opaque)
        self.fg_canvas = render.canvas(canvas_w, canvas_l)

        back_tiles, fore_tiles = self._prerender(tiles, calendar)
        render.construct(self.bg_canvas, back_tiles)
        render.construct(self.fg_canvas, fore_tiles)

    def _prerender(self, 
        tiles: List[Asset], 
        calendar: CalendarState
    ) -> tuple[list, list]:
        back_tiles, fore_tiles = [], []

        for tile in tiles:
            # Query macro-temporal era projection
            frame_keys = tile.frame.eras(tile.id, calendar)

            for frame_key, ox, oy in frame_keys:
                tex_data = self.registry.image(frame_key)
                if not tex_data:
                    continue

                tex, sx, sy, sw, sl = tex_data
                tile_tuple = (
                    tex, sx, sy, sw, sl,
                    tile.state.position.x + ox,
                    tile.state.position.y + oy,
                    tile.dimensions.w, tile.dimensions.l,
                    tile.state.multiple.nx, tile.state.multiple.ny
                )

                if tile.taxonomy.instance == AssetInstances.BACK.value:
                    back_tiles.append(tile_tuple)
                elif tile.taxonomy.instance == AssetInstances.FORE.value:
                    fore_tiles.append(tile_tuple)

        return back_tiles, fore_tiles

    def reconstruct(self, tiles: List[Asset], calendar: CalendarState) -> None:
        """Bakes updated seasonal tile frames without reallocating GPU texture memory."""
        back_tiles, fore_tiles = self._prerender(tiles, calendar)
        render.construct(self.bg_canvas, back_tiles)
        render.construct(self.fg_canvas, fore_tiles)

    def rebake(self, 
        tiles: List[Asset], 
        boardsize: Dimensions,
        calendar: CalendarState,
        screensize: Dimensions = None
    ) -> None:
        if self.bg_canvas:
            render.destroy(self.bg_canvas)
        if self.fg_canvas:
            render.destroy(self.fg_canvas)

        if screensize:
            self.screensize = screensize

        self.boardsize = boardsize
        canvas_w = max(boardsize.w, self.screensize.w)
        canvas_l = max(boardsize.l, self.screensize.l)

        is_opaque = len(tiles) == 0
        self.bg_canvas = render.canvas(canvas_w, canvas_l, opaque=is_opaque)
        self.fg_canvas = render.canvas(canvas_w, canvas_l)

        back_tiles, fore_tiles = self._prerender(tiles, calendar)
        render.construct(self.bg_canvas, back_tiles)
        render.construct(self.fg_canvas, fore_tiles)
```

###### 5. Architectural Verification Across Lifecycles

1. **Boot / Pipeline Construction (`Builder.build_pipeline`)**: 

`Screen` is instantiated with `calendar=self.board.calendar`.

2. **Hydration / Save File Loading (`Migrator.step`)**: 

When the world state finishes hydrating, `Migrator` calls:

```python
screen.rebake(
    tiles=board.categories(AssetCategories.TILES.value, layer),
    boardsize=board.size(layer)[0],
    calendar=board.calendar
)
```

If a saved game had `calendar.season = "autumn"`, the screen rebakes into Autumn on frame 1. The hydration bug is completely resolved.

3. **Runtime Period Boundary (`SeasonEventHandler.handle`)**: 

`SeasonEventHandler` does not touch any frames or global variables:
```python
class SeasonEventHandler(EventHandler):
    def handle(self, event: SeasonEvent, context: EventContext) -> None:
        calendar = context.board.calendar
        for layer, screen in context.screens.items():
            tiles = context.board.categories(AssetCategories.TILES.value, layer)
            screen.reconstruct(tiles, calendar)
```


4. **Future Extensibility (Aging / Reproduction)**:

If an environmental asset (e.g., an ancient monolithic ruin, a seasonal moss layer, or perennial groundcover) is baked into the canvas, its frame can implement `eras(id, calendar)` to reflect centuries elapsed or seasonal snowmelt without polluting dynamic entity loops.

##### User Review IV

A problem appears to be, in my opinion, the Stage transition configuration has its transition node spread across two fields (next, phase), and the Executor requires the transition to be returned under the next field . I believe the correct solution, instead of introducing a totally separate implementation, is to encapsulate the Executor return type in an abstraction, i.e. Node, and then refactor the Plot and Intention transition mechanics to respect the new interface. Then it becomes evaluate(current_state, locals) -> Node. 

Actually, wait. Just noticed something. I don't think Phase is actually necessary. The phases are a natural part of the transition tree and are redundant, i.e. genesis (sapling -> adult) homeostatis (vibrant -> snowcapt) and apoptosis (dying -> dead). The only problem is the transition from dying to adult requires adult to sit between two partitions of homeostasis and genesis. However, if dying is pointed healthy, then tree re-enters homeostasis naturally. 

So the entire problem is moot anyway, because phase is not required. Analyze this.

However, the problem of needing the lifespan to evaluate is a real and legitimate dependency. Perhaps a better solution is to instantiate a separate executor for each possible lifespan and register in the Builder separately. Mechanics can request multiple executors in the configuration, theoretically (although it's never been tested). 


##### Architectural Analysis VI

The need for `phase` was an illusion created by a category error during early analysis, compounded by making the `adult` stage serve double-duty as a recovery hub.

###### The Origin of the False Dependency

The concern in Architectural Analysis II—that *"without phase, a hundred-year-old forest would reset to saplings upon every Spring arrival"*—only applies to a **stateless function** $f(\text{season}, \text{cycle}, \text{retention}) \to \text{stage}$.

In a stateful Finite State Machine (FSM), the state of the entity is anchored in `resource.state.stage`. The transition engine only evaluates outgoing edges from the *current* node:

* A mature tree in Winter is at `snowcapt`.
* When Spring arrives, the only outgoing edge evaluated is `snowcapt -> vibrant`.
* It cannot jump to `sapling` because `snowcapt` has no transition edge to `sapling`.

###### Disjoint State Partitions

If you partition the tree stage space:

* $S_{\text{genesis}} = \{\text{sapling}, \text{bush}, \text{branch}, \text{adult}\}$
* $S_{\text{homeostasis}} = \{\text{vibrant}, \text{healthy}, \text{abscise}, \text{snowcapt}\}$
* $S_{\text{apoptosis}} = \{\text{dying}, \text{dead}, \text{stump}\}$

These sets are **mutually disjoint**:

$$S_{\text{genesis}} \cap S_{\text{homeostasis}} \cap S_{\text{apoptosis}} = \emptyset$$

Because every stage identifier is unique across the entire lifecycle, the active stage itself defines which macro-phase the entity occupies. Storing `phase` alongside `stage` on `ResourceState` is storing redundant state.

```
GENESIS (Directed DAG):
sapling ──► bush ──► branch ──► adult ──► healthy
                                             │
HOMEOSTASIS (Directed Cycle):                ▼
┌───────────────────────────────────────► healthy
│                                            │
│                                            ▼
vibrant ◄── snowcapt ◄── abscise ◄───────────┘
   ▲                         │
   │                         ▼ (unhydrated)
   │                      dying ──► dead ──► stump ──► sapling (Spring)
   │                         │
   └────── (Spring/Summer) ──┘
          Recovery Edges

```

###### The `adult` Bottleneck & Clean Recovery

In the original draft, `dying` routed back to `adult`, and `adult` branched into four separate seasonal transitions (`adult -> vibrant`, `adult -> healthy`, etc.). That forced `adult` to require `resource.phase == homeostasis` to prevent young Genesis trees from jumping directly into Autumn or Winter.

By routing recovery from `dying` directly into Homeostasis based on the active season:

* **Spring recovery**: `dying -> vibrant` (if `season == SPRING` and `retention >= 20.0`)
* **Summer recovery**: `dying -> healthy` (if `season == SUMMER` and `retention >= 20.0`)
* **Autumn/Winter failure**: `dying -> dead -> stump`

`adult` is restored to its natural role: the final growth stage of Genesis (`branch -> adult -> healthy`). It no longer needs to act as a recovery junction, eliminating all ambiguity.

###### Lifespan-Partitioned Executors

Instantiating separate executors per lifespan (`annual`, `perennial`, `centennial`) is architecturally superior to building 2-tier executors or introducing a `Node` abstraction.

**Native Architectural Alignment**

The base architecture already supports this pattern natively:

1. `Mechanic.executors` is already a dictionary: `Dict[str, Any]` (`app.game.logic.mechanics.base`).
2. `MechanicsInstance.executors` is already a list of keys: `List[str]` (`app.models.config.mechanics`).
3. `Factory.mechanics()` iterates through `m.executors` and executes `mechanic.set_executor(key, executors[key])`.

###### Unification of the Translation Pipeline

If `/src/data/config/stages/main.yaml` partitions rules by lifespan:

```yaml
annual:
  sprout:
    - next: growth
      conditions: [...]
perennial:
  sapling:
    - next: bush
      conditions: [...]
centennial:
  trace:
    - next: deposit
      conditions: [...]

```

Each lifespan dictionary (`stages["annual"]`, `stages["perennial"]`) has the exact schema expected by `Translator.compile()`: `Dict[str, List[Configuration]]`.

This provides major architectural simplifications:

* **Zero changes to `Translator` and `Executor` interfaces**: `evaluate(current_state: str, locals: Dict[str, Any]) -> Optional[str]` remains completely untouched.
* **No `Node` abstraction or compound return types**: The transition target is simply `next: str`.
* **Zero AST compiler modifications**: `CompilerTranslator` and `LambdaTranslator` compile each lifespan graph directly without custom 2-tier nesting logic.

###### Runtime Dispatch in `SeasonMechanics`

In `SeasonMechanics.update()`:

```python
for asset in board.categories(AssetCategories.RESOURCES.value):
    lifespan = asset.properties.lifespan  # e.g., "annual", "perennial"
    executor = self.executors.get(lifespan)
    if not executor:
        continue

    locals_env = {
        "resource": asset.state,
        "calendar": board.calendar,
    }

    next_stage = executor.evaluate(asset.state.stage, locals_env)
    if next_stage:
        asset.state.stage = next_stage
```

Dispatching through `self.executors.get(lifespan)` is an $O(1)$ dictionary lookup with no conditional branching on entity types.

##### Bug Reports

###### Bug B015: State Persistence Omission for Calendar and World Metadata

**STATUS**: OPEN

**SEVERITY**: Medium

**Description**

In `Board.serialize()`, only `self._assets` are exported to the target slot dictionary. Abstract world metadata—specifically `board.calendar` and `board.plot`—are omitted from the serialization dump, causing game saves to reset to Year 1, Spring, Onset, and default plot state upon loading.

**Proposed Remediation**

Update `Board.serialize()` to serialize `asdict(self.calendar)` under the `calendar` key and `asdict(self.plot)` under `plots` in the target save state dictionary.

###### Bug B016: Migrator Calendar Unpacking Crash and Desynchronized World Metadata

**STATUS**: OPEN

**SEVERITY**: High

**Description**

In `Migrator._build_generator()`, abstract metadata fields on `StateSchema` are filtered using `category_key in Shortcuts`. Because `Shortcuts` lacks `CALENDAR`, `Migrator` treats `CalendarState` as a physical asset category and attempts to iterate `instance_list = getattr(category_data, "year")`, raising `TypeError: 'int' object is not iterable`. Additionally, `self.board.calendar` is never hydrated from `self.state.calendar`.

**Steps to Replicate**

1. Save or load a state containing `calendar: CalendarState(year=2, season="autumn")`.
2. Execute `Migrator.step()`.
3. The generator crashes with `TypeError: 'int' object is not iterable`.

**Proposed Remediation**

1. Add `CALENDAR = "calendar"` to `Shortcuts` in `app.config.enums`.
2. In `Migrator._build_generator()`, extract `self.state.calendar` and assign it directly to `self.board.calendar = self.state.calendar`.

##### Goals

###### Goal: Temporal Board State & Schema Integrity

Establish typed data contracts and configurations for temporal tracking and resource entities. Register `calendar: CalendarState` on `Board`, integrate it into `StateSchema`, and uncomment resource schemas across properties and states.

```python
# app.models.state.core
@dataclass(slots=True)
class CalendarState:
    year: int = 1
    season: str = Seasons.SPRING.value
    cycle: str = SeasonCycles.ONSET.value
    period: int = 0
    elapsed: float = 0.0

```

###### Goal: Seasonal Tile Invalidation & Screen Reconstruction

Implement `SeasonalFrame` in `app.assets.frames.tiles` to map 36-cell ($4 \times 9$) tile sheets to `{id}-{season}-{cycle}-{period}` keys. Implement `Screen.reconstruct(tiles)` to execute `render.construct` on existing canvas texture pointers without destroying GPU contexts. Wire `SeasonEventHandler` to sync `SeasonalFrame` and rebuild canvases on period boundaries.

###### Goal: Resource ECS Data Hierarchy & Stage Framing

Complete resource data models in `app.models.state.assets.resources` (`YieldState`, `RenewState`, `TectonicState`). Implement `StageFrame` in `app.assets.frames.resources` mapping `state.stage` directly to horizontal atlas offsets `{id}-{state.stage}`. Bind resource instances to `NoAnimation` in recipes.

###### Goal: Declarative Stage Transition Architecture

Author `/src/data/config/stages/main.yaml` declaring transition rules for crops and trees without string-token concatenation. Add `stages` to `ConfigurationSchema`, load via `Loader`, and compile into `StageExecutor` within `Builder.build_executors()`.

###### Goal: SeasonMechanics World Pipeline Execution

Implement `SeasonMechanics` in `app.game.logic.mechanics.world.seasons`. Integrate $\Delta t$ into `board.calendar.elapsed`, dispatch `SeasonEvent` across period boundaries, calculate hydrological moisture diffusion from adjacent `board.fluid()` spatial buckets into resource states, and evaluate stage transitions via `self.executor`.


```python
# Hydrological Diffusion & Evaporation Integration
is_near_water = any(
    board.fluid(resource.state.layer, probe_pos)
    for probe_pos in self._probes(resource)
)
if is_near_water:
    resource.state.retention = min(
        settings.MAX_RETENTION, 
        resource.state.retention + settings.DIFFUSION_RATE * delta
    )
else:
    mod = settings.SEASON_EVAPORATION_MODIFIERS[board.calendar.season]
    resource.state.retention = max(
        0.0, 
        resource.state.retention - settings.EVAPORATION_RATE * mod * delta
    )
```

###### Goal: Lifespan-Partitioned Configuration & Executor Registration

Compile `/src/data/config/stages/main.yaml` into independent executors keyed by `Lifespans` enum values.

```python
# In Builder.build_executors()
for lifespan in Lifespans:
    stage_rules = self.context.configurations.stages.get(lifespan.value)
    if stage_rules:
        self.executors[lifespan.value] = translator.compile(stage_rules)

```

###### Goal: Phase-Free Stage Graph & State Model

Remove `phase` from `ResourceState` and simplify `stages/main.yaml` into a planar, single-target transition graph.

```python
# In SeasonMechanics.update()
executor = self.executors.get(asset.properties.lifespan)
if executor:
    next_stage = executor.evaluate(asset.state.stage, locals_env)
    if next_stage:
        asset.state.stage = next_stage

```

##### Tasks

**1. Task: Temporal Schema & State Integration**

*Objective*: Establish data contracts and configurations for temporal progression and resource types.

* [x] Subtask: Add `Seasons`, `Cycles`, `Phases`, `Lifespans`, `AnnualStages`, `CentennialStages`, and `PerennialStages` to `app.config.enums`.
* [x] Subtask: Configure `SEASON_DURATION_SECONDS` in `app.config.settings` (3600).
* [x] Subtask: Implement `CalendarState` in `app.models.state.core` with `year`, `season`, `cycle`, `period`, and `elapsed`.
* [x] Subtask: Add `calendar: CalendarState = field(default_factory=CalendarState)` to `StateSchema`.
* [x] Subtask: Register `SeasonEvent: SeasonEventHandler()` in `Engine.handlers` dictionary inside `app.game.engine`.
* [x] Subtask: Add `CALENDAR = "calendar"` to `Shortcuts` in `app.config.enums`.
* [x] Subtask: Update `Migrator._build_generator()` to unpack `self.state.calendar` and assign it directly to `self.board.calendar`.
* [x] Subtask: Update `Board.serialize()` to serialize `self.calendar` and `self.plot` into the state save dictionary (resolving Bug B015).

*Objective*: Restructure `/src/data/config/stages/main.yaml` to eliminate `phase` targets and condition conjuncts.

* [x] Subtask: Strip all `phase:` keys and `resource.phase` conditions from `stages/main.yaml`.
* [x] Subtask: Configure direct Homeostasis recovery edges from `dying` (`dying -> vibrant` in Spring, `dying -> healthy` in Summer).
* [x] Subtask: Update `/src/data/config/mechanics/main.yaml` to bind `annual`, `perennial`, and `centennial` executors to `season: SeasonMechanics`.

**2. Task: Seasonal Tile Frame Indexing & Screen Integration**

*Objective*: Support multi-season tile sprite sheets and connect macro-temporal invalidation to Screen canvas baking via the Frame.eras interface.

- [x] Subtask: Implement `SeasonalFrame` in `app.assets.frames.tiles` indexing 36 cells ($4\text{ rows} \times 9\text{ columns}$) formatted as `{id}-{season}-{cycle}-{period}`.
- [x] Subtask: Add `eras(id: str, calendar: CalendarState) -> List[Tuple[str, int, int]]` to foundational `Frame` class in `app.assets.base`, defaulting to `self.keys(id, None)`.
- [x] Subtask: Implement `SeasonalFrame.eras(id, calendar)` to emit `[(f"{id}-{calendar.season}-{calendar.cycle}-{calendar.period}", 0, 0)]`.
- [x] Subtask: Update `Screen.__init__`, `Screen._prerender`, and `Screen.rebake` to accept `calendar: CalendarState` and route tile frame resolution through `tile.frame.eras(tile.id, calendar)`.
- [x] Subtask: Implement `Screen.reconstruct(tiles: List[Asset], calendar: CalendarState)` to recompile `bg_canvas` and `fg_canvas` without destroying VRAM targets.
- [x] Subtask: Implement `SeasonEventHandler.handle(event, context)` in `app.game.menus.handlers.seasons` to call `screen.reconstruct(tiles, context.board.calendar)` across active screens.
- [x] Subtask: Add `SeasonalFrame` to `app.services.generators.game.factory`.

**3. Task: Resource Hierarchy Models & Stage Framing**

*Objective*: Implement the Resource category using unified lifespan typing.

- [x] Subtask: Add `Lifespans` enum (`ANNUAL`, `PERENNIAL`, `CENTENNIAL`) .
- [x] Subtask: Update `ResourceProperties` in `app.models.properties` with `dimensions: Dimensions`, `lifespan: str`, `loot: str`, `hitboxes: List[Hitbox]`, and `mass: int = 0`.
- [x] Subtask: Implement unified `ResourceState` in `app.models.state.assets.resources` with `position`, `stage`, `retention`, `phase`, and `harvested`.
- [x] Subtask: Implement generic `StageFrame` in `app.assets.frames.resources` indexing horizontal strips dynamically using `properties.lifespan`.
- [x] Subtask: Configure resource recipes in `app.services.orchestrator` binding resources to `StageFrame`, `NoAnimation`, `ResourceProperties`, and `ResourceState`.
* [x] Subtask: Add `StageFrame` to `app.services.generators.game.factory`.

**4. Task: Declarative Stage Transition Architecture**

*Objective*: Build the declarative transition engine partitioned by Lifespan.

- [x] Subtask: Author `/src/data/config/stages/main.yaml` declaring stage transition graphs partitioned by `lifespan` (`annual`, `perennial`, `centennial`).
- [x] Subtask: Add `StageConfiguration` to `app.models.config.core` and register `stages: Dict[str, Dict[str, List[StageConfiguration]]]` on `ConfigurationSchema`.
- [!] Subtask: Implement `StageExecutor` compiling `/src/data/config/stages/main.yaml` to evaluate `(lifespan, current_stage, locals)` and return `StageTransition(next, phase)`.
- [!] Subtask: Register `stage: StageExecutor` in `Builder.build_executors()` under `Executors.STAGE.value`.
- [!] Subtask: Update the Transition Executor `Environ` to include Seasonality enums.

*Objective*: Register lifespan-keyed executors in `Builder.build_executors()`.

* [x] Subtask: Iterate `Lifespans` in `Builder.build_executors()`, compiling each configuration block via `translator.compile()` and storing under `self.executors[lifespan.value]`.


**5. Task: SeasonMechanics Simulation Pipeline**

*Objective*: Implement `SeasonMechanics` driving calendar accumulation, fluid diffusion, and lifespan stage transitions.

* [x] Subtask: Implement `SeasonMechanics` inheriting from `Mechanic` in `app.game.logic.mechanics.world.seasons`.
* [x] Subtask: Implement temporal integration ticking `board.calendar.elapsed`, cycling periods, cycles, seasons, and years, and dispatching `SeasonEvent` on period boundaries.
* [x] Subtask: Implement hydrological moisture diffusion in `SeasonMechanics` using `board.fluid()` spatial buckets.
* [x] Subtask: Evaluate stage transitions in `SeasonMechanics` via `self.executors.get(asset.properties.lifespan).evaluate(asset.state.stage, locals)` and assign `asset.state.stage = next_stage`.

