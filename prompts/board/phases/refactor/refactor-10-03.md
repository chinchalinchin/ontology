#### Refactor: Phase 10.03 - Flowers, Pixies & Reproduction

**Overview**

Implements the `Flower` resource type, codifies the `Pixie` asset category for lightweight 4-row directional fauna, and introduces `FaunaMechanics` to govern insect instincts, pollination, and gradient-driven seed dispersion..

##### Architectural Analysis

Integrating floral reproduction and entomological fauna connects three decoupled engine subsystems:

1. **Hydrological Potential Fields** (`MoistureField`): Providing environmental gradients for directional propagation.
2. **Resource Lifecycle Automata** (`SeasonMechanics` & ISL `Executor`): Regulating vegetative, bloom, and seed phases.
3. **Kinematic Airborne Entities** (`Pixies` & `FaunaMechanics`): Lightweight agents bypassing terrain-bound RRT pathfinding.

```
       [ SeasonMechanics (1 Hz) ]
                   │
                   ▼ (Transitions to 'bloom')
           Flower (Resource) ───────────┐
                   │                     │ Attracts (Sensory Radius)
                   │                     ▼
                   │             Bee (Pixie / Sheet)
                   │                     │
                   │ Pollinated by       │ Intersects Hitbox
                   │ (FaunaMechanics)    │
                   ▼                     ▼
          Evaluate Gradient:      Transition Instinct:
          ∇Φ(x, y) on Field      POLLINATE ──> ROAM
                   │
                   ▼
          Cradle.spawn_child(
              x + h·u_grad, 
              stage='sprout'
          )
```

###### 1. Mathematical Formulation: Moisture Gradient Reproduction

Let $\Phi(\mathbf{x})$ denote the soil moisture potential field at coordinates $\mathbf{x} = (x, y)$ on layer $L$, evaluated as the linear superposition of active stream segments and annular pools:


$$
\Phi(\mathbf{x}) = \sum_{i \in \text{Streams}} \Phi_i(\mathbf{x}) + \sum_{j \in \text{Pools}} \Phi_j(\mathbf{x})
$$

The directional propagation of a pollinated flower follows the local gradient $\nabla \Phi(\mathbf{x})$. To maintain grid alignment and prevent continuous sub-pixel drift into static obstacles, the child spawn location $\mathbf{x}_{\text{child}}$ is selected by evaluating the discrete gradient over cardinal neighbors at dispersion distance $h$ (where $h = \text{tile\_w} = 32\text{ px}$):

$$
\mathbf{x}_{\text{child}} = \mathbf{x} + \Delta \mathbf{x}^*, \quad \text{where } \Delta \mathbf{x}^* = \underset{\Delta \mathbf{x} \in \mathcal{N}_h}{\operatorname{argmax}} \, \Phi(\mathbf{x} + \Delta \mathbf{x})
$$

$$
\mathcal{N}_h = \{ (0, -h), (-h, 0), (0, h), (h, 0) \} \quad (\text{North, West, South, East})
$$

**Constraints on Child Allocation:**

1. **Obstacle Occlusion**: $\mathbf{x}_{\text{child}}$ must not intersect static obstacles ($\text{is\_obstacle}(\mathbf{x}_{\text{child}}) = \text{False}$).
2. **Substrate Validity**: Must reside on a valid background tile (`board.tile(layer, pos) is not None`).
3. **Fluid Submersion**: $\mathbf{x}_{\text{child}}$ cannot fall directly into open fluid corridors ($\text{board.fluid}(layer, \mathbf{x}_{\text{child}}) = \text{False}$).
4. **Saturation Guard**: If $\Phi(\mathbf{x} + \Delta \mathbf{x})$ is uniform across all valid neighbors, select a uniform random direction $\Delta \mathbf{x} \in \mathcal{N}_h$.

###### 2. Pixie Architecture & Variable-Row Sheet Indexing

`Pixie` entities encapsulate lightweight dynamic fauna. Unlike `Sprites`, Pixies:

* Do not utilize combat attackboxes, equipment stacks, inventory bags, or dialogue lexicons.
* Ignore ground friction and obstacle RRT pathfinding (aerial locomotion).
* Partition sheets into strictly 4 directional rows (`up: 0`, `left: 1`, `down: 2`, `right: 3`), where each row may have an independent frame count $N_d$.

**Frame & Indexing Specification (`DirectionFrame`)**

```
Row 0: UP    [ 0 ][ 1 ][ 2 ][ 3 ] ... [ N_up - 1 ]
Row 1: LEFT  [ 0 ][ 1 ][ 2 ] ...       [ N_left - 1 ]
Row 2: DOWN  [ 0 ][ 1 ][ 2 ][ 3 ] ... [ N_down - 1 ]
Row 3: RIGHT [ 0 ][ 1 ][ 2 ] ...       [ N_right - 1 ]
```

* **Index**: `{id}-{direction}-{frame}` mapped to `(frame * w, row_index * l, w, l)`.
* **Keys**: Evaluated via `(state.direction, state.animation.frame)`.

**Instinctual Automata (`PixieInstinct`)**

To avoid running ISL AST evaluations at 60 Hz for large swarms, Pixies evaluate a hardcoded, zero-allocation state machine within `FaunaMechanics`:

```
   ┌────────────────────────────────────────────────────────┐
   │                                                        │
   ▼                                                        │
[ ROAM ] ──( Blooming Flower within R_sense )──> [ FORAGE ] │ Cooldown Expired
   ▲                                                 │      │
   │                                                 ▼      │
   └────────( Intersects Flower Hitbox )───── [ POLLINATE ] ┘
```

1. **`ROAM`**: Pseudo-random kinematic drift. Velocity vector steers towards an oscillating target offset within a bounding territory.
2. **`FORAGE`**: Vector steering directly toward the flower's coordinate: $\vec{v} = \text{normalize}(\mathbf{x}_{\text{flower}} - \mathbf{x}_{\text{bee}}) \cdot \text{speed}$
3. **`POLLINATE`**: Hover over flower center for duration $T_{\text{linger}}$. Sets `flower.state.pollinated = True`. Transitions to `ROAM` with foraging cooldown $T_{\text{cooldown}}$.

###### 3. Pipeline Integration: `FaunaMechanics`

`FaunaMechanics` executes within the `world` pipeline of `Engine._play()`, sequenced immediately following `MotionMechanics` and prior to `SeasonMechanics`:

```yaml
# src/data/config/mechanics/main.yaml
mechanics:
  world:
    - key: motion
    - key: collision
    - key: fauna        # Evaluates Pixie locomotion, pollination, and reproduction
    - key: fluid
    - key: seasons      # Evaluates continuous moisture integration & stage progression
```

##### Goals

###### Goal: Pixie Asset Architecture & Variable-Row Keying

Establish `PixieProperties`, `PixieState`, and `PixieFrame` supporting 4-directional sprite sheets with asymmetric frame counts per row.

```python
@dataclass(slots=True)
class PixieRow:
    row: int
    count: int

@dataclass(slots=True)
class PixieProperties(AssetProperties):
    dimensions: Dimensions
    rows: Dict[str, PixieRow]
    delay: int = 2
    speed: float = 30.0
    mass: int = -1

@dataclass(slots=True)
class PixieState(AssetState):
    position: Position
    velocity: Velocity
    direction: str = Directions.DOWN.value
    instinct: str = "roam"
    target_id: Optional[str] = None
    linger_timer: float = 0.0
    cooldown_timer: float = 0.0
    animation: AnimationState = field(default_factory=AnimationState)

```

###### Goal: Flower Resource Lifecycle & Pollination State

Extend resource definitions with `FlowerState`, tracking pollination and child dispersion states. Define stages (`sprout` $\to$ `growth` $\to$ `bloom` $\to$ `seed` $\to$ `stump`).

```python
@dataclass(slots=True)
class FlowerState(ResourceState):
    pollinated: bool = False
    reproduced: bool = False

```

###### Goal: FaunaMechanics & Gradient Ascent Child Dispersion

Implement `FaunaMechanics` to update Pixie steering, evaluate pollination intersections, and execute gradient-driven child spawning via `MoistureField`.

```python
class FaunaMechanics(Mechanic):
    def update(self, board: Board, delta: float, bus: deque, payload: DevicePayload) -> None:
        # 1. Update Pixies: ROAM, FORAGE, POLLINATE
        # 2. On pollination: evaluate moisture gradient around flower and spawn child

```

##### Tasks

**1. Task: Pixie Data Models & Schema Support**

*Objective*: Codify `PixieProperties` and `PixieState` in models and property schemas.

* [ ] Subtask: Define `PixieProperties` and `PixieRow` in `app.models.properties` supporting asymmetric directional row counts.
* [ ] Subtask: Define `PixieState` in `app.models.state.assets.sheets` with tracking fields for instinct, target reference, and timers.
* [ ] Subtask: Add `pixies: Dict[str, PixieProperties]` to `SheetPropertyInstances` in `app.models.properties`.
* [ ] Subtask: Register `PixieProperties` validation in Pydantic schema adapters.

**2. Task: Variable-Row Directional PixieFrame**

*Objective*: Implement `PixieFrame` and `PixieAnimation` for 4-directional sheets.

* [ ] Subtask: Implement `PixieFrame.index()` in `app.assets.frames.sheets` mapping rows (`UP=0`, `LEFT=1`, `DOWN=2`, `RIGHT=3`) to `{id}-{direction}-{frame}` using individual row counts.
* [ ] Subtask: Implement `PixieFrame.keys()` in `app.assets.frames.sheets` emitting current frame tuple from `state.direction` and `state.animation.frame`.
* [ ] Subtask: Implement `PixieAnimation.animate()` cycling frames within the active direction row limit based on `properties.delay`.

**3. Task: Flower Lifecycle Configuration & State Models**

*Objective*: Configure the Flower resource stage graph and extend resource state representation.

* [ ] Subtask: Define `FlowerState` in `app.models.state.assets.resources` inheriting `ResourceState` with `pollinated` and `reproduced` flags.
* [ ] Subtask: Add `flowers: Dict[str, ResourceProperties]` to `ResourcePropertyInstances` in `app.models.properties`.
* [ ] Subtask: Add stage transitions for `floral` lifespan in `src/data/config/stages/main.yaml` mapping `sprout` $\to$ `growth` $\to$ `bloom` $\to$ `seed` $\to$ `stump`.
* [ ] Subtask: Add `Lifespans.FLORAL` enum member to `app.config.enums.assets`.

**4. Task: FaunaMechanics Implementation**

*Objective*: Implement the world mechanic governing Pixie instinct loops and pollination logic.

* [ ] Subtask: Create `FaunaMechanics` in `app.game.logic.mechanics.world.fauna`.
* [ ] Subtask: Implement Pixie steering towards blooming flowers within perception radius ($R_{\text{sense}} = 128\text{ px}$).
* [ ] Subtask: Detect intersection between Bee hitboxes and blooming Flower hitboxes using `geometry.intersects`.
* [ ] Subtask: Linger over flower during `POLLINATE` instinct and set `flower.state.pollinated = True`.

**5. Task: Moisture Gradient Reproduction Engine**

*Objective*: Sample `MoistureField` and spawn child flowers along the gradient vector.

* [ ] Subtask: Implement `_find_highest_moisture_neighbor(flower_pos, layer, board)` in `FaunaMechanics` evaluating cardinal displacements $h=32$.
* [ ] Subtask: Validate candidate child coordinate against boundaries, static obstacles, and active fluid corridors.
* [ ] Subtask: Invoke `board.cradle.spawn_resource()` to instantiate child flower at candidate position with `stage="sprout"`.
* [ ] Subtask: Register `fauna` mechanic in `src/data/config/mechanics/main.yaml` within the `world` execution list.










### Architectural Synthesis: The Emergent Ecology

With the completion of **Phase 10.01 (Stage Hitboxes & Optimizations)**, the engine bridges a longstanding architectural gap between macro-environmental mechanics and physical spatial simulation.

The core thesis of *Ontology* is **simulation and emergence at all costs**—the elimination of procedural scripting in favor of deterministic initial conditions evolving under invariant systemic laws. Previously, physical collision bounds remained statically bound to asset recipes. While `SeasonMechanics` transitioned biological entities across complex life cycles (Genesis, Homeostasis, and Apoptosis) and updated visual sprite atlas projections via `StageFrame`, physical bodies remained frozen in their initial footprints. Mature deciduous canopies obstructed open air, saplings blocked adult creatures, and harvested stumps behaved like ancient oaks.

Elevating physical hitboxes into a first-class, stateless ECS behavior strategy (`HitboxSchema`) alongside `Frame` and `Animation` resolves this tension:

1. **Decoupled Physical Representation**: The physical collision hull is now an emergent projection of state and properties rather than a static asset property.
2. **Contract Invariance**: `Asset.hitboxes` preserves its external contract (`List[Hitbox]`), allowing downstream spatial pipelines (`CollisionMechanics`, `NavigationMechanics`, and Cython broad/narrow-phase spatial hashing) to consume dynamic bounds without inner-loop branching.
3. **Foundation for Ecology & Fauna**: By resolving juvenile passability and dynamic footprint expansion in $O(1)$ time, the stage is set for **Phase 10.03 (Flowers, Pixies & Reproduction)** and **Phase 10.04 (Cythonization)**. Flora can now propagate seeds into traversable juvenile patches, and simple fauna (Pixies) can navigate dense foliage without snagging on phantom canopy boundaries.

---

#### Review: Phase 10.01 - Stage Hitboxes & ECS Architecture

##### Context

* **Affected Systems**: `app.assets.base` (`Asset`, `HitboxSchema`), `app.assets.hitboxes` (`StaticHitbox`, `DynamicHitbox`, `StageHitbox`, `NoHitbox`), `app.models.properties` (`ResourceProperties`), `app.services.generators.game.factory` (`Factory.hitbox`), and asset hydration pipelines (`Migrator`, `Decomposer`, `Cradle`).
* **Initial Conditions**: Resources maintained static `hitboxes` declared on immutable properties. A falsy check (`if not hbs and self.dimensions`) converted passable entities (`hitboxes: []`) into full-dimension obstacles.
* **Prior Assumptions**: Biological stage transitions mutate `resource.state.stage` deterministically via `SeasonMechanics`. Hitbox resolution must execute in $O(1)$ time during the 60 Hz physics update without heap allocation.

##### Implementation Control

* **Specification Met**: `HitboxSchema` strategy hierarchy implemented and integrated into the `Recipe` configuration schema. Stage-indexed dictionaries on `ResourceProperties` resolve dynamic collision hulls in $O(1)$ time. Trunk and stump hitboxes configured for deciduous trees; passable juvenile stages verified.
* **Edge Cases**:
* Explicit passable declarations (`hitboxes: []`) correctly bypass fallback bounding box generation via `if properties.hitboxes is None`.
* Non-stage entities defaulting to `StaticHitbox` maintain exact legacy behavior with zero configuration changes.


* **Errors Handling**: `StageHitbox.get` gracefully returns an empty list if a stage is absent from the property dictionary, though it lacks a safeguard if `properties.hitboxes` is configured as `None` (see Bug B016).

##### Quality Control

* **Comments & Docstrings**: Module-level docstrings and interface contracts across `app.assets.hitboxes` conform to project guidelines.
* **Code Smells**:
* `Factory.hitbox()` instantiates a new strategy object on every invocation (`return target_cls()`) instead of returning pre-instantiated stateless singletons.
* `Asset.__init__` accepts `hitbox: HitboxSchema = None` and assigns `self.hitbox = hitbox` directly without a fallback default, creating a potential `NoneType` attribute error if instantiated outside `Factory`.


* **Application Constraint Violations**: The naming convention in `HitboxSchema` deviates from the documentation draft: implemented as `get(properties, state, frame)` rather than `resolve(properties, state, frame)`.
* **Readability**: Strategy dispatch cleanly isolates biological stage logic from generic static objects, eliminating the sprawling procedural conditionals previously accumulating on `Asset.hitboxes`.

##### Optimization Control

* **Cython Candidates**: `StageHitbox.get()` dictionary lookups currently occur within the Python runtime. When `Asset.primitive()` is called during broad-phase collision sweeps, packing hitboxes into Cython integer tuples incurs Python dictionary overhead. In Phase 10.04, stage hitbox arrays should be indexed via integer stage enums in C-contiguous memory.
* **Allocation Bottlenecks**: Hydrating large boards with thousands of constituent assets currently allocates individual `HitboxSchema` instances due to `Factory.hitbox()` returning new instances rather than singletons.

---

##### Bug B016: StageHitbox AttributeError on Unconfigured Resource Properties

**STATUS**: OPEN

**SEVERITY**: Medium

**Description**

In `app.models.properties.ResourceProperties`, the `hitboxes` field defaults to `None`:

```python
hitboxes: Dict[str, Optional[List[Hitbox]]] = None

```

In `app.assets.hitboxes.resources.StageHitbox`, stage resolution queries the dictionary directly without verifying non-null property initialization:

```python
def get(
    self,
    properties: ResourceProperties,
    state: ResourceState,
    frame: Optional[Frame] = None
) -> List[Hitbox]:
    return properties.hitboxes.get(state.stage, []) or []

```

If a resource recipe or test fixture instantiates `ResourceProperties` with `hitboxes=None` (or omits the field entirely in YAML), invoking `asset.hitboxes` raises:

```text
AttributeError: 'NoneType' object has no attribute 'get'

```

**Steps to Replicate**

1. Instantiate a `ResourceProperties` model without explicitly supplying `hitboxes`: `props = ResourceProperties(dimensions=Dimensions(32, 32), loot="wood", lifespan=Lifespans.PERENNIAL)`.
2. Instantiate an `Asset` using `props`, a valid `ResourceState(stage="sapling")`, and `hitbox=StageHitbox()`.
3. Query `asset.hitboxes`.
4. Observe `AttributeError`.

**Proposed Remediation**

Evaluate non-null state before dictionary lookup in `StageHitbox.get`:

```python
def get(
    self,
    properties: ResourceProperties,
    state: ResourceState,
    frame: Optional[Frame] = None
) -> List[Hitbox]:
    if not properties.hitboxes:
        return []
    return properties.hitboxes.get(state.stage, []) or []

```

---

##### Bug B017: Asset Instantiation Defaults Hitbox to Unbound NoneType

**STATUS**: OPEN

**SEVERITY**: Low

**Description**

In `src/app/assets/base.py`, `Asset.__init__` accepts `hitbox: HitboxSchema = None` and binds it directly:

```python
def __init__(
    self,
    taxonomy: Taxonomy,
    properties: AssetProperties, 
    state: AssetState, 
    frame: Frame=None, 
    animation: Animation=None,
    hitbox: HitboxSchema=None,
):
    ...
    self.hitbox = hitbox

```

If an asset is instantiated directly (such as in lightweight unit test mocks or fixture loaders) without passing an explicit `hitbox`, `self.hitbox` remains `None`. Subsequent calls to `asset.hitboxes` or `asset.primitive()` trigger `AttributeError: 'NoneType' object has no attribute 'get'`.

**Steps to Replicate**

1. Instantiate an `Asset` directly with `hitbox=None`.
2. Access `asset.hitboxes`.
3. Observe `AttributeError: 'NoneType' object has no attribute 'get'`.

**Proposed Remediation**

Provide a safe default strategy fallback during initialization:

```python
from app.assets.hitboxes.core import StaticHitbox

self.hitbox = hitbox if hitbox is not None else StaticHitbox()

```

---

#### Draft: Interface Alignment for HitboxSchema

* **Page**: `docs/01-assets.md`
* **Heading**: `Asset Architecture`

##### Drift

The architectural documentation in `01-assets.md` records the strategy interface method as `resolve(properties, state, frame)`. However, the implementation in `app.assets.base.HitboxSchema` and all downstream strategy classes (`StaticHitbox`, `DynamicHitbox`, `StageHitbox`, `NoHitbox`) defines the method as `get(properties, state, frame)`.

##### Update

```markdown
5. **Behavior: Hitbox:** Stateless collision boundary resolution strategies injected via Recipes. Resolves active physical obstacles dynamically without mutating cached properties:
    - `get(properties: AssetProperties, state: AssetState, frame: Optional[Frame]) -> List[Hitbox]`: Emits the active physical collision footprint for spatial broad-phase and narrow-phase physics.

```

---

#### Draft: Hitbox Concept Modernization

* **Page**: `docs/00-overview.md`
* **Heading**: `Hitboxes`

##### Drift

The concept section in `00-overview.md` documents hitboxes as strictly static properties residing exclusively on `properties.hitboxes`. This does not reflect the ECS strategy component architecture introduced in Phase 10.01, which accommodates dynamic stage-based hitboxes (`StageHitbox`) and state-driven boundary hulls (`DynamicHitbox`).

##### Update

```markdown
### Hitboxes

Many Assets have Hitboxes. Hitboxes define the physical collision and interaction boundaries of an entity. To ensure coordinate consistency, Hitbox positions are normalized relative to the Asset's top-left origin `(0, 0)`, while dimensions are absolute.

Physical boundaries are resolved through decoupled, stateless `HitboxSchema` behavior components:
- **Static**: Uniform entities (crates, obstacles) query immutable `properties.hitboxes`.
- **Stage**: Biological and geological resources (trees, crops, ore) query stage-indexed dictionaries (`properties.hitboxes[state.stage]`), dynamically adjusting collision hulls across growth and harvesting lifecycles.
- **Dynamic**: Procedural landforms (shorelines, fluid boundaries) evaluate active spatial contours on `state.hitboxes`.
- **None**: Passable background substrate tiles, passive particle effects, and screen overlays emit empty collision lists.

```

---

#### Refactor: Phase 10.03 - Flowers, Pixies & Reproduction

**Overview**

With stage hitboxes established for perennial trees and annual crops, the ecological loop requires autonomous reproductive and entomological agents. Currently, vegetation stages advance strictly along a deterministic single-track progression; they do not reproduce, cross-pollinate, or spawn progeny. Furthermore, the `pixies` sheet instance remains an inert, uncoordinated sprite variant.

Phase 10.03 introduces the `flowers` resource instance (annual/perennial nectar producers) and activates `pixies` as dynamic ecological agents. Pixies traverse between flowering flora, accumulating pollen potential and triggering seed dispersal into neighboring fertile soil tiles based on moisture potential fields ($\Phi(\mathbf{x})$).

##### Specification

1. **Flower Resource Definition (`src/assets/resources/main.yaml`)**:
* Model `flowers` under `resources` with lifespans (`annual`, `perennial`), nectar loot tables, and stage progression: `sprout` $\to$ `growth` $\to$ `bloom` $\to$ `pollinated` $\to$ `seed` $\to$ `stump`.
* Configure stage hitboxes: passable (`[]`) during `sprout` and `growth`; localized stem footprint during `bloom` and `pollinated`.


2. **Pixie Ecological Behavior**:
* Register `pixie` navigation routines in `CognitionMechanics` targeting active `bloom` stages on the layer.
* Pixies intersecting a `bloom` flower increment `pixie.state.pollen` and transition the flower to `pollinated`.


3. **Seed Dispersal & Propagation (`ReproductionMechanics`)**:
* When a pollinated flower reaches the `seed` stage, calculate dispersal trajectories along active wind/fluid vectors.
* If candidate coordinates satisfy moisture thresholds ($\Phi(\mathbf{x}) \ge \theta_{\text{germination}}$) and are unoccupied by static obstacles, instantiate new juvenile `sprout` assets via `board.cradle`.



##### Architectural Analysis 1

The reproduction loop must operate entirely within existing architectural boundaries:

* **Decoupled Spawning**: Entity instantiation must route strictly through `Board.cradle` to preserve ID registration, spatial bucket insertion, and cache indexing.
* **Moisture Coupling**: Seed viability queries the compiled `MoistureField` directly (`board.moisture(layer, x, y)`), reinforcing the dependency between hydrology (`FluidMechanics`) and vegetation density.
* **Zero Scripting**: No scripted quests or manual trigger zones. Forest and flower meadow proliferation emerges entirely from fluid flow, moisture diffusion, and pixie pollination paths.

##### Goals

###### Goal: Floral Resource Lifecycle & Pollination Schemas

Author declarative stage transitions for `flowers` in `src/data/config/stages/main.yaml`. Bind nectar loot and biological lifespans to enable pollination transitions without modifying core simulation loops.

###### Goal: Pixie Foraging & Emergent Seed Dispersal

Implement `ReproductionMechanics` within the `world` mechanics pipeline to evaluate germination potentials and spawn juvenile flora via `Cradle`.

##### Tasks

**1. Task: Flower Resource Schema & Atlas Indexing**

*Objective*: Author asset property declarations and biological stage configs for flowers.

* [ ] Subtask: Define `flowers` under `resources` in `src/assets/resources/main.yaml` with dimensions, loot, and stage-indexed hitboxes.
* [ ] Subtask: Configure `annual` and `perennial` stage transition graphs for flowers in `src/data/config/stages/main.yaml`.
* [ ] Subtask: Register `flowers` recipe in `src/data/config/recipes/main.yaml` with `frame: stage`, `animation: none`, and `hitbox: stage`.

**2. Task: Pixie Foraging Cognition & Pollination Logic**

*Objective*: Direct Pixie sheet entities toward flowering resources and manage pollination states.

* [ ] Subtask: Extend `CognitionMechanics` to evaluate `FORAGE` goals targeting flora in the `bloom` stage.
* [ ] Subtask: Add `pollen: int` to `PixieState` in `app.models.state.assets.sheets`.
* [ ] Subtask: Transition flowers from `bloom` to `pollinated` upon pixie contact.

**3. Task: ReproductionMechanics & Seed Dispersal Pipeline**

*Objective*: Introduce world pipeline mechanic for seed drop evaluation and hydration.

* [ ] Subtask: Create `app.game.logic.mechanics.world.reproduction.ReproductionMechanics`.
* [ ] Subtask: Implement germination spatial checks evaluating tile clearance and `board.moisture(layer, x, y) >= threshold`.
* [ ] Subtask: Inject newborn `sprout` assets into the board via `board.cradle.spawn()`.
* [ ] Subtask: Register `reproduction` in `src/data/config/mechanics/main.yaml` within the `world` pipeline.