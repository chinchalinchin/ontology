#### Refactor: Phase 10.01 - Stage Hitboxes & Optimizations

**Overview**

Presently, `Resource` entities maintain static hitboxes declared on immutable `ResourceProperties` (`properties.hitboxes`). When `SeasonMechanics` transitions a resource across biological stages (e.g., from `sapling` to `adult` to `stump`, or `sprout` to `bloom`), physical hitboxes remain invariant. An adult oak tree retains the physical footprint of a sapling, and a harvested crop or stump blocks navigation identically to a mature plant. Furthermore, fallback hitbox logic treats empty hitbox declarations (`[]`) as falsy, forcing passable juvenile stages to obstruct characters with full-canopy bounding boxes.

This phase refactors hitbox resolution into an explicit, decoupled ECS behavior component (`HitboxSchema`), mirroring the architecture of `Frame` and `Animation`. Asset recipes declare their hitbox schema, and `Factory.hitbox()` injects pre-instantiated, zero-allocation behavior singletons into all hydrated assets. Dynamic biological lifecycle stages resolve collision bounds in $O(1)$ time while maintaining immutable property caching and contract invariance across all game mechanics.

##### Bug Reports

###### Bug B014: Falsy Hitbox Fallback Overrides Explicit Passable Entities

**STATUS**: OPEN
**SEVERITY**: High

**Description**

In `src/app/assets/base.py`, property hitbox resolution evaluates as follows:

```python
hbs = self.properties.hitboxes
if not hbs and self.dimensions:
    hbs = [Hitbox(Position(0, 0), self.dimensions)]
return hbs

```

When an entity explicitly declares an empty list of hitboxes (`hitboxes: []`) to indicate that it is passable (such as a juvenile crop sprout, a submerged fluid current sensor, or a decorative craft), Python's `not hbs` condition evaluates to `True`. The fallback overrides the empty list and assigns a hitbox matching the entire bounding box of the asset (`(0, 0, dimensions.w, dimensions.l)`). This makes intended passable entities completely impassable to characters and projectiles.

**Steps to Replicate**

1. Configure an asset with explicit dimensions `w: 32, l: 32` and an empty hitbox list `hitboxes: []`.
2. Instantiate the asset and query `asset.hitboxes`.
3. Observe that `asset.hitboxes` returns `[Hitbox(Position(0, 0), Dimensions(32, 32))]` instead of `[]`.

**Proposed Remediation**

Evaluate explicit `None` rather than falsiness:

```python
hbs = self.properties.hitboxes
if hbs is None and self.dimensions:
    return [Hitbox(Position(0, 0), self.dimensions)]
return hbs or []
```

##### Architectural Analysis I

###### 1. The Conflict with Static Hitbox Architecture

In `src/app/assets/base.py`, hitbox resolution evaluates as follows:

```python
@property
def hitboxes(self) -> List[Hitbox]:
    state_hbs = getattr(self.state, "hitboxes", None)
    if state_hbs is not None:
        return state_hbs
    hbs = self.properties.hitboxes
    if not hbs and self.dimensions:
        hbs = [Hitbox(Position(0, 0), self.dimensions)]
    return hbs

```

When `hitboxes: null` is configured on `ResourceProperties`:

1. `hbs` resolves to `None`.
2. `if not hbs and self.dimensions` assigns a fallback hitbox covering the entire entity bounding box (`(0, 0, 94, 137)` for a deciduous tree).
3. This creates two simulation bugs:
  * **Full-Canopy Obstruction**: In top-down 2.5D perspective, characters must walk behind the tree canopy (depth sorted by $y + l$). Obstructing the full $94 \times 137$ box makes the entire air canopy impassable.
  * **Juvenile Collision Imbalance**: A `sapling` (a 12px plant) shares the identical physical obstacle footprint as a mature $94 \times 137$ `adult` tree.

###### 2. Constraints

* **Immutability of Properties**: `AssetProperties` are static and must never mutate at runtime.
* **Zero Allocation in the Inner Loop**: Reconstructing `Hitbox` objects or allocating lists on each collision frame degrades performance.
* **Uniform Sprite Atlas Bounds**: In `StageFrame`, each stage cell occupies an identical $(w, l)$ slice ($94 \times 137$) along the horizontal strip. The coordinate space for hitboxes across all stages remains normalized relative to the cell's top-left origin $(0, 0)$.

###### 3. Resolution: Stage-Indexed Hitbox Mapping

Mirror the existing `SheetProperties.attackboxes` pattern:

* Allow `ResourceProperties.hitboxes` to accept either:
* A static `List[Hitbox]` (for uniform entities like boulders or ores).
* A stage dictionary `Dict[str, List[Hitbox]]` mapping biological stages (`sapling`, `bush`, `adult`, `stump`) to localized collision boxes.


* Update `Asset.hitboxes` to evaluate:
```python
if isinstance(hbs, dict):
    stage = getattr(self.state, "stage", None)
    if stage and stage in hbs:
        return hbs[stage]
    return hbs.get("default", [])

```

* Because `ResourceProperties` is pre-instantiated at boot, indexing `hbs[stage]` returns a cached `List[Hitbox]` in $O(1)$ time with zero heap allocation. When `SeasonMechanics` mutates `resource.state.stage`, the active collision footprint updates on the following frame.

##### User Review I

Not a fan of what `Asset.hitboxes` is turning into; It's slowly morphing into a nightmare of hyper-specific logic and filtering edge cases, making it hard to parse what exactly is going on or what the intention is. It requires one to know that hitboxes can be found along different property or state nodes in the Asset's field of attributes. It's not an utter monstrosity yet, but it soon will be at this rate.  The basic Asset class should be simple.

Change of direction. Asset Recipes are shown below,

```yaml
recipes:
  tiles:
    back:
      frame: seasonal
      animation: none
    fore:
      frame: single
      animation: none
  crafts:
    bridges:
      frame: oriented
      animation: none
    struts:
      frame: single
      animation: none
  cursors:
    expressions:
      frame: index
      animation: none
    projectiles:
      frame: single
      animation: none
  geography:
    shorelines:
      frame: cardinal
      animation: none
  effects:
    collectables:
      frame: iterable
      animation: lifecycle
    reactables:
      frame: iterable
      animation: lifecycle
    hazards:
      frame: iterable
      animation: lifecycle
    passive:
      frame: iterable
      animation: lifecycle
    fluids:
      frame: fluid
      animation: lifecycle
  objects:
    chests:
      frame: iterable
      animation: binary
    crates:
      frame: single
      animation: none
    doors:
      frame: single
      animation: none
    gates: 
      frame: iterable
      animation: binary
    obstacles:
      frame: single
      animation: none
    plates:
      frame: iterable
      animation: binary
    signs:
      frame: single
      animation: none
    rafts:
      frame: single
      animation: none
  resources:
    crops:
      frame: stage
      animation: none
    ore: 
      frame: stage
      animation: none
    trees:
      frame: stage
      animation: none
  sheets:
    players:
      frame: sprite
      animation: sprite
    pixies:
      frame: state
      animation: state
    sprites:
      frame: sprite
      animation: sprite
    armor:
      frame: state
      animation: none
    tools:
      frame: state
      animation: none
    shields:
      frame: state
      animation: none
    utilities:
      frame: state
      animation: none
    weapons:
      frame: state
      animation: none
  widgets:
    buttons:
      frame: traversal
      animation: traversal
    icons:
      frame: index
      animation: none
    meters:
      frame: meter
      animation: meter
    pages:
      frame: single
      animation: none
    panes:
      frame: single
      animation: none
```

Proposal: Recipes add a Hitbox schema.

- `static`: Static, property-based hitboxes
- `dynamic`: Dynamic, state-based hitboxes
- `attack`:  Attack-based hitboxes (used for Equipment)
- `stage`: Stage-based hitboxes

Equipment will require special care, as it is handled a bit differently. Currently Equipment looks at an optional field on the Sheet Properties, `attackboxes`, so the current refactor can proceed without altering combat mechanicS,  i.e. Equipment hitboxes are not accessed through the `Asset.hitboxes` interface at all. However, Equipment will eventually need to be brought into the new paradigm. This will require refining how Equipment is handled by Orchestration, which doesn't instantiate Equipment Asset, but instead passes Equipment properties through the Board, i.e. Equipment is treated like a stateless Asset (actually, a virtual Asset is more accurate, since Equipment is not instantiated at all, only its properties are referenced in the code)

First, hitbox is registered in the recipe, e.g.

```yaml
recipes:
  resources: 
    trees:
      frame: stage
      animation: none
      hitbox: stage
```

Do so for all existing Assets. Then, Hitbox is abstracted into a class,

```python
class PhysicalHitbox:
  def __init__(self, schema):
    self.schema = schema

  def get(
    id: str,
    properties: AssetProperties, 
    state: AssetState, 
    frame: Frame
  ):
    if schema == HitboxSchemas.STATIC.value:
      return properties.hitboxes

    if schema == HitboxSchemas.DYNAMIC.value:
      return state.hitboxes

    if schema == HitboxSchemas.ATTACK.value:
      key = next(frame.keys(id, state))
      if key:
        return properties.attackboxes[key]

    if schema == HitboxSchemas.STAGE.value:
      return properties.hitboxes[state.stage]
```

In other words, abstract the schema for accessing the hitbox into a well-defined interface.

This block in the Migrator is then changed to accomodate,

```python 
asset = Asset(
  taxonomy        = Factory.taxonomy(
      id          = asset_id, 
      name        = asset_name, 
      category    = category_key, 
      instance    = instance_key
  ),
  properties      = props,
  state           = state_obj,
  frame           = Factory.frame(recipe.frame),
  animation       = Factory.animation(recipe.animation),
  hitbox          = Factory.hitbox(recipe.hitbox)
)
```

Then the base becomes

```python
class Asset:
# ...
  def __init__(self,
    taxonomy: Taxonomy,
    properties: AssetProperties, 
    state: AssetState, 
    frame: Frame=None, 
    animation: Animation=None,
    hitbox: PhysicalHitbox=None,
  ):
    self.taxonomy = taxonomy
    self.properties = properties
    self.state = state
    self.frame = frame
    self.animation = animation
    self.hitbox = hitbox

  @property
  def hitboxes(self) -> List[Hitbox]:
    return self.hitbox.get(self.properties, self.state, self.frame)
```

Then, different hitbox implementations can be easily added. 

**IMPORTANT**: `Asset.hitboxes()` is a core interface for many mechanics, i.e. CollisionMechanics, CombatMechanics, InteractionMechanics. To avoid a substantial refactor, it is important whatever changes are made to the interface are purely internal and do not alter the contract the interface has with the rest of the application.

Evaluate this approach and update phase accordingly.

##### Architectural Analysis II

Elevating the Hitbox resolution mechanism to a first-class Entity-Component-System (ECS) behavior component—joining **Properties**, **State**, **Frame**, and **Animation**—directly aligns with Ontology's design philosophy.

However, implementing this via a single monolithic `PhysicalHitbox` class containing an internal `if/elif self.schema == ...` switch statement merely transposes the procedural branch from `Asset` into a helper class. A cleaner architecture that adheres strictly to the existing patterns in `app.assets.frames` and `app.assets.animations` is a polymorphic strategy hierarchy:

```
                  ┌──────────────────────┐
                  │  HitboxSchema (ABC) │
                  └──────────┬───────────┘
                             │
     ┌───────────────────────┼───────────────────────┬──────────────────────┐
     │                       │                       │                      │
┌────┴────────────┐   ┌──────┴────────────┐   ┌──────┴───────────┐   ┌──────┴──────────┐
│  StaticHitbox   │   │   DynamicHitbox   │   │   StageHitbox    │   │   NullHitbox    │
└─────────────────┘   └───────────────────┘   └──────────────────┘   └─────────────────┘

```

###### Advantages of the Polymorphic Strategy:

1. **Zero Inner-Loop Branching Overhead**: Polymorphic dispatch avoids evaluating a cascade of string/enum equality comparisons on every collision query or 60 Hz spatial check.
2. **Flyweight / Zero Allocation**: Because these behaviors operate as pure, stateless strategies on `(properties, state, frame)`, they can be pre-instantiated as singletons within `Factory` (e.g., `_STATIC = StaticHitbox()`). `Factory.hitbox(recipe.hitbox)` returns these cached singletons in $O(1)$ time, guaranteeing zero heap allocation during hydration.
3. **Open-Closed Extensibility**: Introducing new spatial schemas (such as rotational hitboxes or composite sensor hulls) requires only authoring a new subclass and registering it in `Factory.hitbox()`, leaving existing components untouched.
4. **Contract Invariance**: `Asset.hitboxes` remains an immutable `@property` returning `List[Hitbox]`. Downstream consumers (`CollisionMechanics`, `CombatMechanics`, `NavigationMechanics`, and Cython broad/narrow-phase pipelines) interact with the exact same interface without refactoring.

###### Cross-System Dependencies & Trace Analysis

Introducing a `hitbox` recipe parameter ripples across several subsystems:

```
┌─────────────────────────────────┐
│ src/data/config/recipes/*.yaml  │ ──► RecipeConfiguration (Pydantic / Dataclass)
└────────────────┬────────────────┘
                 │
                 ▼
     ┌───────────────────────┐
     │ Factory.hitbox(...)   │ ──► HitboxSchema Singleton (Flyweight)
     └───────────┬───────────┘
                 │
       ┌─────────┴─────────┐
       ▼                   ▼
┌──────────────┐   ┌──────────────┐
│   Migrator   │   │  Decomposer  │ ──► Asset(..., hitbox=Factory.hitbox(recipe.hitbox))
└──────────────┘   └──────────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │  Asset.hitboxes   │ ──► HitboxSchema.resolve(properties, state, frame)
                 └─────────┬─────────┘
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌─────────────────┐
│  Collision   │   │  Navigation  │   │     Screen      │
│  Mechanics   │   │  Mechanics   │   │ (Depth/Height)  │
└──────────────┘   └──────────────┘   └─────────────────┘

```

1. **Recipe Declarations & Enumerations**: Every entry across `src/data/config/recipes/main.yaml` requires an explicit `hitbox` field. To respect the constraint banning string literals, declare `HitboxRecipe` within `app.config.enums` as a `StringEnum` (e.g., `STATIC = "static"`, `DYNAMIC = "dynamic"`, `STAGE = "stage"`, `ATTACK = "attack"`, `NONE = "none"`).
2. **The Decomposer Impact**: While `Migrator` unpacks discrete assets from YAML state files, `Decomposer` programmatically synthesizes child assets for `Compositions` and `Bridges`. Both instantiation pipelines must query `Factory.hitbox(recipe.hitbox)` to avoid leaving `asset.hitbox` unbound or falling back to `None`.
3. **Passable Entity Falsy Bug**: In `app.assets.base`, `if not hbs and self.dimensions` treats empty lists (`hbs = []`) as falsy, immediately overwriting passable entities (such as juvenile saplings, fluid sensors, or open passages) with full bounding-box obstacles. This must be corrected to strictly evaluate `if hbs is None and self.dimensions`.
4. **Equipment Segregation**: Equipment remains virtual and stateless, referenced via `board.equipment` rather than instantiated into the board as standard `Asset` instances. `CombatMechanics` continues to query `CombatMap.attackboxes`. Adding `ATTACK` to `HitboxRecipe` establishes the schema for future equipment refactoring without disrupting combat resolution today.

###### Implementation Outline

**0. Data Models (`app.models.properties` and `app.models.config.recipes`)**

```python
# ResourceProperties model expansion
@dataclass(slots=True)
class ResourceProperties(AssetProperties):
    dimensions: Dimensions
    loot: str
    lifespan: Lifespans
    mass: int = 0
    hitboxes: Optional[Union[List[Hitbox], Dict[str, List[Hitbox]]]] = field(default_factory=dict)

# Recipe dataclass expansion
@dataclass(slots=True, frozen=True)
class Recipe:
    frame: FrameRecipe = None
    animation: AnimationRecipe = None
    hitbox: HitboxRecipe = None

```

**1. Polymorphic Behavior Component Hierarchy**

Rather than routing through branching logic within `Asset.hitboxes`, hitbox retrieval is delegated to an abstract `HitboxSchema` interface residing in `app.assets.hitboxes.base`:

```python
class HitboxSchema(ABC):
    @abstractmethod
    def resolve(
        self,
        properties: AssetProperties,
        state: AssetState,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        pass

```

The concrete strategies partition responsibilities cleanly:

* **`StaticHitbox`**: Evaluates static `properties.hitboxes`. If explicitly `None` and dimensions exist, applies the fallback bounding box. If empty list `[]`, returns `[]` without triggering bounding box substitution.
* **`DynamicHitbox`**: Checks `getattr(state, "hitboxes", None)`. Used by procedural geography (`Shorelines`) and hydraulic grids (`Fluids`) where boundary hulls update during world execution. Falls back to static hitboxes if `state.hitboxes` is absent.
* **`StageHitbox`**: Resolves stage-indexed dictionaries on `ResourceProperties`. Queries `properties.hitboxes.get(state.stage, properties.hitboxes.get("default", []))` in $O(1)$ time without runtime list re-allocation.
* **`NullHitbox`**: Emits an empty list `[]` unconditionally for passable background/foreground tiles, passive effects, and screen overlays.
* **`AttackHitbox`**: Resolves directional and action-keyed hitboxes (reserved for equipment integration).

**2. Zero-Allocation Singleton Pattern**

Strategy instances carry zero mutable state. `Factory` instantiates each behavior singleton once during application bootstrapping:

```python
class Factory:
    _HITBOX_STRATEGIES = {
        HitboxRecipe.STATIC: StaticHitbox(),
        HitboxRecipe.DYNAMIC: DynamicHitbox(),
        HitboxRecipe.STAGE: StageHitbox(),
        HitboxRecipe.NONE: NullHitbox(),
        HitboxRecipe.ATTACK: AttackHitbox(),
    }

    @classmethod
    def hitbox(cls, recipe_key: Optional[HitboxRecipe]) -> HitboxSchema:
        return cls._HITBOX_STRATEGIES.get(recipe_key, cls._HITBOX_STRATEGIES[HitboxRecipe.STATIC])

```

**3. Base Asset Contract Preservation**

`Asset` receives the injected strategy during instantiation:

```python
class Asset:
    taxonomy: Taxonomy
    properties: AssetProperties
    state: AssetState
    frame: Frame
    animation: Animation
    hitbox: HitboxSchema

    def __init__(
        self,
        taxonomy: Taxonomy,
        properties: AssetProperties,
        state: AssetState,
        frame: Optional[Frame] = None,
        animation: Optional[Animation] = None,
        hitbox: Optional[HitboxSchema] = None,
    ):
        self.taxonomy = taxonomy
        self.properties = properties
        self.state = state
        self.frame = frame
        self.animation = animation
        self.hitbox = hitbox or StaticHitbox()

    @property
    def hitboxes(self) -> List[Hitbox]:
        return self.hitbox.resolve(self.properties, self.state, self.frame)

```

##### Specification

###### 1. Recipe Configuration Schema (`src/data/config/recipes/main.yaml`)

```yaml
recipes:
  resources:
    crops:
      frame: stage
      animation: none
      hitbox: stage
    ore:
      frame: stage
      animation: none
      hitbox: stage
    trees:
      frame: stage
      animation: none
      hitbox: stage
  geography:
    shorelines:
      frame: cardinal
      animation: none
      hitbox: dynamic
  effects:
    fluids:
      frame: fluid
      animation: lifecycle
      hitbox: dynamic
    passive:
      frame: iterable
      animation: lifecycle
      hitbox: none
  tiles:
    back:
      frame: seasonal
      animation: none
      hitbox: none
    fore:
      frame: single
      animation: none
      hitbox: none

```

###### 2. Resource Hitbox Configuration (`src/assets/resources/main.yaml`)

```yaml
resources:
  trees:
    deciduous:
      dimensions:
        w: 94
        l: 137
      lifespan: perennial
      loot: wood
      mass: 0
      hitboxes:
        sapling:
          - position: { x: 42, y: 122 }
            dimensions: { w: 10, l: 12 }
        bush:
          - position: { x: 36, y: 114 }
            dimensions: { w: 22, l: 20 }
        branch:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        adult:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        vibrant:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        healthy:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        abscise:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        snowcapt:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        dying:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        dead:
          - position: { x: 36, y: 110 }
            dimensions: { w: 22, l: 24 }
        stump:
          - position: { x: 30, y: 115 }
            dimensions: { w: 34, l: 18 }
```

##### Goals

###### Goal: Hitbox Component Abstraction & Recipe Pipeline

Elevate hitbox resolution into a first-class, stateless behavior strategy. Integrate `HitboxRecipe` into recipe configurations, instantiate behavior singletons in `Factory`, and inject them into `Asset` across `Migrator` and `Decomposer`.

###### Goal: Declarative Stage Hitboxes & Model Extension

Support stage-partitioned hitbox dictionaries in `ResourceProperties` and Pydantic validators. Ensure mature trees collide exclusively at trunk bounds and juvenile stages remain freely traversable without canopy obstruction.

##### Tasks

**1. Task: Enum & Recipe Configuration Schema Expansion**

*Objective*: Define `HitboxRecipe` enumerations and integrate `hitbox` fields across recipe configuration schemas.

* [x] Subtask: Define `HitboxRecipe(StringEnum)` in `app.config.enums` with values `static`, `dynamic`, `stage`, `attack`, and `none`.
* [x] Subtask: Update `Recipe` in `app.models.config.recipes` to include `hitbox: Optional[HitboxRecipe] = HitboxRecipe.STATIC`.
* [x] Subtask: Populate `hitbox` definitions across all category blocks in `src/data/config/recipes/main.yaml` (`resources.*: stage`, `geography.shorelines: dynamic`, `effects.fluids: dynamic`, `tiles.*: none`, `effects.passive: none`, objects/crafts/sheets: `static`).

**2. Task: Hitbox Behavior Strategy Hierarchy**

*Objective*: Implement polymorphic `HitboxSchema` strategies with zero runtime heap allocation.

* [x] Subtask: Create `app.assets.base` declaring abstract interface `HitboxSchema(ABC)` with method `resolve(properties, state, frame) -> List[Hitbox]`.
* [ ] Subtask: Implement `StaticHitbox`, `DynamicHitbox`, `StageHitbox`, `NoHitbox`, and `AttackHitbox` in `app.assets.hitboxes`.
* [ ] Subtask: Fix the falsy hitbox bug by replacing `if not hbs and self.dimensions` with `if hbs is None and self.dimensions` across static fallbacks to preserve explicit `[]` passable declarations.
* [x] Subtask: Register pre-instantiated singletons in `Factory.hitbox()` within `app.services.generators.game.factory`.

**3. Task: Resource Properties Model Extension & YAML Configuration**

*Objective*: Support stage-indexed hitbox dictionaries in data models and author deciduous tree collision bounds.

* [x] Subtask: Update `ResourceProperties` in `app.models.properties` to type `hitboxes: Optional[Dict[str, List[Hitbox]]]`.
* [x] Subtask: Configure stage hitboxes for `trees.deciduous` in `src/assets/resources/main.yaml` constraining adult collision to trunk bounds (`x=36, y=110, w=22, l=24`) and stump bounds (`x=30, y=115, w=34, l=18`).
* [x] Subtask: Configure passable/empty hitboxes (`[]`) for juvenile crop stages in `src/assets/resources/main.yaml`.

**4. Task: ECS Injection in Migrator and Decomposer**

*Objective*: Update asset instantiation pipelines to inject `HitboxSchema` into `Asset` constructors.

* [~] Subtask: Update `Asset.__init__` in `app.assets.base` to accept `hitbox: Optional[HitboxSchema] = None` and delegate `@property def hitboxes` to `self.hitbox.resolve(self.properties, self.state, self.frame)`.
* [x] Subtask: Update `Migrator._build_generator` in `app.services.orchestration.migrator` to pass `hitbox=Factory.hitbox(recipe.hitbox)` to `Asset`.
* [x] Subtask: Update `Decomposer.unpack` and `Decomposer.bridge` in `app.services.generators.game.decomposer` to inject `Factory.hitbox(recipe.hitbox)` into generated constituent assets.
* [x] Subtack: Update `Cradle` instantiation methods to inject `Factory.hitbox(recipe.hitbox)`.

**5. Task: State Dump Serialization & Verification**

*Objective*: Verify dynamic stage collision resolution and test suite compatibility.

* [!] Subtask: Update `src/data/templates/state.md` to format `props.hitboxes` cleanly when configured as a stage dictionary.
* [!] Subtask: Author unit tests in `tests/unit/app/assets/test_hitboxes.py` verifying that `tree.hitboxes` matches trunk dimensions when `stage = "adult"`, stump dimensions when `stage = "stump"`, and passes through canopy coordinates without collision.
* [!] Subtask: Execute live verification via `python src/cli.py --dump-state start` ensuring characters navigate freely behind deciduous tree canopies.
