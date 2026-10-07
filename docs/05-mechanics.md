# Ontology: Mechanics

!!! note
    Mechanics are listed below using `key: class`, where `key` is the unique string identifier for the associated Mechanic implementation class. This `key` is used in the [Mechanics Configuration](#configuration) to specify the order of execution.

A Mechanic is an implementation of an abstract interface the engine calls during the game loop; All Mechanics must implement an `update(board: Board, delta: float, bus: collections.deque, payload: DevicePayload)` method. The arguments of this interface are the [Board](./00-overview.md#board), a game loop time delta, an [Event Bus](./06-widgets.md#events) for storing Menu Events and the current [Device](./02-sprites.md#devices) Payload. These arguments are injected from above by the [Engine](./00-overview.md#engine)

## Overview

Mechanics, [Intentions and Goals](./04-intentions.md) are the "foundation" of the gameplay. Their interplay and dynamic generates all of the complexity within the game engine. Mechanics are the "*laws of nature*" and Intentions & Goals are the "*states of mind*"

1. Navigational Intentions (`find`, `follow`, `hunt`, `escape`, `wander`, `return`)
    - Handled by: CognitionMechanics, MotionMechanics
    - Logic: Cognition moves the Goal Position coordinate. Motion accelerates the velocity vector toward it.
2. Spatial/Interactive Intentions (`attack`, `mine`, `build`, `interaction`)
    - Handled by: CombatMechanics, InteractionMechanics
    - Logic: These Mechanics iterate only over Sprites in their respective Intention "statelessly". For example, CombatMechanics does not care how a Sprite got into the `attack` intention; it only applies logic once the Sprite is in `attack`.
3. Communicative Intentions (`speak`, `threaten`, `barter`)
    - Handled by: SocialMechanics
    - Logic: Iterates over Sprites in communicative Intentions, checking if they are within conversational radius of their target to swap prices or rumors.

**Sprite AI**

As should already be obvious, much of the logic in Mechanics is in support of Sprite AI, via the management of [Goals & Intentions](./04-intentions.md). NPC behavior is distributed across four sequential Mechanics in the `world` pipeline:

- **CognitionMechanics ("The Brain")**: Manages high-level strategic `Goal` models (target entity tracking, cross-layer door subsumption, autonomous wander sampling).
- **TransitionMechanics ("The Instinct")**: Evaluates the [ISL Transition Matrix](./04-intentions.md#transition-matrix) to transition `Intention` states and map animation actions.
- **NavigationMechanics ("The Navigator")**: Manages tactical spatial steering. Validates line-of-sight, extracts obstacle hitboxes, executes RRT avoidance paths, and populates `sprite.state.trajectory`.
- **MotionMechanics ("The Muscle")**: Steers velocity vectors toward `sprite.state.trajectory.target` and integrates physics.

To visualize how this all ties together for a [Sprite](./02-sprites.md) in a single frame,

```mermaid
--8<-- "static/mmd/mechanics-sprite-flow.mmd"
```

### Core

These Mechanics handle the core engine logic.

- `animation AnimationMechanics`: Translates current states into FrameKeys for the renderer.
- `remove: RemoveMechanics`: General garbage collection for Assets whose lifespan has expired.
- `motion: MotionMechanics`: Applies acceleration and velocity integrations to Assets to arrive at their next position.
- `menu: MenuMechanics`: Handles Menu and Widget interactions.

### MotionMechanics

#### Dynamics

Assets with Mass are divided into Kinematic, Motive, Inert, and Frictive Assets.

* **Kinematic Assets (Players)**: Polls input devices. In dry environments, input clamps velocity vectors to `character.speed` and nullifies orthogonal components. When intersecting an active Fluid stream or pool, kinematic snapping is disabled: voluntary input velocity is added vectorally to the underlying fluid current:
  $$\vec{v}_{\text{final}} = \vec{v}_{\text{input}} + \vec{v}_{\text{current}}$$
* **Motive Assets (Sprites)**: Guided by `NavigationMechanics`. Evaluates avoidance and waypoint steering vectors. In fluid corridors, the environmental current vector is added to the steering vector.
* **Frictive Assets (Crates)**: Passively receive momentum from physical collisions, decaying via tile friction. Floating dynamic bodies in fluids drift along the stream vector.
* **Rafts**: Specialized dynamic objects that do not obstruct fluid propagation. Rafts passively drift at the fluid current velocity $\vec{v}_{\text{current}}$. Passengers aboard a Raft adopt the Raft's velocity as their baseline reference frame, suppressing the submerged state.
* **Inert Assets (Projectiles)**: Translate along ballistic linear trajectories until lifetime expiration or boundary collision triggers garbage collection.

The mathematical bounds for Friction are $[0, \infty)$.

* **Lower Bound ($0$):** A value of exactly $0$ yields $\Delta v = 0$, meaning the asset will glide indefinitely without losing momentum until it strikes a static body. 
* **Upper Bound ($\infty$):** There is no programmatic upper bound. Any value satisfying the condition $\text{friction} \cdot \Delta t \ge \vert v \vert$ will eventually halt the asset.

The `friction` property defines the rate of linear velocity decay, measured in pixels per second squared ($px/s^2$).

**Updates**

The engine updates the velocity magnitude $v$ via Symplectic Euler Integration:

$$v_{n+1} = \max(0, v_n - \text{friction} \cdot \Delta t)$$

#### Fields

##### Fluids

Dynamic bodies ($m > 0$) interacting with active Fluid streams and pools evaluate hydrodynamic buoyancy via `properties.buoyant`:

**Buoyant Dynamic Bodies (`buoyant: True`)**

$$
\vec{v}_{\text{body}} = \vec{v}_{\text{current}}
$$

* Enter the submerged state (`mutators.triggers.submerged = True`).
* Tile friction decay is suspended in `frictive.py`, allowing continuous drift along the hydrological network.

**Non-Buoyant Dynamic Bodies (`buoyant: False`)**

* Sink to the substrate. Fluid current velocity is not imparted ($\vec{v}_{\text{drift}} = \vec{0}$).
* Enter the submerged state (`mutators.triggers.submerged = True`).
* Tile friction remains active, causing unpushed non-buoyant objects to settle and resist water flow.

**Motive and Kinematic Characters (Sheets)**

* Voluntary locomotion is preserved and vectorally superimposed with current velocity:

$$
\vec{v}_{\text{final}} = \vec{v}_{\text{locomotion}} + \vec{v}_{\text{current}}
$$

### MenuMechanics

!!! note
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

### Spatial

These Mechanics handle spatial interactions and collisions between Assets.

- `switch: SwitchMechanics`: (Cython) Binds the Gate and Plate states together based on their `switch`.
- `projectile: ProjectileMechanics`: (Cython) Increment projectile positions, checks intersections and resolves impacts.
- `collision: CollisioMechanics`: Resolves collisions.
- `combat: CombatMechanics`: (Cython) Resolves attack hitbox overlaps, decrements health, etc.
- `interaction: InteractionMechanics`: (Cython) Resolves Asset interactions.
- `social: SpeechMechanics`: Handle `speak` Intentions and [Plot calculations](./08-plots.md).

#### InteractionMechanics

!!! note
    `|` is used as a quantifier in the following.

- Source: `source = sprite | sprite.state.intention = 'interact'`
- Target: `target = asset | intersects(sprite, asset)`
- Logic:
    - `if source.instance == 'sprites'`:
        - `if target.instance == 'chests': TODO`
        - `if target.instance == 'doors': source.state.layer = door.state.outlayer` 
    - `if source.instance == 'players':`
        - `if target.instance == 'chests': bus.append(MenuEvent('inventory', { 'context': player.state})` 
        - `if target.instance == 'doors': source.state.layer = door.state.outlayer` 
        - `if target.instance == 'signs': bus.append(MenuEvent('dialogue', { 'object': sign.state, 'plot': plot.state}))`

#### CollisionMechanics

When Assets collide, overlap resolution uses inverse mass ratios to correct spatial positioning, ensuring immutable Assets with no Mass (`m = 0`) remain completely immobile while dynamic Assets with Mass (`m > 0`) absorb 100% of the displacement shift. Post-separation, Velocities are updated via elastic collision formulas, conserving momentum across all participating masses,

$$
v_{1f} = \frac{v_1(m_1 - m_2) + 2m_2v_2}{m_1 + m_2}
$$

The [Player](./02-sprites.md#player) does not observe momentum transfers. Instead, the Player follows the procedures outlined below,

* **Property Level:** The Player retains a normal, dynamic mass (e.g., $m = 10$).
* **Phase 1 - Spatial Resolution:**
    * **Player vs. Wall ($m=0$):** `inv_total` is $> 0$. The Wall absorbs 0% of the overlap shift, and the Player absorbs 100%. The Player halts at the wall boundary.
    * **Player vs. Crate ($m=5$):** Both absorb the spatial shift proportional to their inverse mass. The Player pushes the Crate out of the way.
* **Phase 2 - Momentum Transfer:** Bypass the 1D elastic collision calculation *only* for the Player.

#### CombatMechanics

```mermaid
--8<-- "static/mmd/mechanics-combat.mmd"
```

In CombatMechanics, entities do not query spatial reach using their default body hitboxes (`asset.hitboxes`). Because CollisionMechanics prevents overlapping physical boundaries, character torsos will rarely intersect target bodies during weapon strikes. Instead, CombatMechanics queries the active weapon attackbox (`CombatMap.attackboxes`) associated with the entity's current `(action, direction, frame)`. Attacker spatial primitives are injected into the broad-phase spatial hash using their active weapon reach, evaluating collisions strictly against the target's physical hitboxes. Attackers with no attackboxes configured on their current animation frame bypass combat collision checks entirely.

### Intentional

These Mechanics handle Sprite intentionality, goal-seeking, and tactical navigation.

- `player: PlayerMechanics`: Resolves Device input into Player (Intention, Goal)-state.
- `cognition: CognitionMechanics`: Manages high-level strategic Goal selection and memory stacks.
- `transition: TransitionMechanics`: Evaluates ISL condition matrices and transitions Intention states.
- `navigation: NavigationMechanics`: Resolves tactical steering, sensory anchors, line-of-sight, and RRT waypoint queues.
- `commerce: CommerceMechanics`: Translates communicative intentions (`barter`, `attract`) into trades and price updates.

!!! important
    CognitionMechanics mutates Goals, TransitionMechanics mutates Intentions, NavigationMechanics populates Trajectories, and MotionMechanics integrates velocities. This separation of concerns **must** be preserved at all times.

#### CognitionMechanics

CognitionMechanics acts as the Sprite's deliberative core. It operates exclusively on high-level **Strategic Goals**. For example, for Sprite in the given Intention states, CognitionMechanics generates and manages the following Goals:

- `wander`: Samples a random coordinate within the vision radius bounded by layer dimensions and commits a `Goal(name="wander", category=POSITION)`.
- `find / follow / hunt`: Queries the Board for the target entity. If visible, updates `goal.position` to match the target's physical coordinates. If the target leaves the vision radius, coordinates freeze at the last known position.
- `escape`: Extrapolates a spatial coordinate in the vector direction opposite to the threat.
- **Cross-Layer Subsumption**: When a goal's layer mismatches the sprite's layer, Cognition pushes the goal to `memory.goals` and substitutes a prerequisite `OBJECT` goal for the nearest transition door.

This is by no means an exhaustive list of CognitionMechanics' responsibility, but instead an example of its domain operation, e.g. Sprites and their Goals. CognitionMechanics is completely decoupled from geometric obstacles, intermediate waypoints, and line-of-sight raycasts. Intermediate path planning is offloaded entirely to `NavigationMechanics`.

Since CognitionMechanics is intrinsically tied to Sprite Intentions and Goals, the cognition workflow is covered in more detail in the [Intentions amd Goals documentation](./04-intentions.md#cognition).

#### NavigationMechanics

NavigationMechanics acts as the Sprite's tactical navigator, bridging strategic intent with physical locomotion:

1. **Goal Verification**: Verifies `sprite.state.goal` exists and `sprite.state.intention` belongs to NavigationIntentions. Clears `trajectory` and yields if false.
2. **Anchor Resolution**: Computes sensory footprints using `anchor(sprite)` and target footprint offsets, preventing top-left origin hitbox drift.
3. **Line-of-Sight Check**: Raycasts using Cython `geometry.los()` against active layer weights (`board.weights`) and boundary perimeters (`board.perimeters`).
4. **Path Maintenance**:
    - **Clear LOS**: Clears `trajectory.vertices` and sets `trajectory.target = sprite.state.goal.position`.
    - **Occluded LOS**: If `trajectory.vertices` is empty, extracts obstacle hitboxes, executes `Planner.plan()`, converts waypoints to canvas coordinates by subtracting anchor displacement, and populates `trajectory.vertices`. Sets `trajectory.target = trajectory.vertices[0]`.
    - **Dynamic Invalidation**: If active intermediate waypoints lose LOS due to a moving dynamic body (e.g., pushed crate), invalidates the queue and replans immediately.
5. **Waypoint Arrival**: When the entity arrives within `action_radius` of `trajectory.target`, pops the completed waypoint from `trajectory.vertices` and sets `target` to the next vertex (or strategic goal when vertices are exhausted).
6. **Stall & Cooldown Handling**: When RRT cannot resolve a collision-free path, sets `trajectory.stalled = True` and starts a `cooldown` timer (`settings.PATH_RETRY_INTERVAL`) to prevent per-frame re-planning thrash.

### World

These Mechanics handle ambient world state, high-level game calculations and other abstract accounting.

- `plot: PlotMechanics`: Evaluates the [Plot Transition matrix](./08-plots.md) to transition the [Board's](./00-overview.md#board) plot state.
- `fluid: FluidMechanics`: Resolves directional fluid propagation, obstacle impact truncation, and radial pool perimeter calculation.

#### FluidMechanics

```mermaid
--8<-- "static/mmd/mechanics-fluid.mmd"
```

FluidMechanics governs fluid emission, recursive bifurcation, and procedural shoreline margins across active layers. It executes after physical momentum updates (`MotionMechanics` and `CollisionMechanics`) and uses a 3-tier reactive dirty-checking architecture:

1. **Spatial Corridor Filtering**: Inspects switch-linked gates (`AssetInstances.GATES`). A mutating gate only flags the layer's fluids as `dirty` if the gate's AABB intersects active fluid compound hitboxes or falls within downstream emission corridors.
2. **Debounce Accumulator**: Consecutive gate oscillations are coalesced using `settings.FLUID_INVALIDATION_DEBOUNCE_TICKS` before triggering propagation.
3. **Pass 1 (Fluid Propagation & Bifurcation)**: For invalidated layers, `Actuator.propagate()` updates stream lengths, expands annular pools around static obstacles (\(m = 0\)), derives secondary branch corridors, and updates `board.update_fluid_cache(layer)`. Cache slots (`fluid.state._keys`) are cleared.
4. **Pass 2 (Geometric Shift Detection & Shoreline Synthesis)**: Compares the pre- and post-propagation geometric signature (`_fluid_signature`: stream lengths, pool bounds, branch positions). If water geometry is invariant, shoreline regeneration is bypassed. If geometry shifted (or during hydration), `Cartographer.purge()` and `Cartographer.generate()` synthesize updated boundary contours.

#### SeasonMechanics

`SeasonMechanics` executes within the `world` mechanics pipeline, driving global time, soil hydrology, and biological resource lifecycles:

1. **Temporal Integration**: Accumulates frame $\Delta t$ into `board.calendar.elapsed`. When elapsed time reaches `settings.PERIOD_DURATION_SECONDS` (400.0s), the mechanic advances `period` (0..2), `cycle` (`onset`, `peak`, `decline`), `season` (`spring`, `summer`, `autumn`, `winter`), and `year`, appending a `SeasonEvent` to the engine bus.
2. **Hydrological Diffusion**: Iterates over `board.categories(AssetCategories.RESOURCES.value)`. Probes cardinal offsets against `board.fluid()` spatial buckets:
   * **Moist Substrate**: Accumulates moisture via $\text{retention} \mathrel{+}= \kappa_{\text{diffusion}} \cdot \Delta t$.
   * **Dry Substrate**: Evaporates moisture via $\text{retention} \mathrel{-}= \kappa_{\text{evap}} \cdot \mu_{\text{season}} \cdot \Delta t$.
3. **Declarative Stage Transitions**: Queries the appropriate lifespan executor (`self.executors.get(resource.properties.lifespan).evaluate(resource.state.stage, locals)`) against compiled stage rules.
## Configuration

* Location: `/src/data/config/mechanics/main.yaml`

Mechanics Configuration defines what Mechanic classes are instantiated by the game engine and what dependencies to inject into them. The order in which they are specified in the schema becomes the order of execution in the game engine.

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

Mechanics are divided into `world` Mechanics and `core` Mechanics. `core` Mechanics execute every single game loop, regardless of whether or not the [Board](./00-overview.md#board) is paused; These include AnimationMechanics and MenuMechanics. `world` Mechanics only execute when the Board is unpaused.

### Executors

Mechanics Executors are services made available to the request Mechanics. Available Executors are enumerated below.

- `plot`: Executor for evaluating the conditions for [Plot Transitions](./08-plots.md).
- `intention`: Executor for evaluating the conditions for [Intention Transitions](./04-intentions.md)
- `actuator`: Executor for generating [Fluid](./01-assets.md#fluids) and [Shoreline](./01-assets.md#shorelines) Assets.
- `annual`: ISL executor evaluating stage transitions for annual vegetation (crops).
- `perennial`: ISL executor evaluating stage transitions for perennial flora (trees).
- `centennial`: ISL executor evaluating geological progression (ores).


### Relations

Relations are static mappings configured at runtime. Available relations are enumerated below.

- `shorelines`: A map of [Shoreline Geography Asset IDs](./01-assets.md#shorelines) to a compound index of [Tile Asset IDs](./01-assets.md#tiles) and [Fluid Asset ID](./01-assets.md#fluids). This relation maps Fluid Shorelines to the Tiles in which they are embedded, e.g. `grassy-shore` Shorelines are mapped to `grass` Tiles and `water` Fluids. 