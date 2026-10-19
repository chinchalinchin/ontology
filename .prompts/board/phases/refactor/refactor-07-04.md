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

```python
# src/app/config/enums.py
class MaterialGenera(StrEnum):
    ORGANICS = "organics"
    GEOLOGICS = "geologics"
    METALLICS = "metallics"
    CHROMATICS = "chromatics"

class OrganicMaterials(StrEnum):
    COTTON = "cotton"
    THATCHES = "thatches"
    WOOD = "wood"

class GeologicMaterials(StrEnum):
    LIMESTONE = "limestone"
    FELDSPAR = "feldspar"
    GRANITE = "granite"
    MARBLE = "marble"

class MetallicMaterials(StrEnum):
    COPPER = "copper"
    IRON = "iron"
    GOLD = "gold"

class ChromaticMaterials(StrEnum):
    NEUTRAL = "neutral"
    BLUE = "blue"
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"

MATERIAL_PARTITIONS: Dict[str, Tuple[str, ...]] = {
    MaterialGenera.ORGANICS.value: tuple(m.value for m in OrganicMaterials),
    MaterialGenera.GEOLOGICS.value: tuple(m.value for m in GeologicMaterials),
    MaterialGenera.METALLICS.value: tuple(m.value for m in MetallicMaterials),
    MaterialGenera.CHROMATICS.value: tuple(m.value for m in ChromaticMaterials),
}

class BlueprintSchemas(StrEnum):
    BUILDINGS = "buildings"
    CORRIDORS = "corridors"
    COLUMNS = "columns"

class BuildingBlueprints(StrEnum):
    FLOORS = "floors"
    WALLS = "walls"
    FLATS = "flats"
    ROOFS = "roofs"
    PATHS = "paths"
    HALLS = "halls"

class CorridorBlueprints(StrEnum):
    SOLIDS = "solids"
    STRIPES = "stripes"
    DESIGNS = "designs"

class ColumnBlueprints(StrEnum):
    CROWNS = "crowns"
    SHAFTS = "shafts"
    BASES = "bases"

class MultiplicationStrategies(StrEnum):
    SIMPLE = "simple"
    EXPANSION = "expansion"

BLUEPRINT_PARTITIONS: Dict[str, Tuple[str, ...]] = {
    BlueprintSchemas.BUILDINGS.value: tuple(b.value for b in BuildingBlueprints),
    BlueprintSchemas.CORRIDORS.value: tuple(b.value for b in CorridorBlueprints),
    BlueprintSchemas.COLUMNS.value: tuple(b.value for b in ColumnBlueprints),
}

BLUEPRINT_STRATEGIES: Dict[str, str] = {
    BlueprintSchemas.BUILDINGS.value: MultiplicationStrategies.SIMPLE.value,
    BlueprintSchemas.CORRIDORS.value: MultiplicationStrategies.SIMPLE.value,
    BlueprintSchemas.COLUMNS.value: MultiplicationStrategies.EXPANSION.value,
}

SUBSTRATE_BLUEPRINTS = frozenset({
    BuildingBlueprints.FLOORS.value,
    BuildingBlueprints.PATHS.value,
    CorridorBlueprints.SOLIDS.value,
    CorridorBlueprints.STRIPES.value,
    CorridorBlueprints.DESIGNS.value,
})

OBSTACLE_BLUEPRINTS = frozenset({
    BuildingBlueprints.WALLS.value,
    BuildingBlueprints.HALLS.value,
    ColumnBlueprints.BASES.value,
})

```

###### Goal: Property, State & Market Configuration Models (`properties.py`, `crafts.py`, `markets.py`)

Remove `cost` from `CraftProperties`, add `Material` (`genus`, `host`) and `blueprints`, define `StrutState` (`material`, `blueprint`, `multiple`), and add `MarketConfiguration` to `app.models.config`.

```python
# src/app/models/properties.py
@dataclass(slots=True)
class Material:
    genus: str
    host: Optional[str] = None

    def __post_init__(self):
        if self.genus == MaterialGenera.CHROMATICS.value:
            if self.host not in MATERIAL_PARTITIONS[MaterialGenera.ORGANICS.value]:
                raise ValueError(
                    f"Chromatic material requires an organic host; got '{self.host}'."
                )
        elif self.host is not None:
            raise ValueError(
                f"Non-chromatic genus '{self.genus}' cannot declare a host material."
            )

@dataclass(slots=True)
class CraftProperties(AssetProperties):
    mass: int = 0
    material: Optional[Material] = None
    blueprints: Optional[str] = None
    hitboxes: Optional[Union[Dict[int, List[Hitbox]], Dict[str, Optional[List[Hitbox]]], List[Hitbox]]] = None  # type: ignore

```

```python
# src/app/models/state/assets/crafts.py
@dataclass(slots=True)
class PropertyState(AssetState):
    owner: Optional[str] = None
    position: Optional[Position] = None  # type: ignore

@dataclass(slots=True)
class StrutState(PropertyState):
    material: Optional[str] = None
    blueprint: Optional[str] = None
    multiple: Optional[Multiple] = None  # type: ignore

```

```python
# src/app/models/config/markets.py
@dataclass(slots=True, frozen=True)
class Cost:
    item: str
    quantity: int

@dataclass(slots=True, frozen=True)
class MarketConfiguration(Configuration):
    materials: Dict[str, float] = field(default_factory=dict)
    blueprints: Dict[str, float] = field(default_factory=dict)

```

###### Goal: `Materializer` Service (`src/app/services/markets/materializer.py`)

Implement `Materializer` to compute crafting costs dynamically from `Dimensions`, `Material`, `Blueprint`, and `Multiple`, removing all cost logic from `Decomposer`.

```python
# src/app/services/markets/materializer.py
"""
# Ontology: app.services.markets.materializer

Service for calculating dynamic crafting and construction costs.
"""
from typing import List, Optional
from app.config.enums import (
    MaterialGenera,
    ChromaticMaterials,
    BLUEPRINT_STRATEGIES,
    MultiplicationStrategies
)
from app.models.config.markets import MarketConfiguration, Cost
from app.models.properties import Material
from libs.core.models import Dimensions, Multiple

UNIT_FOOTPRINT = 1024.0

class Materializer:
    markets: MarketConfiguration

    def __init__(self, markets: MarketConfiguration):
        self.markets = markets

    def cost(
        self,
        dimensions: Dimensions,
        material: str,
        blueprint: str,
        material_spec: Optional[Material] = None,
        blueprint_schema: Optional[str] = None,
        multiple: Optional[Multiple] = None
    ) -> List[Cost]:
        nx = multiple.nx if multiple and multiple.nx else 1
        ny = multiple.ny if multiple and multiple.ny else 1

        strategy = BLUEPRINT_STRATEGIES.get(
            blueprint_schema or "",
            MultiplicationStrategies.SIMPLE.value
        )
        if strategy == MultiplicationStrategies.EXPANSION.value:
            total_units = nx * (ny + 2)
        else:
            total_units = nx * ny

        norm_area = ((dimensions.w * dimensions.l) / UNIT_FOOTPRINT) * total_units
        delta = self.markets.blueprints.get(blueprint, 1.0)

        costs: List[Cost] = []
        if material_spec and material_spec.genus == MaterialGenera.CHROMATICS.value:
            host_item = material_spec.host
            mu_host = self.markets.materials.get(host_item, 1.0)
            host_qty = max(1, round(norm_area * mu_host * delta))
            costs.append(Cost(item=host_item, quantity=host_qty))

            if material != ChromaticMaterials.NEUTRAL.value:
                mu_dye = self.markets.materials.get(material, 1.0)
                dye_qty = max(1, round(norm_area * mu_dye))
                costs.append(Cost(item=material, quantity=dye_qty))
        else:
            mu_mat = self.markets.materials.get(material, 1.0)
            qty = max(1, round(norm_area * mu_mat * delta))
            costs.append(Cost(item=material, quantity=qty))

        return costs

```

###### Goal: 2D `MaterialFrame` & Blueprint-Aware `MaterialHitbox`

Implement `MaterialFrame` to index `(blueprint_row, material_col)` cells and `MaterialHitbox` to resolve collision geometry per blueprint partition.

```python
# src/app/assets/frames/crafts.py
class MaterialFrame(Frame):
    """
    Indexes 2D Strut Sheet atlases where rows correspond to Blueprint partitions
    and columns correspond to Material genus partitions.
    """
    def keys(self, id: str, state: StrutState) -> List[Tuple[str, int, int]]:
        if state and state.blueprint and state.material:
            key = settings.SEPARATOR.join([id, state.blueprint, state.material])
            return [(key, 0, 0)]
        return [(id, 0, 0)]

    def index(
        self,
        id: str,
        properties: CraftProperties
    ) -> Dict[str, Tuple[int, int, int, int]]:
        w = properties.dimensions.w
        l = properties.dimensions.l
        if not properties.material or not properties.blueprints:
            return {id: (0, 0, w, l)}

        rows = BLUEPRINT_PARTITIONS.get(properties.blueprints, ())
        cols = MATERIAL_PARTITIONS.get(properties.material.genus, ())

        atlas: Dict[str, Tuple[int, int, int, int]] = {}
        for r_idx, bp in enumerate(rows):
            for c_idx, mat in enumerate(cols):
                key = settings.SEPARATOR.join([id, bp, mat])
                atlas[key] = (c_idx * w, r_idx * l, w, l)
        return atlas

```

```python
# src/app/assets/hitboxes/crafts.py
class MaterialHitbox(HitboxSchema):
    """
    Resolves blueprint- and material-dependent hitboxes for Struts.
    Passable surface blueprints emit [] while structural blueprints emit active hitboxes.
    """
    def elevations(self, properties: CraftProperties, state: StrutState) -> List[int]:
        if getattr(state, "blueprint", None) not in OBSTACLE_BLUEPRINTS:
            return []
        return [max(0, state.elevation if state.elevation is not None else 0)]

    def get(
        self,
        properties: CraftProperties,
        state: StrutState,
        elevation: int,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        bp = getattr(state, "blueprint", None)
        if bp not in OBSTACLE_BLUEPRINTS:
            return []

        target_e = max(0, state.elevation if state.elevation is not None else 0)
        if max(0, elevation) != target_e:
            return []

        if properties.hitboxes is None:
            if properties.dimensions:
                return [Hitbox(Position(0, 0), properties.dimensions)]
            return []

        if isinstance(properties.hitboxes, dict):
            return properties.hitboxes.get(bp, []) or []

        return properties.hitboxes

```

###### Goal: Strategy-Driven `Decomposer.multiply()` (`simple` & `expansion`)

Implement `Decomposer.multiply()` to handle both 2D `simple` tiling (`buildings`, `corridors`) and vertical `expansion` capping (`columns`: `crown` at $y_0$, $n_y$ `shafts`, `base` at $y_0 + (n_y + 1)l$).

```python
# src/app/services/generators/game/decomposer.py
def multiply(
    self,
    state: StrutState,
    category: str,
    instance: str
) -> List[Asset]:
    cat_props = getattr(self.properties, category, {})
    instance_props = getattr(cat_props, instance, {})
    props = instance_props.get(state.id, None)

    if props is None:
        logger.error(
            settings.SEPARATOR.join([
                "Decomposer",
                "MultiplyMissingProperties",
                state.id
            ])
        )
        return []

    w = props.dimensions.w
    l = props.dimensions.l
    base_pos = state.position or Position(0, 0)
    layer = state.layer or "0"
    nx = state.multiple.nx if state.multiple and state.multiple.nx else 1
    ny = state.multiple.ny if state.multiple and state.multiple.ny else 1

    strategy = BLUEPRINT_STRATEGIES.get(
        props.blueprints or "",
        MultiplicationStrategies.SIMPLE.value
    )

    cat_recipes = getattr(self.recipes, category, None)
    recipe = getattr(cat_recipes, instance, None)
    unit_assets: List[Asset] = []
    idx = 0

    if strategy == MultiplicationStrategies.EXPANSION.value:
        # Column expansion: [crown] + ny * [shaft] + [base] along +y axis
        for ix in range(nx):
            col_x = base_pos.x + ix * w
            base_y = base_pos.y + (ny + 1) * l
            base_ground = base_y + l

            segments: List[Tuple[str, int]] = [
                (ColumnBlueprints.CROWNS.value, base_pos.y)
            ]
            for k in range(ny):
                segments.append(
                    (ColumnBlueprints.SHAFTS.value, base_pos.y + (k + 1) * l)
                )
            segments.append((ColumnBlueprints.BASES.value, base_y))

            for bp_part, seg_y in segments:
                unit_name = settings.SEPARATOR.join([
                    state.name or state.id,
                    bp_part,
                    str(idx)
                ])
                idx += 1
                seg_anchor = int(base_ground - (seg_y + l))

                unit_state = dataclasses.replace(
                    state,
                    name=unit_name,
                    layer=layer,
                    position=Position(col_x, seg_y),
                    blueprint=bp_part,
                    multiple=Multiple(1, 1),
                    anchor=seg_anchor
                )
                unit_assets.append(
                    Asset(
                        taxonomy=Factory.taxonomy(state.id, unit_name, category, instance),
                        properties=props,
                        state=unit_state,
                        frame=Factory.frame(recipe.frame),
                        animation=Factory.animation(recipe.animation),
                        hitbox=Factory.hitbox(recipe.hitbox)
                    )
                )
    else:
        # Simple 2D grid multiplication
        for iy in range(ny):
            for ix in range(nx):
                seg_pos = Position(base_pos.x + ix * w, base_pos.y + iy * l)
                unit_name = settings.SEPARATOR.join([
                    state.name or state.id,
                    str(idx)
                ])
                idx += 1

                unit_state = dataclasses.replace(
                    state,
                    name=unit_name,
                    layer=layer,
                    position=seg_pos,
                    multiple=Multiple(1, 1)
                )
                unit_assets.append(
                    Asset(
                        taxonomy=Factory.taxonomy(state.id, unit_name, category, instance),
                        properties=props,
                        state=unit_state,
                        frame=Factory.frame(recipe.frame),
                        animation=Factory.animation(recipe.animation),
                        hitbox=Factory.hitbox(recipe.hitbox)
                    )
                )

    return unit_assets

```

##### Tasks

**1. Task: Ordered Enumerations & Schema Models**

*Objective*: Codify the ordered `Material` genera, `Blueprint` schemas, `MultiplicationStrategies`, `StrutState`, and `CraftProperties` in the application models.

* [ ] Subtask: Add `MaterialGenera`, `OrganicMaterials`, `GeologicMaterials`, `MetallicMaterials`, `ChromaticMaterials`, `MATERIAL_PARTITIONS`, `BlueprintSchemas`, `BuildingBlueprints`, `CorridorBlueprints`, `ColumnBlueprints`, `BLUEPRINT_PARTITIONS`, `MultiplicationStrategies`, `BLUEPRINT_STRATEGIES`, `SUBSTRATE_BLUEPRINTS`, and `OBSTACLE_BLUEPRINTS` to `src/app/config/enums.py`.
* [ ] Subtask: Rename all references of `brick` to `feldspar` and `stone` to `limestone` across enums, configs, and property indices.
* [ ] Subtask: Update `src/app/models/properties.py` (and Pydantic adapters) to add `Material(genus, host)`, remove `cost` from `CraftProperties`, and add `material: Optional[Material]` and `blueprints: Optional[str]` to `CraftProperties`.
* [ ] Subtask: Update `src/app/models/state/assets/crafts.py` to define `StrutState(PropertyState)` with `material: Optional[str]`, `blueprint: Optional[str]`, and `multiple: Optional[Multiple]`, and update `CraftStateInstances.struts` in `src/app/models/state/schemas.py`.

**2. Task: `app.services.markets` & `Materializer` Implementation**

*Objective*: Decouple cost data from Craft properties into `/src/data/config/markets/main.yaml` and implement the `Materializer` service.

* [ ] Subtask: Create `src/app/models/config/markets.py` defining `Cost` and `MarketConfiguration`, and register `markets: MarketConfiguration` on `ConfigurationSchema`.
* [ ] Subtask: Create `/src/data/config/markets/main.yaml` containing the rebranded material valuation factors ($\mu_{\text{mat}}$ for `organics`, `geologics`, `metallics`, `chromatics`) and blueprint factors ($\delta_{\text{blueprint}}$).
* [ ] Subtask: Implement `Materializer` in `src/app/services/markets/materializer.py` with `cost(dimensions, material, blueprint, material_spec, blueprint_schema, multiple)` supporting chromatic host + dye decomposition and column expansion unit counts.
* [ ] Subtask: Remove `_accumulate_cost`, `_aggregate_components_cost`, `cost`, and `bridge_cost` from `src/app/services/generators/game/decomposer.py`.
* [ ] Subtask: Remove `cost` keys from all `/src/assets/crafts/**/*.yaml` files.

**3. Task: `MaterialFrame`, `MaterialHitbox` & Substrate Priority**

*Objective*: Implement 2D `(Blueprint, Material)` atlas indexing, blueprint-aware hitbox resolution, and substrate priority sorting.

* [ ] Subtask: Implement `MaterialFrame` in `src/app/assets/frames/` to index `{id}-{blueprint}-{material}` at `(c * w, r * l, w, l)` and resolve `keys(id, state)` from `(state.blueprint, state.material)`.
* [ ] Subtask: Implement `MaterialHitbox` in `src/app/assets/hitboxes/crafts.py` returning `[]` for passable blueprints (`floors`, `paths`, `solids`, `stripes`, `designs`, `crowns`, `shafts`) and active hitboxes for `OBSTACLE_BLUEPRINTS` (`walls`, `halls`, `bases`).
* [ ] Subtask: Update `Asset` / `Screen._sort` so `Strut` instances with `state.blueprint in SUBSTRATE_BLUEPRINTS` evaluate tertiary sort priority as `-1`.
* [ ] Subtask: Register `MaterialFrame` and `MaterialHitbox` in `Factory` and `src/data/config/recipes/main.yaml`.

**4. Task: Strategy-Driven `Decomposer.multiply()` & `Migrator` Integration**

*Objective*: Implement `simple` and `expansion` multiplication strategies in `Decomposer.multiply()` and wire them into `Decomposer` and `Migrator`.

* [ ] Subtask: Implement `Decomposer.multiply()` in `src/app/services/generators/game/decomposer.py` handling `simple` 2D grid expansion and `expansion` vertical column construction (`crown`, $n_y$ `shafts`, `base` with baseline `anchor` alignment).
* [ ] Subtask: Update `Decomposer._unpack_node()` and `Decomposer._unpack_components()` to route `AssetInstances.STRUTS` through `self.multiply()`.
* [ ] Subtask: Update `Migrator._build_generator()` in `src/app/services/orchestration/migrator.py` to route standalone `struts` state entries through `self.decomposer.multiply()`.
* [ ] Subtask: Add unit tests covering `simple` multiplication, `expansion` column capping (`base.position.y` greater than `crown.position.y`), and `MaterialFrame` key generation.

**5. Task: Strut Sheet Re-Indexing & Composition Migration**

*Objective*: Replace legacy `/src/assets/crafts/struts/**` indices with the 10 curated 2D Strut Sheets and refactor existing Compositions to the new schema.

* [ ] Subtask: Index `hut`, `home`, `store`, `suburb`, `mansion`, `hallway`, `carpet`, `avenue`, `pillar`, and `tower` in `/src/assets/crafts/struts/main.yaml` using `material: { genus, host }` and `blueprints`.
* [ ] Subtask: Relocate non-Strut decor and bespoke structures (`decor`, `structures`) to their dedicated Craft instances.
* [ ] Subtask: Refactor `src/data/config/compositions/main.yml` (`C000`, `C001`, `C002`) and `/src/data/state/**` to use the new `(id, blueprint, material, multiple)` Strut schema.

### Architectural Drill-Down: Dynamic `anchor`/`priority` vs. Relative `Substrates`

#### 1. Why Dynamic `anchor`/`priority` Resolution Breaks Down

Let $S$ be a walkable surface Strut (`floors`, `paths`, `flats`, `corridors`) or `Stairs` with dimensions $(w_S, l_S)$, and let $P$ be a Sprite with dimensions $(w_P, l_P) = (64, 64)$ on the same elevation $E$. When $P$ stands on $S$ north of its southern edge:

$$S.y < P.y + P.l < S.y + S.l \implies \text{ground\_y}(P) < \text{ground\_y}(S)$$

Because `Screen._sort` evaluates the lexicographical tuple $(\text{elevation}, \text{ground\_y}, \text{priority})$, the secondary key $\text{ground\_y}$ is strictly unequal ($\text{ground\_y}(P) < \text{ground\_y}(S)$), so the tertiary key $\text{priority}$ is **never evaluated**.

Attempting to solve this dynamically by mutating $S.\text{state.anchor}$ when $P$ intersects $S$ introduces three structural failures:

1. **Multi-Body Contradiction (Non-Scalar Anchor)**: `state.anchor` is a single scalar on $S$. Suppose a static wall or table $W$ rests on floor $S$ at baseline $W.y + W.l = S.y + 32$, while a Sprite $P$ stands on $S$ at baseline $P.y + P.l = S.y + 80$. To render under $P$, $S$ only needs $\text{ground\_y}(S) \le S.y + 80$; if $S.\text{anchor}$ is mutated to match $P$, then $\text{ground\_y}(S) = S.y + 80 > \text{ground\_y}(W) = S.y + 32$, causing the floor $S$ to **overdraw the wall/table $W$**!
2. **Static `anchor = -S.dimensions.l` Failure on Stacked Substrates**: If $S$ statically sets `anchor = -S.dimensions.l` so $\text{ground\_y}(S) = S.y$, then a `carpet` (`corridors`, $l = 96$) placed at $y = 0$ on top of a `floor` (`buildings`, $l = 96$) at $y = 0$ shares the exact same baseline $\text{ground\_y} = 0$ and `priority = -1`. Worse, if a smaller rug ($l = 64$) is placed near the bottom of a large room floor ($l = 400$) at $y = 300$, its top edge $y = 300 > 0$ sorts above the floor, whereas if a long runner ($l = 400$, $y = 0$) is placed over a local floor slab ($l = 96$, $y = 96$), the floor slab has $\text{ground\_y} = 96 > \text{ground\_y}(\text{runner}) = 0$, causing the floor slab to **overdraw the carpet runner**.
3. **Physics Pipeline Pollution**: Walkable Strut surfaces (`floors`, `paths`, `corridors`) have no collision footprint (`NoHitbox` / empty hitboxes). Dynamically computing `anchor` on intersection would force `CollisionMechanics` or `MotionMechanics` to run AABB overlap checks against every passive floor and carpet tile every frame.

---

#### 2. Why `Substrates` Worked for Fluids/Geography—and Why `Asset.elevation` Conflated Two Axes

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

---

#### 3. The Exact Solution: Fibered `(elevation, substrate, ground_y, priority)` Sorting

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

---

### Bug Report: Surface & Stair Overdraw

##### Bug B019: Walkable Surface Struts and Stairs Overdraw Traversing Sprites

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

In `Screen.draw()`, active renderables are sorted by `(asset.elevation, ground_y, asset.properties.priority)`. When a dynamic `Sprite` ($64 \times 64$) traverses a walkable surface `Strut` (`floors`, `paths`, `flats`, `corridors`) or `Stairs` (`steps-stone`) on the same `elevation` tier $E$, any position where the Sprite's feet are north of the surface's bottom edge ($P.y + P.l < S.y + S.l$) yields $\text{ground\_y}(P) < \text{ground\_y}(S)$. Because `ground_y` is evaluated prior to `priority`, the floor, carpet, or stair asset renders **on top of** the Sprite. Additionally, `Asset.elevation` in `src/app/assets/base.py` only queries `settings.SUBSTRATES` when `self.state.elevation is None`, causing any substrate asset with an explicit `state.elevation` (e.g., `0` or `1`) to lose its substrate ordering altogether.

**Steps to Replicate**

1. Deploy `steps-stone` (`w: 64, l: 96`) or a `floor-wood` / `support-granite-border` Strut (`w: 96, l: 96`) at `position: { x: 100, y: 100 }`, `elevation: 0`.
2. Move the Player Sprite (`w: 64, l: 64`, `elevation: 0`) onto the asset at `position: { x: 100, y: 110 }` such that `player.ground_y = 174 < surface.ground_y = 196`.
3. Observe that `Screen.draw()` renders the stair or floor texture over the Player Sprite.

**Proposed Remeditation**

1. Decouple macro-tier `Asset.elevation` ($\ge 0$) from intra-tier `Asset.substrate` ($\in [-4, 0]$) on `Asset` (`src/app/assets/base.py`):
```python
@property
def elevation(self) -> int:
    return self.state.elevation if self.state.elevation is not None else 0

@property
def substrate(self) -> int:
    bp = getattr(self.state, "blueprint", None)
    if bp and bp in settings.SUBSTRATES:
        return settings.SUBSTRATES[bp]
    return settings.SUBSTRATES.get(self.taxonomy.instance, 0)

```


2. Update `Screen._sort` in `src/app/game/screen.py` to sort by the 4-tuple `(asset.elevation, asset.substrate, ground_y, asset.properties.priority)`.
3. Register `AssetInstances.STAIRS.value: Substrates.OVERLAYS.value` (`-1`), `BuildingBlueprints` surfaces (`floors`, `paths`, `flats`: `-2`), and `CorridorBlueprints` (`solids`, `stripes`, `designs`: `-1`) in `settings.SUBSTRATES`.

---

### Addendum: Phase 07.04 Grooming Updates

The following sections append directly to **Refactor: Phase 07.04 - Materialization** to incorporate `User Review II`.

```markdown
##### User Review II

For Architectural Analysis #2.1, priority only matters when the elevations and vertical displacements are equal; it is the fallback tie-breaker. For dynamic Assets, when a Sprite is walking on a surface in which it is wholly contained (`sprite.state.position.y + sprite.dimensions.l < strut.state.position.y + strut.dimensions.l` AND `sprite.state.position.y > strut.state.position.y`), the surface will render on top of the Sprite (which also currently occurs with Stairs). 

Rather than dynamically resolving `anchor`/`priority` via collision checks, extend the `SUBSTRATES` mechanism so Strut blueprints and Stairs lazily resolve intra-tier substrate offsets relative to their deployed `elevation`.

##### Architectural Analysis III

###### Relative Intra-Tier `Substrates` (`Asset.substrate` & `Screen._sort`)

Previously, `Asset.elevation` returned negative `settings.SUBSTRATES` values only when `state.elevation is None`. Because Struts, Stairs, and Bridges can be deployed at arbitrary macro-elevations ($E \in \{0, 1, 2, \dots\}$) and receive explicit `state.elevation` integers during `Decomposer` hydration, intra-tier substrate ordering must be orthogonal to `state.elevation`.

1. **`Substrates` Enumeration (`src/app/config/enums.py`)**:
   ```python
   class Substrates(int, Enum):
       ENVIRON    = -4
       FLUIDS     = -3
       SHORELINES = -2
       SURFACES   = -2
       OVERLAYS   = -1
       STANDARD   =  0

```

2. **Blueprint & Instance Substrate Mapping (`src/app/config/settings.py`)**:
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

###### Updated Subtask in Task 3 (`MaterialFrame`, `MaterialHitbox` & Substrate Priority)

* [ ] Subtask: Add `Substrates.SURFACES (-2)` and `Substrates.OVERLAYS (-1)` to `src/app/config/enums.py`, map surface/corridor blueprints and `stairs` in `settings.SUBSTRATES`, expose `Asset.substrate` on `src/app/assets/base.py`, and update `Screen._sort` in `src/app/game/screen.py` to sort by `(asset.elevation, asset.substrate, ground_y, asset.properties.priority)`.

```

<FollowUp label="Want me to draft the implementation patch for Bug B019 in `base.py` and `screen.py`?" query="Draft the implementation patch for Bug B019 across `src/app/config/enums.py`, `src/app/config/settings.py`, `src/app/assets/base.py`, and `src/app/game/screen.py`, along with unit tests."/>

```