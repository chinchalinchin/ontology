#### Context: Draft Notes

**Motivation** 

- Reduce the Strut overhead and Asset proliferation by affecting a simplification through hierarchical organization of Struts via `material` and `blueprint`.

**Context**

- The Asset Hierarchy has been an endeavor to impose a strict schema on Asset files from the LPC asset database. The raw Asset files, with a few exceptions like Sprite Sheets and Tile Atlases, do not have a regular schema. Much of the work of the project has been "discovering" the relationships within the Asset files and re-aligning their atlases to conform to a Frame schema.

**Notes**

- Determine which Assets need pruned to ensure all conform to the schema and simplify the amount of boilerplate.
- Many assets will need edited so their dimensions align along the `material` axis, or else MaterialHitbox will need introduced so segregate hitboxes by `material`.
- How to handle decor, which has a Material dependence, but does not conform to partitioning. Perhaps Decor should be a separate Craft category, due to the bespoke nature of the Asset file.
    - Many Strut Structures, Enclosures and Additions also have this property of oblique, but not categorical, dependence on marble, i.e. they don't partition cleanly into frames.
- Strut Frames (`frame-brick`, `frame-adobe`, etc.) do not exactly conform to the `material`, `blueprint` schema due to the specialization of the Asset file. They may also be candidates for a separate Instance in the Craft Category.
- Materials, Blueprints: Enumeration of all Strut materials and blueprints.
- MaterialFrame: Index Assets by material columns.
- PropertyState: `material` and `blueprint` definition and specification.
- Decomposer needs an analogous method to `orient()` for `multiply()` for Assets without orientations that still need multiplied. It has become clear certain Struts (walls, surfaces, buttresses) need to be able to multiply their dimensions to conserve verbosity in the configuration.
    - Needs to be called during Migrator state migration.
    - This seems to indicate another Instance of Crafts is necessary to support MultiplierStates and simple positional PropertyStates. 

---

#### Refactor: Phase 07.04 - Materialization

**Overview**

Reduce `Strut` configuration overhead, YAML state verbosity, and Asset file proliferation by partitioning `Crafts` into distinct functional Instances (`struts`, `structures`, `decor`), indexing multi-material `Strut` atlases along a `material` axis via `MaterialFrame` and `MaterialHitbox`, and introducing 2D grid expansion (`Decomposer.multiply()`) across `Decomposer` and `Migrator`.

##### Specification

1. **Taxonomic Partitioning of `Crafts**`:
    * **`struts` (`StrutState`, `MaterialFrame`, `MaterialHitbox`)**: Modular, repeatable architectural primitives (`walls`, `surfaces`, `buttresses`, `pillars`, `roofs`) whose textures partition cleanly across a `Materials` enum axis and support 2D grid multiplication (`multiple: Multiple(nx, ny)`).
    * **`structures` (`PropertyState`, `SingleFrame`, `StaticHitbox`)**: Monolithic or bespoke architectural shells, enclosures, frames, additions, and towers (`frame-brick`, `frame-adobe`, `gazebo-stone`, `chimney-brick`, `tower-*`, `skylight-iron-octagon`, `awning-canvas-square`) that have material-derived crafting costs but do not partition into multi-material sprite atlases or tile via grid multipliers.
    * **`decor` (`PropertyState`, `SingleFrame`, `StaticHitbox`)**: Bespoke interior and exterior furnishings, fixtures, shelving, tables, wall decals, paintings, curtains, and windows (`fixture-*`, `shelf-*`, `table-*`, `painting-*`, `curtains-*`, `window-*`).
2. **Enumerations (`app.config.enums`)**:
    * `Materials`: `wood`, `sandstone`, `clay`, `stone`, `slate`, `brick`, `copper`, `cotton`, `granite`, `iron`, `glass`, `marble`, `gold`.
    * `Blueprints`: `bridges`, `carpentry`, `decor`, `platforms`, `railings`, `surfaces`, `stairs`, `structures`, `walls`.
    * `MultipliedAssets`: Tuple/Enum registering `(AssetInstances.STRUTS,)` for 2D grid unpacking during state hydration.
3. **Atlas & Frame Specification (`MaterialFrame`)**:
    * Multi-material `Strut` `.png` files are arranged as a single horizontal row of uniform cells $(w, l)$, where column index $i \in [0, M)$ corresponds to `properties.materials[i]`.
    * Crop key format: `f"{id}-{material}"` $\to$ `(i * w, 0, w, l)`.
4. **2D Grid Multiplication (`Decomposer.multiply`)**:
    * Unpacks a `StrutState` with `multiple: Multiple(nx, ny)` into $n_x \times n_y$ unit `Asset` instances positioned at $(x_0 + i_x \cdot w,\; y_0 + i_y \cdot l)$ for $i_x \in [0, n_x),\; i_y \in [0, n_y)$, resetting each spawned unit's state to `Multiple(1, 1)`.

##### Architectural Analysis I

###### 1. Composition Boilerplate Compression via `Decomposer.multiply()`

In `Composition C002` (`regalia-galleria`), paving the $768 \times 288$ central concourse required 24 discrete `support-granite-border` entries and 6 `wall-palace` entries. By equipping `StrutState` with `multiple: Multiple(nx, ny)` and invoking `Decomposer.multiply()` inside both `Decomposer._unpack_node()` (for root/branch struts) and `Decomposer._unpack_components()` (for child components):

```yaml
# Before (30 YAML definitions for 1 hallway shell):
- id: support-granite-border
  name: hallway-floor-r0c0
  position: { x: 0, y: 0 }
# ... repeated 23 more times

# After (2 YAML definitions for the entire hallway shell):
- strut:
    id: wall-palace
    name: hallway-wall-north
    material: stone
    blueprint: walls
    multiple: { nx: 6, ny: 1 }
    layer: 'galleria-hallway'
    position: { x: 0, y: 0 }
  components:
    crafts:
      struts:
        - id: support-border
          name: hallway-floor
          material: granite
          blueprint: surfaces
          multiple: { nx: 8, ny: 3 }
          position: { x: 0, y: 0 }

```

Because `Decomposer.multiply()` emits unit `Asset` objects with `Multiple(1, 1)` prior to `Board.add()`, `Screen.draw()` Painter's Algorithm sorting, `Perimeter` contour generation, `CollisionMechanics`, and `Board.serialize()` require zero downstream changes.

###### 2. Atlas Dimension Normalization vs. `MaterialHitbox`

`Registry` crop indexing and `Asset.dimensions` require each `Asset` ID to declare a single bounding canvas size `Dimensions(w, l)`. Auditing `/src/assets/crafts/struts/**` reveals two distinct sources of dimensional variance across material variants:

1. **Incidental LPC Crop Drift (1–4 px variance)**:
    * Raw walls: `wall-brick` ($92 \times 96$), `wall-slate` ($94 \times 96$), `wall-wood` ($95 \times 96$), `wall-iron` ($96 \times 97$).
    * Streets: `street-cobblestone` ($92 \times 89$), `street-concrete` ($96 \times 94$), `street-granite` ($96 \times 95$), `street-stone` ($96 \times 96$).
    * Shingles: `shingle-brick-hexagon` ($96 \times 52$), `shingle-marble-hexagon` ($96 \times 52$), `shingle-slate-hexgaon` ($95 \times 52$).
    * **Resolution**: Normalize and pad/crop these `.png` cells to canonical tile multiples ($96 \times 96$ for walls/streets/supports, $96 \times 52$ for hexagon shingles, $128 \times 134$ for square shakes) when stitching the horizontal material atlases.
2. **Intrinsic Structural Geometry Variance**:
    * Standard pillars vary in shaft width and height across materials: `pillar-wood` ($12 \times 96$), `pillar-marble` ($20 \times 96$), `pillar-slate` ($22 \times 150$), `pillar-sandstone` ($32 \times 121$).
    * **Resolution**: Pad the atlas cell canvas to the bounding maximum ($32 \times 150$, bottom-aligned so `ground_y` baselines remain invariant) and use `MaterialHitbox` to resolve material-specific collision footprints from `properties.hitboxes[state.material]`. `MaterialHitbox.get()` will support both `list` (uniform hitbox across all materials in the atlas) and `dict` (per-material hitbox override).

###### 3. Pruning & Reclassification Audit

| Current Location | Asset IDs | Target Disposition | Rationale |
| --- | --- | --- | --- |
| `struts/walls` | `wall-brick`, `wall-iron`, `wall-slate`, `wall-stone`, `wall-terracotta`, `wall-thatches`, `wall-wood` | Consolidate $\to$ `struts`: `wall-raw` (`materials: [wood, clay, stone, slate, brick, iron]`); prune `wall-thatches` | `thatches` is non-standard in Material table; `terracotta` maps to `clay`/`brick`. |
| `struts/walls` | `frame-adobe`, `frame-brick`, `frame-hut`, `frame-sandstone`, `frame-wood` | Move $\to$ `structures` (prune `frame-hut`) | Pre-composed building facades with roofs/stoops; bespoke geometry per climate. |
| `struts/surfaces` | `street-cobblestone`, `street-concrete`, `street-granite`, `street-sandstone`, `street-stone` | Consolidate $\to$ `struts`: `street` (`materials: [sandstone, stone, granite]`); prune `street-concrete` | `concrete` is an anachronistic outlier not in the Material valuation table. |
| `struts/surfaces` | `support-granite-border`, `support-stone-border`, `support-stone`, `floor-wood` | Consolidate $\to$ `struts`: `support` & `support-border` | Standard $96 \times 96$ / $128 \times 96$ interior flooring substrates. |
| `struts/surfaces` | `shingle-*-square`, `shingle-*-hexagon`, `shingle-*-sloped`, `base-*-sloped`, `shakes-*-square` | Consolidate $\to$ `struts` by roof shape (`materials: [brick, slate, marble]`); prune `thatches-reeds-*` | Cleanly partitions along `[brick, slate, marble]`; reeds/thatch pruned. |
| `struts/surfaces` | `skylight-iron-octagon`, `awning-canvas-square`, `panels-granite` | Move $\to$ `structures` | Bespoke singular roof fixtures. |
| `struts/structures` | `buttress-marble`, `buttress-slate`, `buttress-stone` | Consolidate $\to$ `struts`: `buttress` (`materials: [stone, slate, marble]`) | Identical $64 \times 33$ dimensions and hitboxes across all three materials. |
| `struts/structures` | `pillar-stone-corinthian`, `pillar-stone-doric`, `pillar-stone-ionic`, `pillar-*` | Consolidate $\to$ `struts`: `pillar`, `pillar-doric`, `pillar-ionic`, `pillar-corinthian` | Columnar structural supports. |
| `struts/structures` | `chimney-brick`, `gazebo-stone`, `tower-*` | Move $\to$ `structures` (prune `tower-brick-smokestack`) | Bespoke silhouettes; industrial smokestack pruned. |
| `struts/decor` | `fixture-*`, `shelf-*`, `table-*`, `curtains-*`, `painting-*`, `window-*` | Move $\to$ `decor` | Bespoke household and gallery items (`SingleFrame`, `StaticHitbox`, `PropertyState`). |

###### 4. Cost Calculation with Material & Multipliers

Currently, `Decomposer._accumulate_cost()` looks up `props.cost` by `asset_id` alone and ignores `state.multiple` and `state.material`. Under Materialization:

* A `Strut` with `multiple: Multiple(nx, ny)` scales its base cost by $n_x \times n_y$.
* For multi-material `Struts`, `CraftProperties.cost` can either be keyed by material (`Dict[str, List[Cost]]`) or computed/scaled from the base footprint and `state.material`. Supporting `Union[List[Cost], Dict[str, List[Cost]], None]` on `CraftProperties.cost` allows exact per-material ledger costs while retaining `List[Cost]` for single-material `structures` and `decor`.

##### User Review I

###### Cost

Cost is extraneous as a property. It can be derived from the area, material, material cost and blueprint. Remove cost property from Crafts, move material cost table to configuration, and remove all cost functions from the Decomposer. Need a new type of service, `app.services.markets`, and a new `Materializer` service. Receives cost configuration during bootstrap, exposes an interface `cost()` that accepts Dimensions, Material, Blueprint and then calculates the list of Costs, e.g. `[ Cost(material, amount) ]`. 

###### Reatlasing 

By curating combinations of different Asset files in the LPC database, the following sheets have been constructed so each cell is exactly 96 px by 96 px.

- Strut Sheet: (bluebrint, material)
    - id: hut
        - blueprints (rows): floors, walls, flats, roofs, paths, halls
        - materials (columms): thatches, wood
    - id: home 
        - blueprints (rows): floors, walls, flats, roofs, paths, halls
        - materials (columns): stone, brick, granite, marble
    - id: mansion
        - blueprints (rows): floors, walls, flats, roofs, paths, halls
        - materials (columns): stone, brick, granite, marble

**Materials**

- Organics: `wood`, `thatches`
- Geologics: `brick`, `granite`, `marble`, `stone`, `sandstone`
- Metallics: `copper`, `iron`, `gold`
- Chromatics: `white`, `red`, `blue`, `yellow`, `green`

**Blueprints**

- Building Blueprints:
    - `floors`: Interior ground surfaces.
    - `walls`: Exterior support surfaces.
    - `flats`: Elevated support surfaces.
    - `roofs`: Building enclosures.
    - `paths`: Exterior ground surfaces.
    - `halls`: Interior support surfaces.
- Corridor Blueprints:
    - `carpets`: Interior ground surfaces
    - `paints`: Interior support surfaces.
    - `planks`: Interior ground surfaces.
    - `wallpapers`: Interior support surfaces.

**Idea**

Struts declare Materials (`organics`, `geologics`, `metallics`, `chromatics`) and Blueprints (`building`, `interior`)
**Notes**

```python
@dataclass
class MaterialState(AssetState):
    # ...
    material: str
    blueprint: str
```

```python
class Materials(str, Enum):
    ORGANICS        = "organics"
    GEOLOGICS       = "geologics"
    METALLICS       = "metallics"

class Organics(str, Enum):
    THATCHES        = "thatches"
    WOOD            = "wood"

class Geologics(str, Enum):
    BRICK           = "brick"
    GRANITE         = "granite"
    MARBLE          = "marble"
    SANDSTONE       = "sandstone"
    SLATE           = "slate"
    STONE           = "stone"
    
class Metallics(str, Enum):
    COPPER          = "copper"
    IRON            = "iron"
    SILVER          = "silver"
    GOLD            = "gold"

class Chromatics(str, Enum):
    WHITE           = "white"
    BLUE            = "blue"
    RED             = "red"
    YELLOW          = "yellow"
    GREEN           = "green"

class Blueprints(str, Enum):
    BUILDINGS       = "buildings"

class Buildings(str, Enum):
    FLATS           = "flats"
    FLOORS          = "floors"
    HALLS           = "halls"
    PATHS           = "paths"
    ROOFS           = "roofs"
    WALLS           = "walls"

class Interiors(str, Enum):
    CARPETS         = "carpets"
    WALLPAPERS      = "wallpapers"
```

##### Goals

###### Goal: Enumerations & Data Models (`enums.py`, `properties.py`, `crafts.py`, `schemas.py`)

Define `Materials`, `Blueprints`, and `MultipliedAssets` in `app.config.enums`. Expand `CraftProperties` to support `materials: Optional[List[str]]` and material-keyed `cost`. Define `StrutState` for materialized, multipliable struts while retaining `PropertyState` for `structures`, `decor`, and `compositions`.

```python
# src/app/config/enums.py
class Materials(StrEnum):
    WOOD = "wood"
    SANDSTONE = "sandstone"
    CLAY = "clay"
    STONE = "stone"
    SLATE = "slate"
    BRICK = "brick"
    COPPER = "copper"
    COTTON = "cotton"
    GRANITE = "granite"
    IRON = "iron"
    GLASS = "glass"
    MARBLE = "marble"
    GOLD = "gold"

class Blueprints(StrEnum):
    BRIDGES = "bridges"
    CARPENTRY = "carpentry"
    DECOR = "decor"
    PLATFORMS = "platforms"
    RAILINGS = "railings"
    SURFACES = "surfaces"
    STAIRS = "stairs"
    STRUCTURES = "structures"
    WALLS = "walls"

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
# src/app/models/properties.py
@dataclass(slots=True)
class CraftProperties(AssetProperties):
    materials: Optional[List[str]] = field(default_factory=list)
    cost: Union[List[Cost], Dict[str, List[Cost]], None] = field(default_factory=list)
    mass: int = 0
    hitboxes: Optional[Union[Dict[int, List[Hitbox]], Dict[str, Optional[List[Hitbox]]], List[Hitbox]]] = None  # type: ignore

@dataclass(slots=True)
class CraftPropertyInstances:
    struts: Dict[str, CraftProperties] = field(default_factory=dict)
    structures: Dict[str, CraftProperties] = field(default_factory=dict)
    decor: Dict[str, CraftProperties] = field(default_factory=dict)
    bridges: Dict[str, CraftProperties] = field(default_factory=dict)
    platforms: Dict[str, CraftProperties] = field(default_factory=dict)
    stairs: Dict[str, CraftProperties] = field(default_factory=dict)
    railings: Dict[str, CraftProperties] = field(default_factory=dict)
    carpentry: Dict[str, CraftProperties] = field(default_factory=dict)

```

###### Goal: `MaterialFrame` & `MaterialHitbox` Strategies

Implement `MaterialFrame` to slice horizontal material atlases by `properties.materials` and `MaterialHitbox` to resolve either uniform (`list`) or material-segregated (`dict`) hitboxes.

```python
# src/app/assets/frames/crafts.py
class MaterialFrame(Frame):
    """
    Indexes multi-material Craft atlases arranged in a single horizontal row
    ordered by properties.materials.
    """
    def keys(self, id: str, state: StrutState) -> List[Tuple[str, int, int]]:
        if state and getattr(state, "material", None):
            return [(f"{id}{settings.SEPARATOR}{state.material}", 0, 0)]
        return [(id, 0, 0)]

    def index(
        self,
        id: str,
        properties: CraftProperties
    ) -> Dict[str, Tuple[int, int, int, int]]:
        w = properties.dimensions.w
        l = properties.dimensions.l
        if not properties.materials:
            return {id: (0, 0, w, l)}
        return {
            f"{id}{settings.SEPARATOR}{mat}": (i * w, 0, w, l)
            for i, mat in enumerate(properties.materials)
        }

```

```python
# src/app/assets/hitboxes/crafts.py
class MaterialHitbox(HitboxSchema):
    """
    Resolves material-partitioned or uniform hitboxes declared on CraftProperties.
    """
    def elevations(self, properties: CraftProperties, state: StrutState) -> List[int]:
        return [max(0, state.elevation if state.elevation is not None else 0)]

    def get(
        self,
        properties: CraftProperties,
        state: StrutState,
        elevation: int,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        target_e = max(0, state.elevation if state.elevation is not None else 0)
        if max(0, elevation) != target_e:
            return []
        if properties.hitboxes is None:
            if properties.dimensions:
                return [Hitbox(Position(0, 0), properties.dimensions)]
            return []
        if isinstance(properties.hitboxes, dict):
            return properties.hitboxes.get(state.material, []) or []
        return properties.hitboxes

```

###### Goal: `Decomposer.multiply()` & `Migrator` State Unpacking

Implement 2D grid expansion in `Decomposer.multiply()` and wire it into `Decomposer._unpack_node()`, `Decomposer._unpack_components()`, `Decomposer._accumulate_cost()`, and `Migrator._build_generator()`.

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

    unit_assets: List[Asset] = []
    cat_recipes = getattr(self.recipes, category, None)
    recipe = getattr(cat_recipes, instance, None)

    idx = 0
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

            unit_asset = Asset(
                taxonomy=Factory.taxonomy(
                    state.id,
                    unit_name,
                    category,
                    instance
                ),
                properties=props,
                state=unit_state,
                frame=Factory.frame(recipe.frame),
                animation=Factory.animation(recipe.animation),
                hitbox=Factory.hitbox(recipe.hitbox)
            )
            unit_assets.append(unit_asset)

    return unit_assets

```

```python
# src/app/services/orchestration/migrator.py
elif task[0] == Shortcuts.ASSETS.value and \
    task[2] in MultipliedAssets:

    multiplied_state = task[3]
    multiplied_assets = self.decomposer.multiply(multiplied_state, task[1], task[2])
    self.board.add(multiplied_assets)

```

##### Tasks

**1. Task: Enumerations, Schemas & Recipes**

*Objective*: Introduce `Materials`, `Blueprints`, `MultipliedAssets`, and the partitioned Craft Instances (`struts`, `structures`, `decor`) across application models and recipe configurations.

* [ ] Subtask: Add `Materials`, `Blueprints`, `MultipliedAssets`, and `AssetInstances.STRUCTURES` / `AssetInstances.DECOR` to `src/app/config/enums.py`.
* [ ] Subtask: Update `CraftProperties` and `CraftPropertyInstances` in `src/app/models/properties.py` (and corresponding Pydantic adapters) to add `materials: Optional[List[str]]`, `structures`, and `decor`.
* [ ] Subtask: Define `StrutState` (with `material`, `blueprint`, `multiple`) in `src/app/models/state/assets/crafts.py` and register `struts: List[StrutState]`, `structures: List[PropertyState]`, and `decor: List[PropertyState]` in `CraftStateInstances` (`src/app/models/state/schemas.py`).
* [ ] Subtask: Update `CompositionPseudoState.strut` typing in `src/app/models/config/compositions.py` to `Union[StrutState, PropertyState]`.
* [ ] Subtask: Register recipes for `crafts.struts` (`MaterialFrame`, `MaterialHitbox`), `crafts.structures` (`SingleFrame`, `StaticHitbox`), and `crafts.decor` (`SingleFrame`, `StaticHitbox`) in `src/data/config/recipes/main.yaml`.

**2. Task: `MaterialFrame` & `MaterialHitbox` Implementation**

*Objective*: Implement and register the frame indexing and hitbox resolution strategies for material-parameterized `Struts`.

* [ ] Subtask: Implement `MaterialFrame` in `src/app/assets/frames/` to index `{id}-{material}` crops across `properties.materials` with fallback to `{id}` when `materials` is empty.
* [ ] Subtask: Implement `MaterialHitbox` in `src/app/assets/hitboxes/crafts.py` supporting both uniform `List[Hitbox]` and material-keyed `Dict[str, List[Hitbox]]`.
* [ ] Subtask: Register `MaterialFrame` and `MaterialHitbox` in `Factory` (`src/app/services/generators/game/factory.py`).
* [ ] Subtask: Add unit tests verifying `Registry` crop-map generation and `Asset.hitboxes` resolution across material variants.

**3. Task: `Decomposer.multiply()` & `Migrator` Hydration**

*Objective*: Enable 2D grid multiplication (`nx`, `ny`) for `Struts` during both standalone state migration and Composition unpacking, and update cost aggregation.

* [ ] Subtask: Implement `Decomposer.multiply()` in `src/app/services/generators/game/decomposer.py`.
* [ ] Subtask: Update `Decomposer._unpack_node()` and `Decomposer._unpack_components()` to route `MultipliedAssets` (and multiplied root/branch struts) through `self.multiply()`.
* [ ] Subtask: Update `Decomposer._accumulate_cost()` to resolve material-specific cost entries and scale quantities by `multiple.nx * multiple.ny`.
* [ ] Subtask: Update `Migrator._build_generator()` in `src/app/services/orchestration/migrator.py` to dispatch `task[2] in MultipliedAssets` to `self.decomposer.multiply()`.
* [ ] Subtask: Add unit tests for `Decomposer.multiply()`, multiplied Composition unpacking, and scaled cost calculation.

**4. Task: Craft Asset Pruning, Atlas Stitching & Re-Indexing**

*Objective*: Prune non-conforming LPC assets, separate `decor` and `structures` into dedicated directories, stitch multi-material `.png` atlases to uniform cell dimensions, and update YAML property indices.

* [ ] Subtask: Prune non-conforming assets (`wall-thatches`, `street-concrete`, `thatches-reeds-*`, `frame-hut`, `tower-brick-smokestack`) from `/src/assets/crafts/struts/`.
* [ ] Subtask: Relocate `decor` assets (`fixture-*`, `shelf-*`, `table-*`, `curtains-*`, `painting-*`, `window-*`) to `/src/assets/crafts/decor/` and re-index under `crafts.decor`.
* [ ] Subtask: Relocate monolithic architectural assets (`frame-*`, `gazebo-stone`, `chimney-brick`, `tower-*`, `skylight-iron-octagon`, `awning-canvas-square`, `panels-granite`) to `/src/assets/crafts/structures/` and re-index under `crafts.structures`.
* [ ] Subtask: Normalize cell dimensions and stitch horizontal material atlases for `struts` (`wall-raw`, `wall-refined`, `wallpaper`, `wall-panel`, `support`, `support-border`, `street`, `carpet`, `buttress`, `pillar`, `shingle-*`, `shakes-square`, `base-sloped`), updating `/src/assets/crafts/struts/**/*.yaml` with `materials`, `hitboxes`, and `cost`.

**5. Task: Composition & Board State Refactoring**

*Objective*: Migrate existing Compositions (`C000: Castle Dawn`, `C001: Citadel of Trials`, `C002: Regalia Galleria`) and Board state files to the materialized schema and `multiple` grid syntax.

* [ ] Subtask: Refactor `src/data/config/compositions/main.yml` to replace repeated wall and floor strut lists with `multiple: { nx, ny }`, `material`, and `blueprint`, and move `decor`/`structures` components to their respective schema keys.
* [ ] Subtask: Update `/src/data/state/**` board files referencing legacy strut IDs.
* [ ] Subtask: Update `01-assets.md` and `03-compositions.md` documentation and Mermaid hierarchy diagrams to reflect `struts`, `structures`, and `decor`.