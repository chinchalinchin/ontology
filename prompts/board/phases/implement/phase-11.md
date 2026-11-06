#### Implement: Phase 11 - Geology

**Overview**

This proposal introduces `Strata` as a new procedural `AssetInstance` under the `Geography` category (`geography.strata`). While `Shorelines` represent 1D directional margins synthesized deterministically at the interface of `Environ` Tiles and `Fluid` Effects, `Strata` represent unidirectional, multi-elevation 2.5D geological formations (`mesas`, `spires`, `buttes`) bound strictly to `Environ` Tiles. During Board hydration, `Cartographer` identifies interior "faultlines" where adjacent `Environ` Tile deployments meet, constructs a spatial probability field localized along those faultlines, and probabilistically samples and spawns `Strata` formations via `StrataIndex` and `Cradle`.

##### Specification

* **Taxonomy**:

* `category`: `AssetCategories.GEOGRAPHY` (`"geography"`)
* `instance`: `AssetInstances.STRATA` (`"strata"`)
* `substrate`: `Substrates.STANDARD` (`0`) — unlike `Shorelines` (`Substrates.SURFACES = -2`), `Strata` are upright volumetric formations that must Y-sort (`ground_y`) coplanarly with `Sprites`, `Objects`, and `Crafts`.

* **Relational Binding (`StrataIndex`)**:

* Binds `tile_id: str` ($\text{Tile}_{\text{Environ}} \to \text{Strata}$) without a `fluid` key.
* Encodes relative formation weights $W = (w_{\text{spires}}, w_{\text{mesas}}, w_{\text{buttes}})$ satisfying $P(\text{spires}) > P(\text{mesas}) > P(\text{buttes})$.

* **Atlas Partitioning `(Row: Formation, Column: Season)`**:

* **Columns (`Seasons`)**: `spring` ($0$), `summer` ($1$), `autumn` ($2$), `winter` ($3$).
* **Rows (`Formations`)**:
    1. `mesas` (Row $0$): Elevated plateau. Obstructs dynamic entities at its deployed elevation $E$ ($m = 0$) and projects a walkable support surface at elevation $E + 1$ for entities descending from $\ge E + 1$ or traversing horizontally at $E + 1$.
    2. `spires` (Row $1$): Vertical monolith. Obstructs dynamic entities at its deployed elevation $E$ ($m = 0$) with no walkable upper surface at $E + 1$.
    3. `buttes` (Row $2$): Inclined plateau. Obstructs dynamic entities along its `UP`, `LEFT`, and `RIGHT` flanks at deployed elevation $E$, exposes a walkable incline outlet on its `DOWN` (southern) edge that transitions dynamic entities between $E$ and $E + 1$ ($\Delta E = \pm 1$), and provides a walkable surface at $E + 1$.

* **Procedural Faultline Synthesis (`Cartographer`)**:

* **Faultline Extraction**: Where two `Environ` Tile regions $T_i, T_j$ share an interior border segment $\mathcal{F}_{ij}$, a faultline segment $\mathbf{s}_k = (\mathbf{a}_k, \mathbf{b}_k)$ is established.
* **Spatial Probability Field**: Faultline segments act as line sources generating an exponentially screened spatial probability density $\mathcal{P}(\mathbf{x}) \in [0, 1]$ across the layer:

$$\mathcal{P}(\mathbf{x}) = 1 - \prod_{k \in \text{Faultlines}} \left(1 - p_0 \exp\left(-\frac{d_k(\mathbf{x})}{\sigma_{\text{strata}}}\right)\right)$$

where $d_k(\mathbf{x})$ is the minimum Euclidean distance from candidate coordinate $\mathbf{x}$ to faultline segment $\mathbf{s}_k$, $p_0 \in (0, 1]$ is the peak faultline nucleation probability, and $\sigma_{\text{strata}}$ is the transverse decay length.
* **Formation Sampling**: At each accepted non-occluded candidate coordinate $\mathbf{x}$, the underlying `Environ` tile $T(\mathbf{x})$ is queried via `board.tile(layer, x)`, resolved through `StrataIndex` to a `strata_id` and categorical distribution $P(\text{Formation} \mid \text{strata\_id})$, and instantiated via `board.cradle.spawn_strata(...)`.

##### Architectural Analysis I

###### 1. State & Property Generalization (`Shorelines` vs. `Strata`)

In `Crafts`, `CraftProperties` and `CraftState` unified disparate structural atlases through `Blueprints` (rows) and `Material` (columns). `Geography` exhibits an isomorphic structure:

* **Columns**: Both `Shorelines` and `Strata` index their horizontal atlas axis by `Seasons` (`spring`, `summer`, `autumn`, `winter`).
* **Rows**: `Shorelines` index their vertical atlas axis by `Directions` (`up`, `left`, `down`, `right`), whereas `Strata` index their vertical axis by `Formations` (`mesas`, `spires`, `buttes`).

To avoid ad-hoc proliferation of unrelated state fields while honoring semantic distinction:

* Define a shared base `GeographyState(AssetState)` in `src/app/models/state/assets/geography.py` containing `position: Optional[Position]`, `season: Seasons`, `hitboxes: List[Hitbox]`, and `_keys: Optional[List[Tuple[str, int, int]]]`.
* `ShorelineState(GeographyState)` declares `orientation: Directions` and `length: int`.
* `StrataState(GeographyState)` declares `formation: Formations` and `delta: int = 1` (used by `buttes` and `mesas` for elevation offset resolution).
* In `GeographyProperties` (`src/app/models/properties/assets.py`), widen `hitboxes` from `Optional[List[Hitbox]]` to mirrored polymorphic formation mappings:
```python
hitboxes: Optional[Union[Dict[str, List[Hitbox]], List[Hitbox]]] = field(default_factory=list)
probabilities: Optional[Dict[str, float]] = None

```


This allows `Shorelines` to retain `hitboxes: null` (synthesized dynamically via `thickness`) while `Strata` YAML property files can declare explicit per-formation relative hitboxes (`mesas`, `spires`, `buttes`) and optional per-asset formation probability overrides.

###### 2. Out-of-Context Systems Affected

Because `Strata` introduce static $m = 0$ obstructions, multi-elevation surfaces ($E + 1$), and incline transitions ($\Delta E = \pm 1$) into `Geography`, the following systems **not** present in the current context window will be impacted:

| System / Module | Address | Impact & Required Modification |
| --- | --- | --- |
| **Semantics** | `src/app/static/semantics.py` | Add `STRATA = "strata"` to `AssetInstances` and `Relations`; add `Formations(Enum)` (`MESAS`, `SPIRES`, `BUTTES`); add `FORMATION = "formation"` to `FrameTypes` and `HitboxTypes`. |
| **Property & State Schemas** | `src/app/models/properties/__init__.py`<br>

<br>`src/app/models/state/__init__.py` | Register `strata: Dict[str, GeographyProperties]` on `GeographyPropertiesSchema` and `strata: List[StrataState]` on `GeographyStateSchema` so `Loader` and `AssetFactory` ingest `/src/assets/geography/strata/**/*.yaml`. |
| **Material Index (Substrates)** | `src/data/config/materials/main.yaml`<br>

<br>`src/app/game/logic/relations/materials.py` | Register `strata` under `Substrates.STANDARD (0)`. If defaulted to `Substrates.SURFACES (-2)` like `shorelines`, Sprites at elevation $E$ would render *on top of* `spires` and `mesas` regardless of `ground_y`. |
| **Spawnable Group & Cradle** | `src/app/models/groups.py`<br>

<br>`src/app/services/generators/game/cradle.py` | Add `strata: Dict[str, GeographyProperties]` to `SpawnableGroup`. Add `Cradle.spawn_strata(...)` to instantiate `Strata` assets using `recipes.geography.strata` and `Substrates.STANDARD`. |
| **Hitbox ECS Component** | `src/app/assets/hitboxes/geography.py` *(or `hitboxes.py`)* | Implement `FormationHitbox(HitboxSchema)`. Must emit `[E]` for `spires` and `[E, E + 1]` for `mesas` and `buttes` in `elevations()`, and return tier-appropriate footprints in `get(properties, state, elevation)`. |
| **Board Queries & Caches** | `src/app/game/board/core.py`<br>

<br>`src/app/game/board/caches.py` | Expose `board.strata(layer=None)`. Ensure `board.weights(layer, elevation)` and `board.obstacles(layer, elevation)` include `geography.strata` ($m = 0$) so `CollisionMechanics`, `NavigationMechanics` (RRT), and `Actuator` (fluid raycasting) recognize `Strata` as static obstacles. |
| **Collision & Incline Physics** | `src/app/game/logic/mechanics/spatial/collision.py`<br>

<br>`src/app/game/logic/mechanics/core/motion.py` | Update Phase 0 incline traversal (`_traverse_stairs`) in `CollisionMechanics` to also evaluate `strata` with `state.formation == Formations.BUTTES.value` along the `DOWN` approach vector ($v_y < 0 \implies E + 1$, $v_y > 0 \implies E - 1$). Ensure gravity/support checks in `MotionMechanics` recognize `mesas` and `buttes` at $E + 1$ as valid supporting surfaces. |
| **Season Mechanics** | `src/app/game/logic/mechanics/world/season.py` | When `SeasonEvent` triggers, iterate `board.strata()` alongside `board.shorelines()` to update `state.season = board.calendar.season` and invalidate `state._keys = None`. |
| **Hydration Pipeline (`Migrator` & `Builder`)** | `src/app/services/orchestration/migrator.py`<br>

<br>`src/app/services/orchestration/builder.py` | Compile `StrataIndex` in `Builder`. In `Migrator`, invoke `Cartographer.generate_strata(layer, board, strata_index)` during Phase 2 hydration. |

###### 3. Hydration Execution Order Invariant

In `Migrator`, procedural generation ordering across `Tiles`, `Strata`, `Perimeter`, and `Fluids` is strictly constrained by causal dependencies:

1. **`Tiles` Hydration**: Populates `board.caches.tilemap[layer][ENVIRON]`.
2. **`Cartographer.generate_strata`**: Extracts faultlines from `Environ` tiles, checks initial static `Objects`/`Crafts` occlusions, and adds `Strata` ($m = 0$) to the `Board`.
3. **`Perimeter.generate`**: Extracts `Tiles`, `Objects`, `Crafts`, and newly spawned `Strata` (`mesas` and `buttes` at $E + 1$, static obstructions at $E$) to build tier boundary hulls.
4. **`Actuator.propagate` & `Cartographer.generate` (Shorelines)**: Raycasts `Fluids` against `board.obstacles` and `board.weights`. Because `Strata` are already on the `Board` with $m = 0$, fluid streams striking a `spire`, `mesa`, or `butte` will automatically truncate, form annular pools around the geological formation, bifurcate, and synthesize `Shorelines` along the resulting water contour.

##### User Review I

*(Reserved for User Review — alignment, constraints, and notes on faultline sampling density, `buttes` outlet hitbox geometry, and hydration seeding.)*

##### Goals

###### Goal: Semantic, Property, and State Schema Expansion

Define `Formations` in `app.static.semantics`, generalize `GeographyProperties` to support per-formation hitboxes and probability weights, and establish `GeographyState` and `StrataState` in `app.models.state.assets.geography`.

```python
# src/app/static/semantics.py
class Formations( str, Enum ):
    MESAS  = "mesas"
    SPIRES = "spires"
    BUTTES = "buttes"

# src/app/models/state/assets/geography.py
@dataclass(slots=True)
class GeographyState(AssetState):
    position: Optional[Position] = None  # type: ignore
    season: Seasons = Seasons.SPRING.value
    hitboxes: List[Hitbox] = field(default_factory=list)  # type: ignore
    _keys: Optional[List[Tuple[str, int, int]]] = None


@dataclass(slots=True)
class ShorelineState(GeographyState):
    orientation: Directions = Directions.DOWN.value
    length: int = 0


@dataclass(slots=True)
class StrataState(GeographyState):
    formation: Formations = Formations.SPIRES.value
    delta: int = 1

```

###### Goal: Relational Indexing & Probability Weights (`StrataIndex`)

Implement `StrataIndex` in `src/app/game/logic/relations/strata.py` to compile `tile -> strata_id` associations and normalize relative formation probabilities (defaulting to `spires: 0.60`, `mesas: 0.30`, `buttes: 0.10` if not overridden on `GeographyProperties`).

```python
# src/app/game/logic/relations/strata.py
class StrataIndex(Singleton):
    """
    Relational index mapping Environ Tile IDs to Strata Asset IDs and
    normalized categorical probability distributions over Formations.
    """
    DEFAULT_WEIGHTS: Dict[str, float] = {
        Formations.SPIRES.value: 0.60,
        Formations.MESAS.value: 0.30,
        Formations.BUTTES.value: 0.10,
    }

    _tile_map: Dict[Tuple[str, Optional[str]], str]
    _fallback_map: Dict[str, str]
    _weights: Dict[str, Dict[str, float]]

    @classmethod
    def from_properties(cls, strata: Dict[str, GeographyProperties]) -> StrataIndex:
        index = cls()
        for strata_id, props in strata.items():
            season = getattr(props, "season", None)
            if season:
                index.register((props.tile, season), strata_id)
            index.register(props.tile, strata_id)

            raw_weights = getattr(props, "probabilities", None) or cls.DEFAULT_WEIGHTS
            total = sum(raw_weights.values()) or 1.0
            index._weights[strata_id] = {
                k: v / total for k, v in raw_weights.items()
            }
        return index

    def resolve(self, tile_id: str, season: Optional[str] = None) -> Optional[str]:
        if season is not None and (tile_id, season) in self._tile_map:
            return self._tile_map[(tile_id, season)]
        return self._fallback_map.get(tile_id)

    def sample_formation(self, strata_id: str, u: float) -> str:
        """
        Inverse-transform sampling over (spires, mesas, buttes) given uniform u in [0, 1).
        """
        dist = self._weights.get(strata_id, self.DEFAULT_WEIGHTS)
        cumulative = 0.0
        for formation, prob in dist.items():
            cumulative += prob
            if u < cumulative:
                return formation
        return Formations.SPIRES.value

```

###### Goal: ECS Frame & Multi-Tier Hitbox Components (`FormationFrame` & `FormationHitbox`)

Implement `FormationFrame` in `src/app/assets/frames/geography.py` to index the $3 \times 4$ `(Formation, Season)` atlas, and `FormationHitbox` in `src/app/assets/hitboxes/geography.py` to project multi-tier collision and surface geometry across elevations $E$ and $E + 1$.

```python
# src/app/assets/frames/geography.py
class FormationFrame(Frame):
    """
    Indexes 3 geological formation rows (mesas, spires, buttes) across 4 calendar
    season columns.
    """
    FORMATION_ROWS = {
        Formations.MESAS.value: 0,
        Formations.SPIRES.value: 1,
        Formations.BUTTES.value: 2,
    }

    def index(self, id: str, properties: GeographyProperties) -> Dict[str, Tuple[int, int, int, int]]:
        w = properties.dimensions.w
        l = properties.dimensions.l
        crops: Dict[str, Tuple[int, int, int, int]] = {}

        for col, season in enumerate(Seasons):
            base_x = col * w
            for formation, row in self.FORMATION_ROWS.items():
                base_y = row * l
                key = settings.SEPARATOR.join([id, season.value, formation])
                crops[key] = (base_x, base_y, w, l)

        return crops

    def keys(self, id: str, state: StrataState) -> List[Tuple[str, int, int]]:
        if state._keys is not None:
            return state._keys
        key = settings.SEPARATOR.join([id, state.season, state.formation])
        state._keys = [(key, 0, 0)]
        return state._keys

```

```python
# src/app/assets/hitboxes/geography.py
class FormationHitbox(HitboxSchema):
    """
    Resolves elevation participation and tier-specific collision footprints
    for mesas, spires, and buttes.
    """
    def elevations(self, properties: GeographyProperties, state: StrataState) -> List[int]:
        base_e = max(0, state.elevation or 0)
        if state.formation in (Formations.MESAS.value, Formations.BUTTES.value):
            return [base_e, base_e + state.delta]
        return [base_e]

    def get(
        self,
        properties: GeographyProperties,
        state: StrataState,
        elevation: int,
        frame: Optional[Frame] = None,
    ) -> List[Hitbox]:
        base_e = max(0, state.elevation or 0)
        w = properties.dimensions.w
        l = properties.dimensions.l
        t = properties.thickness

        # Tier E + 1: Walkable surface footprint for mesas and buttes
        if elevation == base_e + state.delta:
            if state.formation in (Formations.MESAS.value, Formations.BUTTES.value):
                return [Hitbox(Position(0, 0), Dimensions(w, l))]
            return []

        if elevation != base_e:
            return []

        # Tier E: Base collision footprints
        if isinstance(properties.hitboxes, dict) and state.formation in properties.hitboxes:
            return properties.hitboxes[state.formation]

        if state.formation in (Formations.SPIRES.value, Formations.MESAS.value):
            return state.hitboxes or [Hitbox(Position(0, 0), Dimensions(w, l))]

        # Buttes at Tier E: 3-sided obstruction (UP, LEFT, RIGHT), open on DOWN for incline entry
        if state.formation == Formations.BUTTES.value:
            return state.hitboxes or [
                Hitbox(Position(0, 0), Dimensions(w, t)),          # North wall
                Hitbox(Position(0, 0), Dimensions(t, l)),          # West wall
                Hitbox(Position(w - t, 0), Dimensions(t, l)),      # East wall
            ]

        return []

```

###### Goal: Faultline Extraction & Probabilistic Generation in `Cartographer`

Extend `Cartographer` to extract interior faultlines between `Environ` tiles, evaluate the spatial probability distribution localized around faultline segments, and synthesize non-overlapping `Strata` instances.

1. **Faultline Detection (`_collect_faultlines`)**:
* Query all `AssetInstances.ENVIRON` tiles on `layer`.
* Convert each tile deployment into its world AABB $(x_1, y_1, x_2, y_2, \text{id})$.
* Extract shared interior edges where an edge of tile $A$ overlaps or abuts an edge of tile $B$ within the layer bounds (excluding the outer map perimeter).


2. **Spatial Probability Evaluation & Sampling (`generate_strata`)**:
* Partition the layer into candidate cells of size `(w, l)` matching the target `Strata` dimensions (or step grid `STEP_SIZE`).
* For each candidate coordinate $\mathbf{x} = (x, y)$, compute minimum squared distance $d_k^2(\mathbf{x})$ to all faultline segments $\mathbf{s}_k$.
* Evaluate faultline probability $\mathcal{P}(\mathbf{x}) = 1 - \prod_k \left(1 - p_0 \exp(-d_k(\mathbf{x}) / \sigma_{\text{strata}})\right)$.
* If uniform sample $u_1 < \mathcal{P}(\mathbf{x})$ and `_detect_flank_occlusions(x, y, w, l, layer, board)` is `False` (and coordinate does not overlap existing `Strata` or `Fluid` emitters):
* Resolve `tile = board.tile(layer, Position(x + w // 2, y + l // 2))` and `strata_id = strata_index.resolve(tile.id, season)`.
* Sample `formation = strata_index.sample_formation(strata_id, u_2)`.
* Spawn via `board.cradle.spawn_strata(...)`.





###### Goal: Perimeter & Elevation Physics Integration

Update `Perimeter.extract` (`src/app/services/generators/game/perimeter.py`) so `Strata` participate in both Tier $0$ static architecture hulls and Tier $E + 1$ elevated platform contours:

```python
# src/app/services/generators/game/perimeter.py
# Inside Perimeter.extract:
# 2. Map Elevated Substrates (Platform decks, Stair inclines, and Strata mesas/buttes at E > base_e)
if elevation is not None and elevation > 0:
    strata_list = board.instances(AssetInstances.STRATA.value, layer)
    for strata in strata_list:
        base_e = strata.elevation
        if elevation > base_e and elevation in strata.hitbox.elevations(strata.properties, strata.state):
            x1 = int(strata.state.position.x)
            y1 = int(strata.state.position.y)
            rects.append((x1, y1, x1 + strata.dimensions.w, y1 + strata.dimensions.l))

```

In `CollisionMechanics._traverse_stairs`, include `strata` where `state.formation == Formations.BUTTES.value`:

* Entering through the open `DOWN` face with upward velocity ($v_y < 0$) transitions `asset.state.elevation += strata.state.delta`.
* Exiting through the `DOWN` face from $E + 1$ with downward velocity ($v_y > 0$) transitions `asset.state.elevation -= strata.state.delta`.

##### Tasks

**1. Task: Semantics, Models, and Schema Registration**

*Objective*: Induct `Strata` and `Formations` into the application's semantic enumerations, Pydantic validation schemas, and property/state dataclasses.

* [] Subtask: Add `STRATA = "strata"` to `AssetInstances` and `Relations` in `src/app/static/semantics.py`.
* [] Subtask: Add `Formations(Enum)` (`MESAS = "mesas"`, `SPIRES = "spires"`, `BUTTES = "buttes"`) and `FORMATION = "formation"` to `FrameTypes` and `HitboxTypes` in `src/app/static/semantics.py`.
* [] Subtask: Refactor `src/app/models/state/assets/geography.py` to define base `GeographyState(AssetState)`, `ShorelineState(GeographyState)`, and `StrataState(GeographyState)` with `formation: Formations` and `delta: int = 1`.
* [] Subtask: Update `GeographyProperties` in `src/app/models/properties/assets.py` to default `mass: int = 0` for `Strata` (or configure `mass: 0` in YAML), support `hitboxes: Optional[Union[Dict[str, List[Hitbox]], List[Hitbox]]]`, and add `probabilities: Optional[Dict[str, float]] = None`.
* [] Subtask: Register `strata` on `GeographyPropertiesSchema` and `GeographyStateSchema` in `src/app/models/properties/__init__.py` and `src/app/models/state/__init__.py`.

**2. Task: Relational Index, Recipes, and Asset Configuration**

*Objective*: Implement `StrataIndex` for tile-to-strata resolution and relative formation probability sampling, and configure `Strata` recipes and property files.

* [] Subtask: Create `src/app/game/logic/relations/strata.py` implementing `StrataIndex` (`from_properties`, `resolve`, `sample_formation`) and export it in `src/app/game/logic/relations/__init__.py`.
* [] Subtask: Add `geography.strata` recipe (`frame: formation`, `animation: none`, `hitbox: formation`) to `src/data/config/recipes/main.yaml`.
* [] Subtask: Map `strata` to `Substrates.STANDARD (0)` in `src/data/config/materials/main.yaml` and `MaterialIndex`.
* [] Subtask: Configure baseline `Strata` asset properties (`mass: 0`, `tile`, `dimensions`, `thickness`, `probabilities`) in `src/assets/geography/main.yaml`.

**3. Task: ECS Frame, Hitbox, and Cradle Instantiation**

*Objective*: Implement the `FormationFrame` and `FormationHitbox` strategies and wire `Cradle` to spawn `Strata` instances.

* [] Subtask: Implement `FormationFrame` in `src/app/assets/frames/geography.py` to index `(Formation, Season)` crops and cache frame keys on `state._keys`.
* [] Subtask: Implement `FormationHitbox` in `src/app/assets/hitboxes/geography.py` to emit `[E, E + 1]` elevations for `mesas`/`buttes`, `[E]` for `spires`, and formation-specific collision hitboxes per tier.
* [] Subtask: Register `FormationFrame` and `FormationHitbox` in `AssetFactory` component lookup tables.
* [] Subtask: Add `strata` to `SpawnableGroup` (`src/app/models/groups.py`) and implement `Cradle.spawn_strata` in `src/app/services/generators/game/cradle.py`.

**4. Task: Faultline Extraction and Probabilistic Synthesis in `Cartographer**`

*Objective*: Expand `Cartographer` (and `libs.core.math.geometry` if needed) to detect `Environ` tile faultlines, compute localized faultline probability fields, and synthesize `Strata` formations.

* [] Subtask: Implement `Cartographer._collect_faultlines(layer, board)` to extract shared interior boundary segments between adjacent `Environ` tiles.
* [] Subtask: Implement faultline distance and screened probability evaluation $\mathcal{P}(\mathbf{x})$ in `Cartographer` (using segment distance math).
* [] Subtask: Implement `Cartographer.generate_strata(layer, board, strata_index, seed=None)` to sample non-occluded coordinates, resolve `StrataIndex` formations (`P(spires) > P(mesas) > P(buttes)`), and spawn `Strata` via `Cradle`.
* [] Subtask: Implement `Cartographer.purge_strata(layer, board)` for clean layer disposal.

**5. Task: Board, Perimeter, Physics, and Hydration Integration**

*Objective*: Connect spawned `Strata` to `Board` spatial queries, `Perimeter` contour generation, `CollisionMechanics` incline transitions, `SeasonMechanics`, and `Migrator` hydration.

* [] Subtask: Add `board.strata(layer=None)` and include `geography.strata` ($m = 0$) in `board.weights(layer, elevation)` and `board.obstacles(layer, elevation)`.
* [] Subtask: Update `Perimeter.extract` in `src/app/services/generators/game/perimeter.py` to include `mesas` and `buttes` at $E + 1$ in elevated deck contours and `Strata` at $E$ in static obstacle hulls.
* [] Subtask: Update `CollisionMechanics._traverse_stairs` and `MotionMechanics` surface support checks to handle `buttes` southern incline transitions ($\Delta E = \pm 1$) and `mesas`/`buttes` $E + 1$ surface walking.
* [] Subtask: Update `SeasonMechanics` to synchronize `state.season` and clear `state._keys` on active `Strata` upon `SeasonEvent`.
* [] Subtask: Wire `Cartographer.generate_strata` into `Migrator` Phase 2 hydration strictly after `Tiles` ingestion and prior to `Perimeter.generate` and `FluidMechanics`.

**6. Task: Test Fixture & Unit Test Suite Induction**

*Objective*: Induct `StrataIndex` and procedural `Strata` generation into `tests/unit/fixtures` and verify faultline synthesis, formation probabilities, and multi-tier hitboxes.

* [] Subtask: Add `mock_strata_index` and update `mock_relations`, `mock_spawnables`, and `mock_board` in `tests/unit/fixtures/structures.py` and `tests/unit/fixtures/components.py`.
* [] Subtask: Add a secondary `Environ` tile region (`highland`) to `src/data/state/world-testbed/tiles/tiles.yaml` so `world-testbed` naturally forms an interior faultline with `temperate`.
* [] Subtask: Add unit tests in `tests/unit/app/services/generators/game/test_cartographer.py` verifying faultline extraction, probability localization around faultlines, empirical formation ordering (`spires > mesas > buttes`), and `FormationHitbox` elevation resolution.