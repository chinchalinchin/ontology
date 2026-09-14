#### Refactor: Phase 02.06 - Effects

**Goals**: Refactor the Effect Asset.

##### Anaylsis

###### Effect Assets

After examination of the available Effect assets, there appears to be ambiguity in how the specifications relate to the physical asset files. From inspection, logical groupings seem to exist that should be codified. 

All Effect frame indexing can continue utilize the existing `IterableFrame`, as none of the architectural shifts should affect the underlying image files. Rather, the goal is divide Effects into their logical units based on common behavior.

The partitioning of Effects appears to be along two major categorical axes:

- The *type* of animation: `temporary`, `continuous` and `periodic`.
- The *function* of the Effect: `passive`, `collectable`, `hazard` and `interactable`

**Classification**

This is a list of some of the available Asset files, and the proposed categorization,

- Lava: `continuous`, `hazard`
- Spinning Spar Dummy: `temporary`, `interactable`
- Floor Spike: `periodic`, `hazard`
- Coin: `continuous`, `collectable`
- Grandfather Clock: `continuous`, `passive`
- Water Ripples: `continuous`, `passive`
- Magic: `temporary`, `hazard`
- Bomb: `temporary`, `hazard`
- Rain: `periodic`, `passive`
- Candle: `continuous`, `passive`
- Torch: `continuous`, `passive`
- Birdbath: `periodic`, `passive`
- Furnance: `continuous`, `interactable`
- Chemistry Set: `continuous`, `interactable`
- Falling Leaves: `periodic`, `passive`

!!! note
    Not all Temporary effects should be garbage collected.

There are more, but they all appear to fall into the categorical scheme offer by (type, function).

!!! note
    There does not seem to be any dependence between animation type and function type, e.g. `hazard` could be `continuous`, `periodic` or `temporary`.

###### Effect Schema Updates

**EffectProperties**

Properties require minimal changes. Optional hitboxes and mass will need added to account for the `interactable` and `collectable` instances of Effects.

```yaml
objects:
    effects:
        dimensions:
            w: int
            l: int
        hitboxes:
            - position:
                x: int
                y: int
              dimensions:
                w: int
                l: int
        count: int 
        mass: int
```

**Effect Animations**

!!! note
    Possibile implementation strategy, dividing `type` into literal Animation Classes

- `temporary`: Ephemeral effects that halt once they reach the `count`.
    - `if state.animation.frame =< properties.count: state.animation.frame += 1`
- `continuous`: Perpetual effects that never stop iterating over their animation frames. 
    - `if state.animation.frame >= properties.count: state.animation.frame = 0`
- `periodic`: Perpetual effects that periodically repeat their animation frames.
    - `if state.animation.frame < properties.count: state.animation.frame += 1`
    - `if state.animation.frame >= state.frequency: state.animation.frame = 0`

**Effect States**

- PassiveState: Default Effect state. Has no attributes beyond what is necessary to achieve instantiation and animation in the game.
- HazardState: Effect Animations that represent environmental hazards (lava, poisonous gas, rushing water, etc.). When Sprite enter into the Effect's area, they suffer `effect.state.damage`.
    - `damage`:
        - `amount`: Amount of health deducted each `duration`
        - `duration`: How quickly the `amount` is applied to the Sprite.
        - `effect (hinder | bounce)`: Key to determine intersection effects of Hazard, e.g. whether the Sprite's movement is hindered (slowed down) or bounced (jolted away from the Hazard bounds)
- CollectableState: Effect Animations that represent collectable items (spinning coins, bubbling potions, etc.) to be added to `sprite.state.inventory.loot`. Produced when a Sprite in the `mine` Intention acts on a Resource (Resources not yet implemented). When Collectables are collected by a Sprite, they are instantly garbage-collected from the board.
    - `loot`: Loot inventory key received upon intersecting the Effect's hitbox.
- InteractableState: Effect Animations that are triggered when a Sprite within `action` radius of the Effect enters into the preqrequisite `effect.state.action`. 
    - `action`: Action which triggers the animation, e.g. (`cast`, `slash`, `thrust`, `shoot`).

```yaml
objects:
    effects:
        <passive-id>:
            layer: str
            depth: int
            height: int
            frequency: Optional[int]
            position: Position
            animation: AnimationState
        <hazard-id>:
            layer: str
            depth: int
            height: int
            frequency: Optional[int]
            position: Position
            animation: AnimationState
            damage: 
                amount: int
                duration: int
                reaction: str
        <collectable-id>:
            layer: str
            depth: int
            height: int
            frequency: Optional[int]
            position: Position
            animation: AnimationState
            loot: Loot
        <interactable-id>: 
            layer: str
            depth: int
            height: int
            frequency: Optional[int]
            position: Position
            animation: AnimationState
            action: Actions
```

!!! note 
    Need frequency to support the possibility of `periodic` animations.

**Problem**: in current setup, each instance has a determinate state, frame and animation. In other words, the current setup does not support a `<hazard-id-1>` having a TemporaryAnimation and a HazardState, while `<hazard-id-2>` has a ContinuousAniamtion and a HazardState; all instances with a HazardState must have the same Animation implementation. 

The obvious solution is to create instances for each permutation of HazardPeriodic, HazardContinuous, HazardTemporary, etc. Doing so, however, is not very Pythonic or DRY. 

---

Another possible solution is adding a `lifecycle` attribute in the EffectProperties, i.e. explicitly make animation logic depend on the state,

```yaml
lifecycle:
    type: periodic | continuous | temporary
    frequency: int
```

In this case, there would be a single `LifecycleAnimation` that conditionalizes its animation based on the supplied `type`, e.g.

```python

def animate(self, state, properties):
    if properties.lifecycle.type == "periodic":
        # periodic animation logic
    elif properties.lifecycle.type == "temporary":
        # temporary animation logic
    elif properties.lifecycle.type == "continuous":
        # continuous animation logic
```

In this case, frequency becomes part of the properties (which, I think, it should.)

---

Anaylze the problem of categorizing Effects. Determine and propose an optimal, Pythonic solution that utilizes data structures intelligently. (User currently leans towards the `lifecycle` approach.)

### Architectural Analysis: Decoupling Lifecycle from Functional Roles

The current architecture in `src/app/config/enums.py` and `src/app/models/properties.py` partitions Effects by their animation behavior (`temporary` vs. `persistent`) rather than their functional role within the world simulation. This creates an architectural bottleneck:

1. **Category vs. Instance Inversion:** Across all other categories (`objects`, `sheets`, `cursors`), `instance` defines the domain model and gameplay mechanics (`doors` -> `DoorMechanics`, `crates` -> `MotionMechanics`, `chests` -> `ContainerState`). For `effects`, instances currently reflect animation lifespans, leaving no clean mechanism to distinguish between an ambient visual (water ripple), a damaging tile (lava), a world pickup (spinning coin), or an interactive entity (furnace).
2. **Permutational Explosion:** Forcing the lifecycle into the `instance` taxonomy requires $N \times M$ classes (`HazardContinuous`, `HazardPeriodic`, `HazardTemporary`, `PassiveContinuous`, etc.), violating DRY and fracturing Board queries.
3. **The Recommended Architecture:** Partition `AssetInstances` of category `effects` strictly by their **functional role** (`passive`, `hazard`, `collectable`, `interactable`), and shift animation duration and pacing into a unified `LifecycleProperties` model on `EffectProperties`. All Effect instances then consume a single, deterministic `LifecycleAnimation` strategy.

```
                  +-----------------------------------+
                  |      AssetCategory: EFFECTS       |
                  +-----------------------------------+
                                    |
          +-------------------------+-------------------------+
          |                         |                         |
+-------------------+     +-------------------+     +-------------------+
|  Property Model   |     |    State Model    |     | Behavior Strategy |
+-------------------+     +-------------------+     +-------------------+
| EffectProperties  |     |  Functional State |     | LifecycleAnimation|
| - dimensions      |     | - passive         |     | - continuous      |
| - hitboxes        |     | - hazard          |     | - periodic        |
| - mass            |     | - collectable     |     | - temporary       |
| - lifecycle       |     | - interactable    |     +-------------------+
+-------------------+     +-------------------+

```

---

### Data Models & Strategy Design

#### 1. Lifecycle Specification (`EffectProperties`)

Lifecycle attributes belong in static configuration (`src/assets/effects/main.yaml`) as properties. Frame pacing and repetition rely on three parameters:

* `type`: `continuous | periodic | temporary`
* `delay`: Game ticks per frame advancement (analogous to Sheet `Action.delay`).
* `frequency`: Total cycle duration in ticks for `periodic` effects (encompassing both active animation and idle duration).
* `persist`: Optional boolean for `temporary` effects. When `True`, the effect clamps to its final frame instead of self-terminating.

```python
@dataclass(slots=True)
class LifecycleProperties:
    type: str  # continuous | periodic | temporary
    delay: int = 1
    frequency: int = 0
    persist: bool = False

@dataclass(slots=True)
class EffectProperties(AssetProperties):
    dimensions: Dimensions
    count: int
    lifecycle: LifecycleProperties
    mass: int = -1
    hitboxes: Optional[List[Hitbox]] = field(default_factory=list)

```

#### 2. Deterministic `LifecycleAnimation`

By leveraging `state.animation.tick` alongside `state.animation.frame`, all three lifecycles execute within a single stateless animation component with zero runtime heap allocation:

```python
class LifecycleAnimation(Animation):
    def animate(self, state: AssetState, properties: EffectProperties) -> AssetState:
        lifecycle = properties.lifecycle
        anim = state.animation
        anim.tick += 1

        if lifecycle.type == "continuous":
            if anim.tick >= lifecycle.delay:
                anim.tick = 0
                anim.frame = (anim.frame + 1) % properties.count

        elif lifecycle.type == "temporary":
            if anim.frame < properties.count:
                if anim.tick >= lifecycle.delay:
                    anim.tick = 0
                    anim.frame += 1

        elif lifecycle.type == "periodic":
            active_duration = properties.count * lifecycle.delay
            if anim.tick < active_duration:
                anim.frame = anim.tick // lifecycle.delay
            else:
                anim.frame = 0  # Resting / idle frame
            
            if anim.tick >= max(lifecycle.frequency, active_duration):
                anim.tick = 0
                anim.frame = 0

        return state

```

#### 3. Functional State Taxonomy

| Effect Instance | State Model | Required Attributes | Consuming System |
| --- | --- | --- | --- |
| `passive` | `AnimatorState` | `position, layer, depth, height, animation` | `AnimationMechanics` |
| `hazard` | `HazardState` | `position, layer, depth, height, animation, damage: (amount, duration, reaction)` | `CombatMechanics` |
| `collectable` | `CollectableState` | `position, layer, depth, height, animation, loot: str, quantity: int` | `InteractionMechanics` |
| `interactable` | `InteractableState` | `position, layer, depth, height, animation, action: str, cooldown: int` | `InteractionMechanics` |

---

### Task Backlog Update

#### Backlog: Refactor: Phase 02.06 - Effects

**Overview**

Refactor the Effect Asset hierarchy by decoupling animation lifecycle mechanics from functional simulation instances. Replace the `temporary` and `persistent` instances with functional variants (`passive`, `hazard`, `collectable`, `interactable`), introduce `LifecycleProperties` to govern frame updates, and implement a unified `LifecycleAnimation` strategy.

##### Goal: Schema and Hierarchy Restructuring

Migrate Effect instances in `app.config.enums.AssetInstances` from temporal definitions to functional roles. Update `PropertiesSchema` and `StateSchema` to support typed metadata for hazard damage, inventory pickup payloads, and interaction triggers.

##### Goal: Unified Animation Engine

Implement `LifecycleAnimation` in `app.assets.animations.core` to resolve `continuous`, `periodic`, and `temporary` cycles using internal tick accumulators. Deprecate `TemporaryAnimation` and `PersistentAnimation`.

##### Goal: Engine Lifecycle & Garbage Collection Integration

Update `RemoveMechanics` to query expired temporary effects across any functional instance whose `animation.frame >= properties.count` (when `persist == False`). Align `Cradle` spawning routines to instantiate properly typed functional states.

##### Tasks

**1. Task: Asset Taxonomy and Property Models Refactor**

*Objective*: Update the enums and property models to support functional Effect instances and lifecycle configurations.

* [ ] Subtask: Replace `PERSISTENT` and `TEMPORARY` in `AssetInstances` with `PASSIVE`, `HAZARD`, `COLLECTABLE`, and `INTERACTABLE`.
* [ ] Subtask: Define `LifecycleProperties` in `app.models.properties` with `type`, `delay`, `frequency`, and `persist` attributes.
* [ ] Subtask: Update `EffectProperties` to include `lifecycle`, `mass`, and optional `hitboxes`.
* [ ] Subtask: Update `EffectPropertyInstances` in `PropertiesSchema` to index `passive`, `hazard`, `collectable`, and `interactable`.

**2. Task: Functional State Models Implementation**

*Objective*: Create typed state models in `app.models.state.objects` for non-passive effects.

* [ ] Subtask: Define `HazardState` containing a typed `damage` payload (`amount`, `duration`, `reaction`).
* [ ] Subtask: Define `CollectableState` containing `loot` and `quantity` fields.
* [ ] Subtask: Define `InteractableState` containing `action` trigger requirements and `cooldown`.
* [ ] Subtask: Register new state models to `StateRecipe` and the loader type adaptors.

**3. Task: LifecycleAnimation Strategy Implementation**

*Objective*: Implement a unified animation strategy replacing `TemporaryAnimation` and `PersistentAnimation`.

* [ ] Subtask: Implement `LifecycleAnimation` in `app.assets.animations.core` supporting continuous, periodic, and temporary behaviors.
* [ ] Subtask: Register `LifecycleAnimation` in `app.services.generators.factory.Factory` under `AnimationRecipe.LIFECYCLE`.
* [ ] Subtask: Update `default.yaml` recipe configurations to map all Effect instances to `FrameRecipe.ITERABLE` and `AnimationRecipe.LIFECYCLE`.

**4. Task: Engine Mechanics and Cradle Alignment**

*Objective*: Adapt lifecycle garbage collection, spawning, and mechanics to the new Effect hierarchy.

* [ ] Subtask: Refactor `RemoveMechanics` in `app.game.logic.mechanics.core` to inspect `board.categories(AssetCategories.EFFECTS)` for expired temporary effects.
* [ ] Subtask: Refactor `Cradle.spawn_temporary` to `Cradle.spawn_effect`, accepting the target instance type and instantiating `AnimatorState` or its subclasses instead of `PositionalState`.
* [ ] Subtask: Update `SpawnableGroup` to index spawnable effects under functional categories.
* [ ] Subtask: Ensure `board.serialize()` continues to cleanly skip transient effect states while preserving world hazards if configured.

---

### Bug Reports

##### Bug B007: PositionalState Instantiation in Cradle.spawn_temporary

**STATUS**: OPEN

**SEVERITY**: HIGH

**Description**

`Cradle.spawn_temporary()` in `src/app/services/generators/cradle.py` instantiates the spawned asset with `PositionalState`. `PositionalState` only provides `position` and `velocity`; it does not contain the `animation: AnimationState` field. When `AnimationMechanics.update()` iterates over Effect assets and invokes `animate()`, `TemporaryAnimation` attempts to access `state.animation.frame`, triggering an unhandled `AttributeError`. Additionally, `RemoveMechanics` crashes when attempting to read `effect.state.animation.frame`.

**Steps to Replicate**

1. Invoke `board.cradle.spawn_temporary("dust-puff", "0", Position(10, 10))` during runtime.
2. Advance the engine tick into `AnimationMechanics.update()`.
3. Observe `AttributeError: 'PositionalState' object has no attribute 'animation'`.

**Proposed Remediation**

Modify `Cradle.spawn_temporary()` to instantiate `AnimatorState` (or its functional derivative) initialized with a valid `AnimationState` instance.


##### Bug B009: FontProperties Color Field Uses Lambda Default Instead of Default Factory

**STATUS**: OPEN

**SEVERITY**: MEDIUM

**Description**

In `src/app/models/properties.py`, `FontProperties` defines its default color using `field(default=lambda: RGBA(...))`:

```python
@dataclass(slots=True)
class FontProperties:
    alignment: Alignments = Alignments.START.value
    color: RGBA = field(default=lambda: RGBA(r=255, g=255, b=255, a=255))

```

In Python's standard `dataclasses` module, `default` stores the assigned value verbatim. As a result, uninitialized `FontProperties.color` fields evaluate to a function pointer (`>`) rather than an `RGBA` object instance, leading to runtime failures when Cython rendering attempts to unpack `color.r`, `color.g`, and `color.b`.

**Steps to Replicate**

1. Instantiate `props = FontProperties()`.
2. Inspect `type(props.color)`.
3. Observe `instead of`.

**Proposed Remediation**

Change the field definition in `app/models/properties.py` to use `default_factory`:

```python
color: RGBA = field(default_factory=lambda: RGBA(r=255, g=255, b=255, a=255))

```

---

### Documentation Amendments (`docs/01-assets.md`)

Update the Effects section in `01-assets.md` to reflect the functional taxonomy:

```markdown
## Effects

* Property File: `/src/assets/effects/main.yaml`

Effects are animate visual assets used for environmental dressing, hazards, pickups, and interactive mechanisms. All Effects iterate over a single row of frames using `IterableFrame` and advance via `LifecycleAnimation`.

**Properties: EffectProperties**

* `dimensions: Dimensions`
* `count: int`
* `mass: int`
* `hitboxes: List[Hitbox]`
* `lifecycle: LifecycleProperties`
    * `type: str` (`continuous`, `periodic`, `temporary`)
    * `delay: int` (tick pacing between frames)
    * `frequency: int` (tick interval for periodic resets)
    * `persist: bool` (whether temporary effects persist on their final frame)

### Instances

- **Passive (`AnimatorState`):** Ambient environmental effects that do not participate in collision resolution or health interactions (e.g., torches, water ripples, falling leaves).
- **Hazard (`HazardState`):** Environmental hazards that deal damage to overlapping dynamic entities (e.g., lava, floor spikes, poison gas clouds).
- **Collectable (`CollectableState`):** World pickups that transfer loot keys into a Sprite's or Player's inventory upon hitbox intersection (e.g., dropped coins, potions).
- **Interactable (`InteractableState`):** Mechanized world props whose animations and states trigger upon intentional player or sprite actions (e.g., furnaces, sparring dummies).
```