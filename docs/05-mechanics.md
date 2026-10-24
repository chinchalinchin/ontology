# Ontology Docs: Mechanics

A Mechanic is an implementation of an abstract interface the [Engine](./00-overview.md#component-engine) calls during its core loop. All Mechanics must implement the following method signature:
 
`update(board: Board, delta: float, bus: collections.deque, payload: DevicePayload)`  

* `board`: The Application [Board](./00-overview.md#component-board) database.
* `delta`: Time delta of the current [Engine](./00-overview.md#component-engine) loop.
* `bus`: A Bus for storing [Events](./06-widgets.md#events)
* `payload`: The current [Device](./02-sprites.md#devices) Payload. 

Once a Mechanic registered in the [Mechanics Configuration](./appendices/01-schemas.md#configuration-mechanics) and implements this signature, the arguments will be injected from above by the [Engine](./00-overview.md#componentengine) each tick of its loop.

!!! note "Mechanic Keys"
    Mechanics are listed below using `key: class`, where `key` is the unique string identifier for the associated Mechanic implementation. This `key` is used in the [Mechanics Configuration](#configuration) to specify the order of execution.

### Mechanics: Core

* Address: `app.game.logic.mechanics.core`

These Mechanics handle the core engine logic.

* `animation AnimationMechanics`: Translates current states into FrameKeys for the renderer.
* `remove: RemoveMechanics`: General garbage collection for Assets whose lifespan has expired.
* `motion: MotionMechanics`: Applies acceleration and velocity integrations to Assets to arrive at their next position.
* `menu: MenuMechanics`: Handles Menu and Widget interactions.
* `telemetry: TelemetryMechanics`: Manages TCP socket queries for game state requests.

#### Core Mechanic: AnimationMechanics

TODO

#### Core Mechanic: MotionMechanics

**Behavior: Updates**

MotionMechanics updates the Velocity of Assets via Symplectic Euler Integration:

$$
v_{n+1} = \max(0, v_n - \text{friction} \cdot \Delta t)
$$

##### Motion: Dynamics

Assets with Mass are divided into behavioral groups.

**Kinematic Assets: Players**

Polls input devices. In dry environments, input clamps Velocity vectors to Speed and nullifies orthogonal components. When intersecting an active Fluid stream or pool, kinematic snapping is disabled: voluntary input velocity is added vectorally to the underlying fluid current:

$$
\vec{v}_{\text{final}} = \vec{v}_{\text{input}} + \vec{v}_{\text{current}}
$$

**Motive Assets: Sprites**

Guided by NavigationMechanics. Evaluates avoidance and Trajectory vectors. In [Field](#motion-fields) streams, the Field vector is added to the Trajectory vector.

**Frictive Assets: Crates**

Passively receive momentum from physical collisions, decaying via tile friction. Floating dynamic bodies in fluids drift along the stream vector.

The mathematical bounds for Friction are $[0, \infty)$.

* *Lower Bound* ($0$): A value of exactly $0$ yields $\Delta v = 0$, meaning the asset will glide indefinitely without losing momentum until it strikes a static body. 
* *Upper Bound* ($\infty$): Any value satisfying the condition $\text{friction} \cdot \Delta t \ge \vert v \vert$ will eventually halt the Asset.

!!! note "Units"
    The `friction` Property of [Environ Tiles](./01-assets.md#tile-environ) defines the rate of linear velocity decay, measured in pixels per second squared ($px/s^2$).

**Galilean Assets: Rafts**

Specialized Assets that do not obstruct Fluid propagation. Rafts passively drift at the Fluid current velocity $\vec{v}_{\text{current}}$. Passengers aboard a Raft adopt the Raft's velocity as their baseline reference frame, suppressing the `submerged` Mutator.

**Inert Assets: Projectiles**: 

Translates along linear trajectories until lifetime expiration or boundary collision triggers garbage collection.

##### Motion: Fields

###### Field: Fluids

!!! @TODO(T002)
    Bouyancy is not yet fully implemented.

Dynamic Assets ($m > 0$) interacting with active Fluid streams and pools evaluate buoyancy via the `buoyant` Property.

**Behavior: Buoyancy**

* `if properties.bouyant`:
    * $\vec{v}_{\text{final}} = \vec{v}_{\text{self}} + \vec{v}_{\text{current}}$
    * `state.mutators.triggers.submerged = true`
    * Tile Friction is suspended, allowing drift.
* `if not properties.buoyant`:
    * TODO: equations with friction
    * `state.mutators.triggers.submerged = True`
    * Tile Friction remains active, causing Assets to resist water flow.

###### Field: Gravity

!!! @TODO(07-03)
    Needs elaboration.

Let world space be parameterized by $(X, Y, Z)$, where $(X, Y)$ spans the horizontal ground plane ($E = 0$) and $Z \ge 0$ is the vertical elevation axis perpendicular to the ground plane:

1. **Assumption**: Camera rays are parallel and intersect the horizontal ground plane $(X, Y)$ at a constant inclination angle $\theta = 60^\circ$.

2. **Assumption**: For a point at discrete elevation $E$ dropping by $\Delta E = 1$ to $E - 1$, the vertical elevation change ($\Delta z$), the horizontal ground change ($\Delta y$), and the camera line-of-sight ray ($L_{\text{LOS}}$) form a right triangle $\triangle$ with right angle at the base of the vertical leg and acute angle $\theta = 60^\circ$ at the ground intercept.

$$
\tan(\theta) = \frac{\Delta z}{\Delta y}, \qquad \sin(\theta) = \frac{\Delta z}{L_{\text{LOS}}}, \qquad \cos(\theta) = \frac{\Delta y}{L_{\text{LOS}}}
$$

**Unit Elevation Drop ($\Delta y_{\text{elevation}}$):**

Taking the horizontal ground run of one unit Tile as the adjacent leg ($\Delta y = U = 32\text{ px}$), the vertical leg opposite $\theta = 60^\circ$ (the Screen-space $+y$ of one unit elevation) is:

$$
\Delta y_{\text{elevation}} = U \cdot \tan(60^\circ) = 32\sqrt{3} \approx 55.43\text{ px}
$$

Equivalently, taking the line-of-sight hypotenuse across a two-tile Sprite frame ($L_{\text{LOS}} = 2U = 64\text{ px}$) yields the same opposite vertical leg:

$$
\Delta y_{\text{elevation}} = L_{\text{LOS}} \cdot \sin(60^\circ) = 64 \cdot \frac{\sqrt{3}}{2} = 32\sqrt{3} \approx 55.43\text{ px}$$

Under this formulation, Gravity is purely a property of the topological elevation planes $E \in \mathbb{Z}$: every $\Delta y_{\text{elevation}} = U \tan(\theta)$ pixels of vertical freefall transitions the entity down one discrete elevation plane ($E \to E - 1$), where support is re-evaluated immediately.

#### Core Mechanic: MenuMechanics

!!! note "Menu Stack"
    In the event of multiple Menus (e.g. a dialogue modal over a trade menu), MenuMechanics is constrained to interact with the top of the Menu stack (`board.menus[-1]`).

MenuMechanics delegates to logic to MenuController classes. MenuMechanics is responsible for general Menu logic (e.g. traversal, opening, closing). The MenuController is responsible for particular Menu logic (e.g. equipping, buying, selling). The general workflow of MenuMechanics is given below,

1. **Check Stack:** If `len(board.menus) == 0`, exit early.
2. **Get Top Menu:** `menu = board.menus[-1]`
3. **Poll Input:**
    * If `NORTH/SOUTH/WEST/EAST`: Look at `menu.state.focus`. Look up the key in `active_menu.state.graph`. If a neighbor exists, change `focus` and update the `TraversalAnimation` status of the respective Button Assets.
    * If `SELECT`: Call `amenu.controller.select(menu.state.focus, menu, board)`.
    * If `CANCEL`: Pop the menu off the stack. (Unpause the board if the stack is now empty).
4. **Tick:** Call `menu.controller.update()` so continuous menus (like the View) can update their meters.

AnimationMechanics strictly governs "World Time". MenuMechanics governs "Menu Time". The `animate()` interface for Widgets is called inside MenuMechanics, iterating over `board.overlays` (always) and `board.menus[-1]` (if active).

### Mechanics: Spatial

* Address: `app.game.logic.mechanics.spatial`

These Mechanics handle spatial interactions and collisions between Assets.

* `switch: SwitchMechanics`: Binds the Gate and Plate states together based on their `switch`.
* `projectile: ProjectileMechanics`: Increment projectile positions, checks intersections and resolves impacts.
* `collision: CollisioMechanics`: Resolves collisions.
* `combat: CombatMechanics`: Resolves attack hitbox overlaps, decrements health, etc.
* `interaction: InteractionMechanics`:Resolves Asset interactions.
* `social: SocialMechanics`: Handle Social Intentions and [Plot calculations](./08-plots.md).

**Base: SpatialMechanics**

This class serves to unpack the Application data structures into raw primitives to pass through the Cython boundary, and then package the results back into the Application data structures. All Spatial Mechanics inherit from this class to abstract away the boilerplate and core geometrical calculations of collisions.

* `collisions(assets) -> List[(asset, asset)]`: Returns pairs of colliding Assets.
* `intersections(assets) -> List[(asset, asset)]`: Returns pairs of intersecting Assets.
* `proximities(assets) -> List[(asset, asset)]`: Returns pairs of Assets within each other's Mutator Action radius. 
* `constrain(asets, boundaries, elevation) -> [(asset, boundary)]`: Returns pairs of colliding Asset and Boundaries.

#### Spatial Mechanic: InteractionMechanics

* `source | source.state.intention == Intentions.INTERACT`
* `target | (source, target) in self.intersections(assets)`
* `if source.instance == AssetInstances.SPRITES`:
    * `if target.instance == AssetInstances.CHESTS`: 
        * `TODO`
    * `if target.instance == AssetInstances.DOORS`:
        * `source.state.layer = door.state.outlayer` 
    * `if target.instance == AssetInstances.PLATES`: 
        * `gates[plate.state.link].state.switch = plate.state.switch`
* `if source.instance == AssetInstances.PLAYERS:`
    * `if target.instance == AssetInstances.CHESTS`: 
        * `bus.append(MenuEvent('inventory'))` 
    * `if target.instance == AssetInstances.PLATES`: 
        * `gates[plate.state.link].state.switch = plate.state.switch`
    * `if target.instance == AssetInstances.DOORS`: 
        * `source.state.layer = door.state.outlayer` 
    * `if target.instance == AssetInstances.SIGNS`: 
        * `bus.append(MenuEvent('dialogue'))`

#### Spatial Mechanic: CollisionMechanics

!!! @TODO
    Out of date.

When Assets collide, overlap resolution uses inverse mass ratios to correct spatial positioning, ensuring immutable Assets with no Mass (`m = 0`) remain  immobile while dynamic Assets with Mass (`m > 0`) absorb the displacement shift. Post-separation, Velocities are updated via elastic collision formulas, conserving momentum across all participating masses,

$$
v_{1f} = \frac{v_1(m_1 - m_2) + 2m_2v_2}{m_1 + m_2}
$$

The [Player](./02-sprites.md#player) does not observe momentum transfers. Instead, the Player follows the procedures outlined below,

* **Property Level:** The Player retains a normal, dynamic mass (e.g., $m = 10$).
* **Phase 1 - Spatial Resolution:**
    * **Player vs. Wall ($m=0$):** `inv_total` is $> 0$. The Wall absorbs 0% of the overlap shift, and the Player absorbs 100%. The Player halts at the wall boundary.
    * **Player vs. Crate ($m=5$):** Both absorb the spatial shift proportional to their inverse mass. The Player pushes the Crate out of the way.
* **Phase 2 - Momentum Transfer:** Bypass the 1D elastic collision calculation *only* for the Player.

CollisionMechanics partitions active weights by discrete elevation tiers (`tier = max(0, w.elevation)`), isolating Phase 1 boundary constraint solving and Phase 2 elastic momentum resolution.

Incline transitions (`_traverse_stairs`) execute in Phase 0 of `CollisionMechanics` strictly prior to tier partitioning, ensuring elevation mutations take effect within the current frame's broad-phase spatial hash.

#### Spatial Mechanic: CombatMechanics

```mermaid
--8<-- "static/mmd/mechanics-combat.mmd"
```

CombatMechanics queries the active Attackboxes associated with the entity's current AnimationState. Attacker primitives are injected into the spatial hash using the result and used to evaluate the collision. Attackers with no attackboxes configured on their current Animation State `frame` bypass Combat collision checks.

### Mechanics: Intentional

These Mechanics handle Sprite intentionality, goal-seeking, and tactical navigation.

* `player: PlayerMechanics`: Resolves Device input into Player (Intention, Goal)-state.
* `cognition: CognitionMechanics`: Manages high-level strategic Goal selection and memory stacks.
* `transition: TransitionMechanics`: Evaluates Intention Transition condition matrices and transitions Intention States.
* `navigation: NavigationMechanics`: Resolves tactical steering, line-of-sight, and waypoint queues.
* `commerce: CommerceMechanics`: Translates communicative intentions (`barter`, `attract`) into trades and price updates.

!!! important "Separation of Duties"
    [CognitionMechanics](#intentional-mechanic-cognitionmechanics) mutates Goals, [TransitionMechanics](#intentional-mechanic-transitionmechanics) mutates Intentions, [NavigationMechanics](#intentional-mechanic-navigationmechanics) populates Trajectories, and [MotionMechanics](#core-mechanic-motionmechanics) integrates velocities. This separation of concerns is **strictly** enforced.

Mechanics, [Intentions and Goals](./04-intentions.md) are the "crux" of the Application. Their interplay and dynamic is the locus of the Application. Mechanics are "*laws of nature*" and Intentions & Goals are "*states of mind*"; Intentional Mechanics are, therefore, the "*psychological laws of the mind*".

1. Navigational Intentions (`find`, `follow`, `hunt`, `escape`, `wander`, `return`)
    * Handled by: CognitionMechanics, MotionMechanics
    * Logic: CognitionMechanics moves the Goal Position coordinate. Motion Mechanics accelerates Velocity vectors toward it.
2. Spatial/Interactive Intentions (`attack`, `mine`, `build`, `interaction`)
    * Handled by: CombatMechanics, InteractionMechanics
    * Logic: These Mechanics iterate "statelessly" over Sprites in their respective Intention. For example, CombatMechanics does not care how a Sprite got into the `attack` intention; it only applies logic once the Sprite is in `attack`.
3. Communicative Intentions (`speak`, `threaten`, `barter`)
    * Handled by: SocialMechanics, CommerceMechanics
    * Logic: Iterates over Sprites in communicative Intentions, checking if they are within conversational radius of their target to swap prices or rumors.

**Sprite AI**

Much of the logic in Mechanics is in support of Sprite AI, via the management of [Goals & Intentions](./04-intentions.md). NPC behavior is distributed across four sequential Mechanics in the World pipeline:

* **CognitionMechanics**: Manages high-level strategic Goal models (target tracking, cross-layer door subsumption, autonomous wander sampling, etc.).
* **TransitionMechanics**: Evaluates the [Intention Transition Matrix](./04-intentions.md#transition-matrix) to transition Intention States and map Actions to Animations.
* **NavigationMechanics**: Manages tactical spatial steering. Validates line-of-sight, extracts obstacle hitboxes, executesavoidance paths, and manages the Sprite's trajectory.
* **MotionMechanics**: Steers velocity vectors toward the trajectory's target and integrates physics.

To visualize how this all ties together for a [Sprite](./02-sprites.md) in a single frame,

```mermaid
--8<-- "static/mmd/mechanics-sprite-flow.mmd"
```

#### Intentional Mechanic: CognitionMechanics

CognitionMechanics acts as the Sprite's deliberative core. It operates exclusively on high-level Goals. 

For example, for Sprites in the given Intention states, CognitionMechanics generates and manages the following Goals:

* `wander`: Samples a random coordinate within the vision radius bounded by layer dimensions and commits a `Goal(name="wander", category=POSITION)`.
* `find / follow / hunt`: Queries the Board for the target entity. If visible, updates the Sprite Goal to match the target's coordinates. If the target leaves the Sprite's vision radius, coordinates freeze at the last known position.
* `escape`: Extrapolates a spatial coordinate in the vector direction opposite to the threat.
* **Cross-Layer Subsumption**: When a Goal's layer mismatches the sprite's layer, Cognition pushes the goal to Memory and substitutes a Goal for the nearest Door.

This is by no means an exhaustive list of CognitionMechanics' responsibility, but instead an example of its domain OF operation, e.g. Sprites and their Goals. CognitionMechanics is completely decoupled from geometric obstacles, intermediate waypoints, and line-of-sight raycasts. Intermediate path planning is offloaded entirely to [NavigationMechanics](#intentional-mechanic-navigationmechanics).

Since CognitionMechanics is intrinsically tied to Sprite Intentions and Goals, the cognition workflow is covered in more detail in the [Intentions amd Goals documentation](./04-intentions.md#cognition).

#### Intentional Mechanic: NavigationMechanics

NavigationMechanics acts as the Sprite's tactical navigator, bridging strategic Goals with physical locomotion:

1. **Goal Verification**: Verifies Goal exists and Intention belongs to NavigationIntentions. Clears Trajectory and yields if false.
2. **Anchor Resolution**: Computes sensory footprints using Anchors and targets footprint offsets, preventing top-left origin hitbox drift.
3. **Line-of-Sight Check**: Raycasts against active Layer obstacles and boundary perimeters.
4. **Path Maintenance**:
    - **Clear LOS**: Clears Trajectory and sets new target to Goal.
    - **Occluded LOS**: If Trajectory is empty, extracts obstacle hitboxes, executes a Plan, converts vertices to coordinates by subtracting anchor displacement, and populates Trajectories. Sets target to the first segment of the Trajectory.
    - **Dynamic Invalidation**: If active intermediate segments lose line-of-sight due to a moving dynamic Asset, invalidates the queue and replans immediately.
5. **Waypoint Arrival**: When the entity arrives within proximal range of target, pops the completed segment from its Trajectory and sets target to the next vertex (or Goal when vertices are exhausted).
6. **Stall & Cooldown Handling**: When Navigation cannot resolve a collision-free path, sets to `stalled` and starts a `cooldown` timer to prevent per-frame re-planning thrash.

**Module: Planner**

* `Planner(start, target, obstacles).plan(): returns [Position]`

The Planner is a wrapper around a Cython implementation of the Rapidly-Exploring Random Tree path-finding algorithm. See [Library: Math](./11-architecture.md#library-math) for more information.

**Model: Trajectory**

* `target`: 
* `vertices`:
* `stalled`:
* `cooldown`:

#### Intentional Mechanic: TransitionMechanics

TODO

### Mechanics: World

The World is a collection of correlated fields stored on the [Board](./00-overview.md#component-board). World Mechanics handle and mutate this macro State, performing high-level calculations and other abstract accounting.

* `plot: PlotMechanics`: Evaluates the [Plot Transition matrix](./08-plots.md#transition-matrix) to transition the [Board](./00-overview.md#component-board) [plot State](./08-plots.md#plot-states).
* `fluid: FluidMechanics`: Resolves [Fluid](./01-assets.md#effect-fluids) propagation, stream obstructions, and radial pool perimeter calculation.
* `season: SeasonMechanics`: Handles the accumulation of time, manages the lifespan of [Resources](./01-assets.md#category-resources) and the transition of Seasons on the [Board](./00-overview.md#component-board)

#### World Mechanic: FluidMechanics

```mermaid
--8<-- "static/mmd/mechanics-fluid.mmd"
```

FluidMechanics governs [Fluid](./01-assets.md#effect-fluids) emission and recursive bifurcation across active layers. It executes after physical momentum updates ([MotionMechanics](#core-mechanic-motionmechanics) and [CollisionMechanics](#spatial-mechanic-collisionmechanics)) and uses a 3-tier reactive dirty-checking architecture:

1. **Spatial Corridor Filtering**: Inspects switch-linked gates (`AssetInstances.GATES`). A mutating gate only flags the layer's fluids as `dirty` if the gate's AABB intersects active fluid compound hitboxes or falls within downstream emission corridors.
2. **Debounce Accumulator**: Consecutive gate oscillations are coalesced using `settings.FLUID_INVALIDATION_DEBOUNCE_TICKS` before triggering propagation.
3. **Pass 1 (Fluid Propagation & Bifurcation)**: For invalidated layers, `Actuator.propagate()` updates stream lengths, expands annular pools around static obstacles (\(m = 0\)), derives secondary branch corridors, and updates `board.update_fluid_cache(layer)`. Cache slots (`fluid.state._keys`) are cleared.
4. **Pass 2 (Geometric Shift Detection & Shoreline Synthesis)**: Compares the pre- and post-propagation geometric signature (`_fluid_signature`: stream lengths, pool bounds, branch positions). If water geometry is invariant, shoreline regeneration is bypassed. If geometry shifted (or during hydration), `Cartographer.purge()` and `Cartographer.generate()` synthesize updated boundary contours.

#### World Mechanic: SeasonMechanics

`SeasonMechanics` executes within the `world` mechanics pipeline, driving global time, soil hydrology, and biological resource lifecycles:

1. **Temporal Integration**: Accumulates frame $\Delta t$ into `board.calendar.elapsed`. When elapsed time reaches `settings.PERIOD_DURATION_SECONDS`, the mechanic advances `period` (0..2), `cycle` (`onset`, `peak`, `decline`), `season` (`spring`, `summer`, `autumn`, `winter`), and `year`, appending a `SeasonEvent` to the engine bus.
2. **Environmental Hydrology (Potential Field Integration)**: Soil moisture diffusion operates via a continuous scalar potential field calculated during `FluidMechanics` propagation and cached on `Board`. Dynamic 60 Hz updates avoid spatial lookups by reading `resource.state.moisture_flux`:
   * **Positive Flux**: Accumulates moisture via $\text{retention} \mathrel{+}= \kappa_{\text{diffusion}} \cdot \text{moisture\_flux} \cdot \Delta t$.
   * **Zero Flux**: Evaporates moisture via $\text{retention} \mathrel{-}= \kappa_{\text{evap}} \cdot \mu_{\text{season}} \cdot \Delta t$.
3. **Throttled Stage Transitions**: Biological and geological progression checks (`executor.evaluate(stage, locals)`) are decoupled from the 60 Hz physics loop, evaluating at a 1.0-second throttled frequency or upon calendar period transitions (`period_changed == True`).

#### World Mechanic: PlotMechanics

TODO

## Configuration: Mechanics

* Location: `/src/data/config/mechanics/main.yaml`

Mechanics Configuration defines what Mechanic classes are instantiated by the [Factory](./00-overview.md#service-factory) and what dependencies are injected into them. 

```yaml
mechanics:
    core:
        - key: <mechanic-key>
          executors: 
            - <executor-key>
          relations: 
            - <relation-key>
    world:
        - key: <mechanic-key>
          executors: 
            - <executor-key>
          relations:
            - <relation-key>
```

Mechanics are divided into [World Mechanics](#mechanics-world) and [Core Mechanics](#mechanics-core). Core Mechanics execute every single [Engine loop](./00-overview.md#component-engine), regardless of whether or not the [Board](./00-overview.md#board) is paused; These include [AnimationMechanics](#core-mechanic-animationmechanics) and [MenuMechanics](#core-mechanic-menumechanics). World Mechanics only execute when the [Board](./00-overview.md#component-board) is unpaused.

The order in which Mechanics are specified in the schema becomes the order of execution in the [Engine loop](./00-overview.md#component-engine).

## Dependencies

Systems requiring external services (such as the Actuator for [FluidMechanics](./05-mechanics.md#world-mechanic-fluidmechanics), or compiled Transition Executors for [TransitionMechanics](./05-mechanics.md#intentional-mechanic-transitionmechanics) and [PlotMechanics](./05-mechanics.md#world-mechanic-plotmechanics)) receive them through their constructor via Factory.

```mermaid
--*<-- "static/mmd/mechanics.bootstrap.mmd
```

### Dependency: Executors

Executors are Services made available to Mechanics that register to receive them in the [Configuration](#configuration-mechanics). Available Executors are enumerated below,

* `plot`: Executor for evaluating the conditions for [Plot Transitions](./08-plots.md).
* `intention`: Executor for evaluating the conditions for [Intention Transitions](./04-intentions.md)
* `actuator`: Executor for generating [Fluid](./01-assets.md#fluids) and [Shoreline](./01-assets.md#shorelines) Assets.
* `annual`: Executor evaluating [Resource Stage](./01-assets.md#resources) transitions for annual lifespans.
* `perennial`: Executor evaluating [Resource Stage](./01-assets.md#resources)transitions for perennial lifespans.
* `centennial`: Executor evalutating [Resource Stage](./01-assets.md#resources) transitions for centennial lifespans.

### Dependency: Relations

Relations are static mappings configured at runtime. Available Relations are enumerated below,

* `shorelines`: A map of [Shoreline Geography Asset IDs](./01-assets.md#shorelines) to a compound index of [Tile Asset IDs](./01-assets.md#tiles) and [Fluid Asset ID](./01-assets.md#fluids). This relation maps Fluid Shorelines to the Tiles in which they are embedded, e.g. `grassy-shore` Shorelines are mapped to `grass` Tiles and `water` Fluids. 
* `materials`: TODO

## Modules

### Modules: Maps

Maps associate ancillary Asset states to their final Animation state. See [AnimationMap](./04-intentions.md#animationmap) for more information.

The AnimationMap plays a crucial role in enforcing logical constraints for Animations. For example, TransitionMechanics and PlayerMechanics utilize AnimationMaps to resolve whether an intended action is possible. This guarantees that an `attack` Intention will not translate into a `thrust` Action if the Sprite currently lacks the required tool or weapon equipped in its inventory.

**Interface: Queries**

* `action(state, equipment): returns Action`