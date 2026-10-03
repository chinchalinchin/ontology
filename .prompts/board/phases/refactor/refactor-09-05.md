#### Refactor: Phase 09.05 - Bridges & Bifurication

**Overview**

Transition the fluid and geography mechanics from single-corridor raycasts to branched hydrological networks with downstream flank continuation, and implement procedural architectural bridge crafts that decompose into discrete static sensors, elevating entities over water corridors and shoreline thresholds without obstructing navigation or fluid flow.

##### Architectural Analysis I

###### Recursive Stream Bifurcation & Downstream Continuation

In Phase 09.01–09.04, when an active fluid stream strikes an immovable static obstacle ($m = 0$), `Actuator.propagate()` halts the stream corridor at the annular pool margin. Under the principles of fluid mechanics:

* An obstructed fluid bifurcates across its orthogonal axes and discharges secondary streams continuing in the original `source` vector past the obstacle flanks.
* The maximum bifurcation depth is governed by `flow` (where branching occurs when $\text{flow} > 1$, propagating child streams with $\text{flow} - 1$).

**Impact on Phase 09.04 Subsystems**:

* **`FluidState`**: Augmented with `branches: List[BranchCorridor]` defining offset origins, lengths, flow intensities, and hitboxes for secondary streams.
* **`Actuator.propagate()`**: Following `_partition_pool()`, discharges lateral flank streams if $\text{flow} > 1$ by raycasting in the `source` direction from $(pool.x - fw, pool.y)$ and $(pool.x + pool.w, pool.y)$ (for vertical flows) or orthogonal Y-flanks (for horizontal flows).
* **`Cartographer._collect_water_rectangles()`**: Ingests bounding boxes for both the parent stream, the annular pool, and all active branch corridors into the contour sweep pass (`geometry.contours()`).
* **`Board._cached_watermap` & `Board._in_stream()**`: Extends broad-phase spatial hash population and point-in-stream narrow-phase checks across all child branch corridors.
* **`FluidFrame.keys()`**: Emits tiled texture coordinates and distal remainder slices for each active branch corridor.

###### Static Architectural Bridges & Surface Interception

Currently, `app.game.logic.modules.motion.fields.py` implements a 3-tier environmental resolution pass:

1. **Surface Hierarchy Interception (Rafts)**: Disables submersion, suppresses shoreline drop nudges, and transfers current velocity.
2. **Virtual Edge Crossing (Shorelines)**: Applies orthogonal step-down nudges, sets `submerged = True`, and spawns splash particles.
3. **Direct Environmental Fluid Immersion**: Imparts fluid current velocity and sets `submerged = True`.

**Proposal**:

* Register `AssetInstances.BRIDGES = "bridges"` under `AssetCategories.OBJECTS` with static sensor mass ($m = -1$) and an explicit `elevation: int = 1` or passable deck hitbox.
* In `fields.update()`, evaluate bridge surface interception at the top of the hierarchy (alongside Rafts):
* When an asset's bounding box intersects a `bridge`, mark `on_surface = True`, clear `submerged = False`, and bypass downstream shoreline edge crossing and fluid immersion checks.
* Unlike dynamic Rafts ($m > 0$), bridges are static ($m = -1$), imparting zero drift velocity ($\vec{v}_{\text{drift}} = \vec{0}$).

###### Surface Interception Hierarchy in `fields.py`

```python
# src/app/game/logic/modules/motion/fields.py
def update(assets: List[Asset], board: Board, delta: float) -> None:
    rafts = [a for a in assets if a.instance == AssetInstances.RAFTS.value]
    _update_rafts(rafts, board)

    for asset in assets:
        if asset.instance in (AssetInstances.RAFTS.value, AssetInstances.PROJECTILES.value):
            continue

        layer = asset.state.layer

        # -------------------------------------------------------------
        # 1. SURFACE HIERARCHY INTERCEPTION (BRIDGES & RAFTS)
        # -------------------------------------------------------------
        on_surface = False
        surface_vx = 0.0
        surface_vy = 0.0

        # Evaluate Static Bridges
        bridges = board.instances(AssetInstances.BRIDGES.value, layer)
        for bridge in bridges:
            if _intersects(asset, bridge):
                on_surface = True
                break

        # Evaluate Dynamic Rafts
        if not on_surface:
            for raft in board.instances(AssetInstances.RAFTS.value, layer):
                if _intersects(asset, raft):
                    on_surface = True
                    surface_vx = raft.state.velocity.vx
                    surface_vy = raft.state.velocity.vy
                    break

        if on_surface:
            asset.state.velocity.vx += surface_vx
            asset.state.velocity.vy += surface_vy
            asset.state.mutators.triggers.submerged = False
            continue

        # -------------------------------------------------------------
        # 2. VIRTUAL EDGE CROSSING (SHORELINES)
        # -------------------------------------------------------------
        # ...
```

---

##### Bug Reports

###### Bug B012: Inconsistent Physical Weight Caching Across Board Mutations

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

The physical weight cache `Board._cached_weights` exhibits divergent asset filtering across its lifecycle methods (`_cache`, `add`, and `relayer`). In `_cache()`, assets in `EFFECTS` and `GEOGRAPHY` are explicitly excluded from weights even if their mass is non-negative ($m \ge 0$). However, `add()` only filters `CURSORS`, allowing `EFFECTS` and `GEOGRAPHY` assets with mass to pollute `_cached_weights`. Furthermore, `relayer()` only checks `asset.properties.mass >= 0`, completely omitting category validation. This causes spatial collision routines and `Actuator._collect_obstacles` to evaluate invalid candidate assets after dynamic state additions or layer transitions.

**Proposed Remediation**

Standardize weight predicate filtering into a shared internal method `Board._is_weight(asset: Asset) -> bool`:

```python
def _is_weight(self, asset: Asset) -> bool:
    return (
        hasattr(asset.properties, "mass")
        and asset.properties.mass >= 0
        and asset.category not in (
            AssetCategories.CURSORS.value,
            AssetCategories.EFFECTS.value,
            AssetCategories.GEOGRAPHY.value,
            AssetCategories.TILES.value
        )
    )

```

Apply this predicate uniformly across `_cache()`, `add()`, `relayer()`, and `weights()`.

###### Bug B013: Flank Discharge Coordinate Gap and Texture Overdraw in Proposed Bifurcation Raycasting


**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

The task board's proposed discharge raycast coordinates for bifurcated fluid streams:

$$
(pool.x - fw, pool.y) \quad \text{and} \quad (pool.x + pool.w, pool.y)
$$

place secondary stream origins 1 tile ($fw$) outside the annular pool margin along the X-axis while starting at the upstream face of the pool ($pool.y$). For a stream flowing `DOWN`, this produces an unmeshed 1-tile gap at the pool flank and causes the secondary stream to travel parallel to the annular pool for length $pool.l$, creating severe texture overdraw and duplicate hitbox registrations.

**Proposed Remediation**

Update the bifurcation geometry calculation in `Actuator` so that discharge origins emanate from the downstream edge of the pool boundary ($pool.y + pool.l$ for `DOWN`, $pool.x + pool.w$ for `RIGHT`, $pool.y$ for `UP`, and $pool.x$ for `LEFT`), positioned flush at the lateral flanks ($pool.x$ and $pool.x + pool.w - fw$ for vertical streams).

##### Architectural Analysis II

**Invariants to Maintain**

1. **Decoupled Generator Services**:
    * `Actuator` and `Cartographer` must remain stateless geometric and spatial generators.
    * `Actuator.propagate()` currently executes `board.cache_fluid(fluid)` directly on the database. This violates the principle of separation of concerns; cache mutation belongs to the orchestrating mechanic (`FluidMechanics`) or database mutation hooks.
2. **Strict Spatial Coordinate Contracts**:
    * `Asset.hitboxes` must always be relative to `asset.state.position`.
    * `Cartographer` expects absolute bounding boxes `(min_x, min_y, max_x, max_y)`.
    * Frame keys emitted by `Frame.keys()` must output coordinate offsets relative to `asset.state.position`.
3. **Physical Classification Integrity**:
    * Bridges are static sensors ($m = -1$). They must **never** be registered under `Board.obstacles()`, as `NavigationMechanics` queries `board.obstacles()` to populate RRT spatial barriers. Marking bridges as obstacles would cause NPC pathfinding to navigate around bridges rather than across them.
4. **Physical Buoyancy vs. Locomotion**:
    * Dynamic non-buoyant objects ($m > 0$, `buoyant = False`, such as iron crates or stone blocks) sink in fluid, maintain tile friction, and resist drift.
    * Dynamic buoyant objects ($m > 0$, `buoyant = True`, such as wood crates) float, drift with current velocity ($\vec{v} = \vec{v}_{\text{flow}}$), and suppress ground friction.
    * Characters (Sprites, Players) swim/wade voluntarily: fluid velocity is added vectorally ($\vec{v} = \vec{v}_{\text{input}} + \vec{v}_{\text{flow}}$).

###### Subsystem 1: Stream Bifurcation Geometry

The task board's proposed discharge coordinates for bifurcated streams contain a geometric misalignment:

$$
\text{Proposed Left Flank}: (pool.x - fw, pool.y)
$$

$$
\text{Proposed Right Flank}: (pool.x + pool.w, pool.y)
$$

This formulation produces two defects:

1. **Spatial Disconnect (1-Tile Outward Gap)**: In `_partition_pool()`, the annular pool already spans horizontally from `pool.x` to `pool.x + pool.w`. Raycasting from `pool.x - fw` leaves an unmeshed 1-tile vacuum between the pool's outer margin and the secondary stream.
2. **Texture and Hitbox Overdraw**: Starting at `pool.y` for a `DOWN`-flowing stream causes the secondary stream to travel downstream alongside the pool from `pool.y` down to `pool.y + pool.l`. This reintroduces overlapping hitboxes and shoreline artifacts previously resolved in Bug B010 and Bug B011.

**Downstream Flank Continuation Formulation**

For a fluid flowing in direction $\vec{d}$, the secondary streams must discharge from the **downstream face** of the annular pool, aligned flush with the pool's lateral flanks:

| Stream Direction | Primary Axis Origin | Left/Top Flank Coordinate | Right/Bottom Flank Coordinate | Secondary Stream Raycast Direction |
| --- | --- | --- | --- | --- |
| `DOWN` | $y_{\text{origin}} = pool.y + pool.l$ | $x_1 = pool.x$ | $x_2 = pool.x + pool.w - fw$ | `DOWN` |
| `UP` | $y_{\text{origin}} = pool.y$ | $x_1 = pool.x$ | $x_2 = pool.x + pool.w - fw$ | `UP` |
| `RIGHT` | $x_{\text{origin}} = pool.x + pool.w$ | $y_1 = pool.y$ | $y_2 = pool.y + pool.l - fl$ | `RIGHT` |
| `LEFT` | $x_{\text{origin}} = pool.x$ | $y_1 = pool.y$ | $y_2 = pool.y + pool.l - fl$ | `LEFT` |

```
                       DOWN FLOW SCHEMATIC
                       
                            | Stream | (fx, fy)
                            |        |
                            v        v
         pool.x -------------------------------- pool.x + pool.w
                |          Annular Pool         |
                |         [Obstacle: m=0]       |
     pool.y+pool.l ------------------------------
                   |                          |
                   | Flank 1                  | Flank 2
                   v (DOWN)                   v (DOWN)

```

Each branch corridor must be validated with `geometry.raycast()` against the layer's static obstacles. If an immediate barrier exists at a flank, its length is zero and no corridor is emitted.

###### Subsystem 2: Static Architectural Bridges

**Surface Hierarchy Resolution Order**

In `fields.py`, surface interception must resolve bridges and rafts prior to evaluating virtual edge crossing (shorelines) or direct fluid immersion. When an entity intersects a bridge:

* `on_surface = True`
* `asset.state.mutators.triggers.submerged = False`
* `surface_vx = 0.0, surface_vy = 0.0`
* Section 2 (Shorelines) and Section 3 (Fluids) are bypassed via `continue`.

```
Entity Update in fields.py:
 1. Surface Interception (Bridges & Rafts)
    ├── Intersects Bridge? -> on_surface = True, v_surface = 0, submerged = False -> CONTINUE
    └── Intersects Raft?   -> on_surface = True, v_surface = v_raft, submerged = False -> CONTINUE
 2. Virtual Edge Crossing (Shorelines)
    └── Entry/Exit ledge traversal, splash particles, step-down nudge
 3. Direct Fluid Immersion
    └── Buoyancy velocity assignment, submerged = True

```

**Z-Ordering Model**

To ensure entities crossing a bridge render on top of the bridge deck, while the bridge deck renders on top of the fluid and shorelines:

* `Fluids`: `height = 0, depth = -1`
* `Shorelines`: `height = 0, depth = 0`
* `Bridges`: `height = 0, depth = 1`
* `Entities` (Sprites, Crates): Geometric height ($y + l > 0$)

###### Subsystem 3: Buoyancy Mechanics & Velocity Integration

The Task Board proposed replacing instance checks with `getattr(asset.properties, "buoyant", False)`, but routed non-buoyant entities into an `else` block that applied `+= flow_vx`. This caused non-buoyant objects (e.g., heavy iron crates) to accelerate downstream faster than buoyant ones.

The physical behavior must be partitioned by asset classification:

```python
# -------------------------------------------------------------
# 3. DIRECT ENVIRONMENTAL FLUID IMMERSION (BUOYANCY)
# -------------------------------------------------------------
if in_fluid:
    # Character Locomotion: voluntary movement + environmental drift
    if asset.category == AssetCategories.SHEETS.value:
        asset.state.velocity.vx += flow_vx
        asset.state.velocity.vy += flow_vy
        asset.state.mutators.triggers.submerged = True
    
    # Dynamic Objects (Crates, Barrels, Blocks)
    elif asset.category == AssetCategories.OBJECTS.value:
        if getattr(asset.properties, "buoyant", False):
            # Buoyant objects float and match fluid current velocity directly
            asset.state.velocity.vx = flow_vx
            asset.state.velocity.vy = flow_vy
            asset.state.mutators.triggers.submerged = True
        else:
            # Non-buoyant objects sink: maintain friction and resist stream velocity
            asset.state.mutators.triggers.submerged = True

```

In `frictive.py`, standard tile friction must only be suppressed if an asset is actively submerged **and** buoyant:

```python
# src/app/game/logic/modules/motion/frictive.py
is_submerged = getattr(asset.state.mutators.triggers, "submerged", False)
is_buoyant = getattr(asset.properties, "buoyant", False)

if is_submerged and is_buoyant:
    continue
```

##### Goals

###### Goal: Hydrological Network Bifurcation & Downstream Raycasting

Implement recursive stream branching in `Actuator` when an immovable obstacle ($m = 0$) is struck and $\text{flow} > 1$. Ensure child streams discharge strictly from the downstream face of the annular pool along its lateral flanks, eliminating spatial gaps and texture overdraw. Update `FluidState`, `FluidFrame`, `Board`, and `Cartographer` to index and render branched networks.

```python
# Conceptual discharge derivation in Actuator._propagate_branches()
def _calculate_branch_discharges(
    pool: Pool, 
    direction: str, 
    flow: int, 
    fw: int, 
    fl: int
) -> List[Tuple[Position, str, int]]:
    child_flow = flow - 1
    if child_flow <= 0:
        return []

    if direction == Directions.DOWN.value:
        y = pool.y + pool.l
        left_pos = Position(pool.x, y)
        right_pos = Position(pool.x + pool.w - fw, y)
        return [(left_pos, direction, child_flow), (right_pos, direction, child_flow)]
    elif direction == Directions.UP.value:
        y = pool.y
        left_pos = Position(pool.x, y)
        right_pos = Position(pool.x + pool.w - fw, y)
        return [(left_pos, direction, child_flow), (right_pos, direction, child_flow)]
    elif direction == Directions.RIGHT.value:
        x = pool.x + pool.w
        top_pos = Position(x, pool.y)
        bottom_pos = Position(x, pool.y + pool.l - fl)
        return [(top_pos, direction, child_flow), (bottom_pos, direction, child_flow)]
    elif direction == Directions.LEFT.value:
        x = pool.x
        top_pos = Position(x, pool.y)
        bottom_pos = Position(x, pool.y + pool.l - fl)
        return [(top_pos, direction, child_flow), (bottom_pos, direction, child_flow)]
    return []

```

###### Goal: Architectural Bridges & Surface Interception

Introduce `BRIDGES` under `AssetCategories.OBJECTS` with sensor mass ($m = -1$) and explicit Z-ordering parameters (`height = 0, depth = 1`). Implement surface hierarchy evaluation in `fields.py` to intercept entities traversing bridges, suppressing submersion, splash particles, shoreline nudges, and current drift. Ensure bridges remain accessible to NPC pathfinding by keeping them out of `Board.obstacles()`.

##### User Review I

###### Scoping

- Executive Decision: Bouyancy has been moved to the backlog.

###### Specification

**Bridges**

To avoid the proliferation of bespoke Bridge Assets and the manual construction of Bridges to be deployed through editing software, the Bridge Asset needs a procedure for generating its deployment from simple Assets that meet a precise specification. Bridges Assets will have a vertical and horizontal oriented frame arranged in a physically horizontal row in the image file. 

A Bridge Asset will be built through the `build` intention (i.e. a `build` Menu or a `build` Intention Transition), and the size of a Bridge will be dependent on the Player (or Sprite) specified dimensions and the prerequisite Resource cost being met. Bridges will be extended along vertical or horizontal axes (but not both simultaneously).

!!! note
    The `build` workflow is not important right now. During testing Bridges will be placed manually into the state file.

In other words, Bridges need to be Crafts. Furthermore, they need a state analogous to a Tile MultiplierState. A Bridge Asset needs to be deployed as a directed multiple (e.g. horizontal or vertical multiple) of its base Asset file so it can extend over a Fluid stream. Infact, the MultiplerState may be able to be leveraged directly or as a Base class for Bridge states.

However, whereas Tiles do not participate in collisions and do not have hitboxes, Bridges need hitboxes stretched over the area defined by their multiples. This means Bridges have "stateful" hitboxes. 

However, hitboxes need to remain properties to prevent the overcomplication of logic. So, the solution should be to treat Bridges as a "virtual asset" whose state decomposes into its constituent assets, i.e. if the property index reads,

```yaml
crafts:
    bridges:
        wood-bridge-horizontal:    
            dimensions:
                w: 100
                l: 32
            hitboxes:
                - position:
                    x: 0
                    y: 10
                  dimensions:
                    w: 100
                    l: 22
            mass: -1
```

And if the state file reads,

```yaml
crafts:
    bridges:
        - id: wood-bridge-horizontal
          name: the-bridge-to-terrabithia
          layer: '0'
          position:
            x: 100
            y: 100
          multiple:
            nx: 3
```

This produces a "decomposition" of `multiple.nx` Bridge Assets at `(x, y)=(100, 100)`, `(x + w,y) = (200, 100)` and `(x + 2w, y) = (300, 100)` with hitboxes `[(100, 110, 22, 100)], [(200, 110, 22, 100)], [(300, 110, 22, 100)]`

This is similar to how Struts and Compositions function. A BridgeState is really a "schema" for instantiation. In fact, the "decomposition" of Bridges should probably slot into the existing Decomposer class.

##### Goals

###### Goal: Hydrological Network Bifurcation & Downstream Raycasting

Implement recursive stream branching in `Actuator` when an immovable obstacle ($m = 0$) is struck and $\text{flow} > 1$. Ensure child streams discharge strictly from the downstream face of the annular pool along its lateral flanks, eliminating spatial gaps and texture overdraw. Update `FluidState`, `FluidFrame`, `Board`, and `Cartographer` to index and render branched networks. Decouple `Actuator` from direct `Board` cache mutation.

###### Goal: Architectural Bridge Crafts & Decomposition Engine

Introduce `BRIDGES` under `AssetCategories.CRAFTS`. Define `BridgeState` utilizing a directional multiplier schema. Extend `Decomposer` to unpack bridge schemas into constituent unit `Asset` instances with sensor mass ($m = -1$) and explicit Z-ordering parameters (`height = 0, depth = 1`). Expose `Board.bridges(layer)` while strictly excluding bridges from `Board.obstacles()` and `Board.weights()`. Implement surface hierarchy evaluation in `fields.py` to intercept entities traversing bridges, suppressing submersion, splash particles, shoreline nudges, and current drift.

##### User Review II

Closer to finalization, but not ready for implementation. Ambiguities remain.

###### Bridge Frame Ambiguities

There is a disconnect in the current tasking between the Bridge orientation and Bridge state. The vertical and horizontal frames of the Bridge are embedded in an Asset image file (`.png`) in a physical horizontal frame. In other words, Bridge State needs an `orientation` field, I think. And more clarification is needed on what is meant by properties and state with respect to frames.

The properties of assets are meant to "span" the space of image file, i.e. properties define how to arrange the frames of an asset to achieve an animation or generation. The state of Assets are meant to access the partitions created by the property indexing in such a way that the state of the Asset "traverses" an "animation trajectory" in "frame space" as the state evolves as part of the game loop.

Currently this is done in a couple of ways:

- (action, direction) mappings for sheets
- numerical indices for effects
- categorical indices of widgets
- etc.

As the game has developed, certain abstractions are becoming clearer. A discussion is to be had regarding the Frame implementation to use for Bridges, as a segway into a greater discussion about the Frame interface. There are two existing Frame implementation that seem like they can be used:

```python
class IndexFrame(Frame):
    """
    ## IndexFrame

    Parses horizontal sheets where each frame corresponds to a specific string key.
    """
    
    def keys(self, id: str, state: AssetState) -> List[Tuple[str, int, int]]:
        icon_key = getattr(state, "icon", None)
        if not icon_key:
            return []
        return [(settings.SEPARATOR.join([id, icon_key]), 0, 0)]

    def index(self, id: str, properties: WidgetProperties) -> Dict[str, Tuple[int, int, int, int]]:
        w = properties.dimensions.w
        l = properties.dimensions.l
        frames = properties.frames
        crops = {}
        
        # Failsafe: if no frames are defined, index the whole image
        if not frames:
            return {id: (0, 0, w, l)}
            
        for i, frame_name in enumerate(frames):
            frame_index = settings.SEPARATOR.join([id, frame_name])
            crops[frame_index] = (i * w, 0, w, l)
            
        return crops
```

or 

```python
class IterableFrame(Frame):
    """
    ## IterableFrame
    """
    
    def keys(self, id: str, state: AssetState) -> List[str]:
        """
        """
        return [(
            settings.SEPARATOR.join([
                id, 
                str(state.animation.frame)
            ]), 0, 0
        )]

        
    def index(self, id: str, properties: AssetProperties) -> Dict[str, Tuple[int, int, int, int]]:
        """
        """
        w = properties.dimensions.w 
        l = properties.dimensions.l

        return { 
            settings.SEPARATOR.join([
                id,
                str(i)
            ]): (i * w, 0, w, l)
            for i in range(properties.count) 
        }
```

Most Frame classes have been created in an adhoc manner as the engine developed, though reuse and recycling has always been kept in mind.

The indexing methods for both of these implementations are very similar; one simply use a sequence of numbers (IterableFrame with `0, 1, ..., properites.count`) versus a sequence of string categories (Index Frame with `properties.frames`). It is how they access the index via the state formulas that are materially different, e.g. IndexFrame uses a bespoke state field for icons versus IterableFrame's usage of an animation state field.

While BridgeFrames may ultimately require a specific Frame implementation for their orientation of `horizontal` and `vertical`, there are other solutions that involve reusing these implemenations; I am always loathe to introduce polymorphisms and duck-typing, as it significantly decreases the readability of the code, but there does seem to be an asbtraction lurking there that may require neither.

Analyze the problem of Bridge Frames and Frame interfaces in general. 

##### Architectural Analysis III

###### Path A: First-Class Spatial Strategy (`OrientedFrame`)

Directionality is already a first-class concept in Ontology (`Directions`: `UP`, `DOWN`, `LEFT`, `RIGHT`). Linear structures (bridges, fences, barricades, aqueducts) introduce the 2-way orthogonal axis (`Orientations`: `HORIZONTAL`, `VERTICAL`).

Just as `ShorelineFrame` maps cardinal `state.orientation` across rows, `OrientedFrame` maps axial `state.orientation` across a horizontal row:

* **`OrientedFrame.index()`**:
* `f"{id}-{Orientations.HORIZONTAL.value}": (0, 0, w, l)`
* `f"{id}-{Orientations.VERTICAL.value}": (w, 0, w, l)`


* **`OrientedFrame.keys()`**:
* Reads typed `state.orientation: str`.
* Returns `[(f"{id}-{state.orientation}", 0, 0)]`.


* **Pros**: Perfectly mirrors `ShorelineFrame`. Zero duck-typing. High domain readability.
* **Cons**: Adds a small, focused Frame class to `app.assets.frames.crafts`.

###### Path B: Canonical Categorical Slot (`IndexFrame` via `state.variant`)

Standardize all nominal 1D states onto a single protocol. Replace `state.icon` on `AttachmentState` and `state.orientation` on `BridgeState` with a shared field: `state.variant: str`:

* **`IndexFrame.keys()`**: Strictly reads `state.variant`.
* **Pros**: Unifies expressions, icons, and bridges under a single frame component.
* **Cons**: Forces domain concepts (`icon`, `orientation`) into a generic name (`variant`), reducing semantic precision in gameplay logic (e.g., `fields.py` inspecting `bridge.state.variant` instead of `orientation`).

###### Decision

Adopt **Path A (`OrientedFrame`)**.

1. `Orientations` (`horizontal`, `vertical`) represents a fundamental spatial property of world entities, matching the engine's existing treatment of `Directions`.
2. It keeps `BridgeState` semantically clean (`bridge.state.orientation = Orientations.HORIZONTAL.value`).
3. It keeps `IndexFrame` isolated to UI/expressions without polluting it with duck-typing or forcing unrelated states to adopt an abstract `variant` field.

###### Decomposition Logic (`src/app/services/generators/game/decomposer.py`)

When `Decomposer.unpack_bridge()` processes a deployed `BridgeState`:

* If `orientation == HORIZONTAL`: steps $N = \text{multiple.nx}$ times along $+X$, offsetting `Position(pos.x + i * w, pos.y)`.
* If `orientation == VERTICAL`: steps $N = \text{multiple.ny}$ times along $+Y$, offsetting `Position(pos.x, pos.y + i * l)`.
* Each constituent unit segment receives:
* An independent `BridgeState` with `multiple = Multiple(nx=1, ny=1)`.
* A sequential name: `settings.SEPARATOR.join([state.name, str(i)])`.
* The static `CraftProperties` of the unit asset, preserving hitboxes and dimensions.

##### Goals

###### Goal: Hydrological Network Bifurcation & Downstream Raycasting

Implement recursive stream branching in `Actuator` when an immovable obstacle ($m = 0$) is struck and $\text{flow} > 1$. Ensure child streams discharge strictly from the downstream face of the annular pool along its lateral flanks, eliminating spatial gaps and texture overdraw. Update `FluidState`, `FluidFrame`, `Board`, and `Cartographer` to index and render branched networks. Decouple `Actuator` from direct `Board` cache mutation.

###### Goal: Architectural Bridge Crafts & Oriented Frame Decomposition

Introduce `Orientations` enum and register `BRIDGES` under `AssetCategories.CRAFTS`. Implement `OrientedFrame` to index horizontal and vertical deck tiles from a single asset image. Define `BridgeState` with structural multipliers and explicit Z-ordering parameters (`height = 0, depth = 1`). Extend `Decomposer` to unpack bridge schemas into constituent unit `Asset` instances with sensor mass ($m = -1$). Expose `Board.bridges(layer)` while strictly excluding bridges from `Board.obstacles()` and `Board.weights()`. Implement surface hierarchy evaluation in `fields.py` to intercept entities traversing bridges, suppressing submersion, splash particles, shoreline nudges, and current drift.

##### Tasks

**1. Task: Recursive Stream Bifurcation & Hydrodynamic Network Modeling**

*Objective*: Implement lateral flank discharge raycasting in `Actuator` and extend broad-phase spatial caching, shoreline synthesis, and frame key emission across all active branches.

- [x] Subtask: Define `BranchCorridor` dataclass in `src/app/models/state/effects.py` and register `branches: List[BranchCorridor]` on `FluidState`.
- [x] Subtask: Refactor `Actuator.propagate()` to compute downstream flank origins from the pool boundary ($pool.y + pool.l$ for `DOWN`, $pool.x + pool.w$ for `RIGHT`, $pool.y$ for `UP`, $pool.x$ for `LEFT`) and raycast secondary child streams with `flow - 1`.
- [x] Subtask: Decouple `Actuator` from `Board` cache mutation by removing `board.cache_fluid()` calls from `Actuator.propagate()`, delegating cache invalidation to `FluidMechanics`.
- [x] Subtask: Update `Board._add_fluid_to_watermap()` to index parent corridors, annular pools, and all child branch corridors into `_cached_watermap`.
- [x] Subtask: Update `Board._in_stream()` to evaluate candidate coordinates against active child branch corridor bounding boxes.
- [x] Subtask: Update `Cartographer._collect_water_rectangles()` to compile primitive AABB tuples across all active branch corridors for contour analysis.
- [x] Subtask: Update `FluidFrame.keys()` to emit full-tile keys and distal remainder slices for each active branch corridor relative to `state.position`.

**2. Task: Architectural Bridge Crafts & Oriented Frame Strategy**

*Objective*: Implement static bridge assets as Crafts using `OrientedFrame` and decompose multiplier configurations via `Decomposer`.

- [x] Subtask: Add `Orientations` (`HORIZONTAL = "horizontal"`, `VERTICAL = "vertical"`) and `AssetInstances.BRIDGES = "bridges"` to `src/app/config/enums.py`.
- [x] Subtask: Add `bridges: Dict[str, CraftProperties]` to `CraftPropertyInstances` in `src/app/models/properties.py`.
- [x] Subtask: Create `BridgeState` in `src/app/models/state/crafts.py` with `orientation: str`, `multiple: Multiple`, `depth: int = 1`, and `height: int = 0`.
- [x] Subtask: Implement `OrientedFrame` in `src/app/assets/frames/crafts.py` mapping horizontal and vertical frame tiles. Register in the Factory.
- [x] Subtask: Register `bridges` in `RecipeConfiguration.crafts` (`frame: oriented`, `animation: none`, `state: BridgeState`).
- [x] Subtask: Implement `Decomposer.bridge(deployed_state: BridgeState) -> List[Asset]` to expand directed multipliers into constituent unit assets with sequential names, offset positions, and static hitboxes.
- [x] Subtask: Implement `Decomposer.bridge_cost(id: str, multiple: Multiple) -> List[Cost]` to calculate linear resource requirements ($N \times \text{cost}$).
- [x] Subtask: Update hydration loaders and `Board` instantiation to unpack `crafts.bridges` via `Decomposer`.
    - [x]: Add `spawn_bridge()` to `Cradle`.
    - [x]: Add Bridge tasks to `Migrator` to called new `Decomposer` method.
- [x] Subtask: Expose `Board.bridges(layer)` query method on `Board`, ensuring bridges are strictly excluded from `Board.obstacles()` and `Board.weights()`.

**3. Task: Surface Interception Hierarchy in Motion Fields**

*Objective*: Intercept entities traversing bridges in `fields.py` to suppress fluid immersion, current drift, and shoreline step-down nudges.

- [x] Subtask: Update `fields.update()` to evaluate bridge surface interception at the top of the hierarchy prior to dynamic Rafts.
- [x] Subtask: When intersecting a bridge, mark `on_surface = True`, set zero surface drift velocity ($\vec{v}_{\text{drift}} = \vec{0}$), clear `asset.state.mutators.triggers.submerged = False`, and bypass downstream shoreline edge crossing and fluid immersion passes.

--- 

Bug For Later: When a submerged Asset (i.e. an Asset moving under the influence of a Fluid field) intersects a bridge, it should render underneath of the Bridge and continue moving through the field, i.e. it should "pass underneath" the Bridge when its velocity is transverse to the orientation of the Bridge.

---

### Latent Technical Debt & Architectural Tensions

#### 1. The Bridge Underpass Dilemma (2.5D Elevation Collapse)

Currently, `fields.py` checks AABB intersection with bridges unconditionally:

```python
layer_bridges = board.instances(AssetInstances.BRIDGES.value, layer)
for bridge in layer_bridges:
    if _intersects(asset, bridge):
        on_surface = True
        # ...

```

If an entity is already floating in a fluid stream and drifts beneath a bridge deck whose span is perpendicular to the flow, `fields.py` intercepts the entity, clears `submerged = False`, and halts its drift. Because the engine models 2D planar space with pseudo-depth (`height`, `depth`), an asset cannot distinguish between being *on top of* the bridge deck versus *underneath* it. Resolving this requires formalizing an `elevation` or entry-trajectory state attribute.