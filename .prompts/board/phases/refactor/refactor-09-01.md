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

Option B delivers identical visual fidelity with zero registry key bloat and no impact on the core animation system.

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

##### User Review

1. Rafts and Relative Velocity (Response to Goals: *Environment Current Vector Field* and *Raft Object Entity & Galvanic Reference Frames*)

I am wondering if disabling snapping is the correct approach, or if there should be a "field processing step" in MotionMechanics, which applies after the kinematic and motive physics steps, that mutates the velocity vectors based on the field (e.g. fluid (and perhaps future fields, like magnetism)) in which the Sprite (or Object) is immersed. 

I also wonder if it's even necessary to "inherit" the Raft velocity. If both the Raft and Sprite are in the field and acquire the same velocities, won't relativity just naturally fall out of it? It seems like all that needs to occur in that case is the Raft has to intercept the `submerged` attribute and block it from it getting set to `true`, no?

2. Animation Logic Ambiguity (Response to Goal: *Submersion State & Splash Particular Spawning*)

I realize drawing a transculent frame onto a Sprite is a hyperspecific operation that can't possibly be encapsulated into the existing Frame interface. However, introducing this level of object awareness into the Screen does not seem like a good plan, i.e. querying state attributes to determine how they should be rendered (duck-typing). It requires the Screen to be aware of what it is drawing. It also requires the Board be injected into the `draw()` method.

Rather than putting the logic into Screen, I believe the correct approach is to add an interface to Frame for `channels(state: AssetState)`. All existing Frame implementations can pass on its implementation, and the SpriteFrame can implement `channels(state: SpriteState)` and apply Sprite specific logic (e.g., `sprite.state.mutators.triggers.submerged`) to calculate the rendering information. Screen can call the interface and if it returns not None, render it.

Evaluate the feasibility of this approach. If feasible, define the interface that would be necessary. `channels()` should probably return some sort of primitive data that can be passed down into Cython through the Screen. It may, in addition, require an interface in `libs.graphics.render` that Screen can call.

##### Architectural Analysis

**1. Environmental Fields & Galilean Relativity**

*The Post-Locomotive Field Processing Step*

Moving fluid acceleration out of `kinematic.py` and `motive.py` into a dedicated **Field Processing Step** is architecturally superior.

Currently, `MotionMechanics.update()` executes:

```python
kinematic.update(players, payload, delta)
motive.update(sprites, board, delta)
frictive.update(crates, board, delta)

all_mutable = players + sprites + crates + projectiles
physics.integrate(all_mutable, delta)
```

If environmental currents are injected directly into `kinematic.py` or `motive.py`, those modules lose cohesion by coupling voluntary volition (input polling and RVO steering) with ambient environmental forces. Furthermore, adding future fields (conveyor belts, wind zones, magnetic pulls) would require modifying every locomotion module.

By placing a field evaluation step immediately before integration:

```python
kinematic.update(players, payload, delta)   # Resolves voluntary v_locomotion
motive.update(sprites, board, delta)       # Resolves autonomous v_locomotion
frictive.update(crates, board, delta)      # Resolves passive decay

fields.update(all_mutable, board, delta)   # Superposition: v_net = v_locomotion + v_field

physics.integrate(all_mutable, delta)      # Symplectic Euler integration
```

* **Kinematic snapping is preserved:** The player's device input still snaps cleanly to cardinal and diagonal vectors ($\vec{v}_{\text{locomotion}}$).
* **Superposition governs immersion:** If an entity is immersed in a field, $\vec{v}_{\text{field}}$ is added vectorally:

$$
\vec{v}_{\text{net}} = \vec{v}_{\text{locomotion}} + \vec{v}_{\text{field}}
$$

When the player lets go of the joystick ($\vec{v}_{\text{locomotion}} = \vec{0}$), they drift downstream at $\vec{v}_{\text{field}}$. When swimming across or against the current, the velocities combine naturally.

*Relativity and the Raft: The Grounding Boundary Condition*

In open, unconstrained laminar flow, treating the Raft as merely a hitbox that blocks `submerged = True` while both Raft and passenger independently sample $\vec{v}_{\text{field}}$ is mathematically clean:

$$
\vec{v}_{\text{rel}} = \vec{v}_{\text{passenger}} - \vec{v}_{\text{raft}} = (\vec{v}_{\text{walk}} + \vec{v}_{\text{field}}) - \vec{v}_{\text{field}} = \vec{v}_{\text{walk}}
$$

Relativity falls out for free—**until the Raft strikes an obstacle or docks at a shoreline.**

Consider the boundary conditions when a Raft hits an occluding barrier ($m = 0$ map perimeter, a closed gate, or a sandbar):

1. **The Independent Field Model (Passenger samples water directly):**
    * The Raft hits the shore; `CollisionMechanics` sets $\vec{v}_{\text{raft}} = \vec{0}$.
    * The water continues to flow around the barrier.
    * Because the passenger is still sampling the underlying water field, $\vec{v}_{\text{passenger}}$ remains $\vec{v}_{\text{field}}$.
    * **Failure mode:** The passenger is violently swept off the deck of the stationary, docked raft into the obstacle.
2. **The Surface Interception Model (Medium hierarchy):**
    * The Raft intercepts the fluid medium. The water exerts force on the Raft, not the passenger.
    * The passenger is immersed in the **Raft Deck**, not the water.
    * If the Raft drifts freely: $\vec{v}_{\text{raft}} = \vec{v}_{\text{field}} \implies \vec{v}_{\text{passenger}} = \vec{v}_{\text{walk}} + \vec{v}_{\text{raft}} = \vec{v}_{\text{walk}} + \vec{v}_{\text{field}}$.
    * If the Raft is halted against a shore: $\vec{v}_{\text{raft}} = \vec{0} \implies \vec{v}_{\text{passenger}} = \vec{v}_{\text{walk}} + \vec{0} = \vec{v}_{\text{walk}}$.

To make relativity work both while drifting *and* while grounded, the rule is: **Surface Hierarchy Interception**.

In the field resolution pass, entities query what they are standing on. An active Raft hitbox masks the underlying Fluid sensor, intercepting the water's force and suppressing `submerged = True`. The Raft drifts at $\vec{v}_{\text{field}}$, and any passenger aboard inherits the Raft's current velocity ($\vec{v}_{\text{deck}} = \vec{v}_{\text{raft}}$) as their baseline reference frame.

**2. Render Channels Architecture (`Frame.channels`)**

*Feasibility & Architectural Evaluation*

Injecting `Board` into `Screen.draw()` or inspecting domain state attributes (`state.mutators.triggers.submerged`) directly inside the rendering loop breaks the separation of concerns. `Screen.draw()` should remain an asset-agnostic pipeline that translates high-level draw manifests into primitive C-stack tuples for SDL.

Adding a secondary `channels()` interface to `Frame` is an optimal pattern:

* `Frame.keys()` governs **Primary Texture Blitting** (diffuse sprite passes, equipment overlays).
* `Frame.channels()` governs **Auxiliary Graphics Passes** (surface tints, masks, weather washes, status-effect flashes).

By delegating channel generation to `Frame`, the `Frame` component inspects the specific `AssetState` subclass it was designed for, calculates pixel-space bounds relative to the asset origin, and emits primitive draw directives. `Screen.draw()` remains completely unaware of what "water" or "submersion" means.

*Interface Specification: `Frame.channels`*

Add the channel interface to `src/app/assets/base.py`:

```python
class Frame(ABC):
    @abstractmethod
    def keys(self, id: str, state: AssetState) -> List[Tuple[str, int, int]]:
        pass

    def channels(self, id: str, state: AssetState) -> List[Tuple]:
        """
        Emits auxiliary rendering directives (tints, masks, overlays)
        evaluated against dynamic asset state.
        
        Default returns an empty list (no secondary channel passes).
        """
        return []

```

*Channel Primitive Schema*

To cross the Python-to-Cython boundary without heap allocations, `channels()` emits uniform primitive tuples:

$$
\text{Channel Tuple} = (\text{channel\_type: int},\, \text{ox: int},\, \text{oy: int},\, \text{ow: int},\, \text{ol: int},\, \text{r: int},\, \text{g: int},\, \text{b: int},\, \text{a: int})
$$

Where `channel_type` maps to an engine enum:

* `ChannelTypes.TINT = 0`: Solid alpha-blended color fill rect.
* `ChannelTypes.MODULATE = 1`: Multiplicative color filter over existing texture pixels.

*Concrete Implementation: `SpriteFrame.channels`*

In `src/app/assets/frames/core.py`:

```python
class SpriteFrame(StateFrame):
    def channels(self, id: str, state: SpriteState) -> List[Tuple[int, int, int, int, int, int, int, int, int]]:
        channel_directives = []
        
        # Waistline Submersion Tint
        if getattr(state.mutators.triggers, "submerged", False):
            # Target lower 50% of the sprite's length
            w = self.tile_w
            l = self.tile_l
            half_l = l // 2
            
            # (CHANNEL_TINT, ox, oy, ow, ol, r, g, b, a)
            # e.g., deep translucent aquatic tint: RGBA(28, 84, 142, 140)
            channel_directives.append((
                0,        # ChannelTypes.TINT
                0,        # ox
                half_l,   # oy (starts halfway down the body)
                w,        # ow
                half_l,   # ol (covers waist to feet)
                28, 84, 142, 140
            ))
            
        return channel_directives
```

**3. Cython Renderer Interface (`libs/graphics/render.pyx`)**

Add a zero-allocation primitive batch drawer for channel overlays:

```cython
def channel(list channel_ops, int cam_x, int cam_y):
    """
    Renders auxiliary channel passes (tints, highlights) directly over the backbuffer.
    channel_ops format: (c_type, dx, dy, dw, dl, r, g, b, a)
    """
    cdef SDL_Rect rect
    cdef int c_type, dx, dy, dw, dl, r, g, b, a

    SDL_SetRenderDrawBlendMode(_renderer, SDL_BLENDMODE_BLEND)

    for op in channel_ops:
        c_type, dx, dy, dw, dl, r, g, b, a = op
        rect.x = dx - cam_x
        rect.y = dy - cam_y
        rect.w = dw
        rect.h = dl

        if c_type == 0:  # TINT / Fill Rect
            SDL_SetRenderDrawColor(_renderer, r, g, b, a)
            SDL_RenderFillRect(_renderer, &rect)

```

**4. High-Level Dispatch in `Screen.draw()` (`src/app/game/screen.py`)**

In `Screen.draw()`, query both `keys()` and `channels()` in the draw loop:

```python
active_primitives = []
channel_primitives = []

for asset in active_assets:
    # 1. Primary Texture Tuples
    for frame_key, ox, oy in asset.frame.keys(asset.id, asset.state):
        tex_data = self.registry.image(frame_key)
        if tex_data:
            tex, sx, sy, sw, sl = tex_data
            active_primitives.append((
                tex, sx, sy, sw, sl,
                asset.state.position.x + ox,
                asset.state.position.y + oy,
                sw, sl
            ))

    # 2. Auxiliary Channel Tuples
    ch_ops = asset.frame.channels(asset.id, asset.state)
    if ch_ops:
        for c_type, ox, oy, ow, ol, r, g, b, a in ch_ops:
            channel_primitives.append((
                c_type,
                asset.state.position.x + ox,
                asset.state.position.y + oy,
                ow, ol,
                r, g, b, a
            ))

# Render world texture layer
render.render(self.bg_canvas, self.fg_canvas, active_primitives, cam_x, cam_y, screen_w, screen_l)

# Render auxiliary channel layer directly over matching world coordinates
if channel_primitives:
    render.channel(channel_primitives, cam_x, cam_y)

```

##### Tasks

**1. Task: Schemas, Taxonomy & Raft Registration**

*Objective*: Register `rafts` under `AssetCategories.OBJECTS` and configure `submerged` mutator.

* [x] Subtask: Add `RAFTS` to `AssetInstances` enum and `ObjectPropertyInstances` schema in `models/properties.py`.
* [x] Subtask: Add `submerged: bool = False` to `MutatorTriggers` in `models/state/sheets.py`.
* [x] Subtask: Add recipe for `rafts` (`SingleFrame`, `NoAnimation`, `PositionalState`) in `recipes/main.yaml`.
* [x] Subtask: Ensure `Actuator._collect_obstacles` bypasses `AssetInstances.RAFTS.value`.

**2. Task: Environmental Field Step & Surface Interception**

*Objective*: Decouple ambient fluid force resolution from voluntary locomotion in `MotionMechanics`.

* [x] Subtask: Create `app/game/logic/modules/motion/fields.py` to evaluate active fluid streams and calculate $\vec{v}_{\text{field}}$.
* [x] Subtask: Implement Surface Interception: if an entity intersects an active Raft hitbox, set `mutators.triggers.submerged = False` and assign $\vec{v}_{\text{field}} = \vec{v}_{\text{raft}}$.
* [x] Subtask: If an entity directly touches fluid without a Raft, set `mutators.triggers.submerged = True` and apply $\vec{v}_{\text{net}} = \vec{v}_{\text{locomotion}} + \vec{v}_{\text{field}}$.
* [x] Subtask: Wire `fields.update()` into `MotionMechanics.update()` directly preceding `physics.integrate()`.

**3. Task: Frame Channels Architecture & Submersion Rendering**

*Objective*: Implement `Frame.channels()` to render the waistline submersion tint without polluting `Screen`.

* [x] Subtask: Add `channels(id, state)` default method to `Frame` in `app/assets/base.py`.
* [x] Subtask: Implement `SpriteFrame.channels()` to emit `(CHANNEL_TINT, 0, l//2, w, l//2, r, g, b, a)` when `submerged == True`.
* [x] Subtask: Implement `render.channel()` C-routine in `libs/graphics/render.pyx` using `SDL_RenderFillRect` with `SDL_BLENDMODE_BLEND`.
* [x] Subtask: Connect `channel_primitives` collection and dispatch inside `Screen.draw()`.

**4. Task: Solid Annular Pool Partitioning & Splash Generation**

*Objective*: Resolve transparent pixel bleeding around obstacles and spawn waterline particles.

* [x] Subtask: Refactor `Actuator._partition_pool` to flood the complete obstacle bounding box, relying on `height: 0, depth: -1` to sort beneath obstacle graphics.
* [x] Subtask: Add `spawn_passive()` factory method to `Cradle` in `app/services/generators/game/cradle.py`.
* [x] Subtask: Dispatch `cradle.spawn_passive("splash", layer, pos)` in `fields.py` when an entity transitions from dry land to `submerged == True`.


**5. Task: Two-Tier Navigation Planning**

*Objective*: Integrate fluid avoidance and aquatic pathfinding into `NavigationMechanics`.

* [!: Moved to Another Phase] Subtask: Update `NavigationMechanics.obstacles()` to optionally include fluid hitboxes during standard path planning.
* [!: Moved to Another Phase] Subtask: Implement two-tier fallback in `NavigationMechanics._navigate()`: attempt dry path; if stalled, retry without fluid barriers.
* [!: Moved to Another Phase] Subtask: Adjust arrival tolerance for waypoints located in active fluid currents to prevent waypoint overshoot.

##### User Review

**Updates**

Updated Frame channels interface to include properties and updated the channel calculations for submersions (`tile_w` and `tile_l` do not exist):

```python
# src/app/assets/base.py
class Frame(ABC):
    @abstractmethod
    def channels(self, 
        id: str, 
        state: AssetState,
        properties: AssetProperties
    ) -> List[Tuple]:
        """
        Emits auxiliary rendering directives (tints, masks, overlays) evaluated against dynamic asset state.
        """
        pass

# src/app/assets/frames/core.py
class SpriteFrame(StateFrame):
    def channels(self, 
        id: str, 
        state: SpriteState,
        properties: SheetProperties
    ) -> List[Tuple[int, int, int, int, int, int, int, int, int]]:
        channel_directives = []
        
        # Waistline Submersion Tint
        if state.mutators.triggers.submerged:
            # Target lower 50% of the sprite's length
            w = properties.dimensions.w
            l = properties.dimensions.l
            half_l = l // 2
            
            # (CHANNEL_TINT, ox, oy, ow, ol, r, g, b, a)
            # e.g., deep translucent aquatic tint: RGBA(28, 84, 142, 140)
            channel_directives.append((
                0,        # ChannelTypes.TINT
                0,        # ox
                half_l,   # oy (starts halfway down the body)
                w,        # ow
                half_l,   # ol (covers waist to feet)
                28, 84, 142, 140
            ))
            
        return channel_directives
```

**Fluid Properties**

```yaml
effects:
  fluids:
    # -------------------------------------------------------
    waterflow-00:
      dimensions:
        w: 32
        l: 32
      lifecycle: 
        type: continuous
        delay: 60
      count: 3
      hitboxes: null
      mass: 0
    # -------------------------------------------------------
    waterflow-01:
      dimensions:
        w: 32
        l: 96
      lifecycle:
        type: continuous
        delay: 20
      count: 5
      hitboxes: null
      mass: 0
```

**Passive Properties**

```yaml
effects:
    splash: 
      count: 3
      dimensions:
        w: 60
        l: 12
      lifecycle: 
        type: temporary
        delay: 15
      hitboxes: null
      mass: -1
```

**Sprite Propertes**

```yaml
sheets:
  sprites:
    # ------------------------------------------------
    # ------------------------------ PLAYER PROPERTIES
    # ------------------------------------------------
    player:
      mass: 7
      dimensions:
        w: 64
        l: 64
      attackboxes: null
      hitboxes: 
        - position: 
            x: 23
            y: 34
          dimensions:
            w: 18
            l: 15
      stack:
        - human-male-ivory
        - feet-boots-black
        - legs-robe-black
        - torso-shirt-male-black
        - toros-cape-black
        - head-glasses
        - head-beard-white
        - hair-curls-white
        - head-wizard-hat-moon
      actions: lpc-full
```

**Initial Fluid State**

```yaml
effects:
  fluids:
    - id: waterflow-00
      name: jasilynns-tears-00
      layer: '0'
      position:
        x: 70
        y: 0
      flow: 2
      source: down
    - id: waterflow-00
      name: jasilynns-tears-01
      layer: '0'
      position:
        x: 600
        y: 600
      source: left
    - id: waterflow-00
      name: jasilynns-tears-02
      layer: '0'
      flow: 4
      position:
        x: 632
        y: 0
      source: down
```

**Relevant State Dumps**

```markdown

## jasilynns-rock

- **Taxonomy:**
  - Category: `objects`
  - Instance: `obstacles`
  - ID: `gray-rock-00`
  - Name: `jasilynns-rock`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SingleFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 56
    - Length: 56
  - Mass: 0
  - Count: 1
- **State:**
  - Layer: `0`
  - Depth: 0
  - Position: (68, 600)
  - Velocity: (0.0, 0.0)


## jasilynns-other-rock

- **Taxonomy:**
  - Category: `objects`
  - Instance: `obstacles`
  - ID: `gray-rock-00`
  - Name: `jasilynns-other-rock`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.NoAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SingleFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 56
    - Length: 56
  - Mass: 0
  - Count: 1
- **State:**
  - Layer: `0`
  - Depth: 0
  - Position: (632, 600)
  - Velocity: (0.0, 0.0)

## jasilynns-tears-00

- **Taxonomy:**
  - Category: `effects`
  - Instance: `fluids`
  - ID: `waterflow-00`
  - Name: `jasilynns-tears-00`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.LifecycleAnimation'>`
  - Frame: `<class 'app.assets.frames.core.FluidFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: 0
  - Lifecycle: Lifecycle(type=<Lifecycles.CONTINUOUS: 'continuous'>, delay=60, frequency=0, cooldown=60, persist=False)
  - Count: 3
  - Hitboxes:
    - Position: (0, 0) | Dimensions: w: 32, l: 600
    - Position: (-128, 472) | Dimensions: w: 312, l: 312
- **State:**
  - Layer: `0`
  - Depth: -1
  - Height: 0
  - Position: (70, 1)
  - Active: `True`
  - Animation:
    - Action: `walk`
    - Direction: `down`
    - Frame: 2
    - Tick: 39
  - Source: `down`
  - Flow: 2
  - Length: 600
  - Dirty: False
  - Pool:
    - Position: (4, 536)
    - Dimensions: w: 184, l: 184
  - Hitboxes:
    - Position: (0, 0) | Dimensions: w: 32, l: 600
    - Position: (-66, 536) | Dimensions: w: 184, l: 184


## jasilynns-tears-01

- **Taxonomy:**
  - Category: `effects`
  - Instance: `fluids`
  - ID: `waterflow-00`
  - Name: `jasilynns-tears-01`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.LifecycleAnimation'>`
  - Frame: `<class 'app.assets.frames.core.FluidFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: 0
  - Lifecycle: Lifecycle(type=<Lifecycles.CONTINUOUS: 'continuous'>, delay=60, frequency=0, cooldown=60, persist=False)
  - Count: 3
  - Hitboxes:
    - Position: (0, 0) | Dimensions: w: 32, l: 600
    - Position: (-128, 472) | Dimensions: w: 312, l: 312
- **State:**
  - Layer: `0`
  - Depth: -1
  - Height: 0
  - Position: (600, 600)
  - Active: `True`
  - Animation:
    - Action: `walk`
    - Direction: `down`
    - Frame: 2
    - Tick: 39
  - Source: `left`
  - Flow: 1
  - Length: 476
  - Dirty: False
  - Pool:
    - Position: (36, 568)
    - Dimensions: w: 120, l: 120
  - Hitboxes:
    - Position: (-476, 0) | Dimensions: w: 476, l: 32
    - Position: (-564, -32) | Dimensions: w: 120, l: 120


## jasilynns-tears-02

- **Taxonomy:**
  - Category: `effects`
  - Instance: `fluids`
  - ID: `waterflow-00`
  - Name: `jasilynns-tears-02`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.LifecycleAnimation'>`
  - Frame: `<class 'app.assets.frames.core.FluidFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 32
    - Length: 32
  - Mass: 0
  - Lifecycle: Lifecycle(type=<Lifecycles.CONTINUOUS: 'continuous'>, delay=60, frequency=0, cooldown=60, persist=False)
  - Count: 3
  - Hitboxes:
    - Position: (0, 0) | Dimensions: w: 32, l: 600
    - Position: (-128, 472) | Dimensions: w: 312, l: 312
- **State:**
  - Layer: `0`
  - Depth: -1
  - Height: 0
  - Position: (632, 1)
  - Active: `True`
  - Animation:
    - Action: `walk`
    - Direction: `down`
    - Frame: 2
    - Tick: 39
  - Source: `down`
  - Flow: 4
  - Length: 600
  - Dirty: False
  - Pool:
    - Position: (504, 472)
    - Dimensions: w: 312, l: 312
  - Hitboxes:
    - Position: (0, 0) | Dimensions: w: 32, l: 600
    - Position: (-128, 472) | Dimensions: w: 312, l: 312


## player

- **Taxonomy:**
  - Category: `sheets`
  - Instance: `players`
  - ID: `player`
  - Name: `player`
- **Components:**
  - Animation: `<class 'app.assets.animations.core.SpriteAnimation'>`
  - Frame: `<class 'app.assets.frames.core.SpriteFrame'>`
- **Properties:**
  - Dimensions:
    - Width: 64
    - Length: 64
  - Mass: 7
  - Stack:
    - `human-male-ivory`
    - `feet-boots-black`
    - `legs-robe-black`
    - `torso-shirt-male-black`
    - `toros-cape-black`
    - `head-glasses`
    - `head-beard-white`
    - `hair-curls-white`
    - `head-wizard-hat-moon`
  - Hitboxes:
    - Position: (23, 34) | Dimensions: w: 18, l: 15
  - Actions:
    - `cast`:
      - Count: 7
      - Delay: 1
      - Directions:
        - `Directions.UP`: row 0
        - `Directions.LEFT`: row 1
        - `Directions.DOWN`: row 2
        - `Directions.RIGHT`: row 3
    - `thrust`:
      - Count: 8
      - Delay: 1
      - Directions:
        - `Directions.UP`: row 4
        - `Directions.LEFT`: row 5
        - `Directions.DOWN`: row 6
        - `Directions.RIGHT`: row 7
    - `walk`:
      - Count: 9
      - Delay: 3
      - Directions:
        - `Directions.UP`: row 8
        - `Directions.LEFT`: row 9
        - `Directions.DOWN`: row 10
        - `Directions.RIGHT`: row 11
    - `slash`:
      - Count: 6
      - Delay: 5
      - Directions:
        - `Directions.UP`: row 12
        - `Directions.LEFT`: row 13
        - `Directions.DOWN`: row 14
        - `Directions.RIGHT`: row 15
    - `shoot`:
      - Count: 13
      - Delay: 1
      - Directions:
        - `Directions.UP`: row 16
        - `Directions.LEFT`: row 17
        - `Directions.DOWN`: row 18
        - `Directions.RIGHT`: row 19
    - `die`:
      - Count: 6
      - Delay: 1
      - Directions:
        - `Directions.UP`: row 20
- **State:**
  - Layer: `0`
  - Depth: 0
  - Position: (56, 218)
  - Velocity: (0.0, 40.0)
  - Animation:
    - Action: `walk`
    - Direction: `down`
    - Frame: 0
    - Tick: 0
  - Character:
    - Strength: 5
    - Defense: 5
    - Speed: 100
    - Impulse: 25
  - Meters:
    - Health: 50 / 100
    - Magic: 100 / 100
  - Inventory:
    - Wallet: 0
    - Equipment:
      - Weapon: `shortsword`
      - Shield: `buckler`
  - Goal:
    - Position: (56, 218)
  - Mutators:
    - Triggers:
      - Animated: False
      - Frightened: False
      - Dead: False
      - Vision: False
    - Parameters:
      - Fear:
        - Radius: 30
        - Limit: 0.5
        - Enemy: 5
      - Vision:
        - Radius: 30
      - Action:
        - Radius: 30
  - Intention: `idle`
```

!!! note
    New fields not yet part of state dump.

**Notes**

- Splash effect is appended upon entering a Fluid.
- Fluid flow is added to Sprite speed when travelling down.
- **BUG** the `left` source in the state does not produce velocity additions. 
- **BUG** the hitboxes for the fluids appear to be calculated incorrectly?
- Channels are correctly applied, but it is apparent basing the channels on the asset dimensions is not correct. Opacity is apply to the transparent edges around the asset file, so that there is a transculent rectangle appended to the Sprite while submerged. 
    - Query: Is is possible to apply the translucency filter to *only* the non-transparent pixels in the Sprite Frame? Let me rephrase. It's probably possible. Can it be done in a way that is not ugly and verbose, and without breaking the architecture? 
        - Currently, the channels are effectively an entirey different image superimposed on the underlying Sprite frame.
    - Follow up query: If the previous is not possible in a Pythonic way, is it possible to clip the channel to the non-transparent pixels in the Sprite frame?
    - Otherwise, the channel calculations will need to be rethought altogether. It currently looks very strange and unnatural.

##### Root Cause Analysis

The issue traces to a structural conflict between `Asset.hitboxes` and property mutation:

```
+-----------------------------------------------------------------------------+
|                             YAML Asset Index                                |
|  waterflow-00: EffectProperties(hitboxes=None, dimensions=(32, 32))         |
+-----------------------------------------------------------------------------+
                                      │
                   Shared instance reference across entities
                                      │
             ┌────────────────────────┼────────────────────────┐
             ▼                        ▼                        ▼
     jasilynns-tears-00       jasilynns-tears-01       jasilynns-tears-02
       (source: down)           (source: left)           (source: down)
             │                        │                        │
             ▼                        ▼                        ▼
   pump(): state.hitboxes   pump(): state.hitboxes   pump(): state.hitboxes
      (0, 0, 32, 600)         (-476, 0, 476, 32)       (0, 0, 32, 600)
    (-66, 536, 184, 184)     (-564, -32, 120, 120)   (-128, 472, 312, 312)
             │                        │                        │
             └────────────────────────┴────────────────────────┘
                                      │
              fluid.properties.hitboxes = hitboxes (MUTATION)
                                      ▼
             Shared EffectProperties.hitboxes overwritten with
               jasilynns-tears-02 hitboxes on all three fluids!
                                      │
                                      ▼
                      Asset.hitboxes returns properties
            _intersects() tests jasilynns-tears-01 against tears-02!

```

*Shared Property Mutation in `Actuator.pump`*

In `Actuator.pump`, the assignment:

```python
fluid.properties.hitboxes = hitboxes
```

mutates `EffectProperties`, which is a single shared object across every fluid instance referencing `id: waterflow-00`. Because `jasilynns-tears-02` pumped last during world hydration, its hitboxes `[(0, 0, 32, 600), (-128, 472, 312, 312)]` overwrote the hitboxes of `jasilynns-tears-00` and `jasilynns-tears-01`.

*Property Bypass in `Asset.hitboxes`*

In `src/app/assets/base.py`, `Asset.hitboxes` reads only `self.properties.hitboxes`:
```python
@property
def hitboxes(self) -> List[Hitbox]:
    hbs = self.properties.hitboxes
    if not hbs and self.dimensions:
        hbs = [Hitbox(Position(0, 0), self.dimensions)]
    return hbs
```

It completely ignored dynamic `self.state.hitboxes`. When `fields.py` tested `_intersects(player, jasilynns-tears-01)`, `jasilynns-tears-01.hitboxes` resolved to `jasilynns-tears-02`'s vertical hitbox (`x: [600, 632]`, `y: [600, 1200]`). The horizontal corridor (`x: [124, 600]`, `y: [600, 632]`) had no active hitbox, so intersection checks failed and no leftward velocity was imparted.

*Coordinate Offsets*

The negative coordinates on `jasilynns-tears-01.state.hitboxes` (`Position(-476, 0)` and `Position(-564, -32)`) are mathematically valid relative to `Position(600, 600)`:

* Stream corridor: `600 + (-476) = 124` to `124 + 476 = 600` at `y = 600..632`.
* Annular pool: `600 + (-564) = 36` to `36 + 120 = 156` at `y = [568, 688]`.

Once `Asset.hitboxes` reads `self.state.hitboxes` and property mutation is removed, these coordinates align.

**Evaluation of Clipping & Alpha Translucency in SDL2**

*Why the Translucent Box Formed*

`render.channel()` executed:

```cython
SDL_SetRenderDrawColor(_renderer, r, g, b, a)
SDL_RenderFillRect(_renderer, &rect)
```

`SDL_RenderFillRect` rasterizes a solid geometric rectangle over the backbuffer. Because LPC sprites are padded sheets (64×64 pixels) where the character silhouette only occupies roughly 24×32 pixels, the quad fills the transparent padding, producing a translucent rectangle floating over the terrain.

*Can SDL2 Clip to Sprite Alpha?*

* `SDL_RenderSetClipRect` only accepts an axis-aligned bounding box (`SDL_Rect`), not an arbitrary alpha channel mask.
* SDL2's standard rendering pipeline has no stencil buffer support.
* Performing pixel masking via an offscreen scratch texture (`SDL_SetRenderTarget`) per entity per frame forces GPU pipeline flushes and breaks the zero-allocation architecture.

*The Solution: Texture-Modulated Slicing*

SDL2 natively supports texture modulation via:

```c
SDL_SetTextureColorMod(SDL_Texture* texture, Uint8 r, Uint8 g, Uint8 b);
SDL_SetTextureAlphaMod(SDL_Texture* texture, Uint8 alpha);
```

When a texture is rendered with color and alpha modulation, transparent pixels (`alpha == 0`) remain 100% transparent. Only the character's diffuse pixels (boots, robes, legs) receive the aquatic tint and opacity reduction.

Rather than drawing a separate fill quad, `SpriteFrame.channels` emits a `CHANNEL_SUBMERGE` directive:

```python
(ChannelTypes.SUBMERGE, split_y, r, g, b, a)
```

In `Screen.draw()`, any asset with an active `CHANNEL_SUBMERGE` splits its texture passes into:

* **Upper Slice**: `[sy, sy + split_y]` rendered at `dy` (normal color/alpha).
* **Lower Slice**: `[sy + split_y, sy + sl]` rendered at `dy + split_y` with `(r, g, b, a)` texture modulation.

This preserves separation of concerns:

* `SpriteFrame` determines the split boundary and palette.
* `Screen.draw` remains decoupled from domain logic.
* Draw calls remain on the C-stack with zero GPU pipeline stalls.
* Zero transparent bounding-box bleed.

**Code Updates**

1. `src/app/assets/base.py`

Update `Asset.hitboxes` to prefer `self.state.hitboxes` when present:

```python
    @property
    def hitboxes(self) -> List[Hitbox]:
        """
        Unified hitbox retrieval. Prefers dynamic state hitboxes if present,
        falling back to static property definitions.
        """
        state_hbs = getattr(self.state, "hitboxes", None)
        if state_hbs:
            return state_hbs

        hbs = self.properties.hitboxes
        if not hbs and self.dimensions:
            hbs = [Hitbox(Position(0, 0), self.dimensions)]
            
        return hbs
```

2. `src/app/services/generators/game/actuator.py`

Remove property mutation in `Actuator.pump`:

```python
    def pump(self, fluid: Asset, board: Board) -> Tuple[int, Optional[Pool], List[Hitbox]]:
        source_prop = fluid.state.source
        direction = source_prop.value if hasattr(source_prop, "value") else str(source_prop)        
        flow = fluid.state.flow
        fw = fluid.properties.dimensions.w
        fl = fluid.properties.dimensions.l
        fx = fluid.state.position.x
        fy = fluid.state.position.y

        fluid.frame.tile_w = fw
        fluid.frame.tile_l = fl

        obstacle_tuples = self._collect_obstacles(fluid, board, direction)
        max_dist = self._calculate_max_distance(fluid, board, direction)

        stream_length, struck_obstacle = geometry.raycast(
            fx,
            fy,
            fw,
            fl,
            direction,
            obstacle_tuples,
            max_dist
        )

        hitboxes: List[Hitbox] = []
        stream_hb = self._build_stream_hitbox(direction, stream_length, fw, fl)
        if stream_hb:
            hitboxes.append(stream_hb)

        pool_bounds: Optional[Pool] = None
        if isinstance(struck_obstacle, Asset) and flow > 0:
            pool_bounds, pool_hitboxes = self._partition_pool(struck_obstacle, fluid, flow)
            hitboxes.extend(pool_hitboxes)

        fluid.state.length = stream_length
        fluid.state.pool = pool_bounds
        fluid.state.hitboxes = hitboxes
        fluid.state.dirty = False
        # Do not mutate fluid.properties.hitboxes (properties are static/shared across instances)

        logger.info(
            settings.SEPARATOR.join([
                "Telemetry:Fluid",
                fluid.name,
                direction
            ]) + f" | Length: {stream_length}px | Struck: {getattr(struck_obstacle, 'name', 'bounds')} | Pool: {pool_bounds is not None}"
        )

        return stream_length, pool_bounds, hitboxes

```

3. `src/app/assets/frames/core.py`

Define `ChannelTypes.SUBMERGE = 1` and emit the split directive from `SpriteFrame.channels`:

```python
class ChannelTypes:
    TINT = 0
    SUBMERGE = 1


class SpriteFrame(StateFrame):
    """
    Specialized Frame component for Sprites that yields a strict Z-indexed list
    of frame keys based on the Sprite's inventory.
    """

    def channels(self, 
        id: str, 
        state: SpriteState,
        properties: SheetProperties
    ) -> List[Tuple]:
        channel_directives = []
        
        if state.mutators.triggers.submerged:
            l = properties.dimensions.l
            half_l = l // 2
            
            # (CHANNEL_SUBMERGE, split_y, r, g, b, a)
            # e.g., deep aquatic modulation: RGBA(40, 110, 180, 170)
            channel_directives.append((
                ChannelTypes.SUBMERGE,
                half_l,
                40, 110, 180, 170
            ))
            
        return channel_directives

```

4. `src/app/game/screen.py`

Update `Screen.draw()` to split primitives when a `SUBMERGE` channel directive is present:

```python
    def draw(self, 
        assets: List[Asset], 
        focus: Position,
        dim: Dimensions
    ) -> None:
        pov = self.camera(focus, dim)
        active_assets = []

        assets.sort(key=lambda a: (
            a.state.height if a.state.height is not None else (
                (a.state.position.y + (a.dimensions.l if a.dimensions else 0))
            ),
            a.state.depth
        ))

        for asset in assets:
            if asset.category == AssetCategories.TILES: continue

            # Query auxiliary channel directives
            ch_ops = asset.frame.channels(asset.id, asset.state, asset.properties)
            submerge_op = next((op for op in ch_ops if op[0] == 1), None)

            frame_keys = asset.frame.keys(asset.id, asset.state)
            for frame_key, ox, oy in frame_keys:
                tex_data = self.registry.image(frame_key)

                if not tex_data: 
                    if not (
                        isinstance(asset.state, SpriteState) or 
                        isinstance(asset.state, PlayerState)
                    ):
                        logger.warning(f"Registry MISS! Frame key not found: '{frame_key}'")
                    continue 

                tex, sx, sy, sw, sl = tex_data
                dx = asset.state.position.x + ox
                dy = asset.state.position.y + oy
                dw, dl = sw, sl

                if not (dx + dw >= pov.x and dx <= pov.x + self.screensize.w and
                        dy + dl >= pov.y and dy <= pov.y + self.screensize.l):
                    continue

                if submerge_op:
                    _, split_y, r, g, b, a = submerge_op
                    # Upper slice: normal rendering
                    active_assets.append((
                        tex, sx, sy, sw, split_y,
                        dx, dy, dw, split_y,
                        255, 255, 255, 255
                    ))
                    # Lower slice: submerged texture modulation
                    rem_l = sl - split_y
                    active_assets.append((
                        tex, sx, sy + split_y, sw, rem_l,
                        dx, dy + split_y, dw, rem_l,
                        r, g, b, a
                    ))
                else:
                    active_assets.append((
                        tex, sx, sy, sw, sl,
                        dx, dy, dw, dl,
                        255, 255, 255, 255
                    ))

        render.render(
            self.bg_canvas, 
            self.fg_canvas,
            active_assets, 
            pov.x, 
            pov.y, 
            self.screensize.w, 
            self.screensize.l
        )

```

5. `src/libs/graphics/render.pyx`

Expose `SDL_SetTextureColorMod` and `SDL_SetTextureAlphaMod`, and unpack the modulation channels during `render()`:

```cython
cdef extern from "SDL2/SDL.h":
    ...
    int SDL_SetTextureColorMod(
        SDL_Texture* texture, 
        unsigned char r, 
        unsigned char g, 
        unsigned char b
    )
    int SDL_SetTextureAlphaMod(
        SDL_Texture* texture, 
        unsigned char alpha
    )


def render(
    TexturePtr background, 
    TexturePtr foreground, 
    list assets, 
    int cam_x, 
    int cam_y, 
    int screen_w, 
    int screen_l, 
    TexturePtr target=None
):
    """
    Executes the active frame render passing flat coordinates to bypass Python object allocations.
    assets format: (TexturePtr, src_x, src_y, src_w, src_l, dst_x, dst_y, dst_w, dst_l, r, g, b, a)
    """
    if target is not None:
        SDL_SetRenderTarget(_renderer, target.ptr)

    cdef SDL_Rect c_src, c_dst, bg_src, bg_dst
    cdef TexturePtr tex_wrapper
    cdef int sx, sy, sw, sl, dx, dy, dw, dl, r, g, b, a

    if background is not None:
        bg_src.x = cam_x if cam_x >= 0 else 0
        bg_src.y = cam_y if cam_y >= 0 else 0
        bg_dst.x = 0 if cam_x >= 0 else -cam_x
        bg_dst.y = 0 if cam_y >= 0 else -cam_y
        bg_src.w = min(screen_w - bg_dst.x, background.w - bg_src.x)
        bg_src.h = min(screen_l - bg_dst.y, background.l - bg_src.y)
        bg_dst.w = bg_src.w
        bg_dst.h = bg_src.h

        SDL_RenderCopy(_renderer, background.ptr, &bg_src, &bg_dst)

    for asset in assets:
        tex_wrapper, sx, sy, sw, sl, dx, dy, dw, dl, r, g, b, a = asset
        c_src.x, c_src.y, c_src.w, c_src.h = sx, sy, sw, sl
        c_dst.x = dx - cam_x
        c_dst.y = dy - cam_y
        c_dst.w = dw
        c_dst.h = dl

        if r != 255 or g != 255 or b != 255:
            SDL_SetTextureColorMod(tex_wrapper.ptr, r, g, b)
        if a != 255:
            SDL_SetTextureAlphaMod(tex_wrapper.ptr, a)

        SDL_RenderCopy(_renderer, tex_wrapper.ptr, &c_src, &c_dst)

        if r != 255 or g != 255 or b != 255:
            SDL_SetTextureColorMod(tex_wrapper.ptr, 255, 255, 255)
        if a != 255:
            SDL_SetTextureAlphaMod(tex_wrapper.ptr, 255)

    if foreground is not None:
        bg_src.x = cam_x if cam_x >= 0 else 0
        bg_src.y = cam_y if cam_y >= 0 else 0
        bg_dst.x = 0 if cam_x >= 0 else -cam_x
        bg_dst.y = 0 if cam_y >= 0 else -cam_y
        bg_src.w = min(screen_w - bg_dst.x, foreground.w - bg_src.x)
        bg_src.h = min(screen_l - bg_dst.y, foreground.l - bg_src.y)
        bg_dst.w = bg_src.w
        bg_dst.h = bg_src.h

        SDL_RenderCopy(_renderer, foreground.ptr, &bg_src, &bg_dst)

    if target is not None:
        SDL_SetRenderTarget(_renderer, NULL)
```

##### User Review

I like the idea of channels in general, so accepted, but with these revisions:

```python
# src/app/assets/frames/core.py
class SpriteFrame(StateFrame):

    def channels(self, 
        id: str, 
        state: SpriteState,
        properties: SheetProperties
    ) -> List[Tuple]:
        channel_directives = []
        
        if state.mutators.triggers.submerged:
            l = properties.dimensions.l
            half_l = l // 2
            
            # (CHANNEL_SUBMERGE, split_y, r, g, b, a)
            # e.g., deep aquatic modulation: RGBA(40, 110, 180, 170)
            # TODO: this should be codified in a ChannelPayload data structure to pass to the screen. Screen should unpack channel payload into Cython primitives.
            payload = half_l, 40, 110, 180, 170
            channel_directives.append((
                ChannelTypes.SUBMERGE.value,
                payload
            ))
            
        return channel_directives
```

```python
# src/app/game/screen.py:

    def draw(self, 
        assets: List[Asset], 
        focus: Position,
        dim: Dimensions
    ) -> None:
        """
        Calculates viewport positioning, culls non-visible items, and routes data to the renderer.
        """
        pov = self.camera(focus, dim)
        active_assets = []
        active_channels = []

        # Height-sort the assets directly prior to querying asset.frame.keys()
        #   Primary Sort: Explicit Height OR (Y + Length)
        #   Secondary Sort: Depth-index tie-breaker for overlapping entities
        assets.sort(key=lambda a: (
            a.state.height if a.state.height is not None else (
                (a.state.position.y + (a.dimensions.l if a.dimensions else 0))
            ),
            a.state.depth
        ))


        for asset in assets:
            if asset.category == AssetCategories.TILES: continue

            frame_keys = asset.frame.keys(asset.id, asset.state)
            channels = asset.frame.channels(asset.id, asset.state, asset.properties)
            submerge_channel = next((op for op in channels if op[0] == ChannelTypes.SUBMERGE.value), None)

            for frame_key, ox, oy in frame_keys:
                tex_data = self.registry.image(frame_key)

                if not tex_data: 
                    if not (
                        isinstance(asset.state, SpriteState) or 
                        isinstance(asset.state, PlayerState)
                    ):
                        logger.warning(f"Registry MISS! Frame key not found: '{frame_key}'")
                    continue 

                # Flatten mapping to C-level PRIMITIVE INTEGERS for destination logic
                tex, sx, sy, sw, sl = tex_data
                dx, dy = asset.state.position.x + ox, asset.state.position.y + oy
                dw, dl = sw, sl

                # Strict Camera Culling: Only pass geometry if intersecting the camera frame 
                if (dx + dw >= pov.x and dx <= pov.x + self.screensize.w and
                    dy + dl >= pov.y and dy <= pov.y + self.screensize.l):
                    if submerge_channel is None:
                        active_assets.append((
                            tex, sx, sy, sw, sl, 
                            dx, dy, dw, dl,
                            255, 255, 255, 255
                        ))
                    else:
                        split_y, r, g, b, a = submerge_channel[1]
                        # Upper slice: normal rendering
                        active_assets.append((
                            tex, sx, sy, sw, split_y,
                            dx, dy, dw, split_y,
                            255, 255, 255, 255
                        ))
                        # Lower slice: submerged texture modulation
                        rem_l = sl - split_y
                        active_assets.append((
                            tex, sx, sy + split_y, sw, rem_l,
                            dx, dy + split_y, dw, rem_l,
                            r, g, b, a
                        ))

                # 2. Auxiliary Channel Tuples
                for c_type, payload in channels:
                    if c_type == ChannelTypes.TINT.value:
                        ox, oy, ow, ol, r, g, b, a = payload
                        active_channels.append((
                            c_type,
                            asset.state.position.x + ox,
                            asset.state.position.y + oy,
                            ow, ol,
                            r, g, b, a
                        ))

        logger.debug(f"Render Payload: Camera({pov.x}, {pov.y}) | Total Assets: {len(active_assets)}")

        # Pass purely native integers to bypass heavy object allocation
        render.render(
            self.bg_canvas, 
            self.fg_canvas,
            active_assets, 
            pov.x, 
            pov.y, 
            self.screensize.w, 
            self.screensize.l
        )

        if active_channels:
            render.channel(active_channels, pov.x, pov.y)
```

This is good! It behaves as expected. 

There is, of course, one slight problem that might possibly be a gigantic can worms we may or may not leave closed until a later date. The problem is:

The channel does its job. It only covers the Sprite frame based on the split calculations and only applies to non-transparent pixels. However, along the edges of the Fluid, the "submersion" channel renders slightly above where the Fluid actually starts, due to the non-dependence of the split calculation on the Fluid asset it is occupying. 

It seems like in order to rectify this the Screen would have to know the locations of Fluids, which violates the separate of responsbilities. I don't see a nice way around it.

##### Architectural Analysis

The root problem is a mismatch of dimensional assumptions:

**The 1D Local Assumption vs. 2D World Reality**

* `SpriteFrame.channels` assumes immersion is a static, 1D attribute of the character: *"If submerged, the water surface is always at local $y = \frac{l}{2}$ across the full width $w$."*
* In the world, immersion is a **2D spatial intersection**. When an entity steps into water from the top, their feet ($y + l$) cross the threshold first. Until the character's waist ($y + \frac{l}{2}$) reaches the fluid coordinate $y_{\text{fluid}}$, applying a $\frac{l}{2}$ split causes the aquatic tint to start in mid-air over dry land.

**Path 1: Leave the Can of Worms Closed (Level Design & Anchor Tuning)**

This is how most classical 2D engines (and LPC specifications) handle water:

1. *Gate Submersion on Footprint Anchors, Not Bounding Boxes:*

Currently, `_intersects(asset, fluid)` checks the whole entity body or default hitbox. If the player's top-left origin is at $y = 180$ and $l = 64$, their feet are at $y = 244$. If the fluid starts at $y = 220$, the collision flags `submerged = True` immediately, while the waist is still up at $y = 212$ (over dry land).

* If `fields.py` only triggers `submerged = True` when the entity's **sensory anchor / feet** penetrate past the waistline depth ($y + \frac{l}{2} \ge y_{\text{fluid}}$), the tint never appears prematurely on dry land.


2. *Masking with the Splash Particle:*

This is the primary functional reason the `splash` effect was added: the temporary splash particle spawned at $(x, y_{\text{waterline}})$ draws on top of the boundary during the entry transition frames, visually hiding the transition discontinuity until the character is fully inside the corridor.

3. *Shoreline Colliders:*

In practice, open water is bordered by bank tiles (`fore` decals, shoreline cliffs, or $m = 0$ boundaries) or shallow transition tiles, preventing characters from casually grazing edge boundaries.

**Path 2: Pass Overlap Geometry Through State (Clean Architecture)**

If you *do* want the water line to adjust dynamically without violating separation of concerns, **the logic belongs in `fields.py`, not `Screen`.**

`fields.py` *already* has the asset and the fluid in scope during the physics pass, and it already evaluates their bounding boxes:

```
[fields.py]                               [State]                               [SpriteFrame]                 [Screen]
Calculates overlap:                  Stores relative offset:              Emits dynamic payload:        Unpacks flat primitive:
dy = clamp(fluid.y - asset.y, 0, l)  ──>  mutators.triggers.waterline = dy ──> split_y = state.waterline ──> (tex, ..., split_y, ...)
```

1. *In `fields.py`:*

When an asset intersects a fluid, compute the relative penetration along the vertical axis:

$$
\text{penetration} = \text{fluid.pos.y} - \text{asset.pos.y}
$$

$$
\text{waterline} = \text{clamp}\left(\text{penetration},\, \frac{l}{2},\, l\right)
$$

Assign `asset.state.mutators.triggers.waterline = waterline`.

2. *In `SpriteFrame.channels`:*

Instead of hardcoding `half_l = l // 2`:

```python
split_y = getattr(state.mutators.triggers, "waterline", half_l)
payload = (split_y, 40, 110, 180, 170)
```

3. *In `Screen.draw`:*

Zero changes required. `Screen` already receives `split_y` via the `ChannelTypes.SUBMERGE` payload and splits the texture accordingly.

`Screen` remains completely ignorant of fluids, `Frame` remains decoupled from the world database, and the dynamic waterline is resolved entirely within the motion/physics domain.


**Path 3: The Lateral Boundary Problem (The True Can of Worms)**

The vertical boundary (top/bottom entry) is simple to solve via Path 1 or Path 2 because a horizontal texture split (`split_y`) aligns with the water line.

The real "can of worms" is **lateral boundaries** (e.g., walking east-west across a north-south flowing stream):

* If a 64px-wide sprite wades along the western bank of a 32px-wide stream, half of their torso is over water and half is over grass.
* Because SDL texture modulation (`SDL_SetTextureColorMod`) operates on whole `SDL_Rect` slices, clipping a character vertically *and* horizontally would require quadrant slicing (4 sub-rectangles per equipment layer) or a hardware stencil buffer.

##### User Review

Hmm. This touches on another problem with Fluids, actually, and it might actually yield the cleanest solution. Path 1 is the cleanest solution. However, needto modify it slightly. There are shoreline assets that haven't been brought into the engine yet. The edges of Fluid are currently very abrupt. They need to transition more naturally into the background tiles. They can be put into the assets directory to index them, but the question is what is the asset category and instance? Inclined to call them Geography and put them under Effects, and part of the Actuator's job can be instantiating Geography assets (instance=shoreline) along the edges of the Fluid. Assets have north, south, east and west facing directions. The correct solution is to treat the shoreline as a virtual edge, so when the the lower boundary of the sprite or object crosses the shoreline, it "falls" into the water, producing the splash and the submersion channel and coinciding with a positional shift equal to the dimension of the shore being traversed (horizontal or vertical dimensions). Subsequent problem will be multiplying the shoreline assets across the boundary, as they will need to be indexed in a similar (or possibly identical, so FluidFrame can probably be reused here) to Fluids. 

Discuss this approach, analyze it and what needs changed to achieve it. Put together a phase for the backlog for this refactor.

##### Architectural Analysis: Shorelines & Virtual Edge Hydrodynamics

**`Category: Effects` vs. Dedicated `Category: Geography`**

In the engine’s Entity-Component-System (ECS) architecture:

* **Category** dictates the *Properties Model* (`AssetProperties`) loaded at boot time via `src/assets//main.yaml`.
* **Instance** dictates the *State Model* (`AssetState`) hydrated dynamically on the `Board`.

Placing Shorelines under `AssetCategories.EFFECTS` as `AssetInstances.SHORELINES` (or `GEOGRAPHY`) has distinct advantages:

1. **Property Alignment:** Shorelines frequently require frame-animation for water lapping, waves, or foam cascades. `EffectProperties` already contains `LifecycleProperties` (`continuous`, `periodic`, `temporary`), `count`, and `dimensions`, avoiding the creation of an entirely redundant Category root in `PropertiesSchema`.
2. **Dynamic Generation:** If shorelines are generated procedurally by `Actuator` when a fluid stream pumps or truncates, they behave as environmental effects coupled to the life of the fluid emitter rather than static terrain tiles.

```
                  AssetCategories.EFFECTS
                             │
     ┌──────────────┬────────┴─────┬──────────────┬──────────────┐
     ▼              ▼              ▼              ▼              ▼
  fluids         passive        hazards      collectables    shorelines
(FluidState)  (AnimatorState) (HazardState)   (LotState)   (ShorelineState)

```

**State & Actuator Coupling: Independent Assets vs. Child Geometry**

A key design fork is whether Shorelines exist on the `Board` as independent `Asset` instances or as composite geometric metadata within `FluidState`.

*The Dynamic Churn Problem*

When a Crate is pushed across a fluid stream, `FluidMechanics` sets `fluid.state.dirty = True`. `Actuator.pump()` recalculates raycasts, truncates lengths, and resizes pools.

* **If Shorelines are Independent Board Assets:** `Actuator` must continuously call `board.remove(old_shores)` and `board.add(new_shores)`, invalidating `Board` spatial grid caches, layer caches, and character tables on every tick a dynamic body moves.
* **If Shorelines are Bound to Fluid:** `FluidState` holds a collection of procedural perimeter descriptors (e.g., `shores: List[ShorelineBoundary]`). `Actuator.pump()` updates them in-place.

**Recommendation:** Treat Shorelines as independent `Asset` instances managed through `Cradle`, but assign them a direct parent reference `fluid_name: str`. When `Actuator.pump()` executes, it clears and rebuilds only the shoreline assets tagged with that fluid's name, preventing full board cache churn.

**The "Virtual Edge" & Ledge Transition Mechanics**

The proposal to treat the shoreline as a virtual edge that triggers a "fall" / hop into the water solves the visual ambiguity of the submersion channel.

```
       [ DRY TERRAIN ]             [ SHORELINE ]              [ FLUID STREAM ]
                                 (w_shore / l_shore)
     ──┬─────────────────────────┬───────────────────────────┬───────────────────
       │                         │                           │
       │                         │  Footprint crosses edge:  │
       │                         │  1. Positional Shift (Δs) ───►  Submerged = True
       │                         │  2. Cradle.spawn(splash)  │     Current Applied
       │                         │                           │

```

*Traversal Mechanics*

1. **The Crossing Condition:**
Immersion should trigger when the entity’s *sensory anchor / footprint* $(x + \frac{w}{2}, y + l)$ crosses the shoreline sensor boundary from the dry side to the wet side.
2. **Positional Shift ($\vec{\delta}_{\text{shore}}$):**
When the entity commits across the virtual edge, add an orthogonal displacement vector pointing into the water:

$$\vec{\delta}_{\text{shore}} = \begin{cases}    (0,\, +l_{\text{shore}}) & \text{North bank (entering South)} \\    (0,\, -l_{\text{shore}}) & \text{South bank (entering North)} \\    (+w_{\text{shore}},\, 0) & \text{West bank (entering East)} \\    (-w_{\text{shore}},\, 0) & \text{East bank (entering West)}    \end{cases}$$

This instantaneous shift visually simulates stepping down off a bank or hopping off a ledge, clearing the edge boundary in a single frame.
3. **Transition Triggering:**
The moment $\vec{\delta}_{\text{shore}}$ applies:

* `mutators.triggers.submerged` switches to `True`.
* `Cradle.spawn_passive("splash", layer, pos)` instantiates the water splash particle.
* The entity is now squarely inside the fluid hitbox; `fields.py` immediately begins imparting $\vec{v}_{\text{current}}$.

4. **Bi-Directional vs. One-Way Ledges:**
* **Cliffs / Sheer Banks:** One-way. Once in the water, the shoreline edge acts as an obstacle ($m = 0$) preventing the sprite from climbing back out.
* **Beaches / Shallow Banks:** Bi-directional. Crossing from water onto the shore clears `submerged = False` and negates current velocity.

**Rendering & Frame Multipliers (`FluidFrame` Reuse)**

Can `FluidFrame` be reused for shorelines?

Yes. `FluidFrame` already handles:

1. Dynamic length expansion.
2. Integer multiple tile repetition (`length // dim`).
3. Fractional sub-pixel truncation slicing (`length % dim`).

**Necessary Adaptation: Orthogonal Orientation**

In `FluidFrame`, the textures tile *along* the direction of the fluid (`source`). A shoreline, however, tiles *along* the border of the stream (e.g., an East shoreline runs along the Y-axis for a North-South fluid, but its visual face points West into the water).

* Either parameterize `FluidFrame` with an `axis: Axis.PARALLEL | Axis.ORTHOGONAL` setting, or create a specialized `ShorelineFrame(Frame)` that accepts `(orientation: Directions, length: int)`.
* **Z-Ordering:** Shorelines must declare:

$$\text{depth} = 0, \quad \text{height} = 0$$

This ensures the shoreline sorts *above* the underlying water (`depth: -1`) so the transparent water-lapping foam renders over the fluid, while characters (`depth: 0, height = y + l`) sort cleanly on top.

**Codebase Changes Required**

1. **Schemas & Enums (`models/properties.py`, `config/enums.py`):**
    * Add `SHORELINES = "shorelines"` to `AssetInstances`.
    * Add `shorelines: Dict[str, EffectProperties]` to `EffectPropertyInstances`.
2. **State Models (`models/state/objects.py`):**
    * Create `ShorelineState(AssetState)`: contains `position`, `orientation: Directions`, `length: int`, `bidirectional: bool`, `parent_fluid: str`.
3. **Asset Frame (`assets/frames/core.py`):**
    * Generalize `FluidFrame` or implement `ShorelineFrame` to tile cardinal border segments (`north`, `south`, `east`, `west`) with distal edge slicing.
4. **Actuator Perimeter Decomposition (`services/generators/game/actuator.py`):**
    * Update `Actuator` to calculate perimeter flanks of active streams and annular pools.
    * Dispatch shoreline generation to construct bounding shore sensors along unoccluded fluid borders.
5. **Environmental Motion & Virtual Edge (`logic/modules/motion/fields.py`):**
    * Intercept shoreline crossings.
    * Apply positional shift $\vec{\delta}_{\text{shore}}$, spawn splash particles, and toggle `mutators.triggers.submerged`.

[Discussion Moved to Refactor Phase 09.02](./refactor-09-02.md)