#### Refactor: Phase 09.01 - Fluid Flows

**Overview**

Expand Phase 09 hydrodynamics into an interactive vector field. Implements momentum transfer to wading entities, relative reference-frame motion aboard dynamic rafts, solid-base annular pooling, character submersion rendering, and current-aware RRT path planning.

**Primary Objective**

- When Sprites and Players (and Pixies, not yet implemented) intersect a Fluid Effect, they should get swept along the Fluid's `source` direction.
- A specialized object called a Raft shall be introduced. It will not participate in Fluid obstruction, but instead obey the same physics as Sheet Assets, i.e. getting swept in the `source` direction
- The speed that is imparted to the "flowing" Asset should be proportional to the `flow` of the Fluid Effect `source`, i.e. the higher the `flow`, the faster the Asset will be swept away. 
- When an underlying Fluid adjusts velocity, Players and Sprites can still navigate, but no longer obey the laws of kinematic snapping. Instead, the Fluid `flow` is added vectorally to the Sheet velocity. 

**Secondary Concerns**

- Removing the obstacle dimensions from the Pool calculations was a mistake, as the background tiles are now visible along the transparent edges of the obstacle (i.e. the obstacle image doesn't fill its dimensions).
- Will probably need to add a mutator to the Sprite state for `submerged`. This needs to trigger a temporary Passive Temporary (Possibly Periodic) Effect, `splash`.
    - Evaluate the feasibility of "submerging" the Sheet Asset, so from the "waist down" (let's say half of `dimensions.l` for now, though we may need a property somewhere to parameterize it) the Sprite frame is darkened/opaque (mimicking the look of a submerged body), with a `splash` effect triggered along the boundary of the submersion. 
    - **NOTE**: This will require the Cradle to spawn the Splash effect.
- The goal of a Raft is to allow Sprites to use it to traverse bodies of Fluids. Consideration needs to be given on how to achieve this sort of relative motion, i.e. the Sprite can move relative to the Raft while aboard and in motion.
- The presence of Fluid flow should influence the RRT pathfinding velocity selection. The question is: in what capacity? Traversing a Fluid needs a "cost", so Sprites can path-find around it.

##### Architectural Analysis

```
+---------------------------------------------------------------------------------------+
|                                    BOARD STATE                                        |
|  - Emitters: (source: DOWN, flow: 2) -> Compound Hitboxes & Current Vectors           |
|  - Surfaces: Ground (Back Tiles) < Fluids (Depth -1) < Rafts (Depth 0) < Dynamic Bodies|
+---------------------------------------------------------------------------------------+
                                           │
                                           ▼
+---------------------------------------------------------------------------------------+
|                                 MOTION MECHANICS                                      |
|                                                                                       |
|  1. Kinematic (Player):  v_intended = Device Input * Speed                            |
|                          v_final    = v_intended + v_current (Snapping Disabled)      |
|                                                                                       |
|  2. Motive (Sprites):    v_steer    = RVO Avoidance / Target Steering                 |
|                          v_final    = v_steer + v_current                             |
|                                                                                       |
|  3. Dynamic (Rafts):     v_final    = v_current                                       |
|                                                                                       |
|  4. Relative Frame:      If Asset on Raft: v_final = v_intended + v_raft              |
|                          (Fluid current bypassed; Submersion = False)                 |
+---------------------------------------------------------------------------------------+
                                           │
                                           ▼
+---------------------------------------------------------------------------------------+
|                              PHYSICS & SPATIAL UPDATE                                 |
|  - Symplectic Euler Integration: x_(n+1) = x_n + v_final * dt                         |
|  - Submersion Check: If in Fluid & not on Raft -> mutators.triggers.submerged = True  |
|  - Waterline Visual: Half-height tint blit + Cradle.spawn_passive("splash")           |
+---------------------------------------------------------------------------------------+
```

**1. Hydrodynamic Vector Field: Vector Addition vs. Kinematic Snapping**

Currently, `kinematic.py` clamps velocity along orthogonal input axes:

```python
physics.kinematics(player.state.velocity, ix, iy, player.state.character.speed)
```

This overwrites `player.state.velocity` each tick, destroying any external momentum. Similarly, `motive.py` assigns `sprite.state.velocity = avoid_vel`.

To support fluid currents:

* The fluid emitter defines an environmental current vector derived from its orientation and intensity:

$$
\vec{v}_{\text{current}} = \text{flow} \times \text{BASE\_FLOW\_SPEED} \times \hat{u}_{\text{source}}
$$

* When an entity's sensory anchor intersects an active fluid hitbox, `MotionMechanics` suspends pure kinematic snapping. Instead of replacing the velocity vector, the environmental current is combined with the entity's voluntary locomotion:

$$
\vec{v}_{\text{final}} = \vec{v}_{\text{locomotion}} + \vec{v}_{\text{current}}
$$

* If the player releases all controls ($\vec{v}_{\text{locomotion}} = \vec{0}$), the player is swept downstream at $\vec{v}_{\text{current}}$. If swimming against the stream ($\vec{v}_{\text{locomotion}} \cdot \vec{v}_{\text{current}} < 0$), net forward progress occurs only when $\vert\vec{v}_{\text{locomotion}}\vert > \vert\vec{v}_{\text{current}}\vert$.

**2. Surface Layer Hierarchy & Galilean Invariance for Raft Traversal**

A Raft (`AssetCategories.OBJECTS`, `AssetInstances.RAFTS`) serves as a dynamic, floating platform. To resolve whether an entity is floating *on* a raft or swept away *in* the water, `MotionMechanics` evaluates surfaces along a vertical hierarchy:

$$\text{Terrain Canvas} < \text{Fluid Sensor} < \text{Raft Deck} < \text{Passenger Body}$$

1. **Raft Dynamics**: A Raft does not occlude fluid propagation (it is explicitly bypassed in `Actuator._collect_obstacles`). In `MotionMechanics`, the Raft passively acquires the underlying fluid's current vector: $\vec{v}_{\text{raft}} = \vec{v}_{\text{current}}$.
2. **Passenger Dynamics**: When a character's footprint intersects an active Raft hitbox, the Raft acts as a local reference frame:
* The Raft's physical deck shields the character from direct fluid contact (`triggers.submerged = False`).
* The passenger retains voluntary movement relative to the deck:

$$
\vec{v}_{\text{passenger}} = \vec{v}_{\text{locomotion}} + \vec{v}_{\text{raft}}
$$

* When the passenger stands still ($\vec{v}_{\text{locomotion}} = \vec{0}$), they drift with the raft, maintaining a constant relative coordinate without requiring complex parent-child container trees.

**3. Visual Submersion: Waistline Cropping vs. Water-Wash Blending**

The goal is to render characters waist-deep in water with an active water line and splash particles.

* **Feasibility Analysis of Texture Slicing vs. Blending**:
* *Option A (Discrete Texture Slicing)*: Dividing LPC character sheets into upper/lower sub-rectangles via `SpriteFrame` would require indexing every animation frame, equipment layer, and direction into upper and lower halves. For an LPC sheet with equipment stacks, this doubles the draw calls per character from 5 to 10.
* *Option B (Waistline Surface Tint & Splash Anchor)*: Render the character normally, but when `state.mutators.triggers.submerged = True`:
1. `Screen.draw()` blits a semi-transparent water overlay (`water_wash`) across the lower half of the character's bounding box: $[y + \frac{l}{2}, y + l]$.
2. `Cradle.spawn_passive()` instantiates a temporary `splash` effect anchored at $(x, y + \frac{l}{2})$.

* Option B delivers identical visual fidelity with zero registry key bloat and no impact on the core animation system.

**4. Pool Geometry & Transparent Pixel Bleed**

Excluding the obstacle's bounding box $(o_x, o_y, o_w, o_l)$ from the annular pool leaves a void in the fluid canvas. Because sprite artwork for obstacles (e.g., crates, rocks) contains transparent padding around rounded edges, dry background terrain tiles bleed through the boundary.

Because `FluidState` declares `height = 0` and `depth = -1`, the entire compound fluid sorts *underneath* obstacles (`depth = 0`, `height = pos.y + dim.l`). The pool should render as a complete, unbroken rectangle across the entire flood zone $[x_{\text{pool}}, y_{\text{pool}}, w_{\text{pool}}, l_{\text{pool}}]$. The obstacle renders directly over the water, naturally eliminating background tile bleed through transparent pixels.

**5. RRT Pathfinding Dynamics: Traversability Costs vs. Soft Barriers**

Currently, `paths.pyx` executes standard RRT against a binary collision buffer (`_is_segment_clear`). Fluids cannot simply be injected as static obstacles, or sprites will be permanently blocked from swimming or boarding rafts.

* **Two-Tier Path Generation**:
    1. **Tier 1 (Dry-Land Bias)**: `NavigationMechanics` appends active fluid stream and pool hitboxes to the candidate `obstacles` list passed to `Planner.plan()`. RRT seeks a dry-land route around the water.
    2. **Tier 2 (Hydrodynamic Fallback)**: If Tier 1 fails (due to a river severing the layer, returning `stalled = True`), `NavigationMechanics` re-runs `Planner.plan()` without fluid hitboxes.

* When executing a Tier 2 water route, `NavigationMechanics` adjusts the arrival radius and anticipates current displacement, while `CognitionMechanics` can evaluate strategic goals for nearby rafts.


##### Goal: Environmental Current Vector Field

Impart directional velocities to entities intersecting fluid corridors. In `FluidMechanics`, calculate active current vectors for all fluid emitters based on `source` and `flow`. In `MotionMechanics`, combine current vectors with player and sprite locomotion, disabling orthogonal snapping when submerged.

```python
# Conceptual Velocity Addition in Motion Submodules
v_current = fluid.current_velocity()  # (flow * BASE_SPEED * unit_vector)
final_vx = locomotion_vx + v_current.vx
final_vy = locomotion_vy + v_current.vy

```

##### Goal: Raft Object Entity & Galvanic Reference Frames

Introduce `rafts` under `AssetCategories.OBJECTS` with `PositionalState`. Rafts drift passively with fluid currents without obstructing fluid raycasts. Sprites boarding a Raft inherit its drift velocity as a baseline reference frame, suppressing the `submerged` mutator.

##### Goal: Solid-Base Annular Pool Rendering

Eliminate transparent border bleed around struck obstacles. Update `Actuator._partition_pool` and `FluidFrame.keys` to render a solid rectangular field of water across the full outer pool perimeter, relying on `height = 0` and `depth = -1` to sort beneath the obstacle body.

##### Goal: Submersion State & Splash Particle Spawning

Introduce `triggers.submerged` to `SpriteState.mutators`. When an un-rafted entity enters a fluid corridor, flag `submerged = True`, apply a half-height water wash tint in `Screen.draw()`, and dispatch `Cradle.spawn_passive()` to spawn temporary splash effects along the waterline.

##### Goal: Two-Tier Water-Aware Pathfinding

Enable autonomous sprites to intelligently navigate around or through fluid bodies. In `NavigationMechanics`, execute a dry-land RRT path pass with fluids marked as barriers; if occluded, fallback to an aquatic pass with current-biased steering.

##### Tasks

**1. Task: Schemas, Taxonomy & Raft Registration**

*Objective*: Register `rafts` in the asset taxonomy and add hydrodynamic attributes to state models.

* [ ] Subtask: Register `rafts` under `AssetInstances` enum and `ObjectPropertyInstances` schema in `models/properties.py`.
* [ ] Subtask: Add `submerged: bool = False` to `MutatorTriggers` in `models/state/sheets.py`.
* [ ] Subtask: Define default recipes for `rafts` in `src/data/config/recipes/main.yaml`.
* [ ] Subtask: Update `Actuator._collect_obstacles` to explicitly exclude `AssetInstances.RAFTS.value` from fluid obstruction.

**2. Task: Hydrodynamic Current Calculation & Velocity Integration**

*Objective*: Implement directional force transfer from fluid streams to dynamic entities.

* [ ] Subtask: Add `current_velocity(flow: int, source: Directions) -> Velocity` helper to `app.game.logic.modules.world.fluid`.
* [ ] Subtask: Update `kinematic.py` to sample underlying fluid currents and apply vector addition ($\vec{v}_{\text{final}} = \vec{v}_{\text{input}} + \vec{v}_{\text{flow}}$).
* [ ] Subtask: Update `motive.py` to add underlying fluid currents to autonomous avoidance vectors.
* [ ] Subtask: Implement passive drift in `MotionMechanics` for un-piloted rafts and floating dynamic crates.

**3. Task: Solid Annular Pool Partitioning**

*Objective*: Fix transparent background bleed around internal obstacles by eliminating the hollow pool core.

* [ ] Subtask: Refactor `Actuator._partition_pool()` to generate hitboxes covering the complete bounding box $[x_{\text{pool}}, y_{\text{pool}}, w_{\text{pool}}, l_{\text{pool}}]$.
* [ ] Subtask: Update `FluidFrame.keys()` to blit a continuous grid of water tiles across the entire pool area.
* [ ] Subtask: Verify Z-ordering guarantees the struck obstacle sorts cleanly above the solid pool canvas.

**4. Task: Submersion Visuals & Cradle Passive Spawning**

*Objective*: Implement waistline water rendering and dynamic splash particles.

* [ ] Subtask: Add `spawn_passive(id: str, layer: str, position: Position)` to `app.services.generators.game.cradle.py`.
* [ ] Subtask: Add `submerged` evaluation in `SpatialMechanics` / `FluidMechanics`, toggling `sprite.state.mutators.triggers.submerged`.
* [ ] Subtask: Trigger `cradle.spawn_passive("splash", layer, waterline_pos)` upon initial fluid entry.
* [ ] Subtask: Add waistline alpha-blended tint blit in `Screen.draw()` for entities with `submerged == True`.

**5. Task: Two-Tier Navigation Planning**

*Objective*: Integrate fluid avoidance and aquatic pathfinding into `NavigationMechanics`.

* [ ] Subtask: Update `NavigationMechanics.obstacles()` to optionally include fluid hitboxes during standard path planning.
* [ ] Subtask: Implement two-tier fallback in `NavigationMechanics._navigate()`: attempt dry path; if stalled, retry without fluid barriers.
* [ ] Subtask: Adjust arrival tolerance for waypoints located in active fluid currents to prevent waypoint overshoot.

---

### Documentation Divergences

#### Draft: MotionMechanics Hydrodynamic Velocity Integration

* **Page**: `docs/05-mechanics.md`
* **Heading**: `MotionMechanics`

##### Drift

The documentation specifies that kinematic assets (Players) strictly clamp velocity vectors to cardinal directions and snap orthogonal components to zero, while motive assets (Sprites) steer solely via RVO and line-of-sight waypoints. It does not account for environmental velocity offsets imparted by fluid currents.

##### Update

```markdown
**MotionMechanics**

Assets with Mass are divided into Kinematic, Motive, Inert, and Frictive Assets.

* **Kinematic Assets (Players)**: Polls input devices. In dry environments, input clamps velocity vectors to `character.speed` and nullifies orthogonal components. When intersecting an active Fluid stream or pool, kinematic snapping is disabled: voluntary input velocity is added vectorally to the underlying fluid current:
  $$\vec{v}_{\text{final}} = \vec{v}_{\text{input}} + \vec{v}_{\text{current}}$$
* **Motive Assets (Sprites)**: Guided by `NavigationMechanics`. Evaluates avoidance and waypoint steering vectors. In fluid corridors, the environmental current vector is added to the steering vector.
* **Frictive Assets (Crates)**: Passively receive momentum from physical collisions, decaying via tile friction. Floating dynamic bodies in fluids drift along the stream vector.
* **Rafts**: Specialized dynamic objects that do not obstruct fluid propagation. Rafts passively drift at the fluid current velocity $\vec{v}_{\text{current}}$. Passengers aboard a Raft adopt the Raft's velocity as their baseline reference frame, suppressing the submerged state.

```

---

#### Draft: Raft Object Taxonomy & Properties

* **Page**: `docs/01-assets.md`
* **Heading**: `Objects`

##### Drift

The object hierarchy lists Chests, Crates, Doors, Gates, Plates, and Signs, but does not specify the Raft instance or its interactions with fluids and passengers.

##### Update

```markdown
### Rafts

Rafts are dynamic Objects that allow Sprites and Players to traverse Fluid corridors without entering the `submerged` state or being swept away individually. Rafts do not obstruct Fluid flow.

**Dynamics & Relative Motion**

* When deployed in a Fluid corridor, a Raft drifts along the Fluid's `source` vector at a speed proportional to `flow`.
* Characters boarding a Raft have their `mutators.triggers.submerged` mutator suppressed.
* While aboard, character locomotion is evaluated relative to the Raft's deck:
  $$\vec{v}_{\text{world}} = \vec{v}_{\text{locomotion}} + \vec{v}_{\text{raft}}$$

**Properties: ObjectProperties**

* `dimensions: Dimensions`
* `hitboxes: List[Hitbox]`
* `mass: int = 10`

**Frame: SingleFrame**

* `keys(id, state)`: returns `[(id, 0, 0)]`
* `index(id, properties)`: returns `{id: (0, 0, properties.dimensions.w, properties.dimensions.l)}`

**State: PositionalState**

* `layer: str`
* `position: Position`
* `velocity: Velocity`
* `depth: int = 0`
* `height: Optional[int] = None`

```

---

#### Draft: Sprite Submerged Mutator & Splash Lifecycle

* **Page**: `docs/02-sprites.md`
* **Heading**: `Mutators`

##### Drift

The mutator specifications document `animated`, `dead`, `fear`, and `vision`, but omit the `submerged` trigger used for aquatic rendering and splash effect dispatching.

##### Update

```markdown
**Triggers**

* `triggers.animated`: Triggered if a Sprite is currently able to animate.
* `triggers.dead`: Triggered if `character.health.current == 0`.
* `triggers.fear`: Triggered when health falls below threshold or nearby enemies exceed limit.
* `triggers.vision`: Triggered when Goal is within line of sight.
* `triggers.action`: Triggered when within interaction radius of Goal.
* `triggers.submerged`: Triggered when the entity's footprint intersects an active Fluid stream or pool without being aboard a Raft or Bridge. When active, `Screen.draw` renders a semi-transparent water tint over the lower half of the Sprite, and `Cradle` dispatches a temporary `splash` effect.

```

---

### Bug Reports

##### Bug B012: Annular Pool Hollow Obstacle Core Transparency Bleed

**STATUS**: OPEN

**SEVERITY**: MEDIUM

**Description**

In `Actuator._partition_pool`, the annular pool geometry is generated by creating four perimeter flank rectangles around the obstacle's bounding box $[o_x, o_y, o_w, o_l]$, leaving the interior core unflooded.

Because obstacle assets (such as crates, barrels, and rocks) have transparent pixels along their edges, the underlying dry terrain canvas (`bg_canvas`) shows through around the obstacle contours.

**Steps to Replicate**

1. Place an obstacle Crate of dimensions $(32, 32)$ at $(100, 100)$.
2. Direct a fluid stream with `flow = 2` into the crate.
3. Observe the rendered output in non-headless mode: dry grass tiles appear inside the transparent corners of the crate graphic instead of water.

**Proposed Remediation**

In `Actuator._partition_pool`, return a single outer bounding box covering $[o_x - F \cdot w, o_y - F \cdot l, o_w + 2F \cdot w, o_l + 2F \cdot l]$. In `FluidFrame.keys`, blit the grid of water tiles across the entire rectangular extent. Because `FluidState` declares `height = 0` and `depth = -1`, the obstacle will naturally draw on top of the water, filling transparent areas with water texture.

---

##### Bug B013: Missing Passive Effect Generation Interface in Cradle

**STATUS**: OPEN

**SEVERITY**: LOW

**Description**

`Cradle` in `src/app/services/generators/game/cradle.py` exposes explicit spawn factory methods for `spawn_projectile`, `spawn_collectable`, `spawn_hazard`, `spawn_strut`, and `spawn_composition`.

However, it lacks a `spawn_passive` method for instantiating temporary, non-damaging environmental effects under `AssetInstances.PASSIVE` (e.g., `splash`, `water_ripple`). Any mechanic attempting to spawn dynamic particles at runtime cannot do so via `Cradle`.

**Steps to Replicate**

1. Inspect `Cradle` methods in `src/app/services/generators/game/cradle.py`.
2. Attempt to spawn a water splash effect: `cradle.spawn_passive("splash", layer, pos)`.
3. An `AttributeError: 'Cradle' object has no attribute 'spawn_passive'` is raised.

**Proposed Remediation**

Implement `spawn_passive` on `Cradle`:

```python
def spawn_passive(self, id: str, layer: str, position: Position) -> Asset:
    recipe = self.recipes.effects.passive
    properties = self.spawnables.passive.get(id)
    name = self.name()

    state = AnimatorState(
        id=id,
        name=name,
        layer=layer,
        position=position,
        animation=AnimationState()
    )
    frame = Factory.frame(recipe.frame)
    animation = Factory.animation(recipe.animation)
    taxonomy = Factory.taxonomy(
        id=id,
        name=name,
        category=AssetCategories.EFFECTS,
        instance=AssetInstances.PASSIVE
    )
    return Asset(taxonomy, properties, state, frame, animation)

```