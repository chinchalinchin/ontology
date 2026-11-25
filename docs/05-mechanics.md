# Ontology Docs: Mechanics

A Mechanic is an implementation of an abstract interface the [Engine](./00-overview.md#component-engine) calls during its core loop. All Mechanics must implement the following method signature:
 
`update(board: Board, delta: float, bus: collections.deque, payload: DevicePayload)`  

* `board`: The Application [Board](./00-overview.md#component-board) database.
* `delta`: Time delta of the current [Engine](./00-overview.md#component-engine) loop.
* `bus`: A Bus for storing [Events](./06-widgets.md#events)
* `payload`: The current [Device](./02-sprites.md#devices) Payload. 

Once a Mechanic is registered in the [Mechanics Configuration](./appendices/01-schemas.md#configuration-mechanics) and implements this signature, the arguments will be injected from above by the [Engine](./00-overview.md#componentengine) each tick of its loop.

!!! note "Mechanic Keys"
    Mechanics are listed below using `key: class`, where `key` is the unique string identifier for the associated Mechanic implementation. This `key` is used in the [Mechanics Configuration](#configuration) to specify the order of execution.

### Mechanics: Core

* Address: `app.game.logic.mechanics.core`

These Mechanics handle the core [Engine](./00-overview.md#component-engine) logic.

* `animation AnimationMechanics`: Translates current states into FrameKeys for the renderer.
* `remove: RemoveMechanics`: General garbage collection for Assets whose lifespan has expired.
* `motion: MotionMechanics`: Applies acceleration and velocity integrations to Assets to arrive at their next position.
* `menu: MenuMechanics`: Handles Menu and Widget interactions.
* `telemetry: TelemetryMechanics`: Manages TCP socket queries for Telemetry requests.

#### Core Mechanic: AnimationMechanics

TODO

#### Core Mechanic: MotionMechanics

**Behavior: Updates**

MotionMechanics updates the Velocity of Assets via Symplectic Euler Integration:

$$
--8<-- "static/tex/algorithms/algorithm-000-sympletic-euler.tex"
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

Passively receive momentum from physical collisions, decaying via [Environ Tile](./01-assets.md#tile-environ) friction. Assets suspended in [Fluid](./01-assets.md#effect-fluids) drift along at the Fluid's stream vector.

The mathematical bounds for Friction are $[0, \infty)$.

* *Lower Bound* ($0$): A value of exactly $0$ yields $\Delta v = 0$, meaning the Asset will glide indefinitely without losing momentum until it strikes a static Asset or enters a region with friction. 
* *Upper Bound* ($\infty$): Any value satisfying the condition $\text{friction} \cdot \Delta t \ge \vert v \vert$ will eventually halt the Asset.

!!! note "Units"
    The `friction` Property of [Environ Tiles](./01-assets.md#tile-environ) defines the rate of linear velocity decay, measured in pixels per second squared ($px/s^2$).

**Galilean Assets: Rafts**

Specialized Assets that do not obstruct Fluid propagation. Rafts passively drift at the Fluid current velocity $\vec{v}_{\text{current}}$. Passengers aboard a Raft adopt the Raft's velocity as their baseline reference frame, suppressing the `submerged` Mutator.

**Inert Assets: Projectiles**

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

Let world space be parameterized by $(X, Y, Z)$, where $(X, Y)$ spans the horizontal ground plane ($E = 0$) and $Z \ge 0$ is the vertical elevation axis perpendicular to the ground plane:

1. **Assumption (Orthographic Parallelism)**: Camera rays are parallel and intersect the horizontal ground plane $(X, Y)$ at a constant inclination angle $\theta = 60^\circ$.
2. **Assumption (Right Triangle Formation)**: For a point at discrete elevation $E$ dropping by $\Delta E = 1$ to $E - 1$, the vertical elevation change ($\Delta z$), the horizontal ground change ($\Delta y$), and the camera line-of-sight ray ($L_{\text{LOS}}$) form a right triangle $\triangle$ with right angle at the base of the vertical leg and acute angle $\theta = 60^\circ$ at the ground intercept:

$$
--8<-- "static/tex/laws/law-002-perspective-ratios.tex"
$$


**Unit Elevation Drop ($\Delta y_{\text{elevation}}$):**

Taking the horizontal ground run of one unit Tile as the adjacent leg ($\Delta y = U = 32\text{ px}$), the vertical leg opposite $\theta = 60^\circ$ (the Screen-space $+y$ displacement of one unit elevation) is:

$$
--8<-- "static/tex/formulae/formula-001-tier-drop.tex"
$$

Under this formulation, Gravity is purely a property of the topological elevation planes $E \in \mathbb{Z}_{\ge 0}$: every $\Delta y_{\text{elevation}} = \text{TIER\_DROP\_DISTANCE} = 55\text{ px}$ of vertical freefall transitions an unsupported entity down one discrete elevation plane ($E \to E - 1$), where substrate support is re-evaluated immediately.

**Behavior: Substrate Support**

At Step 0 of `fields.update()`, entities at $E > 0$ are evaluated against walkable substrates occupying tier $E$ on the active layer via Cython's zero-allocation `geometry.occluded`. An entity is supported at tier $E > 0$ if its active hitboxes (or bounding dimensions) intersect any of the following Craft footprints:

* **Bridges**: Deployed at $e_{\text{base}} = E$.
* **Stairs**: Spanning $e_{\text{base}} < E \le e_{\text{base}} + \Delta e$, evaluated across the full stair tread bounding box $(x, y, w, l)$.
* **Struts**: Deployed at $e_{\text{base}} = E$ with a non-obstacle surface blueprint ($\neg\text{MaterialIndex.is\_obstacle}(\text{blueprint})$, e.g., `floors`, `flats`, `paths`, `corridors`) or sensor mass ($m < 0$).

Base terrain ($E = 0$) is unconditionally supported.

**Behavior: Freefall & Parabolic Momentum**

When an entity at $E > 0$ steps off its supporting substrate:

1. **Freefall Onset**: `state.mutators.triggers.falling` is set to `True`, `state.mutators.parameters.descension` and `state.position.ry` are reset to `0.0`, and upward vertical velocity is clamped via $v_y = \max(0.0, v_y)$.
2. **Orthogonal Momentum Preservation**: Because the $60^\circ$ orthographic pitch occurs strictly in the $(Y, Z)$ plane, horizontal velocity $v_x$ is orthogonally decoupled from vertical drop:

$$
--8<-- "static/tex/laws/law-002-freefall-velocities.tex"
$$

Preserving $v_{x,0}$ produces a natural screen-space parabolic trajectory $y(x) = y_0 + \frac{g}{2v_{x,0}^2}(x - x_0)^2$ until landing.

3. **Tier Stepping & Remainder Clamping**: Each tick, integer vertical displacement $\Delta y_{\text{step}} = \lfloor r_y + v_y \Delta t \rfloor$ is compared against the remaining distance to the next elevation plane, $\Delta y_{\text{rem}} = \text{TIER\_DROP\_DISTANCE} - \text{descension}$:
   * If $\Delta y_{\text{step}} \ge \Delta y_{\text{rem}}$, the entity's Y-coordinate advances to the exact plane intercept ($y + \Delta y_{\text{rem}}$), its elevation decrements ($E \to E - 1$), and support is re-evaluated at the new tier.
   * **Supported Landing ($E \ge 0$)**: If supported at $E - 1$, `falling` is cleared to `False`, `descension`, `position.ry`, and `velocity.vy` are zeroed, clamping the landing coordinate to an exact multiple of $\text{TIER\_DROP\_DISTANCE}$. On the subsequent frame, normal locomotion (`kinematic`, `motive`, or `frictive`) resumes and resolves any residual horizontal velocity $v_x$.
   * **Continuous Multi-Tier Fall**: If unsupported at $E - 1$, the entity retains $v_y$, updates `descension` with the overshoot remainder, and continues falling through intermediate planes until reaching a supported tier or $E = 0$.

**Behavior: System Suppression**

While `state.mutators.triggers.falling == True`, the entity is between discrete topological planes:

* **Locomotion & Navigation**: `kinematic.update()`, `motive.update()`, `frictive.update()`, and [NavigationMechanics](#intentional-mechanic-navigationmechanics) bypass the entity, preventing mid-air directional input, RVO steering, idle velocity zeroing, or tile friction from overriding freefall kinematics.
* **Environmental Fields**: Airborne entities are excluded from Bridge/Raft surface interception, Shoreline step-down nudges, and Fluid immersion in `fields.update()`.
* **Collisions & Ledges**: `CollisionMechanics` excludes airborne entities from Phase 0 stair traversal and Phase 2 solid collisions, and restricts Phase 1 environmental perimeter constraints to `elevation == 0` so dynamic entities can walk off un-walled ledges at $E > 0$.

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

#### Core Mechanic: RemoveMechanics

* Address `app.game.logic.mechanics.core.remove`

TODO

#### Core Mechanic: TelemetryMechanics

* Address: `app.game.logic.mechanics.core.telemetry`

TODO

### Mechanics: Spatial

* Address: `app.game.logic.mechanics.spatial`

These Mechanics handle spatial interactions and collisions between Assets.

* `switch: SwitchMechanics`: Binds the Gate and Plate states together based on their `switch`.
* `projectile: ProjectileMechanics`: Increment projectile positions, checks intersections and resolves impacts.
* `collision: CollisioMechanics`: Resolves collisions.
* `combat: CombatMechanics`: Resolves attack hitbox overlaps, decrements health, etc.
* `interaction: InteractionMechanics`:Resolves Asset interactions.
* `social: SocialMechanics`: Handle Social Intentions and [Plot calculations](./08-narratives.md).

**Base: SpatialMechanics**

This class serves to unpack the Application data structures into raw primitives to pass through the Cython boundary, and then package the results back into the Application data structures. All Spatial Mechanics inherit from this class to abstract away the boilerplate and core geometrical calculations of collisions.

* `collisions(assets) -> List[(asset, asset)]`: Returns pairs of colliding Assets.
* `intersections(assets) -> List[(asset, asset)]`: Returns pairs of intersecting Assets.
* `proximities(assets) -> List[(asset, asset)]`: Returns pairs of Assets within each other's Mutator Action radius. 
* `constrain(asets, boundaries, elevation) -> [(asset, boundary)]`: Returns pairs of colliding Asset and Boundaries.

#### Spatial Mechanic: InteractionMechanics

* Address: `app.game.logic.mechanics.spatial.interaction`

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

* Address: `app.game.logic.mechanics.spatial.collision`

CollisionMechanics resolves elevation transitions, perimeter collisions, and Asset collisions across three phases per active Layer. [Airborne entities](#field-gravity) are excluded from all three phases so freefall kinematics execute unobstructed across elevation planes.

1. **Phase 0 — Stairs**:
   * Prior to the evaluation of collisions, dynamic Asset intersecting Stairs are transitioned to the next elevation to participate in the correct elevation's collision calculations.
2. **Phase 1 — Perimeters**:
   * Queries the [Board's](./00-overview.md#component-board) perimeters and resolves overlap.
3. **Phase 2 — Collisions**:
   * Non-falling Asset are partitioned by elevation $E \in \mathbb{Z}_{\ge 0}$.
   * Colliding Assets have their overlap resolved:
     * **Spatial Separation**: Overlapping Assets shift apart along the minimum penetration axis proportional to their inverse mass ratios ($p_i = \frac{1/m_i}{1/m_1 + 1/m_2}$). Static Asset ($m = 0$) absorb $0\%$ of the shift ($1/m \to 0$), forcing dynamic Asset ($m > 0$) to absorb $100\%$ of the displacement.
     * **1D Elastic Momentum Transfer**: Post-separation velocities update via conservation of momentum:

    $$
    --8<-- "static/tex/laws/law-000-momentum-transfer.tex"
    $$

     * **Player Kinematic Exemption**: The Player retains positive mass ($m > 0$) during resolution against static walls ($m = 0$) and pushing movable Crates ($m > 0$), but bypasses velocity bounces.

#### Spatial Mechanic: CombatMechanics

* Address: `app.game.logic.mechanics.spatial.combat`

```mermaid
--8<-- "static/mmd/mechanics-combat.mmd"
```

CombatMechanics queries the active Attackboxes associated with the entity's current AnimationState. Attacker primitives are injected into the spatial hash using the result and used to evaluate the collision. Attackers with no attackboxes configured on their current Animation State `frame` bypass Combat collision checks.

CombatMechanic spawns a Projectile on the release frame of the Action. The initial scalar speed $s(S, n)$ is a function of the attacker's strength $S$ and the held tick duration $n$ relative to the draw window $N_{\max}$:

$$
--8<-- "static/tex/formulae/formula-003-projectile-speed.tex"
$$

#### Spatial Mechanic: ProjectileMechanics

* Address: `app.game.logic.mechanics.spatial.projectile`

TODO

#### Spatial Mechanic: SocialMechanics

* Address: `app.game.logic.mechanics.spatial.social`

TODO

#### Spatial Mechanic: SwitchMechanics

* Address: `app.game.logic.mechanics.spatial.switch`

TODO

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

**Concept: Intelligence**

Much of the logic in Mechanics is in support of Sprite Intellignece, via the management of [Goals & Intentions](./04-intentions.md). NPC behavior is distributed across four sequential Mechanics in the World pipeline:

* **CognitionMechanics**: Manages high-level strategic Goal models (target tracking, cross-layer door subsumption, autonomous wander sampling, etc.).
* **TransitionMechanics**: Evaluates the [Intention Transition Matrix](./04-intentions.md#transition-matrix) to transition Intention States and map Actions to Animations.
* **NavigationMechanics**: Manages tactical spatial steering. Validates line-of-sight, extracts obstacle hitboxes, executesavoidance paths, and manages the Sprite's trajectory.
* **MotionMechanics**: Steers velocity vectors toward the trajectory's target and integrates physics.

To visualize how this all ties together for a [Sprite](./02-sprites.md) in a single frame,

```mermaid
--8<-- "static/mmd/mechanics-sprite-flow.mmd"
```

#### Intentional Mechanic: PlayerMechanics

TODO 

#### Intentional Mechanic: CognitionMechanics

CognitionMechanics acts as the Sprite's deliberative core. It operates exclusively on high-level Goals. 

For example, for Sprites in the given Intention states, CognitionMechanics generates and manages the following Goals:

* `wander`: Samples a random coordinate within the vision radius bounded by layer dimensions and commits a Position Goal.
* `find / follow / hunt`: Queries the Board for the target entity. If visible, updates the Sprite Goal to match the target's coordinates. If the target leaves the Sprite's vision radius, coordinates freeze at the last known position.
* `escape`: Extrapolates a spatial coordinate in the vector direction opposite to the threat.
* **Cross-Layer Subsumption**: When a Goal's Layer mismatches the Sprite's Layer, Cognition pushes the goal to Memory and substitutes a Goal for the nearest Door.

This is by no means an exhaustive list of CognitionMechanics' responsibility, but instead an example of its domain of operation, e.g. Sprites and their Goals. CognitionMechanics is completely decoupled from geometric obstacles, intermediate waypoints, and line-of-sight raycasts. Intermediate path planning is offloaded entirely to [NavigationMechanics](#intentional-mechanic-navigationmechanics).

Since CognitionMechanics is intrinsically tied to Sprite Intentions and Goals, the cognition workflow is covered in more detail in the [Intentions amd Goals documentation](./04-intentions.md#cognition).

#### Intentional Mechanic: NavigationMechanics

NavigationMechanics acts as a [Sprite's Trajectory](./02-sprites.md#model-trajectory) manager, bridging strategic Goals with physical locomotion:

1. **Goal Verification**: Verifies Goal exists and Intention belongs to NavigationIntentions. Clears Trajectory and yields if false.
2. **Anchor Resolution**: Computes sensory footprints using Anchors and targets Assets using Minkowski inflation extents. 
3. **Line-of-Sight Check**: Raycasts against active Layer obstacles and boundary perimeters.
4. **Path Maintenance**:
    * **Clear LOS**: Clears Trajectory and sets new target to Goal.
    * **Occluded LOS**: If Trajectory is empty, extracts obstacle hitboxes, executes a Plan, converts vertices to coordinates by subtracting anchor displacement, and populates Trajectories. Sets target to the first segment of the Trajectory.
    * **Dynamic Invalidation**: If active intermediate segments lose line-of-sight due to a moving dynamic Asset, invalidates the queue and replans immediately.
5. **Waypoint Arrival**: When the entity arrives within proximal range of target, pops the completed segment from its Trajectory and sets target to the next vertex (or Goal when vertices are exhausted).
6. **Stall & Cooldown Handling**: When Navigation cannot resolve a collision-free path, starts a cooldown timer to prevent per-frame re-planning thrash.

**Module: Planner**

* `Planner(start, target, obstacles).plan(): returns [Position]`

The Planner is a wrapper around a Cython implementation of the Rapidly-Exploring Random Tree path-finding algorithm. See [Library: Math](./12-architecture.md#library-math) for more information.

**Model: Trajectory**

* `target`: 
* `vertices`:
* `stalled`:
* `cooldown`:

#### Intentional Mechanic: TransitionMechanics

TODO

### Mechanics: World

The World is a collection of correlated fields stored on the [Board](./00-overview.md#component-board). World Mechanics handle and mutate this macro State, performing high-level calculations and other abstract accounting.

* `plot: PlotMechanics`: Evaluates the [Plot Transition matrix](./08-narratives.md#transition-matrix) to transition the [Board](./00-overview.md#component-board) [plot State](./08-narratives.md#plot-states).
* `fluid: FluidMechanics`: Resolves [Fluid](./01-assets.md#effect-fluids) propagation, stream obstructions, and radial pool perimeter calculation.
* `season: SeasonMechanics`: Handles the accumulation of time, manages the lifespan of [Resources](./01-assets.md#category-resources) and the transition of Seasons on the [Board](./00-overview.md#component-board)

#### World Mechanic: FluidMechanics

* Address: `app.game.logic.mechanics.world.fluid`

```mermaid
--8<-- "static/mmd/mechanics-fluid.mmd"
```

FluidMechanics governs [Fluid](./01-assets.md#effect-fluids) emission and recursive bifurcation across active layers. It executes after physical momentum updates ([MotionMechanics](#core-mechanic-motionmechanics) and [CollisionMechanics](#spatial-mechanic-collisionmechanics)) and uses a 3-tier reactive dirty-checking architecture:

1. **Spatial Corridor Filtering**: Inspects switch-linked [Gates](./01-assets.md#object-gates). A Gate flags the Layer's [Fluids](./09-ecology.md#effect-fluids) for reconstruction if the [Gate's Hitbox](./01-assets.md#object-gates) intersects active [Fluid](./09-ecology.md#effect-fluids) hitboxes or falls within its stream.
2. **Debounce Accumulator**: Consecutive Gate oscillations ($\text{on} \leftright \text{off}$) are coalesced before triggering propagation.
3. **Pass 1 (Fluid Propagation & Bifurcation)**: For invalidated Layers, the [Actuator](#dependency-executors) updates stream lengths, expands annular pools around obstacles, and derives branch corridors.
4. **Pass 2 (Geometric Shift Detection & Shoreline Synthesis)**: Compares the pre- and post-propagation geometric signature. If water geometry is invariant, shoreline regeneration is bypassed. If geometry shifted (or during hydration), the Cartographer synthesizes updated boundary contours.

#### World Mechanic: SeasonMechanics

SeasonMechanics executes within the `world` mechanics pipeline, driving global time, soil hydrology, and biological resource lifecycles:

1. **Temporal Integration**: Accumulates frame $\Delta t$ into the [Board's Calendar](./00-overview.md#component-board). When the accumulated reaches certain thresholds, this Mechanic emits a [SeasonEvent](./06-widgets.md#concept-asychronicity) to the [Engine Bus](./00-overview.md#component-engine).
2. **Environmental Hydrology (Potential Field Integration)**: Soil moisture diffusion operates via a continuous scalar potential field calculated during [FluidMechanics](#world-mechanic-fluidmechanics) propagation and cached on [Board](./00-overview.md#component-board). Updates avoid spatial lookups by reading `resource.state.moisture_flux`:
   * **Positive Flux**: Accumulates moisture via $\text{retention} \mathrel{+}= \kappa_{\text{diffusion}} \cdot \text{moisture_flux} \cdot \Delta t$.
   * **Zero Flux**: Evaporates moisture via $\text{retention} \mathrel{-}= \kappa_{\text{evap}} \cdot \mu_{\text{season}} \cdot \Delta t$.
3. **Throttled Stage Transitions**: Biological and geological progression checks are decoupled from the [Engine Loop](./00-overview.md#component-engine), evaluating at a 1.0-second throttled frequency or upon calendar period transitions.

#### World Mechanic: PlotMechanics

TODO

## Configuration: Mechanics

* Location: `/src/data/configurations/engine/mechanics/main.yaml`

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

Mechanics are divided into [World Mechanics](#mechanics-world) and [Core Mechanics](#mechanics-core). Core Mechanics execute every single [Engine Loop](./00-overview.md#component-engine), regardless of whether or not the [Board](./00-overview.md#component-board) is paused; These include [AnimationMechanics](#core-mechanic-animationmechanics) and [MenuMechanics](#core-mechanic-menumechanics). World Mechanics only execute when the [Board](./00-overview.md#component-board) is unpaused.

The order in which Mechanics are specified in the schema becomes the order of execution in the [Engine loop](./00-overview.md#component-engine).

## Dependencies

Systems requiring external services (such as the Actuator for [FluidMechanics](./05-mechanics.md#world-mechanic-fluidmechanics), or compiled Transition Executors for [TransitionMechanics](./05-mechanics.md#intentional-mechanic-transitionmechanics) and [PlotMechanics](./05-mechanics.md#world-mechanic-plotmechanics)) receive them through their constructor via Factory.

```mermaid
--8<-- "static/mmd/mechanics-bootstrap.mmd"
```

### Dependency: Executors

Executors are Services made available to Mechanics that register to receive them in the [Configuration](#configuration-mechanics). 

* **Automaton Transition Executors**
    * `plot`: Executor for evaluating the conditions for [Plot Transitions](./08-narratives.md).
    * `intention`: Executor for evaluating the conditions for [Intention Transitions](./04-intentions.md)
    * `annual`: Executor evaluating [Resource Stage](./01-assets.md#resources) transitions for annual Lifespans.
    * `perennial`: Executor evaluating [Resource Stage](./01-assets.md#resources) transitions for perennial Lifespans.
    * `centennial`: Executor evalutating [Resource Stage](./01-assets.md#resources) transitions for centennial Lifespans.
* **Rule Evaluation Executors**
    * `goal`: Evaluates conditions for the [Goal Resolution Matrix](./04-intentions.md#goal-satisfaction).
* **Procedural Generatoration Executors**
    * `actuator`: Executor for generating [Fluid](./01-assets.md#effect-fluids) and [Shoreline](./01-assets.md#shorelines) Assets.

### Dependency: Relations

Relations are static mappings configured at runtime and then injected into requesting Mechanics.

* `shorelines`: A map of [Shoreline Geography Asset IDs](./01-assets.md#shorelines) to a compound index of [Tile Asset IDs](./01-assets.md#category-tiles) and [Fluid Asset ID](./01-assets.md#effect-fluids). This relation maps [Fluid Shorelines](./09-ecology.md#geography-shorelines) to the [Environ Tiles](./01-assets.md#tile-environ) in which they are embedded, e.g. `grassy-shore` Shorelines are mapped to `grass` Environ Tiles and `water` Fluids. 
* `materials`: A map of [Asset Material](./01-assets.md#concept-materiality) containing various Configurations, such as rendering substrates, obstacle classification, [cost constants](./03-compositions.md#materializer-cost) and [Composition formulae](./03-compositions.md).
* `projectiles`: A map of [Projectile Cursors](./01-assets.md#cursor-projectiles) to [Equipment Sheets](./02-sprites.md#sheet-equipment). This mapping determines which Projectile is spawned when a Sprite equipped with the prerequisite Equipment enters into the `attack` [Intention](./04-intentions.md).

## Modules

### Modules: Maps

Maps are stateless domain projections translating Asset State, Equipment, and Relations into target domains consumed by Mechanics. Each Map owns a disjoint codomain.

#### Map: Animation

AnimationMaps enforce State-dependent logical constraints on a Sprite's Animation Space. [TransitionMechanics](#intentional-mechanic-transitionmechanics) and [PlayerMechanics](#intentional-mechanic-playermechanics) utilize AnimationMaps to resolve whether an intended Action is possible. 

An AnimationMap injects constraints into the $\text{Intention} \to \text{Action}$ Sprite State transformation. For example, by passing through an AnimationMap, an `attack` Intention cannot translate into a `thrust` Action unless the Sprite currently possesses the required Weapon in its [Slots](./02-sprites.md#model-slots).

**Interface: Action Mapping**

* `action(state, equipment): returns Action`

$$
--8<-- "static/tex/functions/function-000-action-map.tex"
$$

**Interface: Direction Mapping**

* `direction(position, goal): returns Direction`

$$
--8<-- "static/tex/functions/function-001-direction-map.tex"
$$

#### Map: Combat

CombatMaps map an attacking Sprite's current State and resolve either active melee Attackboxes or ranged Projectile parameters.

**Behavior: Charging**

The `attack` Intention may be "*pressed and held*". This factor contributes to the resultant speed of attack according to the formula,

$$
--8<-- "static/tex/formulae/formula-002-attack-charge.tex"
$$

**Interface: Attack Hitbox Mapping**

* `attackboxes(state, equipment, elevation): returns List[Hitbox]`: Queries the slotted weapon's Hitbox component at the Asset's active `<action>-<direction>-<frame>` key and elevation plane.

$$
--8<-- "static/tex/functions/function-003-attackbox-map.tex"
$$

**Interface: Projectile Asset Mapping**

* `projectile(state, equipment): returns id`: Evaluates whether the slotted Weapon configures a `projectile` ID and `release` Frame matching the Sprite's current Animation Frame. When triggered on the entry tick of the `release` Frame, calculates the initial Projectiles speed $s(S, n)$ from the attacker's strength $S$, held charge duration $n$, and the weapon's draw window $N_{\max} = \max(1, \text{release} \cdot \text{delay})$.

$$
--8<-- "static/tex/functions/function-002-projectile-map.tex"
$$

**Interface: Projectile Release Frame Mapping**

* `release(state, equipment, elevatiob): returns (Position, Frame Index)`:  Evaluates the Weapon's Hitbox on the first tick of its release Frame to determine Projectile spawn Position and Direction.

$$
--8<-- "static/tex/functions/function-004-release-map.tex"
$$

**Interface: Projectile Speed Mapping**

* `speed(state, equipment): returns int`: Maps attacker strength $S$ and held draw duration $n$ to Projectile speed $s(S, n)$.

$$
--8<-- "static/tex/functions/function-005-speed-map.tex"
$$