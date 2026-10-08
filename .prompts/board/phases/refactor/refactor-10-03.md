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