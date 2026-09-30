#### Refactor: Phase 09.05 - Bifurcation, Bridges & Buoyancy

**Overview**

Transition fluid mechanics from single-corridor truncations to branched hydrological networks with downstream flank continuation. Introduce static architectural bridge sensors that elevate entities above water corridors and shoreline thresholds without obstructing navigation. Generalize hydrodynamic flotation across dynamic objects using declarative `buoyant` properties while decoupling generator services from database cache mutation.

##### Architectural Analysis I

###### 1. Recursive Stream Bifurcation & Downstream Continuation

In Phase 09.01–09.04, when an active fluid stream strikes an immovable static obstacle ($m = 0$), `Actuator.propagate()` halts the stream corridor at the annular pool margin. Under the principles of fluid mechanics:

* An obstructed fluid bifurcates across its orthogonal axes and discharges secondary streams continuing in the original `source` vector past the obstacle flanks.
* The maximum bifurcation depth is governed by `flow` (where branching occurs when $\text{flow} > 1$, propagating child streams with $\text{flow} - 1$).

**Impact on Phase 09.04 Subsystems**:

* **`FluidState`**: Augmented with `branches: List[BranchCorridor]` defining offset origins, lengths, flow intensities, and hitboxes for secondary streams.
* **`Actuator.propagate()`**: Following `_partition_pool()`, discharges lateral flank streams if $\text{flow} > 1$ by raycasting in the `source` direction from $(pool.x - fw, pool.y)$ and $(pool.x + pool.w, pool.y)$ (for vertical flows) or orthogonal Y-flanks (for horizontal flows).
* **`Cartographer._collect_water_rectangles()`**: Ingests bounding boxes for both the parent stream, the annular pool, and all active branch corridors into the contour sweep pass (`geometry.contours()`).
* **`Board._cached_watermap` & `Board._in_stream()**`: Extends broad-phase spatial hash population and point-in-stream narrow-phase checks across all child branch corridors.
* **`FluidFrame.keys()`**: Emits tiled texture coordinates and distal remainder slices for each active branch corridor.

###### 2. Static Architectural Bridges & Surface Interception

Currently, `app.game.logic.modules.motion.fields.py` implements a 3-tier environmental resolution pass:

1. **Surface Hierarchy Interception (Rafts)**: Disables submersion, suppresses shoreline drop nudges, and transfers current velocity.
2. **Virtual Edge Crossing (Shorelines)**: Applies orthogonal step-down nudges, sets `submerged = True`, and spawns splash particles.
3. **Direct Environmental Fluid Immersion**: Imparts fluid current velocity and sets `submerged = True`.

**Proposal**:

* Register `AssetInstances.BRIDGES = "bridges"` under `AssetCategories.OBJECTS` with static sensor mass ($m = -1$) and an explicit `elevation: int = 1` or passable deck hitbox.
* In `fields.update()`, evaluate bridge surface interception at the top of the hierarchy (alongside Rafts):
* When an asset's bounding box intersects a `bridge`, mark `on_surface = True`, clear `submerged = False`, and bypass downstream shoreline edge crossing and fluid immersion checks.
* Unlike dynamic Rafts ($m > 0$), bridges are static ($m = -1$), imparting zero drift velocity ($\vec{v}_{\text{drift}} = \vec{0}$).

###### 3. Property-Driven Dynamic Buoyancy

Currently, `fields.py` explicitly whitelists crates (`asset.instance == AssetInstances.CRATES.value`) when applying current velocity and maintaining buoyancy.

**Proposal**:

* Add `buoyant: bool = False` to `ObjectProperties` in `src/app/models/properties.py`.
* In `fields.update()`, replace instance string matching with property inspection:

```python
if in_fluid:
    if getattr(asset.properties, "buoyant", False):
        asset.state.velocity.vx = flow_vx
        asset.state.velocity.vy = flow_vy
```

* Dynamic objects ($m > 0$) with `buoyant = True` (crates, barrels, wooden chests) float and drift with current flow, while non-buoyant dynamic objects (heavy stone blocks, metal iron crates) sink, maintain friction, and resist drift.

##### Technical Specifications

###### Data Model Updates

```python
# src/app/models/properties.py
@dataclass(slots=True)
class ObjectProperties(AssetProperties):
    dimensions: Dimensions
    mass: int = 0
    count: int = 1
    hitboxes: Optional[List[Hitbox]] = field(default_factory=list)
    buoyant: bool = False


# src/app/models/state/effects.py
@dataclass(slots=True)
class BranchCorridor:
    position: Position
    source: str
    flow: int
    length: int = 0
    hitboxes: List[Hitbox] = field(default_factory=list)


@dataclass(slots=True)
class FluidState(EffectState):
    height: Optional[int] = 0
    depth: int = -1
    length: int = 0
    pool: Optional[Pool] = None
    branches: List[BranchCorridor] = field(default_factory=list)
    hitboxes: List[Hitbox] = field(default_factory=list)
    dirty: bool = True
    flow: int = 1
    source: str = Directions.DOWN.value

```

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
        ...

        # -------------------------------------------------------------
        # 3. DIRECT ENVIRONMENTAL FLUID IMMERSION (BUOYANCY)
        # -------------------------------------------------------------
        ...
        if in_fluid:
            if getattr(asset.properties, "buoyant", False):
                asset.state.velocity.vx = flow_vx
                asset.state.velocity.vy = flow_vy
            else:
                asset.state.velocity.vx += flow_vx
                asset.state.velocity.vy += flow_vy
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

##### Goal: Hydrological Network Bifurcation & Downstream Raycasting

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

##### Goal: Architectural Bridges & Surface Interception

Introduce `BRIDGES` under `AssetCategories.OBJECTS` with sensor mass ($m = -1$) and explicit Z-ordering parameters (`height = 0, depth = 1`). Implement surface hierarchy evaluation in `fields.py` to intercept entities traversing bridges, suppressing submersion, splash particles, shoreline nudges, and current drift. Ensure bridges remain accessible to NPC pathfinding by keeping them out of `Board.obstacles()`.

##### Goal: Property-Driven Buoyancy & Frictional Decoupling

Incorporate `buoyant: bool = False` into `ObjectProperties`. Update `fields.py` to drive current drift based on property inspection rather than instance matching. Update `frictive.py` to suspend linear friction only for submerged, buoyant assets, allowing non-buoyant dynamic objects to sink, rest on the substrate, and resist water current. Decouple `Actuator` from `Board` cache mutation.

##### Tasks

**1. Task: Recursive Stream Bifurcation & Hydrodynamic Network Modeling**

*Objective*: Implement lateral flank discharge raycasting in `Actuator` and extend broad-phase spatial caching, shoreline synthesis, and frame key emission across all active branches.

* [ ] Subtask: Define `BranchCorridor` dataclass in `src/app/models/state/effects.py` and register `branches: List[BranchCorridor]` on `FluidState`.
* [ ] Subtask: Refactor `Actuator.propagate()` to compute downstream flank origins from the pool boundary and raycast secondary child streams with `flow - 1`.
* [ ] Subtask: Decouple `Actuator` from `Board` cache mutation by removing `board.cache_fluid()` calls from `Actuator.propagate()`, delegating cache invalidation to `FluidMechanics`.
* [ ] Subtask: Update `Board._add_fluid_to_watermap()` to index parent corridors, annular pools, and all child branch corridors into `_cached_watermap`.
* [ ] Subtask: Update `Board._in_stream()` to evaluate candidate coordinates against active child branch corridor bounding boxes.
* [ ] Subtask: Update `Cartographer._collect_water_rectangles()` to compile primitive AABB tuples across all active branch corridors for contour analysis.
* [ ] Subtask: Update `FluidFrame.keys()` to emit full-tile keys and distal remainder slices for each active branch corridor relative to `state.position`.

**2. Task: Architectural Bridges & Surface Interception Hierarchy**

*Objective*: Implement static bridge assets that elevate entities over fluid corridors and shorelines without interfering with navigation obstacle trees.

* [ ] Subtask: Register `BRIDGES = "bridges"` in `AssetInstances` enum (`src/app/config/enums.py`).
* [ ] Subtask: Add `bridges: Dict[str, ObjectProperties]` to `ObjectPropertyInstances` and state schemas.
* [ ] Subtask: Configure default bridge property schema with $m = -1$, `height = 0`, and `depth = 1`.
* [ ] Subtask: Expose `Board.bridges(layer)` query interface on `Board` while ensuring bridges are strictly excluded from `Board.obstacles()`.
* [ ] Subtask: Update `fields.py` surface hierarchy resolution to evaluate bridge intersections, clearing `submerged = False`, setting zero drift velocity, and bypassing shoreline/fluid checks.

**3. Task: Property-Driven Buoyancy & Friction Interplay**

*Objective*: Generalize hydrodynamic flotation across dynamic bodies and decouple friction decay based on buoyancy properties.

* [ ] Subtask: Add `buoyant: bool = False` to `ObjectProperties` in `src/app/models/properties.py`.
* [ ] Subtask: Update object configurations in `/src/assets/objects/main.yaml` (`wood-crate`, `wood-barrel` to `buoyant: True`; `iron-crate`, `stone-block` to `buoyant: False`).
* [ ] Subtask: Refactor `fields.py` to inspect `asset.properties.buoyant` on objects, applying current matching only to buoyant entities while sinking non-buoyant objects without current acceleration.
* [ ] Subtask: Refactor `frictive.py` to condition friction suspension on `asset.state.mutators.triggers.submerged and getattr(asset.properties, "buoyant", False)`.
