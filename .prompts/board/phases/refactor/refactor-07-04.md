#### Refactor: Phase 07.04 - Materialization

**Overview**

Eliminate `Strut` configuration boilerplate and asset proliferation by reorganizing `Strut` sheets into 2D `(Blueprint x Material)` atlases parameterized by ordered Material Genera (`organics`, `geologics`, `metallics`, `chromatics`) and Blueprint Schemas (`buildings`, `corridors`, `columns`). Decouple crafting cost from static `CraftProperties` into a dedicated `app.services.markets.Materializer` service, and introduce strategy-driven multiplication (`simple` 2D tiling and `expansion` vertical shaft interpolation) across `Decomposer` and `Migrator`.

##### Specification

1. **Ordered Material Space (`app.config.enums`)**:

Order within each partition is strict and determines the horizontal column index $c \in [0, C)$ in a Strut Sheet atlas:

* **`organics`**: `(0: cotton, 1: thatches, 2: wood)`
* **`geologics`**: `(0: limestone, 1: feldspar, 2: granite, 3: marble)`
* **`metallics`**: `(0: copper, 1: iron, 2: gold)`
* **`chromatics`**: `(0: neutral, 1: blue, 2: red, 3: yellow, 4: green)`
* *Host Constraint*: Any Strut declaring `genus: chromatics` must declare a `host` material restricted to the `organics` partition (`cotton`, `thatches`, `wood`). Non-chromatic genera default `host` to `None`.

2. **Ordered Blueprint Space & Multiplication Strategies (`app.config.enums`)**:

Order within each partition is strict and determines the vertical row index $r \in [0, R)$ in a Strut Sheet atlas:

* **`buildings`** (`strategy: simple`): `0: floors`, `1: walls`, `2: flats`, `3: roofs`, `4: paths`, `5: halls`
* **`corridors`** (`strategy: simple`): `0: solids`, `1: stripes`, `2: designs`
* **`columns`** (`strategy: expansion`):
    `0: crowns`, `1: shafts`, `2: bases`

3. **Curated Strut Sheet Registry (`/src/assets/crafts/struts/main.yaml`)**:

| Strut ID | Unit Dimensions ($w \times l$) | Blueprint Schema (Rows) | Material Genus (Columns) | Host Material |
| --- | --- | --- | --- | --- |
| `hut` | $96 \times 96$ | `buildings` (6) | `organics` (3) | `None` |
| `home` | $96 \times 96$ | `buildings` (6) | `geologics` (4) | `None` |
| `store` | $96 \times 96$ | `buildings` (6) | `geologics` (4) | `None` |
| `suburb` | $96 \times 96$ | `buildings` (6) | `chromatics` (5) | `wood` |
| `mansion` | $96 \times 96$ | `buildings` (6) | `geologics` (4) | `None` |
| `hallway` | $96 \times 96$ | `corridors` (3) | `chromatics` (5) | `wood` |
| `carpet` | $96 \times 96$ | `corridors` (3) | `chromatics` (5) | `cotton` |
| `avenue` | $32 \times 32$ | `corridors` (3) | `geologics` (4) | `None` |
| `pillar` | $16 \times 32$ | `columns` (3) | `geologics` (4) | `None` |
| `tower` | $64 \times 64$ | `columns` (3) | `geologics` (4) | `None` |

4. **Market Service (`app.services.markets.Materializer`)**:

* `cost` is removed from `CraftProperties` and `Decomposer`.
* Material valuation weights ($\mu_{\text{mat}}$) and blueprint structural volume factors ($\delta_{\text{blueprint}}$) are loaded from `/src/data/config/markets/main.yaml`.
* `Materializer.cost(dimensions, material, blueprint, multiple=None)` dynamically computes `[Cost(item, quantity)]`.

##### Architectural Analysis I

###### 1. Composition Boilerplate Compression via `Decomposer.multiply()`

In `Composition C002` (`regalia-galleria`), paving the $768 \times 288$ central concourse required 24 discrete `support-granite-border` entries and 6 `wall-palace` entries. By equipping `StrutState` with `multiple: Multiple(nx, ny)` and invoking `Decomposer.multiply()` inside both `Decomposer._unpack_node()` (for root/branch struts) and `Decomposer._unpack_components()` (for child components), repeated structural definitions collapse into single parameterized declarations. Because `Decomposer.multiply()` emits unit `Asset` objects with `Multiple(1, 1)` prior to `Board.add()`, `Screen.draw()` Painter's Algorithm sorting, `Perimeter` contour generation, `CollisionMechanics`, and `Board.serialize()` require zero downstream changes.

###### 2. Atlas Dimension Normalization vs. `MaterialHitbox`

`Registry` crop indexing and `Asset.dimensions` require each `Asset` ID to declare a single bounding canvas size `Dimensions(w, l)`. Standardizing cell dimensions per Strut Sheet allows uniform 2D crop indexing across `(column * w, row * l, w, l)`.

##### User Review I

This is the correct direction, but it can be further refined prior to implementation. I have conducted an exhaustive analysis of the LPC Asset Database. I have discovered the following relationships can be extracted to further clarify Struts and formalize their usage.

###### Side Note: Cost

Cost is now extraneous as a property. It can be derived from the area, material, material cost and blueprint. Remove cost property from Crafts, move material cost table to configuration, and remove all cost functions from the Decomposer. Need a new type of service, `app.services.markets`, and a new `Materializer` service. Receives cost configuration during bootstrap, exposes an interface `cost()` that accepts Dimensions, Material, Blueprint and then calculates the list of Costs, e.g. `[ Cost(material, amount) ]`. Remove cost methods from the Decomposer.

###### Main Note: Reatlasing

**Rebrand**:

To align with the simulation theme, the following relabellings should occur,

* Renaming `brick` to `feldspar`.
* Renaming `stone` to `limestone`

In addition, many materials and assets have been pruned.

**Idea**

Struts declare Material genus (`organics`, `geologics`, `metallics`, `chromatics`) and Blueprint schema (`building`, `corridor`, `tower`) axes in their properties. Rather than enumerating every single Material or Blueprint, they will refer to partitions of each space.

**Reorganization**

By curating combinations of different Asset files in the LPC database, the following sheets have been constructed to conform to regular schemas.

* Strut Sheets:
    * id: hut (96px by 96px)
        * Rows (Blueprint: Building): floors, walls, flats, roofs, paths, halls
        * Columns (Material: Organics): cotton, thatches, wood
    * id: home (96px by 96px)
        * Rows (Blueprint: Building): floors, walls, flats, roofs, paths, halls
        * Columns (Material: Geologics): limestone, feldspar, granite, marble
    * id: store (96px by 96px)
        * Rows (Blueprint: Building): floors, walls, flats, roofs, paths, halls
        * Columns (Material: Geologics): limestone, feldspar, granite, marble
    * id: suburb (96px by 96px)
        * Rows (Blueprint: Building): floors, walls, flats, roofs, paths, halls
        * Columns (Material: Chromatics, Host: Wood): neutral, blue, red, yellow, green
    * id: mansion (96px by 96px)
        * Rows (Blueprint: Building): floors, walls, flats, roofs, paths, halls
        * Columns (Material, Geologics): limestone, feldspar, granite, marble
    * id: hallway (96px by 96px)
        * Rows (Blueprint: Corridor): solids, stripes, designs
        * Columns (Material: Chromatics, Host: Wood): neutral, blue, red, yellow, green
    * id: carpet (96px by 96px)
        * Rows (Blueprint: Corridor): solids, stripes, designs
        * Columns (Material: Chromatics, Host: Cotton): neutral, blue, red, yellow, green
    * id: avenue (32px by 32px)
        * Rows (Blueprint: Corridor): solids, stripes, designs
        * Columns (Material: Geologics): limestone, feldspar, granite, marble
    * id: pillar (16px by 32px)
        * Rows (Blueprint: Column): crowns, shafts, bases
        * Columns (Material: Geologics): limestone, feldspar, granite, marble
    * id: tower (64px by 64px)
        * Rows (Blueprint: Column): crowns, shafts, bases
        * Columns (Material: Geologics): limestone, feldspar, granite, marble

**Material Space**

Order matters, i.e. Material space is ordered along its partitions.

Partitions:

* Organics: `cotton`, `thatches`, `wood`,
* Geologics: `limestone`, `feldspar`, `granite`, `marble`
* Metallics: `copper`, `iron`, `gold` (Not yet culled from database, but from inspection, it is possible to impose this partition on several blueprints and extract several other Strut assets.)
* Chromatics (Dyes): `neutral`, `blue`, `red`, `yellow`, `green`
    * If a Strut declares a Chromatic as its Material, then it must specify a Host Material. This is encapsulated within a Material model that defaults `host` to `None`. Only Organic Material can be a Host Material for Chromatics.

**Blueprints**

Order matters, i.e. Blueprint space is ordered along its partitions.

Partitions:

* Building Blueprint (Simple Multiplication Strategy):
    * `floors`: Interior ground surfaces.
    * `walls`: Exterior support surfaces.
    * `flats`: Elevated support surfaces.
    * `roofs`: Building enclosures.
    * `paths`: Exterior ground surfaces.
    * `halls`: Interior support surfaces.
* Corridor Blueprint (Simple Multiplication Strategy):
    * `solids`: Support surfaces.
    * `stripes`: Support surfaces.
    * `designs`: Support surfaces.
* Column Blueprint (Expansion Multiplication Strategy):
    * `crowns`: Building enclosures.
    * `shafts` (Multiplicands): Elevated surfaces.
    * `bases`: Ground level surface.

**Multiplication Strategies**

* `simple`: Any blueprint can be multiplied.
* `expansion`:
    * `blueprint: columns`:  `base` and `crown` cannot be multiplied and are fixed as caps along the vertical dimension of the Asset, where `base.position.y > crown.position.y`; `shaft` multiplicand expands to make the Asset contiguous.

##### Architectural Analysis II

###### 1. 2D `(Blueprint, Material)` Matrix Indexing in `MaterialFrame`

Because both the Blueprint schema and Material genus form strictly ordered partitions, a single Strut Sheet `.png` of cell dimensions $(w, l)$ is a 2D matrix of $R \times C$ cells:

* Row index $r \in [0, R)$ maps to `BLUEPRINT_PARTITIONS[properties.blueprints][r]`.
* Column index $c \in [0, C)$ maps to `MATERIAL_PARTITIONS[properties.material.genus][c]`.
* Crop coordinate for `(blueprint, material)`:

$$\text{rect}(r, c) = (c \cdot w,\; r \cdot l,\; w,\; l)$$


* Canonical frame key: `f"{id}-{blueprint}-{material}"` (e.g., `mansion-walls-marble`, `carpet-designs-red`, `pillar-shafts-limestone`).

###### 2. Coplanar Priority & Passability Across Unified Strut Sheets

Unifying `floors`, `paths`, `walls`, and `halls` into a single `building` Strut Sheet (`home`, `mansion`, `hut`, `store`, `suburb`) introduces an important interaction with `Screen.draw()` and `CollisionMechanics`:

1. **Rendering Priority (`priority`)**: In `Screen.draw()`, ground substrates (`floors`, `paths`, `solids`, `stripes`, `designs`) must sort with `priority = -1` so characters and furniture standing at the same `ground_y` render above them, whereas upright walls (`walls`, `halls`, `bases`) sort with `priority = 0`. Because all rows of `mansion` share a single `CraftProperties` instance, `Asset` (or `Screen._sort`) should resolve substrate priority dynamically when `state.blueprint` belongs to `SUBSTRATE_BLUEPRINTS = {'floors', 'paths', 'solids', 'stripes', 'designs'}`.

2. **Blueprint-Segregated Hitboxes (`MaterialHitbox`)**: Passable surface rows (`floors`, `paths`, `solids`, `stripes`, `designs`, and column `crowns`/`shafts`) must emit `[]` from `hitbox.get()`, whereas structural obstruction rows (`walls`, `halls`, `bases`) emit active `List[Hitbox]`. By keying `CraftProperties.hitboxes` by blueprint partition (or defaulting to active hitboxes only on `OBSTACLE_BLUEPRINTS = {'walls', 'halls', 'bases'}` when `properties.hitboxes is None`), `floors` and `paths` on a `mass = 0` building sheet remain completely passable without needing separate property definitions.


###### 3. Column `expansion` Strategy & Perspective Baseline Anchoring

For `blueprints: columns` (`pillar`, `tower`), `MultiplicationStrategies.EXPANSION` constructs a vertical column from top to bottom along the positive $y$-axis (`base.position.y` greater than `crown.position.y`):

* Given deployment origin $(x_0, y_0)$ and vertical shaft multiplier $n_y \ge 1$ (and optional horizontal count $n_x \ge 1$):

1. **`crowns` (Top Cap)**: Placed at $(x_0 + i_x \cdot w,\; y_0)$ with `blueprint = 'crowns'`.
2. **`shafts` (Multiplicand)**: $n_y$ contiguous segments placed at $(x_0 + i_x \cdot w,\; y_0 + (k + 1) \cdot l)$ for $k \in [0, n_y)$ with `blueprint = 'shafts'`.
3. **`bases` (Ground Cap)**: Placed at $(x_0 + i_x \cdot w,\; y_0 + (n_y + 1) \cdot l)$ with `blueprint = 'bases'`.


* **Perspective Baseline Alignment (`anchor`)**: In top-down 2.5D rendering, a Sprite walking behind the column's physical footprint (`base`) has `sprite.ground_y` less than `base.ground_y`, but potentially greater than `crown.y + l` or `shaft.y + l`. To prevent a Sprite walking behind a pillar from rendering in front of its upper shaft and crown, `Decomposer.multiply()` automatically sets `anchor = (base.y + l) - (segment.y + l)` on each generated `crown` and `shaft` unit so the entire vertical column sorts atomically at `base.ground_y`.

###### 4. `Materializer` Cost Derivation (`app.services.markets`)

Removing `cost` from `CraftProperties` and `Decomposer` centralizes all economic valuation inside `app.services.markets.Materializer`:

* **Normalized Area ($N$)**:
* For `simple` strategy: $N = \frac{w \cdot l}{1024} \cdot (n_x \cdot n_y)$.
* For `expansion` strategy (`columns`): A column of $n_y$ shafts comprises $(n_y + 2)$ total cells (1 crown + $n_y$ shafts + 1 base) per column, so $N = \frac{w \cdot l}{1024} \cdot n_x \cdot (n_y + 2)$.


* **Chromatic + Host Resolution**:
* If `material_prop.genus != 'chromatics'`:

$$\text{Cost} = \Big[\;\text{Cost}\big(\text{item} = \text{state.material},\; \text{quantity} = \max(1, \text{round}(N \cdot \mu_{\text{material}} \cdot \delta_{\text{blueprint}}))\big)\;\Big]$$


* If `material_prop.genus == 'chromatics'`:
The host organic material (`wood` or `cotton`) provides the structural mass, while non-neutral chromatic selections add a dye cost:

$$\text{Host Cost} = \text{Cost}\big(\text{item} = \text{material\_prop.host},\; \text{quantity} = \max(1, \text{round}(N \cdot \mu_{\text{host}} \cdot \delta_{\text{blueprint}}))\big)$$



If `state.material != 'neutral'`, append $\text{Cost}(\text{item} = \text{state.material},\; \text{quantity} = \max(1, \text{round}(N \cdot \mu_{\text{chromatic}})))$.

##### User Review II

All of the code. tasking and goals look good; however there is a latent bug you touched on that I would like to drill down on.

###### Elevation vs Priority vs Anchors

For [Architectural Analysis #2.1](#2-coplanar-priority--passability-across-unified-strut-sheets), this is a problem that has occured to me. However, priority only matters when the elevations and vertical displacements are equal; it is the fallback tie-breaker. Your solution handles an important edge case, but not the main solution set.  

For dynamic Assets, priority only gets evaluated in the cases where the Sprite happens to be at the same vertical displacement as the static Asset; it is mainly used in conjunction with `anchor` to lock the rendering order of static assets in Compositions. While your solution solves the static case, it does not solve the dynamic case, where a Sprite is walking on a surface in which it is wholly contained `sprite.state.position.y + sprite.dimensions.l < strut.state.position.y + strut.dimensions.l` AND `sprite.state.position.y > strut.state.position.y`. Consider a Strut with dimension `(400, 400)` and a Sprite with standard dimensions `(64, 64)`; once the Sprite passes the boundary, the surface will render on top of the Sprite (This actually currently occurs with Stairs, but I haven't logged the bug yet). Even with the priority resolving dynamically, this setup will not render this situtation correctly. The actual solution, if we go down this route, I believe, is to dynamically resolve the *`anchor`* and the `priority`; as the `anchor` is explicitly there to override vertical displacements so `priority` will be referenced. However, there is another solution to consider.

During Fluid and Geography development, a very similar problem occured and the following solution was implemented. It likely needs to be extended for Struts, as the core issue is "ground level" and "shoulder level" are not the same elevation.

The engine currently utilizes `SUBSTRATES` to ensure the rendering order of certain Assets. Enum is defined,

```python
# src/app/config/enums.py
class Substrates(int, Enum):
    ENVIRON         = -4 
    FLUIDS          = -3
    SHORELINES      = -2
    BRIDGES         = -1
```

Then settings are mapped,

```python
# src/app/config/settings.py
SUBSTRATES: Final[dict[str, int]] = {
    AssetInstances.ENVIRON.value: Substrates.ENVIRON.value,
    AssetInstances.FLUIDS.value: Substrates.FLUIDS.value,
    AssetInstances.SHORELINES.value: Substrates.SHORELINES.value,
    AssetInstances.BRIDGES.value: Substrates.BRIDGES.value
}
"""Instance-keyed map of substrate elevations."""
```

And it is defined as the fallback in the Asset class,

```python
# src/app/assets/base.py
    class Asset:
        # ...
        @property
        def elevation(self) -> int:
            if self.state.elevation is not None:
                return self.state.elevation
            return settings.SUBSTRATES.get(self.taxonomy.instance, 0)
```

And all Hitboxes collapse negative elevations to elevation 0, so all substrates are effectively elevation 0 when collisions are evaluated,

```python
class StaticHitbox(HitboxSchema):
    def elevations(self, properties: AssetProperties, state: AssetState) -> List[int]:
        return [max(0, state.elevation if state.elevation is not None else 0)]
```

Consider this: what if, instead of jury-rigging the priorities or anchors to resolve dynamically, Strut blueprints were assigned and lazily-loaded Substrates? This has a problem that did not occur in the case of Fluids and Geography, insofar that Struts are fundamentally "detached" from elevations and can be deployed anywhere. However, much like Pseudo-State, the Decomposer could reference Pseudo-Substrates so the elevations of internal components are relatively specified.

The other option is to dynamically resolve the `anchor`/`priority` and the question becomes where. This seems the more complicated solution to me, as it involves Asset collisions, i.e. you have to know when a dynamic Asset is intersecting a Strut of a particular `blueprint`. This adds more conditional logic to collisions, which are already sufficiently complicated. However, this does not mean this way is not the solution. 

All of the tasks and goals are good as is, I believe, and do not require further modification, so consider this an addendum. 

##### Goals

###### Goal: Ordered Material & Blueprint Enumerations (`src/app/config/enums.py`)

Define the ordered partitions for `MaterialGenera` (`Organics`, `Geologics`, `Metallics`, `Chromatics`) and `BlueprintSchemas` (`BuildingBlueprints`, `CorridorBlueprints`, `ColumnBlueprints`), along with `MultiplicationStrategies`.

###### Goal: Property, State & Market Configuration Models (`properties.py`, `crafts.py`, `markets.py`)

Remove `cost` from `CraftProperties`, add `Material` (`genus`, `host`) and `blueprints`, define `StrutState` (`material`, `blueprint`, `multiple`), and add `MarketConfiguration` to `app.models.config`.

###### Goal: `Materializer` Service (`src/app/services/markets/materializer.py`)

Implement `Materializer` to compute crafting costs dynamically from `Dimensions`, `Material`, `Blueprint`, and `Multiple`, removing all cost logic from `Decomposer`.

###### Goal: 2D `MaterialFrame` & Blueprint-Aware `MaterialHitbox`

Implement `MaterialFrame` to index `(blueprint_row, material_col)` cells and `MaterialHitbox` to resolve collision geometry per blueprint partition.

###### Goal: Strategy-Driven `Decomposer.multiply()` (`simple` & `expansion`)

Implement `Decomposer.multiply()` to handle both 2D `simple` tiling (`buildings`, `corridors`) and vertical `expansion` capping (`columns`: `crown` at $y_0$, $n_y$ `shafts`, `base` at $y_0 + (n_y + 1)l$).

##### Tasks

**1. Task: Ordered Enumerations & Schema Models**

*Objective*: Codify the ordered `Material` genera, `Blueprint` schemas, `MultiplicationStrategies`, `StrutState`, and `CraftProperties` in the application models.

* [x] Subtask: Add `Materials`, `Organics`, `GeologicMaterials`, `Metallic`, `Chromatics`, `Blueprints`, `Buildings`, `Corridors`, `Columns`, `MultiplicationStrategies` to `src/app/config/enums.py`.
* [x] Add `MATERIAL_PARTITIONS`, `BLUEPRINT_PARTITIONS` and `BLUEPRINT_STRATEGIES`, `SUBSTRATE_BLUEPRINTS`, and `OBSTACLE_BLUEPRINTS` to `src/app/config/settings.py`.
* [x] Subtask: Update `src/app/models/properties.py` (and Pydantic adapters) to add `Material(genus, host)`, remove `cost` from `CraftProperties`, and add `material: Optional[Material]` and `blueprints: Optional[str]` to `CraftProperties`.
* [x] Subtask: Update `src/app/models/state/assets/crafts.py` to define `StrutState(PropertyState)` with `material: Optional[str]`, `blueprint: Optional[str]`, and `multiple: Optional[Multiple]`, and update `CraftStateInstances.struts` in `src/app/models/state/schemas.py`.

**2. Task: `app.services.markets` & `Materializer` Implementation**

*Objective*: Decouple cost data from Craft properties into `/src/data/config/markets/main.yaml` and implement the `Materializer` service.

* [x] Subtask: Create `src/app/models/config/markets.py` defining `Cost` and `MarketConfiguration`, and register `markets: MarketConfiguration` on `ConfigurationSchema`.
* [x] Subtask: Create `/src/data/config/markets/main.yaml` containing the rebranded material valuation factors ($\mu_{\text{mat}}$ for `organics`, `geologics`, `metallics`, `chromatics`) and blueprint factors ($\delta_{\text{blueprint}}$).
* [x] Subtask: Implement `Materializer` in `src/app/services/markets/materializer.py` with `cost(dimensions, material, blueprint, material_spec, blueprint_schema, multiple)` supporting chromatic host + dye decomposition and column expansion unit counts.
* [x] Subtask: Remove `_accumulate_cost`, `_aggregate_components_cost`, `cost`, and `bridge_cost` from `src/app/services/generators/game/decomposer.py`.
* [x] Subtask: Remove `cost` keys from all `/src/assets/crafts/**/*.yaml` files.

**3. Task: `MaterialFrame`, `MaterialHitbox` & Substrate Priority**

*Objective*: Implement 2D `(Blueprint, Material)` atlas indexing, blueprint-aware hitbox resolution, and substrate priority sorting.

* [x] Subtask: Implement `MaterialFrame` in `src/app/assets/frames/` to index `{id}-{blueprint}-{material}` at `(c * w, r * l, w, l)` and resolve `keys(id, state)` from `(state.blueprint, state.material)`.
* [x] Subtask: Implement `MaterialHitbox` in `src/app/assets/hitboxes/crafts.py` returning `[]` for passable blueprints (`floors`, `paths`, `solids`, `stripes`, `designs`, `crowns`, `shafts`) and active hitboxes for `OBSTACLE_BLUEPRINTS` (`walls`, `halls`, `bases`).
* [!: CANCELLED, SEE BELOW] Subtask: Update `Asset` / `Screen._sort` so `Strut` instances with `state.blueprint in SUBSTRATE_BLUEPRINTS` evaluate tertiary sort priority as `-1`.
* [x] Subtask: Register `MaterialFrame` and `MaterialHitbox` in `Factory` and `src/data/config/recipes/main.yaml`.

**4. Task: Strategy-Driven `Decomposer.multiply()` & `Migrator` Integration**

*Objective*: Implement `simple` and `expansion` multiplication strategies in `Decomposer.multiply()` and wire them into `Decomposer` and `Migrator`.

* [x] Subtask: Implement `Decomposer.multiply()` in `src/app/services/generators/game/decomposer.py` handling `simple` 2D grid expansion and `expansion` vertical column construction (`crown`, $n_y$ `shafts`, `base` with baseline `anchor` alignment).
* [x] Subtask: Update `Decomposer._unpack_node()` and `Decomposer._unpack_components()` to route `AssetInstances.STRUTS` through `self.multiply()`.
* [x] Subtask: Update `Migrator._build_generator()` in `src/app/services/orchestration/migrator.py` to route standalone `struts` state entries through `self.decomposer.multiply()`.
* [!] Subtask: Add unit tests covering `simple` multiplication, `expansion` column capping (`base.position.y` greater than `crown.position.y`), and `MaterialFrame` key generation.

**5. Task: Strut Sheet Re-Indexing & Composition Migration**

*Objective*: Replace legacy `/src/assets/crafts/struts/**` indices with the 10 curated 2D Strut Sheets and refactor existing Compositions to the new schema.

* [x] Subtask: Index `hut`, `home`, `store`, `suburb`, `mansion`, `hallway`, `carpet`, `avenue`, `pillar`, and `tower` in `/src/assets/crafts/struts/main.yaml` using `material: { genus, host }` and `blueprints`.
* [~] Subtask: Relocate non-Strut decor and bespoke structures (`decor`, `structures`) to their dedicated Craft instances.
* [!] Subtask: Refactor `src/data/config/compositions/main.yml` (`C000`, `C001`, `C002`) and `/src/data/state/**` to use the new `(id, blueprint, material, multiple)` Strut schema.

##### Architectural Analysis III

###### 1. Why Dynamic `anchor`/`priority` Resolution Breaks Down

Let $S$ be a walkable surface Strut (`floors`, `paths`, `flats`, `corridors`) or `Stairs` with dimensions $(w_S, l_S)$, and let $P$ be a Sprite with dimensions $(w_P, l_P) = (64, 64)$ on the same elevation $E$. When $P$ stands on $S$ north of its southern edge:

$$S.y < P.y + P.l < S.y + S.l \implies \text{ground\_y}(P) < \text{ground\_y}(S)$$

Because `Screen._sort` evaluates the lexicographical tuple $(\text{elevation}, \text{ground\_y}, \text{priority})$, the secondary key $\text{ground\_y}$ is strictly unequal ($\text{ground\_y}(P) < \text{ground\_y}(S)$), so the tertiary key $\text{priority}$ is **never evaluated**.

Attempting to solve this dynamically by mutating $S.\text{state.anchor}$ when $P$ intersects $S$ introduces three structural failures:

1. **Multi-Body Contradiction (Non-Scalar Anchor)**: `state.anchor` is a single scalar on $S$. Suppose a static wall or table $W$ rests on floor $S$ at baseline $W.y + W.l = S.y + 32$, while a Sprite $P$ stands on $S$ at baseline $P.y + P.l = S.y + 80$. To render under $P$, $S$ only needs $\text{ground\_y}(S) \le S.y + 80$; if $S.\text{anchor}$ is mutated to match $P$, then $\text{ground\_y}(S) = S.y + 80 > \text{ground\_y}(W) = S.y + 32$, causing the floor $S$ to **overdraw the wall/table $W$**!
2. **Static `anchor = -S.dimensions.l` Failure on Stacked Substrates**: If $S$ statically sets `anchor = -S.dimensions.l` so $\text{ground\_y}(S) = S.y$, then a `carpet` (`corridors`, $l = 96$) placed at $y = 0$ on top of a `floor` (`buildings`, $l = 96$) at $y = 0$ shares the exact same baseline $\text{ground\_y} = 0$ and `priority = -1`. Worse, if a smaller rug ($l = 64$) is placed near the bottom of a large room floor ($l = 400$) at $y = 300$, its top edge $y = 300 > 0$ sorts above the floor, whereas if a long runner ($l = 400$, $y = 0$) is placed over a local floor slab ($l = 96$, $y = 96$), the floor slab has $\text{ground\_y} = 96 > \text{ground\_y}(\text{runner}) = 0$, causing the floor slab to **overdraw the carpet runner**.
3. **Physics Pipeline Pollution**: Walkable Strut surfaces (`floors`, `paths`, `corridors`) have no collision footprint (`NoHitbox` / empty hitboxes). Dynamically computing `anchor` on intersection would force `CollisionMechanics` or `MotionMechanics` to run AABB overlap checks against every passive floor and carpet tile every frame.

###### 2. Why `Substrates` Worked for Fluids/Geography—and Why `Asset.elevation` Conflated Two Axes

Look at how `Asset.elevation` is currently implemented in `src/app/assets/base.py`:

```python
@property
def elevation(self) -> int:
    if self.state.elevation is not None:
        return self.state.elevation
    return settings.SUBSTRATES.get(self.taxonomy.instance, 0)

```

This implementation conflates two orthogonal topological coordinates into a single integer:

1. **Macro-Elevation ($E \in \mathbb{Z}_{\ge 0}$)**: The discrete story or platform tier (`0`, `1`, `2`, ...) used by `HitboxSchema.elevations()`, `StairMechanics`, and `CollisionMechanics`.
2. **Intra-Tier Substrate ($\sigma \in \mathbb{Z}$)**: The rendering plane *within* macro-elevation $E$ (`environ = -4`, `fluids = -3`, `shorelines = -2`, `bridges = -1`, `standard = 0`).

Because `Asset.elevation` only checks `settings.SUBSTRATES` when `self.state.elevation is None`:

* Any asset whose `state.elevation` is explicitly hydrated to `0` (such as `Decomposer.orient()` setting `elevation=state.elevation` on `bridges`, or `Stairs` initialized with `elevation = 0`) **bypasses `settings.SUBSTRATES` entirely** and sorts at `0` alongside Sprites.
* Any surface deployed on an elevated platform (`state.elevation = 1`) cannot use a global negative `elevation` without falling underneath `elevation = 0` assets.

###### 3. The Exact Solution: Fibered `(elevation, substrate, ground_y, priority)` Sorting

Every macro-elevation tier $E \in \mathbb{Z}_{\ge 0}$ is a local stack of substrate planes $\sigma \in [-4, 0]$. By separating `Asset.elevation` (always $\ge 0$) from `Asset.substrate` (resolved lazily from `(instance, state.blueprint)` via `settings.SUBSTRATES`), the Painter's Algorithm sort key becomes:

$$\text{sort\_key}(A) = \Big(A.\text{elevation},\; A.\text{substrate},\; \text{ground\_y}(A),\; A.\text{properties.priority}\Big)$$

This resolves every static and dynamic case across all elevations without touching `CollisionMechanics` or `Decomposer` coordinate math:

| Plane ($\sigma$) | Enum Key | Assigned Instances & Strut Blueprints | Behavior at Macro-Elevation $E$ |
| --- | --- | --- | --- |
| `-4` | `Substrates.ENVIRON` | `tiles.environ` | Base terrain canvas at $E$. |
| `-3` | `Substrates.FLUIDS` | `effects.fluids` | Streams and pools at $E$. |
| `-2` | `Substrates.SHORELINES` / `SURFACES` | `geography.shorelines`, `struts` (`floors`, `paths`, `flats`) | Base architectural flooring and shorelines at $E$; always renders beneath overlays (`-1`) and upright entities (`0`) at $E$. |
| `-1` | `Substrates.OVERLAYS` | `crafts.bridges`, `crafts.stairs`, `struts` (`solids`, `stripes`, `designs`) | Carpets, hallway runners, bridges, and stairs at $E$; renders **above** `floors`/`paths` (`-2`) at $E$ regardless of dimensions, and **below** all Sprites/walls/furniture (`0`) at $E$. |
| `0` | `Substrates.STANDARD` | `sprites`, `players`, `objects`, `effects`, `decor`, `structures`, `platforms`, `railings`, `struts` (`walls`, `halls`, `bases`, `shafts`, `crowns`) | Sorted by $\text{ground\_y} = y + l + \text{anchor}$ and tied-broken by `priority`. |

> **Why `crowns` and `shafts` stay at `Substrates.STANDARD (0)**`: A Sprite walking *in front* of a pillar (`sprite.ground_y` greater than `base.ground_y`) must occlude the pillar's shaft/crown, whereas a Sprite walking *behind* the pillar (`sprite.ground_y` less than `base.ground_y`) must be occluded by the pillar's shaft/crown. Keeping `bases`, `shafts`, and `crowns` at $\sigma = 0$ while locking `shaft` and `crown` anchors to `base.ground_y` in `Decomposer.multiply()` preserves true 2.5D occlusion in both directions.

##### Task

###### Relative Intra-Tier `Substrates` (`Asset.substrate` & `Screen._sort`)

Previously, `Asset.elevation` returned negative `settings.SUBSTRATES` values only when `state.elevation is None`. Because Struts, Stairs, and Bridges can be deployed at arbitrary macro-elevations ($E \in \{0, 1, 2, \dots\}$) and receive explicit `state.elevation` integers during `Decomposer` hydration, intra-tier substrate ordering must be orthogonal to `state.elevation`.

1. **`Substrates` Enumeration (`src/app/config/enums.py`)**:

```python
class Substrates(int, Enum):
    ENVIRON    = -4
    FLUIDS     = -3
    SURFACES   = -2
    OVERLAYS   = -1
    STANDARD   =  0
```

2. **Blueprint & Instance Substrate Mapping (`src/app/config/settings.py`)**

```python
SUBSTRATES: Final[dict[str, int]] = {
    AssetInstances.ENVIRON.value: Substrates.ENVIRON.value,
    AssetInstances.FLUIDS.value: Substrates.FLUIDS.value,
    AssetInstances.SHORELINES.value: Substrates.SHORELINES.value,
    AssetInstances.BRIDGES.value: Substrates.OVERLAYS.value,
    AssetInstances.STAIRS.value: Substrates.OVERLAYS.value,
    BuildingBlueprints.FLOORS.value: Substrates.SURFACES.value,
    BuildingBlueprints.PATHS.value: Substrates.SURFACES.value,
    BuildingBlueprints.FLATS.value: Substrates.SURFACES.value,
    CorridorBlueprints.SOLIDS.value: Substrates.OVERLAYS.value,
    CorridorBlueprints.STRIPES.value: Substrates.OVERLAYS.value,
    CorridorBlueprints.DESIGNS.value: Substrates.OVERLAYS.value,
}
```


3. **4-Key Lexicographical Sort (`src/app/game/screen.py`)**:

$$\text{sort\_key}(A) = \Big(A.\text{elevation},\; A.\text{substrate},\; \text{ground\_y}(A),\; A.\text{properties.priority}\Big)$$

At any macro-elevation $E$, `SURFACES (-2)` (`floors`, `paths`, `flats`) render first, `OVERLAYS (-1)` (`carpets`, `hallways`, `avenues`, `bridges`, `stairs`) render second, and `STANDARD (0)` (`walls`, `halls`, `columns`, `sprites`, `objects`) sort by `ground_y` and `priority` on top.

**Addendum**

* [x] Subtask: Add `Substrates.SURFACES (-2)` and `Substrates.OVERLAYS (-1)` to `src/app/config/enums.py`, map surface/corridor blueprints and `stairs` in `settings.SUBSTRATES`, expose `Asset.substrate` on `src/app/assets/base.py`, and update `Screen._sort` in `src/app/game/screen.py` to sort by `(asset.elevation, asset.substrate, ground_y, asset.properties.priority)`.

##### User Review III

I believe this is now the correct implementation. However, looking backwards, this nows means Bridge, Railings, Platforms  and Stairs have to be refactored; while `cost` could simply be removed, this is an opportunity to simplify things and reduce sprawl. In addition, there are several prototypes that now have to be refined. Before moving on to user acceptance testing and unit testing, let's expand the phase scope to encompass the entire category of crafts.

I see now that what defines Crafts is their structural nature and the method by which they are arranged in an atlas must be a function of their design and purpose. 

In other words, the Frame schema of an Asset is related to the *Category* of a Asset. Frames in a Sprite Sheet represent Actions, Frames in a Resource represent Lifespan Stages, Frames in an Effect represent Periodicity, etc. Frames in Crafts must be atlased according to structural components. 

Properties exist to demarcate and provide a metric for Frame space; State exists to denote location in the space spanned by the properties; Animations are strategies for moving through that space; Frames and Animation are the underlying process (stuff) that is being abstracted and described by the logical terms *Properties* and *State*. 

Thus begins another reatlasing adventure. 

Review the notes section and then add more addendums to the tasking to accomodate the expansion of the scope.

###### Notes

- IMPORTANT: Deferring discussion and implementation of any modifications to Platforms to Phase 07.03, as Gravity will subsume and deprecate/subtantially alter Platforms.

**Current Recipes**

```yaml
# comments include state, which is hydrated via Pydantic validation.
recipes:
  crafts:
    bridges:
      frame: oriented
      animation: none
      hitbox: oriented
      # state: oriented
    platforms: 
      frame: single
      animation: none
      hitbox: elevated
      # state: platform
    railings:
      frame: oriented
      animation: none
      hitbox: oriented
      # state: oriented
    struts:
      frame: material
      animation: none
      hitbox: material
      # state: strut
    stairs:
      frame: directed
      animation: none
      hitbox: directed
      # state: stair
```

**Simple Cases**

After an inspection, the following atlases can be synthesized from the LPC asset database, 

- Bridges: (rows: orientations, columns: material)
    - Note: cotton = rope bridge.
- Railings: (rows: orientations, columns: material)
- Stairs: (rows: directions, columns: material)

While having the same atlasing schema, Bridges and Railings serve different functional purposes; Bridges suppress Fluids fields while Railings serve as physical obstructions.

* Bridge Sheets
    * id: arch (80px by 103px)
        * rows: horizontal, vertical
        * columns: limestone, feldspar, granite, marble
    * id: suspension (96px by 96px)
        * rows: horizontal, vertical
        * columns: cotton, thatches, wood
* Stair Sheets
    * id: steps
        * rows: up, left, right
        * columns: limestone, feldspar, granite, marble
* Railing Sheets
    * id: crenellation (32px by 32px)
        * rows: horizontal, vertical
        * columns: limestone, feldspar, granite, marble

These assest have been culled from the database. It also appears the following is true, though the assets have yet to be formatted:

- Railings can be extracted along the Metallic and Chromatic-Wood partitions.
- Stairs can be extracted along the Metallic and Chromatic-Wood partitions.

This is mentioned only to ensure the Assets are properly abstracted, i.e. they support the same Material partitions,.

**Complex Case**

Some Railing Asset files are more complex than I initially thought. The current implementation of Railings in the game is actually ignoring a good deal of information contained in some of the raw frames. First, the purely orientable (horizontal-vertical) Assets can remain in the Railing Instance, but a few need split off into a separate *Enclosure* Instance and given further specification.

Enclosures are abstractions of fencing. They require a special MultiplicationStrategy, similar to the Expansion strategy for Columns, but in two dimensions and with special attention paid to hitboxes. Here is how Enclosure atlasing works:

- Enclosures from a continuous perimeter around the edge of the image. There are north, east, south, west faces. 
- The north-south faces are end caps for vertical multiplication, where the space between is extended. Similarly, the west-east faces are end caps for horizontal multiplication. Note: the west-east edge are "shaft" of the north-south caps and the north-south edge are the "shaft" of the east-west edge. 
- Whereas Columns were contiguous hitboxes, so their hitboxes could be multiplied, here the situtation is different, as the Enclosure is a perimeter, with the space enclosed open to movement. Their hitboxes will need special handling.

**Other Notes**

- Stairs are atlased by direction, but do not have a `down` direction, due to the LPC top-down perspective. Current implementation sidesteps this by just having an empty frame in the atlas, but this should be optimized.
- I don't see any use for `blueprints` in the Stairs, Bridge or Railings Instances. It will need to go unspecified for those categories. This is usually an indicator of an incorrect data model. Analyze the problem.

##### Architectural Analysis IV

###### 1. Data Model Diagnosis: Why `blueprints` Appeared Unused on `Bridges`, `Railings`, and `Stairs`

In the Ontology ECS architecture (`01-assets.md#asset-taxonomy`), **Category maps to Properties (`category -> properties`)** while **Instance maps to `(frame, animation, hitbox, state)**`.

* **The Symptom**: In the initial draft, `CraftProperties` declared `blueprints: Optional[str]`, which was populated for `struts` (`buildings`, `corridors`, `columns`) but left `None` for `bridges`, `railings`, and `stairs`. Meanwhile, `bridges` and `railings` relied on `OrientedFrame` / `OrientedHitbox` (`state.orientation`), and `stairs` relied on `DirectedFrame` / `DirectedHitbox` (`state.direction`).
* **Root Cause**: `OrientedFrame` and `DirectedFrame` hardcoded the row metric of the Craft atlas inside the `Frame` strategy instead of reading the metric from `CraftProperties`, while `OrientedState` (`orientation`), `StairState` (`direction`), and `StrutState` (`blueprint`) used three different field names to denote the exact same coordinate: **the row index in the Craft's structural partition**.

**The Unified Craft Metric**

Every multi-material Craft atlas is a 2D Cartesian product of **Structural Blueprint Rows ($R$)** and **Material Genus Columns ($C$)**:

$$
\text{Atlas}(id) = \text{BLUEPRINT\_PARTITIONS}[\text{properties.blueprints}] \times \text{MATERIAL\_PARTITIONS}[\text{properties.material.genus}]
$$

By recognizing that `orientations` (`horizontal`, `vertical`), `inclines` (`up`, `left`, `right`), and `enclosures` (`north`, `east`, `south`, `west`) **are** `BlueprintSchemas`:

1. **`CraftProperties.blueprints` is mandatory across all materialized Crafts**:
    * `struts`: `buildings` | `corridors` | `columns`
    * `bridges`: `orientations`
    * `railings`: `orientations`
    * `enclosures`: `enclosures`
    * `stairs`: `inclines`
2. **`OrientedFrame`, `DirectedFrame`, `OrientedHitbox`, and `DirectedHitbox` are deprecated and deleted**: A single `MaterialFrame` and a single `MaterialHitbox` service every `Strut`, `Bridge`, `Railing`, `Enclosure`, and `Stair` in the game.
3. **`Decomposer.orient()` and `OrientedAssets` are deprecated and deleted**:
`Decomposer.multiply()` handles all Craft expansion via `BLUEPRINT_STRATEGIES[properties.blueprints]`.

**Unified Recipe Table**

Every materialized Craft instance (`struts`, `bridges`, `railings`, `enclosures`, `stairs`) shares the identical component recipe `(frame: material, animation: none, hitbox: material)`.

| Craft Instance | `properties.blueprints` | Row Partition ($r \in [0, R)$) | Multiplication Strategy | Substrate ($\sigma$) | Mass ($m$) |
| --- | --- | --- | --- | --- | --- |
| `struts` (building) | `buildings` | `floors`, `walls`, `flats`, `roofs`, `paths`, `halls` | `simple` ($n_x \times n_y$) | `-2` (surfaces) / `0` (walls) | `0` |
| `struts` (corridor) | `corridors` | `solids`, `stripes`, `designs` | `simple` ($n_x \times n_y$) | `-1` (`OVERLAYS`) | `0` |
| `struts` (column) | `columns` | `crowns`, `shafts`, `bases` | `expansion` ($n_x \times (n_y + 2)$) | `0` (`STANDARD`) | `0` |
| `bridges` | `orientations` | `horizontal`, `vertical` | `oriented` ($n_x \times 1$ or $1 \times n_y$) | `-1` (`OVERLAYS`) | `-1` (Sensor) |
| `railings` | `orientations` | `horizontal`, `vertical` | `oriented` ($n_x \times 1$ or $1 \times n_y$) | `0` (`STANDARD`) | `0` |
| `enclosures` | `enclosures` | `north`, `east`, `south`, `west` | `perimeter` ($2(n_x + n_y + 2)$) | `0` (`STANDARD`) | `0` |
| `stairs` | `inclines` | `up`, `left`, `right` | `simple` ($n_x \times n_y$) | `-1` (`OVERLAYS`) | `-1` (Sensor) |
| `platforms` | *Deferred to Phase 07.03* | *N/A* | *N/A* | `0` (`STANDARD`) | `0` |


###### 2. `Stairs` Atlas Optimization: Eliminating the `down` Row

In top-down 2.5D projection, a south-facing staircase is traversed bidirectionally along the $y$-axis:

* Moving north (`vy < 0`) across `blueprint == 'up'` transitions `elevation += delta`.
* Moving south (`vy > 0`) across the same `blueprint == 'up'` transitions `elevation -= delta`.

By defining `InclineBlueprints = ('up', 'left', 'right')` (3 rows instead of 4), the empty/truncated `down` row is eliminated from the `steps` atlas, reducing Stair VRAM footprint by 25% and removing the dead `direction == 'down'` branch from `StairMechanics`.

###### 3. `Enclosures`: Reciprocal 2D Perimeter Expansion & Hitbox Geometry

An `Enclosure` represents a closed rectangular perimeter (fences, palisades, walled paddocks) with an open interior. Its atlas rows are partitioned by `EnclosureBlueprints = ('north', 'east', 'south', 'west')`.

1. **Reciprocal Cap/Shaft Topology (`MultiplicationStrategies.PERIMETER`)**: Given deployment origin $(x_0, y_0)$, cell dimensions $(w, l)$, and `multiple = Multiple(nx, ny)` where $(n_x, n_y)$ specifies the interior span between opposing caps:
    * Total bounding footprint is $(n_x + 2)w \times (n_y + 2)l$ across grid indices $i_x \in [0, n_x + 1]$ and $i_y \in [0, n_y + 1]$.
    * **Horizontal Span (`north` at $i_y = 0$, `south` at $i_y = n_y + 1$)**: Spawned across $i_x \in [0, n_x + 1]$. Here, `north` and `south` act as the vertical end caps at the top and bottom of the enclosure while repeating horizontally as the "shafts" between the `west` and `east` boundaries.
    * **Vertical Span (`west` at $i_x = 0$, `east` at $i_x = n_x + 1$)**: Spawned across $i_y \in [0, n_y + 1]$. Here, `west` and `east` act as the horizontal end caps at the left and right of the enclosure while repeating vertically as the "shafts" between the `north` and `south` boundaries.
    * **Open Interior ($i_x \in [1, n_x],\; i_y \in [1, n_y]$)**: Zero assets are instantiated in the interior cells, leaving the enclosed courtyard completely open to movement.
    * **Corner Closure**: At the four corners $(0, 0)$, $(n_x + 1, 0)$, $(0, n_y + 1)$, and $(n_x + 1, n_y + 1)$, the horizontal cap (`north`/`south`) and vertical cap (`west`/`east`) superimpose, joining their orthogonal strip hitboxes into sealed `L`-corners without requiring dedicated corner rows in the atlas.
2. **Perimeter Hitbox & 2.5D Baseline Anchoring**:
Each face declares a thin strip hitbox flush against its respective outer edge of the $(w, l)$ cell:
    * `north`: `Position(0, 0), Dimensions(w, t_n)`
    * `south`: `Position(0, l - t_s), Dimensions(w, t_s)`
    * `west`: `Position(0, 0), Dimensions(t_w, l)`
    * `east`: `Position(w - t_e, 0), Dimensions(t_e, l)`


Because the visual rail of the `north` face occupies the top strip $y \in [0, t_n]$ of its $(w, l)$ cell while the remaining $l - t_n$ pixels are transparent interior ground, `Decomposer.multiply()` sets `anchor = -(l - t_n)` on `north` segments. This aligns `ground_y` of the `north` fence to $y_0 + t_n$, ensuring any Sprite walking inside the enclosure ($P.y + P.l > y_0 + t_n$) renders **in front of** the `north` fence and **behind** the `south` fence ($\text{ground\_y} = y_0 + (n_y + 2)l$).

##### Goals

###### Goal: Unified Craft Blueprints, Strategies & Recipes (`enums.py`, `recipes/main.yaml`)

Expand `BlueprintSchemas`, `BLUEPRINT_PARTITIONS`, `MultiplicationStrategies`, and `OBSTACLE_BLUEPRINTS` to cover `struts`, `bridges`, `railings`, `enclosures`, and `stairs`.

###### Goal: Unified `StrutState` & `StairState` Models (`src/app/models/state/assets/crafts.py`)

Consolidate `OrientedState` into `StrutState` (used by `struts`, `bridges`, `railings`, and `enclosures`), and make `StairState` inherit from `StrutState` so every multi-material Craft specifies `(blueprint, material, multiple)`.

###### Goal: Unified `Decomposer.multiply()` (`simple`, `oriented`, `expansion`, `perimeter`)

Replace `Decomposer.orient()` with a strategy-driven `Decomposer.multiply()` supporting all four `MultiplicationStrategies`.

##### Tasks: Addendum II

**6. Task: Category-Wide Craft Frame, Hitbox & State Consolidation**

*Objective*: Unify `Bridges`, `Railings`, `Enclosures`, `Stairs`, and `Struts` under `MaterialFrame`, `MaterialHitbox`, and `StrutState`, deprecating `OrientedFrame`, `DirectedFrame`, `OrientedHitbox`, `DirectedHitbox`, and `OrientedState`.

* [x] Subtask: Add `AssetInstances.ENCLOSURES`, `BlueprintSchemas.ENCLOSURES`, `BlueprintSchemas.ORIENTATIONS`, `BlueprintSchemas.INCLINES`, `EnclosureBlueprints`, `OrientationBlueprints`, `InclineBlueprints`, `MultiplicationStrategies.ORIENTED`, `MultiplicationStrategies.PERIMETER`, and `MULTIPLIED_CRAFT_INSTANCES` to `src/app/config/enums.py`.
* [x] Subtask: Consolidate `OrientedState` into `StrutState` and update `StairState` to inherit from `StrutState` in `src/app/models/state/assets/crafts.py`; register `enclosures` on `CraftPropertyInstances` and `CraftStateInstances`.
* [x] Subtask: Update `src/data/config/recipes/main.yaml` so `bridges`, `railings`, `enclosures`, `struts`, and `stairs` all map to `(frame: material, animation: none, hitbox: material)`, leaving `platforms` untouched (`frame: single, hitbox: elevated`) for Phase 07.03.
* [x] Subtask: Remove `OrientedFrame`, `DirectedFrame`, `OrientedHitbox`, and `DirectedHitbox` from `src/app/assets/` and `Factory`.
* [x] Subtask: Remove the deprecated `direction == 'down'` transition condition from `StairMechanics`.

**7. Task: `Decomposer.multiply()` Strategy Expansion & `Materializer` Perimeter Valuation**

*Objective*: Subsume `Decomposer.orient()` into `Decomposer.multiply()` and add `ORIENTED` and `PERIMETER` multiplication strategies across `Decomposer`, `Migrator`, and `Materializer`.

* [x] Subtask: Expand `Decomposer.multiply()` to execute `ORIENTED` (1D axis-locked tiling for `bridges`/`railings`) and `PERIMETER` (2D hollow boundary capping with `north` baseline anchor adjustment for `enclosures`).
* [x] Subtask: Remove `Decomposer.orient()` and `OrientedAssets`, routing all `MULTIPLIED_CRAFT_INSTANCES` through `Decomposer.multiply()` in both `Decomposer._unpack_components()` and `Migrator._build_generator()`.
* [ ] Subtask: Update `Materializer.cost()` in `src/app/services/markets/materializer.py` to compute `total_units = 2 * (nx + ny + 2)` when `strategy == MultiplicationStrategies.PERIMETER.value` and `total_units = nx` (horizontal) or `ny` (vertical) when `strategy == MultiplicationStrategies.ORIENTED.value`.

**8. Task: Re-Atlasing & Re-Indexing `Bridges`, `Railings`, `Enclosures`, and `Stairs**`

*Objective*: Index the newly synthesized 2D Craft sheets and migrate existing state and composition files.

* [x] Subtask: Update `/src/assets/crafts/bridges/main.yaml` with `arch` (`80x103`, `geologics`, `orientations`) and `suspension` (`96x96`, `organics`, `orientations`).
* [x] Subtask: Update `/src/assets/crafts/railings/main.yaml` with `crenellation` (`32x32`, `geologics`, `orientations`) and create `/src/assets/crafts/enclosures/main.yaml` for 4-face perimeter fences (`north`, `east`, `south`, `west`).
* [x] Subtask: Update `/src/assets/crafts/stairs/main.yaml` with `steps` (`64x96`, `geologics`, `inclines`: `up`, `left`, `right`).
* [x] Subtask: Migrate all `bridges`, `railings`, and `stairs` entries in `src/data/config/compositions/main.yml` and `/src/data/state/**` to the unified `(id, blueprint, material, multiple)` state schema.

##### User Review IV

###### Railings?

Is it even necessary to differentiate Railings from Struts at this point? Stairs and Bridges have unique functionality, but if we are saying Railings are a `orientations` Blueprint, then why not just remove railings altogether and make them a Strut with a special multiplication strategy? 

###### Objects?

Objects are starting to blur with Crafts. Many Object Assets have a Material dimension that can be imposed on the atlas, although the engine does not currently utilize this dimension.

In particular, Bridges and Stairs seem very similar to Objects; since they have effects upon the environment beyond simply demarcating boundaries and stamping decals. However, I think the distinction still holds because Bridges and Stairs have structural rows in their frame sheets. Objects do not have this property. 

Objects, being one of the first Assets implemented in the game, may have some inefficiencies or incorrect models powering them. I believe the Material dimension needs to be added to Objects. Crates, Chests, Doors, Gates and Signs Assets from the LPC database all can have Material atlasing imposed on them; not Plates, though (Plates are exceptionally rare to come across in open-source assets for some reasons; you would think switches to be a natural component, but alas no atlas.).

Obstacles needs moved to Geography, as I have ideas on how to procedurally generate their distribution using geological principles, i.e. where Environ Tiles meet faultlines are formed. 

**Asset Analysis**

The following atlases can be imposed on Object Assets from the LPC database,

* Chest Sheets
    * id: container (32px by 32px)
        * columns (material: organics): cotton, thatches, wood
        * rows: closed, open
    * id: trunk (32px by 32px)
        * columns (material: metallics): copper, iron, gold
        * rows: closed, open
* Crate Sheets
    * id: box (32px by 32px)
        * columns (material: organics): cotton, thatches, wood
    * id: vase (TBD px by TBD px)
        * columns (material: chromatics, host: clay): neutral, blue, red, yellow, green
    * id: bookcase (TBD px by TBD px)
        * columns (material: chromatics, host: wood): neutral, blue, red, yellow, green
* Door Sheets
    * id: panel (32px by 48px)
        * columns (material: chromatics, host: wood): neutral, blue, red, yellow, green
    * id: dutch (32px by 48px)
        * columns (material: chromatics, host: wood): neutral, blue, red, yellow, green
    * id: pivot (32px by 48px)
        * columns (material: metallics): copper, iron, gold
* Gate Sheets
    * id: postern (64px by 64px)
        * columns (material: geologics): limestone, feldspar, granite, marble
        * rows: closed, open
    * id: barred (TBD px by TBD px)
        * columns (material: chromatics, host: wood): neutral, blue, red, yellow, green
        * rows: closed, open
* Sign Sheets
    * id: plaque (24px by 24px)
        * columns (material: geologics): limestone, feldspar, granite, marble
    * id: headstone (TBDpx by TBDpx)
        * columns (material: geologics): limestone, feldspar, granite, marble
    * id: poster (30px by 30px)
        * columns (material: chromatics, host: cotton): neutral, blue, red, yellow, green
    * id: book (TBDpx by TBDpx)
        * columns (material: chromatics, host: cotton): neutral, blue, red, yellow, green

- Will need to add a partition for Clay; However, do not want to invalidate the existing partitions for Struts, if possible. Need to fit everything in a single, unified Material model. 
- Doors need to cast shadows on the layers they are linked to. This is currently achieved by a dedicated `door-shadow-*` asset and explicitly binding those shadowed assets to the original Door. However, this is an unnecessary complexity and requires managing decoupled Door assets within Compositions. 
    - However, if Doors are partitioned by Material, then this becomes an untenable model. Doors need a "footprint" on the layer they are connecting, a frame of solid color and reduced alpha but equal dimensions to the Door. 
    - Moreover, the main issue with shadows will be the "infinite Door interaction" induced by the `outlayer` of a Door, i.e. the Door cannot transport the Sprite to a position in the `outlayer` which intersects with a Door, or else the Sprite will enter into an infinite loop.
        - Objects were implemented before HitboxSchemea was well-defined; This problem seems solvable by having LayeredHitboxes, similar to ElevatedHitboxes, insofar that they must be *relative* to the deployed layer, but whereas Elevation is scalar, Layer is categorical, i.e. not necessarily a number.

##### Self Review I

###### Review: Quality

1. **Duck-Typing Violations (`getattr`, `hasattr`, `isinstance`)**:
    * **`Decomposer` (`src/app/services/generators/game/decomposer.py`)**: Repeatedly uses `getattr(node.strut, 'position', None)`, `getattr(strut_state, 'owner', None)`, `getattr(pseudo_state, 'name', None)`, and `getattr(deployed_state, 'layer', '')`. `node.strut` and `deployed_state` are typed `PropertyState` / `CraftState` instances validated by Pydantic; their fields (`position`, `owner`, `name`, `layer`, `elevation`) are guaranteed by `AssetState` and `PropertyState`.
    * **`Migrator._build_generator()` (`src/app/services/orchestration/migrator.py`)**: Uses `if hasattr(self.state, Shortcuts.COMPOSITIONS.value)` on `self.state`, which is a strictly typed `StateSchema` dataclass where `self.state.compositions`, `self.state.plots`, and `self.state.calendar` always exist as attributes.
    * **`Board.serialize()` (`src/app/game/board/core.py`)**: Uses `frequency = getattr(asset.properties, "frequency", None)` and `hasattr(self.plot, "__dataclass_fields__")` instead of relying on `EffectProperties.frequency` and `PlotState`.
    * **`IndexFrame.keys()` (`src/app/assets/frames/core.py`)**: Uses `icon_key = getattr(state, "icon", None)` instead of typing `state: AttachmentState` (or `IconState`) and reading `state.icon`.
    * **`MaterialHitbox.get()` & `Decomposer.multiply()**`: Uses `isinstance(props.hitboxes, dict)` to branch between list and dictionary hitbox definitions. Normalizing `CraftProperties.hitboxes` to `Dict[str, List[Hitbox]]` via a Pydantic validator (or uniform schema) eliminates runtime type inspection.
2. **Monolithic Conditional Branching in `Decomposer.multiply()`**:
    * `Decomposer.multiply()` embeds a 150-line `if / elif / elif / else` block over `MultiplicationStrategies` with nested loops and inline hitbox boundary math (noted by the inline `# TODO: this seems in need of a handler abstraction`). Extracting strategy methods (`_multiply_simple`, `_multiply_oriented`, `_multiply_expansion`, `_multiply_perimeter`) mapped via a class-level dispatch table flattens the control flow and adheres to fail-fast standards.

###### Review: Logic

1. **Nested Dictionary Lookup Bug & Missing Strategies in `Materializer.cost()` (`src/app/services/markets/materializer.py`)**:
    * `MarketConfiguration` types `materials` and `blueprints` as nested dictionaries (`Dict[str, Dict[str, float]]`, keyed first by genus/schema and second by specific material/blueprint).
    * `Materializer.cost()` queries `self.markets.blueprints.get(blueprint_key, 1.0)` and `self.markets.materials.get(material_key, 1.0)` at the top level. Because top-level keys are genera (`organics`, `geologics`, `metallics`, `chromatics`) and schemas (`buildings`, `corridors`, `columns`), every lookup misses and falls back to `1.0`.
    * Additionally, `Materializer.cost()` only branches on `EXPANSION` (`nx * (ny + 2)`) and `else` (`nx * ny`), omitting `ORIENTED` (`nx` if horizontal else `ny`) and `PERIMETER` (`2 * (nx + ny + 2)`).
2. **Corner Superimposition & Unit Count Mismatch in `MultiplicationStrategies.PERIMETER` (`src/app/services/generators/game/decomposer.py`)**:
    * In `Decomposer.multiply()`, the `PERIMETER` branch loops `ix in range(nx + 2)` for `north`/`south` ($2(n_x + 2)$ units) and `iy in range(ny + 2)` for `west`/`east` ($2(n_y + 2)$ units), spawning $2(n_x + n_y + 4)$ units instead of the specified $2(n_x + n_y + 2)$ units.

###### Review: Architecture

Addressing the four architectural questions raised in **User Review IV**:

1. **Eliminating `Railings` and `Enclosures` as Distinct Craft Instances**:
    * In Ontology's ECS architecture, an `AssetInstance` is justified if and only if it requires a distinct `(frame, animation, hitbox, state)` recipe or participates in a dedicated `Mechanic` query:
    * `bridges`: Sensor ($m = -1$) queried by `board.bridges()` in `MotionMechanics` to suppress fluid immersion and drift.
    * `stairs`: Sensor ($m = -1$) with `StairState.delta` queried by `StairMechanics` to transition `state.elevation`.
    * `platforms`: Uses `ElevatedHitbox` (pending Phase 07.03 Gravity refactor).
    * By contrast, `railings` and `enclosures` share the exact same properties (`CraftProperties`), state (`CraftState`), recipe (`frame: material, animation: none, hitbox: material`), mass ($m = 0$), and substrate (`Substrates.STANDARD = 0`) as `struts`. Their multiplication behavior is governed entirely by `BLUEPRINT_STRATEGIES[properties.blueprints]` (`orientations -> oriented`, `enclosures -> perimeter`).
    * **Conclusion**: Collapse `railings` and `enclosures` into `struts`. Move `crenellation` and `palisade` into `/src/assets/crafts/struts/main.yaml` and delete `AssetInstances.RAILINGS` and `AssetInstances.ENCLOSURES`.
2. **Extending Material Atlasing to `Objects` & Introducing the `Ceramics` (`clay`) Partition**:
    * **Structural vs. Functional Atlasing**:
        * **Crafts** are indexed across 2D `(Blueprint_Row x Material_Col)` sheets because Crafts vary across structural morphology (`floors`, `walls`, `crowns`, `shafts`) and material.
        * **Objects** have a single morphology per ID, varying across **Material Rows ($r \in [0, M)$)** and **State/Switch Columns ($c \in [0, \text{count})$)** where $\text{count} = 1$ for static/kinematic objects (`crates`, `doors`, `signs`) and $\text{count} = 2$ (`0: closed`, `1: open`) for binary objects (`chests`, `gates`).
    * **Unified `Ceramics` Partition for `clay`**:
        * Adding `clay` to `Organics` or `Geologics` would alter the column cardinality of those partitions (`3` and `4` respectively), invalidating every existing Strut atlas.
        * Introducing `Materials.CERAMICS = "ceramics"` with `class Ceramics(str, Enum): CLAY = "clay"` preserves the exact column indices of `Organics`, `Geologics`, `Metallics`, and `Chromatics`.
        * Defining `CHROMATIC_HOSTS: Final[frozenset[str]] = frozenset((*MATERIAL_PARTITIONS[Materials.ORGANICS.value], *MATERIAL_PARTITIONS[Materials.CERAMICS.value]))` allows `vase` (`genus: chromatics, host: clay`) to pass `Material.__post_init__` validation while keeping all Strut sheets untouched.
    * **Unified Object Frame Indexing (`ObjectFrame` / `MaterialFrame`)**:
        * By adding `material: Optional[Material] = None` to `ObjectProperties` and `material: Optional[str] = None` to `AssetState` (or `ObjectState` base class):
        * If `properties.material is None` (e.g., `plates`, `rafts`), row $r = 0$.
        * If `properties.material is not None`, row $r$ iterates over `MATERIAL_PARTITIONS[properties.material.genus]`, and column $c$ iterates over `range(properties.count)` at crop coordinate `(c * w, r * l, w, l)`.
        * Canonical key: `"{id}-{material}-{frame}"` for binary objects (`count > 1`) and `"{id}-{material}"` for single-frame objects (`count == 1`).
3. **Migrating `Obstacles` from `Objects` to `Geography`**:
    * `Obstacles` are immutable, inanimate landforms (`mass = 0`) that do not participate in object interactions and will be procedurally distributed along Environ Tile faultlines. Moving `obstacles` from `ObjectPropertyInstances` / `ObjectStateInstances` to `GeographyPropertyInstances` / `GeographyStateInstances` (with `MotiveState` and recipe `frame: single, animation: none, hitbox: static`) cleanly separates geological landforms from interactive functional `Objects`.
4. **Door Shadow Footprints, Infinite Teleportation Loops & `LayeredHitbox`**:
    * **Why the Infinite Loop Occurs**: When a Sprite interacts with a Door on `layer` at `position`, `InteractionMechanics` transitions `sprite.state.layer = door.state.outlayer` and `sprite.state.position = door.state.out`. If a reciprocal Door or shadow footprint is placed at `door.state.out` with the same hitbox geometry, the arriving Sprite lands *inside* the return Door's active hitbox on the first frame after layer transition, immediately re-triggering teleportation back to `layer`.
    * **Why `door-shadow-*` Assets Fail Under Materialization**: Maintaining separate `door-shadow` PNGs and manual branch Door declarations in Compositions couples every Door placement to a boilerplate twin and breaks when Doors are indexed by `Material`.
    * **The Unified Solution (`LayeredHitbox` + Reciprocal Shadow Channel)**:
        * **Categorical Layer Resolution (`LayeredHitbox`)**: Just as `ElevatedHitbox` resolves hitboxes relative to scalar `elevation` offsets, `LayeredHitbox` resolves hitboxes relative to categorical `layer` keys (`state.layer` vs. `state.outlayer`):
            * On `layer == state.layer` (the upright Door facade at `state.position`): emits the standard door interaction hitbox `properties.hitboxes`.
            * On `layer == state.outlayer` (the shadow footprint at `state.out`): emits a thin threshold strip hitbox offset to the **southern exit edge** of the footprint (`Position(0, l - t_shadow), Dimensions(w, t_shadow)`), while the Sprite's arrival coordinate `state.out` is positioned north of that strip (or offset by `-sprite.dimensions.l` upon exit). Because the arrival coordinate and the return trigger strip are disjoint on `outlayer`, the Sprite cannot re-enter the Door without intentionally walking back across the threshold strip.
        * **Zero-Asset Shadow Rendering (`ChannelTypes.TINT` / `SHADOW`)**:
        During hydration (`Decomposer` / `Migrator`), a single `DoorState` declaration automatically registers its reciprocal shadow projection on `state.outlayer` at `state.out` on `Substrates.OVERLAYS (-1)` using `ChannelTypes.TINT` (`RGBA(0, 0, 0, 110)`), eliminating `door-shadow-*` files and manual Composition twin declarations entirely.

###### Review: Optimization

1. **Hoisting `Factory` Lookups in `Decomposer.multiply()` (`src/app/services/generators/game/decomposer.py`)**:
    * `_spawn_unit()` calls `Factory.frame(recipe.frame)`, `Factory.animation(recipe.animation)`, and `Factory.hitbox(recipe.hitbox)` on **every single unit iteration** inside the `nx * ny` loop. Because `Frame`, `Animation`, and `HitboxSchema` are `Singleton` instances, resolving them once at the top of `multiply()` and passing the resolved references into `_spawn_unit()` eliminates $3 \times (n_x \cdot n_y)$ redundant dictionary/singleton lookups per multiplied Craft.

##### Tasks: Addendum III

To resolve the bugs identified above and incorporate the architectural expansions from **User Review IV**, add the following tasks to **Phase 07.04 - Materialization**:

**9. Task: Phase 07.04 Core Bug Fixes & Strut Consolidation (`Railings` & `Enclosures` $\to$ `Struts`)**

*Objective*: Fix blocking defects in `settings.py`, `core.py`, `base.py`, `crafts.py`, `decomposer.py`, `materializer.py`, and `struts/main.yaml`, and collapse `railings` and `enclosures` into `struts`.

* [x] Subtask: Fix `b.vlaue` typo in `src/app/config/settings.py`, add `Substrates.STANDARD = 0` to `src/app/config/enums/engine.py`, reorder `Columns` to `(CROWNS, SHAFTS, BASES)` in `src/app/config/enums/assets.py`, and add `STAIRS` to `MultipliedAssets`.
* [x] Subtask: Fix `Material.__post_init__` indentation in `src/app/models/properties/core.py`, fix `Asset.substrate` in `src/app/assets/base.py`, and fix `MaterialFrame.keys()` return tuple and `CraftState` import in `src/app/assets/frames/crafts.py`.
* [x] Subtask: Collapse `AssetInstances.RAILINGS` and `AssetInstances.ENCLOSURES` into `AssetInstances.STRUTS`; move `crenellation` (`blueprints: orientations`) and `palisade` (`blueprints: enclosures`) into `/src/assets/crafts/struts/main.yaml`, and remove `railings`/`enclosures` from `CraftPropertyInstances`, `CraftStateInstances`, `MultipliedAssets`, and `recipes/main.yaml`.
* [x] Subtask: Fix `struts/main.yaml` keys (`blueprint`/`blueproint` $\to$ `blueprints`, `shack` $\to$ `hut`, `pillar` length `96` $\to$ `32`, `tower` length `192` $\to$ `64`) and update `stairs` recipe in `src/data/config/recipes/main.yaml` to `(frame: material, animation: none, hitbox: material)`.
* [x] Subtask: Route `node.strut` through `self.multiply()` in `Decomposer._unpack_node()`, refactor `Decomposer.multiply()` into strategy handler methods, and update `Materializer.cost()` to resolve nested `(genus, material)` and `(schema, blueprint)` market dictionaries across all four `MultiplicationStrategies`.

**10. Task: Category-Wide `Objects` Materialization, `Ceramics` Partition & `Obstacles` Migration**

*Objective*: Impose Material atlasing on `Objects` (`chests`, `crates`, `doors`, `gates`, `signs`), add the `Ceramics` (`clay`) genus partition, and migrate `obstacles` to `Geography`.

* [x] Subtask: Add `Materials.CERAMICS = "ceramics"` and `class Ceramics(str, Enum): CLAY = "clay"` to `src/app/config/enums/assets.py`, register `MATERIAL_PARTITIONS[Materials.CERAMICS.value]`, and allow `Ceramics` as a valid host in `Material.__post_init__`.
* [x] Subtask: Add `material: Optional[Material] = None` to `ObjectProperties` and `material: Optional[str] = None` to `Object` state models (`MotiveState`, `ContainerState`, `DoorState`, `SwitchState`, `DialogueState`).
* [x] Subtask: Implement 2D `(Count x Material)` indexing in `MaterialFrame` (or `ObjectFrame`) supporting both static (`count = 1`: `crates`, `doors`, `signs`) and binary (`count = 2`: `chests`, `gates`) Objects, and implement dynamic open/closed hitbox resolution on `gates` (`Bug B008`).
* [!: Deferred to later phase; See User Review V] Subtask: Move `obstacles` from `ObjectPropertyInstances` / `ObjectStateInstances` / `recipes.objects` to `GeographyPropertyInstances` / `GeographyStateInstances` / `recipes.geography`.
* [x] Subtask: Index the curated Object sheets (`container`, `trunk`, `box`, `vase`, `bookcase`, `panel`, `mansion`, `reinforced`, `postern`, `barred`, `plaque`, `headstone`, `poster`, `book`) in `/src/assets/objects/**/*.yaml`.

**11. Task: `Door` Reciprocal Shadow Footprints & `LayeredHitbox`**

*Objective*: Eliminate decoupled `door-shadow-*` assets and prevent infinite teleportation loops via `LayeredHitbox` and alpha-tinted shadow footprints.

* [x] Subtask: Implement `LayeredHitbox` in `src/app/assets/hitboxes/` resolving full facade hitboxes on `state.layer` (`state.position`) and southern-edge threshold sensor strips on `state.outlayer` (`state.out`) disjoint from the Sprite arrival coordinate.
* [x] Subtask: Update `Decomposer` / `Migrator` and `DoorFrame.channels()` so each `Door` automatically projects a darkened footprint (`ChannelTypes.TINT`, `Substrates.OVERLAYS = -1`) at `(state.outlayer, state.out)` with reciprocal return linkage, and remove legacy `door-shadow-*` assets from Compositions.

##### User Review V

Review the additional context and notes below and then complete the open and new tasks.

**Context**

1. Agreed on **Eliminating `Railings` and `Enclosures` as Distinct Craft Instances**.  Files have been moved, properties indices updated, recipes removed, enums pruned and models in the code updated. 

2. Agreed on **Migrating `Obstacles` from `Objects` to `Geography`**, however this will need to wait until the current phase is complete, as Obstacles are currently necessary for the User Acceptance Test Board to stop Fluid flow. State files will need updated, etc.

3. Bugs B017 - B020 have been addressed. B021 is outstanding.

4. `app.config.enums.Ceramics` has been added. `app.config.settings.CHROMATIC_HOSTS` has been added.

5. Object frames have been reatlased yet again to respect existing implementations and make things smoother. This is what is currently available and indexed in the `src/assets/objects` directory. This will be the Object/Craft atlasing strategy going forward, i.e. Material will span columns, Category-Function will span rows.

* Chest Sheets
    * id: container (32px by 32px)
        * columns (material: organics): cotton, thatches, wood
        * rows: closed, open
    * id: trunk (32px by 32px)
        * columns (material: metallics): copper, iron, gold
        * rows: closed, open
* Crate Sheets
    * id: box (32px by 32px)
        * columns (material: organics): cotton, thatches, wood
* Door Sheets
    * id: panel (32px by 48px)
        * columns (material: chromatics, host: wood): neutral, blue, red, yellow, green
    * id: dutch (32px by 48px)
        * columns (material: chromatics, host: wood): neutral, blue, red, yellow, green
    * id: pivot (32px by 48px)
        * columns (material: metallics): copper, iron, gold
* Gate Sheets
    * id: postern (64px by 64px)
        * columns (material: geologics): limestone, feldspar, granite, marble
        * rows: closed, open
* Sign Sheets
    * id: plaque (24px by 24px)
        * columns (material: geologics): limestone, feldspar, granite, marble
    * id: poster (30px by 30px)
        * columns (material: chromatics, host: cotton): neutral, blue, red, yellow, green

The rest will await the completion of the current phase before indexing.

###### New Task: Relationships Masquerading as Settings

* [x] Anaylze the proper way to represent the Blueprint, Material relationships and propose a task list.

`app.config.settings` is beginning to accumulate code that is not exactly a "*setting*". It's more like a relationship. 

A similar issue was encountered during the development of Shoreline Geography and its inherent association with its adjacent Environ Tile and Fluid Assets. The relationship was codified as a property,

```yaml
geography:
  shorelines:
    temperate-banks:
      tile: temperate
      fluid: waterflow
      dimensions: 
        w: 41
        l: 41
      thickness: 22
      mass: -1
      priority: -2
      hitboxes: null
```

Then, in the `app.services.orchestration.builder`, it is compiled from properties into a model using the class in `app.game.logics.modules.relations.ShorelineIndex`,

The difference here is the Material and Blueprint "*settings*" are not properties of a specific (Category, Instance) node, but rather runtime configuration. 

Ultimately, `app.config.settings` will pull its value from the environment using the `os` library, to allow runtime configuration; Everything is simply hard-coded for quicker development. Settings are supposed to represent "knobs" and "dials" that can be set prior to running to the game. The Material and Blueprint fields are more naturally relations that are configured through a `materials` Configuration model. 

I believe all of the enum mappings in `app.config.settings` should be parameterized and shifted into configuration, and then compiled into relations. Possibly just existing as a Configuration model. 

- Also, I think `SUBSTRATE_BLUEPRINTS` is extraneous, as this is already contained in `SUBSTRATES`. 

###### Relevant Code

Object interactions are governed by InteractionMechanics, CollisionMechanics and their base SpatialMechanics case.

##### Architectural Analysis V

###### 1. Distinguishing Environment Settings from Domain Relations

`app.config.settings` is intended to house **runtime environment parameters**—scalar "knobs" and "dials" (`TARGET_FPS`, `TILE_HASH_SIZE`, `MIGRATOR_DELAY`, `LOG_LEVEL`, `SOCKET`, and filesystem roots) that can be overridden via `os.environ` without altering the ontology of the game world.

By contrast, the dictionary mappings currently residing in `app.config.settings` encode **structural domain relationships**:

| `settings.py` | Actual Architectural Role |
| --- | --- |
| `MATERIAL_PARTITIONS` | Ordered projection of `Materials` genera onto their constituent material keys ($c \in [0, C)$). |
| `CHROMATIC_HOSTS` | Relational constraint specifying which material genera (`organics`, `ceramics`) may serve as hosts for `chromatics`. |
| `BLUEPRINT_PARTITIONS` | Ordered projection of `Blueprints` schemas onto their constituent structural rows ($r \in [0, R)$). |
| `BLUEPRINT_STRATEGIES` | Functional mapping from `Blueprints` schema to `MultiplicationStrategies`. |
| `OBSTACLE_BLUEPRINTS` | Subset predicate defining which blueprint partitions emit physical collision geometry in `MaterialHitbox`. |
| `SUBSTRATES` | Topological mapping from `(AssetInstances, Blueprint)` to intra-tier rendering plane $\sigma \in [-4, 0]$. |
| `SUBSTRATE_BLUEPRINTS` | **Redundant**: Completely subsumed by `SUBSTRATES` (any blueprint where $\sigma < 0$). |
| `SEASON_EVAPORATION_MODIFIERS` | Hydrological physics parameter mapping `Seasons` to evaporation scalars (belongs in `mechanics` configuration). |

###### 2. Unifying `Markets`, `Materials`, `Blueprints`, and `Substrates` into a Single Relational Schema

Currently, adding or modifying a Blueprint or Material requires updating six separate locations (`enums/assets.py`, `MATERIAL_PARTITIONS`, `BLUEPRINT_PARTITIONS`, `BLUEPRINT_STRATEGIES`, `OBSTACLE_BLUEPRINTS`, `SUBSTRATES`, and `data/config/markets/main.yaml`).

In reality, all of these mappings are projections of two relational tables—the **Material Space** and the **Blueprint Space**:

1. **Material Space (`materials` section of `/src/data/config/markets/main.yaml` or `/src/data/config/materials/main.yaml`)**:
    * Each **Genus** (`organics`, `geologics`, `metallics`, `chromatics`, `ceramics`) declares:
        * `hosts`: Optional list of valid host genera (`[organics, ceramics]` for `chromatics`, `[]` otherwise).
        * `partitions`: Ordered mapping of `material_key -> weight` ($\mu_{\text{mat}}$). Because Python `dict` and Pydantic preserve insertion order, the keys of `partitions` define the exact column index $c \in [0, C)$ while the values define the economic valuation weight $\mu_{\text{mat}}$.
2. **Blueprint Space (`blueprints` section)**:
    * Each **Blueprint Schema** (`buildings`, `corridors`, `columns`, `enclosures`, `orientations`, `inclines`, `directions`) declares:
        * `strategy`: `MultiplicationStrategies` (`simple`, `expansion`, `perimeter`, `oriented`).
        * `partitions`: Ordered mapping of `blueprint_key -> BlueprintSpec(delta, substrate, obstacle)`:
        * Row index $r \in [0, R)$ is derived from the insertion order of `partitions.keys()`.
        * `delta`: Structural volume cost factor ($\delta_{\text{blueprint}}$).
        * `substrate`: Intra-tier rendering plane ($\sigma \in \{-2, -1, 0\}$).
        * `obstacle`: Boolean flag indicating whether `MaterialHitbox` emits collision hitboxes for this row.

###### 3. Compiling `MaterialIndex` in `Builder.build_relations()` & Hydrating `AssetState.substrate`

1. **`MaterialIndex` (`src/app/game/logic/relations/materials.py`)**:
    * Compiled once in `Builder.build_relations()` via `MaterialIndex.from_config(self.context.configurations.materials)` and registered under `Relations.MATERIALS`.
    * Exposes $O(1)$ lookup methods:
        * `materials(genus: str) -> Tuple[str, ...]`
        * `hosts(genus: str) -> FrozenSet[str]`
        * `blueprints(schema: str) -> Tuple[str, ...]`
        * `strategy(schema: str) -> str`
        * `is_obstacle(blueprint: str) -> bool`
        * `substrate(instance: str, blueprint: Optional[str] = None) -> int`
2. **Hydrating `state.substrate` to Eliminate Per-Frame Dictionary Lookups**:
    * Currently, `Asset.substrate` performs a dictionary lookup in `settings.SUBSTRATES` on every `Screen._sort` comparison at 60 Hz.
    * Adding `substrate: int = Substrates.STANDARD.value` to `AssetState` and resolving it once during hydration (`Decomposer` / `Migrator` via `MaterialIndex.substrate(instance, blueprint)`) reduces `Asset.substrate` to a direct slot read (`return self.state.substrate`) and allows Door shadow projections to explicitly set `state.substrate = Substrates.OVERLAYS.value` (`-1`).

###### Proposed Task List: Task 12 - Relational Configuration & `settings.py` Purification

**12. Task: Relational Configuration & `app.config.settings` Purification**

*Objective*: Evict all domain enum dictionaries from `app.config.settings` into `ConfigurationSchema` and compile them into `MaterialIndex` in `Builder.build_relations()`.

* [x] Subtask: Remove `SUBSTRATE_BLUEPRINTS` from `src/app/config/settings.py`.
* [x] Subtask: Expand `MarketConfiguration` (or `MaterialConfiguration`) in `src/app/models/config/markets.py` and `/src/data/config/markets/main.yaml` to declare ordered `genera` (`hosts`, `partitions`) and `blueprints` (`strategy`, `partitions` with `delta`, `substrate`, `obstacle`), plus instance-level `substrates`.
* [x] Subtask: Move `SEASON_EVAPORATION_MODIFIERS` from `src/app/config/settings.py` to `MechanicsConfiguration` (`/src/data/config/mechanics/main.yaml`).
* [x] Subtask: Implement `MaterialIndex` in `src/app/game/logic/relations/materials.py` and register `Relations.MATERIALS` in `Builder.build_relations()`.
* [x] Subtask: Add `substrate: int = Substrates.STANDARD.value` to `AssetState`, hydrate it via `MaterialIndex` in `Decomposer` and `Migrator`, and update `Asset.substrate` to return `self.state.substrate`.
* [x] Subtask: Convert remaining scalar constants in `src/app/config/settings.py` to read from `os.getenv()` with typed defaults.

##### User Review VI

Review the notes below and then do the following:

- Refer to [Source](#source) below for the dependency injection pipeline which will be relevant for Task 12.
- Complete Task 12. Go with `MaterialConfiguration`, as it is more descriptive of the actual configuration. Markets are derived from materials, not the basis of them. Market configuration will occur another level up, once the foundations of economies are established. 
- Address [Analysis: Animations](#analysis-animations)

###### Note: Removal of Important Clause and Rejection

This bit of code is rejected.

```python
if target.taxonomy.instance == AssetInstances.DOORS.value:
    if source.taxonomy.instance == AssetInstances.SPRITES.value:
        source.state.memory.doors[target.name] = target.state.outlayer

    board.relayer(source, target.state.outlayer)
    source.state.position.x = target.state.out.x
    source.state.position.y = target.state.out.y
    source.state.intention = Intentions.IDLE.value

    processed_sources.add(source.name)
```

**Nothing alters Sprite intentions except TransitionMechanics**. Altering Player Intentions is fine, as they are not hooked into the Intention Transition automaton; Sprite Intentions are off-limits, though. Any changes that violate this constraint are rejected. This is non-negotiable and a non-starter. This block remains in place,

```python
if target.taxonomy.instance == AssetInstances.DOORS.value:
        if source.taxonomy.instance == AssetInstances.SPRITES.value:
            source.state.memory.doors[target.name] = target.state.outlayer
            
        board.relayer(source, target.state.outlayer)
        source.state.position.x = target.state.out.x
        source.state.position.y = target.state.out.y

        if source.taxonomy.instance == AssetInstances.PLAYERS.value:
            source.state.intention = Intentions.IDLE.value

        processed_sources.add(source.name)
```

All other changes accepted, though.

###### Analysis: Animations

Are Object Animations extraneous? 

```python
class BinaryAnimation(Animation):
    """
    """

    def animate(self, state: AssetState, properties: AssetProperties) -> AssetState:
        """
        """
        state.animation.frame = Switches.ON.value if state.switch else Switches.OFF.value
        return state
```

Yet BinaryFrame:

```python
def keys(
        self,
        id: str,
        state: Union[ContainerState, SwitchState]
    ) -> List[Tuple[str, int, int]]:
        frame_idx = str(state.animation.frame)
        if not state.material:
            return [(settings.SEPARATOR.join([id, frame_idx]), 0, 0)]
        key = settings.SEPARATOR.join([id, frame_idx, state.material])
        return [(key, 0, 0)]
```

It seems like another solution would be having a Frame implementation retrieve the Frame keys directly via the `state.switch` field, and removing the BinaryAnimation component altogether. The Animation `animate()` is only called in AnimationMechanics (also, MenuMechanics, but that's only for Widgets), so really, the only purpose of BinaryAnimation is to intercede before the Screen calls `keys()`.

However, this raises the question: what exactly *is* an Animation, and *what* actually needs Animation components? I suppose Animations are the "flow of time". Binary Objects change their state instantaneously upon interaction, whereas Animations change their state over time. So I suppose the critera for determining whether an Asset requires an Animation is whether its state change is discrete or continuous, i.e. Animations are the "glue" of continuity. 

With that in mind, I believe one of the defining characteristics of Objects in the Asset Hierarchy is their *lack* of Animations (animacy). They are inherently inanimate, even the ones that change their Frame based on interactions. I think the BinaryFrame should retrieve frame keys directly from State, that being the purpose of Frame component, i.e. `index()` imposes a metric on the Asset file and measures its space while `keys()` create the binding between Asset state and Frame space. 

###### Source

The Decomposer will need injected with the Material Index. This will need to occur in the `app.services.orchestration.builder`. This is then orchestrated in `app.services.orchestration.orchestrator`

##### Architectural Analysis VI

###### 1. Ontological Distinction: Instantaneous State Projection vs. Temporal Continuity

In the ECS architecture:

* **Properties** define the static metric space of an Asset's texture sheet (`dimensions`, `material`, `blueprints`, `count`).
* **State** records the entity's coordinates within that space (`switch`, `material`, `blueprint`, `stage`).
* **Frame** (`index`, `keys`) is a stateless projection mapping `Properties` to crop rectangles (`index`) and mapping `State` to active texture keys (`keys`).
* **Animation** (`animate`) is a discrete-time progression operator ($\Delta t \to \Delta \text{frame}$) ticked by `AnimationMechanics` for categories whose visual representation evolves continuously over time (`Sheets`, `Effects`, `Widgets`).

`Objects` (`chests`, `crates`, `doors`, `gates`, `obstacles`, `plates`, `signs`, `rafts`) are **inanimate**. Binary Objects (`chests`, `gates`, `plates`) transition instantaneously when their `state.switch` boolean mutates during an interaction or collision event. Maintaining `BinaryAnimation` and `state.animation: AnimationState` on `ContainerState` and `SwitchState` only served to copy `state.switch` into `state.animation.frame` on every 60 Hz tick of `AnimationMechanics` before `Screen.draw()` called `Frame.keys()`.

Projecting `state.switch` directly inside `BinaryFrame.keys()` enforces the category invariant that **all `Objects` have `animation: none**`:

1. `BinaryAnimation` is deleted from `src/app/assets/animations/` and `Factory.animation()`.
2. `animation: AnimationState` is removed from `ContainerState` and `SwitchState` in `src/app/models/state/assets/objects.py`.
3. `chests`, `gates`, and `plates` all map to `frame: binary` and `animation: none` in `src/data/config/recipes/main.yaml`.

##### User Review VII

All changes accepted, except it is not clear where to set the substrate in Migrator. Also, the MaterialIndex isn't being passed in or instantiated currently in the Migrator, to compound the ambiguity. Fix these final items and then conduct an exhaustive analysis of everything that has been changed.  Search for any bugs or logical errors. Isolate any documentation divergences and propose updates to align with current implementation. Once documentation is updated, UAT and Unit testing will start.

##### Tasks: Addendum IV

1. `src/app/services/orchestration/migrator.py`

* [x] Injects `materials: Optional[MaterialIndex] = None` into `Migrator.__init__()` (defaulting to `MaterialIndex.from_configuration(self.configurations.materials)` when not explicitly supplied by `Builder`), passes the same `MaterialIndex` instance to the fallback `Decomposer`, and hydrates `state_obj.substrate = self.materials.substrate(instance_key)` directly in the standalone asset branch of `_build_generator()`.

2. `src/app/services/generators/game/decomposer.py`

* [x] Resolves `state.substrate` without duck-typing across `_spawn_unit()`, `project_door()`, and `_create_asset()`, restores full `range(ny + 2)` corner superimposition in `_multiply_perimeter()`, ensures idempotent reload behavior for serialized units (`multiple=None`), and computes strategy-aware vertical span lengths in `_get_span_length()` for `anchor()` macros.

3. `src/app/models/properties/core.py` & `src/app/services/orchestration/builder.py`

* [x] Removes the deleted `settings.MATERIAL_PARTITIONS` / `settings.CHROMATIC_HOSTS` import from `src/app/models/properties/core.py` by validating chromatic host membership directly against `(Organics, Ceramics)` enums, and updates `Builder.build_board()` and `Builder.build_registry()` so `MaterialIndex` is always compiled and injected into both `Decomposer` and `Migrator`.

##### User Review VIII

Making `substrate` part of the state was a mistake. 

1. It is fundamentally not part of the state. It never changes. That is the point of shifting all of the this information into the `materials.yaml` and the MaterialIndex. It shouldn't be a state field at all. By detaching it from the lazy-loading of settings and setting the substrate on the state, the process is now broken for things that aren't compositions because the substrate never gets hydrated anywhere. Now, instead of the substrate coming from settings, it needs to be set on the Asset somehow. Now the hydration needs a step for processing substrates.

##### Tasks: Addendum V

**13. Task: Multiplier Pipeline & Door Projection Remediation**

*Objective*: Resolve the `Multiplier` binding exceptions, fix Door `OUT` threshold geometry and return coordinates, and close remaining Composition scope bugs (`B015`, `B019`).

* [x] Decouple `substrate` from `state`. Rewire the Asset base class and dependnecy injection pipeline to hydrate substrate correctly from configuration.
* [x] Subtask: Import `MaterialIndex` in `src/app/game/logic/modules/multipliers/base.py` to resolve `unit_substrate`, move the `state.multiple is None` reload guard into `ExpansionMultiplier` and `PerimeterMultiplier`, and bind `Decomposer._strategies` to instantiated `Multiplier` singletons (`Bug B022`).
* [ ] Subtask: Offset the `OUT` sensor hitbox in `LayeredHitbox.get()` to `Position(0, l - sensor_l)` and offset `shadow_state.out` in `Decomposer.project()` clear of the primary `IN` door's solid hitbox (`Bug B023`).
* [x] Subtask: Register `node.strut` in `scope_lookup` within `Decomposer._unpack_node()` / `_unpack_components()` (`Bug B015`) and namespace `SwitchState.link` in `Decomposer._hydrate_state()` (`Bug B019`).
* [ ] Subtask: Add `material` and `blueprint` parameters to `Cradle.spawn_strut()` and `material` to `Cradle.spawn_bridge()`, routing `spawn_strut()` through `self.decomposer.multiply()`.
* [ ] Subtask: Update `01-assets.md`, `03-compositions.md`, and `11-architecture.md` to reflect the finalized Phase 07.04 models and signatures.