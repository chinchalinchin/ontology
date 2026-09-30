-- CURRENT DRAFT

#### Refactor: Phase 09.05 - Bridges & Bifurication

**Overview**

Transition fluid mechanics from single-corridor truncations to branched hydrological networks with downstream flank continuation. Introduce static architectural bridge sensors that elevate entities above water corridors and shoreline thresholds without obstructing navigation. 

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

###### Data Model Updates

```python
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

##### User Review

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

**src/app/models/config/core.py**

```python
"""
# Ontology: app.models.config.core

Models for typing the configuration attributes of Mechanics, Menus and other game components. See documentation for a more in-depth explanation of each field and its purpose. 
"""

# ...

@dataclass(slots=True, frozen=True)
class CompositionPseudoState:
    strut: PropertyState
    components: StateSchema

@dataclass(slots=True, frozen=True)
class CompositionConfiguration(Configuration):
    root: CompositionPseudoState
    branches: Optional[List[CompositionPseudoState]] = field(default_factory=list)
```

**src/app/services/generators/game/decomposer.py**

```python
"""
# Ontology: app.services.generators.decomposer

Package for decomposing Compositions into their constituent Assets. 
"""
# Standard Libraries
import re
import dataclasses
import logging
from typing import (
    Dict, 
    List, 
    Any
)

# Application Libraries
from app.assets.base import Asset
from app.config.enums import (
    AssetCategories, 
    AssetInstances
)
from app.services.generators.game.factory import Factory
from app.models.config import (
    CompositionConfiguration, 
    RecipeConfiguration
)
from app.models.properties import (
    PropertiesSchema, 
    Cost
)
from app.models.state import (
    PropertyState, 
    AssetState
)

# Cython Libraries
from libs.core.models import Position

logger = logging.getLogger(__name__)

class Decomposer:
    compositions: Dict[str, CompositionConfiguration]
    properties: PropertiesSchema
    recipes: RecipeConfiguration
    _increment: int

    def __init__(self, 
        compositions: Dict[str, CompositionConfiguration], 
        properties: PropertiesSchema, 
        recipes: RecipeConfiguration
    ):
        self.compositions = compositions
        self.properties = properties
        self.recipes = recipes
        self._increment = 0

    # ---------------------------------------------------------
    # ------------------------------------------ COST UTILITIES

    def _accumulate_cost(self, 
        cat: str, 
        inst: str, 
        asset_id: str, 
        cost_map: Dict[str, int]
    ) -> None:
        if cat == AssetCategories.CRAFTS.value:
            cat_props = getattr(self.properties.crafts, inst, {})
            props = cat_props.get(asset_id)
            for c in props.cost:
                cost_map[c.item] = cost_map.get(c.item, 0) + c.quantity


    def _aggregate_components_cost(self, 
        components: Any, 
        cost_map: Dict[str, int]
    ) -> None:
        if not components: 
            return
        
        for cat_field in dataclasses.fields(components):
            cat_key = cat_field.name
            cat_data = getattr(components, cat_key)

            if not cat_data: continue
            
            for inst_field in dataclasses.fields(cat_data):
                inst_key = inst_field.name
                inst_list = getattr(cat_data, inst_key)

                if not inst_list: continue
                
                for state_obj in inst_list:
                    self._accumulate_cost(cat_key, inst_key, state_obj.id, cost_map)

    # ---------------------------------------------------------
    # ------------------------------------- HYDRATION UTILITIES

    def _resolve_bind(self, 
        val: Any, 
        root_context: Dict[str, Any], 
        parent_context: Dict[str, Any]
    ) -> Any:
        """
        Map Composition `bind(root|parent.(.*))` binding to context.
        """
        if not isinstance(val, str):
            return val
            
        # Prioritize explicit parent bindings
        match_parent = re.match(r"^bind\(parent\.(.*?)\)$", val)
        if match_parent:
            key = match_parent.group(1)
            return parent_context.get(key, val)
            
        # Support root bindings (and legacy bindings without a prefix)
        match_root = re.match(r"^bind\((?:root\.)?(.*?)\)$", val)
        if match_root:
            key = match_root.group(1)
            return root_context.get(key, val)
            
        return val


    def _hydrate_state(self, 
        state_obj: AssetState, 
        root_context: Dict[str, Any], 
        parent_context: Dict[str, Any], 
        inc: int, 
        inst_key: str, 
        is_strut: bool = False
    ) -> AssetState:
        kwargs = {}
        for f in dataclasses.fields(state_obj):
            val = getattr(state_obj, f.name, None)
            kwargs[f.name] = self._resolve_bind(val, root_context, parent_context)
        
        if 'layer' in kwargs and not kwargs['layer']:
            kwargs['layer'] = parent_context['layer']
        if 'owner' in kwargs and not kwargs['owner']:
            kwargs['owner'] = parent_context['owner']

        # Layer Transition Boundary: If moving to an independent layer, reset local origin
        is_cross_layer = kwargs.get('layer') != parent_context.get('layer')
        base_pos = Position(0, 0) if is_cross_layer else parent_context['position']

        pseudo_pos = kwargs.get('position')
        if pseudo_pos:
            kwargs['position'] = Position(
                x=base_pos.x + pseudo_pos.x,
                y=base_pos.y + pseudo_pos.y
            )
        else:
            kwargs['position'] = Position(base_pos.x, base_pos.y)

        # Teleport destination coordinate mapping
        pseudo_out = kwargs.get('out')
        if pseudo_out:
            outlayer = kwargs.get('outlayer')
            # If returning to root layer, offset by deployed root position
            if outlayer == root_context.get('layer'):
                kwargs['out'] = Position(
                    x=root_context['position'].x + pseudo_out.x,
                    y=root_context['position'].y + pseudo_out.y
                )
            else:
                # Target is an interior layer; coordinates are local to that layer
                kwargs['out'] = Position(pseudo_out.x, pseudo_out.y)

        base_inst = inst_key[:-1] if inst_key.endswith('s') else inst_key
        
        if is_strut:
            b_name = kwargs.get('name') or root_context['name']
            kwargs['name'] = '-'.join([base_inst, b_name, str(inc)])
        else:
            kwargs['name'] = '-'.join([base_inst, parent_context['name'], str(inc)])
        
        return type(state_obj)(**kwargs)
    

    def _create_asset(self, 
        cat_key: str, 
        inst_key: str, 
        state_obj: AssetState
    ) -> Asset:
        cat_recipes = getattr(self.recipes, cat_key, None)
        recipe = getattr(cat_recipes, inst_key, None)
        
        prop_instance_key = inst_key

        if cat_key == AssetCategories.SHEETS.value and inst_key == AssetInstances.PLAYERS.value:
            prop_instance_key = AssetInstances.SPRITES.value
            
        cat_props = getattr(self.properties, cat_key, None)
        inst_props = getattr(cat_props, prop_instance_key, {}) 
        props = inst_props.get(state_obj.id)
        
        taxonomy = Factory.taxonomy(state_obj.id, state_obj.name, cat_key, inst_key)
        frame = Factory.frame(recipe.frame)
        animation = Factory.animation(recipe.animation)
        
        return Asset(taxonomy, props, state_obj, frame, animation)

    # ---------------------------------------------------------
    # ------------------------------------- EXPANSION UTILITIES

    def _unpack_node(self, 
        node: Any, 
        root_context: Dict[str, Any], 
        parent_context: Dict[str, Any], 
        inc: int, 
        is_root: bool = False
    ) -> List[Asset]:
        assets = []
        
        strut_state = self._hydrate_state(
            node.strut,
            root_context,
            parent_context,
            inc,
            AssetInstances.STRUTS.value,
            is_strut=True
        )
        strut_asset = self._create_asset(
            AssetCategories.CRAFTS.value, 
            AssetInstances.STRUTS.value, 
            strut_state
        )
        assets.append(strut_asset)

        # 1. Calculate the physical bottom edge (height) of the instantiated Strut
        node_height = strut_state.position.y + (strut_asset.dimensions.l if strut_asset.dimensions else 0)

        # 2. Inject it into the context dictionary for child components to reference
        node_context = {
            "position": strut_state.position,
            "layer": strut_state.layer,
            "owner": getattr(strut_state, 'owner', None),
            "name": strut_state.name,
            "height": node_height
        }
        
        # 3. If this is the root strut, its height becomes the root height
        if is_root:
            root_context["height"] = node_height

        self._unpack_components(node.components, root_context, node_context, inc, assets)
        return assets


    def _unpack_components(self, 
        components: Any, 
        root_context: Dict[str, Any], 
        parent_context: Dict[str, Any], 
        inc: int, 
        assets: List[Asset]
    ) -> None:
        if not components: 
            return
            
        for cat_field in dataclasses.fields(components):
            cat_key = cat_field.name
            cat_data = getattr(components, cat_key)
            if not cat_data: continue
            
            for inst_field in dataclasses.fields(cat_data):
                inst_key = inst_field.name
                inst_list = getattr(cat_data, inst_key)
                if not inst_list: continue
                
                for pseudo_state in inst_list:
                    new_state = self._hydrate_state(
                        pseudo_state,
                        root_context,
                        parent_context,
                        inc,
                        inst_key,
                        is_strut=False
                    )
                    assets.append(self._create_asset(cat_key, inst_key, new_state))


    # ---------------------------------------------------------
    # ------------------------------------------ PUBLIC METHODS


    def unpack(self, deployed_state: PropertyState) -> List[Asset]:
        """Flattens a Composition configuration into a native 1D list of fully hydrated Assets."""
        assets = []
        comp_config = self.compositions.get(deployed_state.id)
        if not comp_config:
            return assets

        self._increment += 1
        inc = self._increment

        root_context = {
            "id": deployed_state.id,
            "name": getattr(deployed_state, 'name', ''),
            "layer": getattr(deployed_state, 'layer', ''),
            "owner": getattr(deployed_state, 'owner', None),
            "position": getattr(deployed_state, 'position', Position(0,0))
        }

        # Unpack Root node first, explicitly flagging it as the root
        assets.extend(self._unpack_node(comp_config.root, root_context, root_context, inc, is_root=True))

        if comp_config.branches:
            for branch in comp_config.branches:
                assets.extend(self._unpack_node(branch, root_context, root_context, inc, is_root=False))

        return assets


    def cost(self, comp_id: str) -> List[Cost]:
        """Calculates the aggregate cost of an entire Composition tree."""
        config = self.compositions.get(comp_id)
        if not config: 
            return []
        
        cost_map = {}
        
        # Traverse Root
        self._accumulate_cost(
            AssetCategories.CRAFTS.value, 
            AssetInstances.STRUTS.value, 
            config.root.strut.id, 
            cost_map
        )
        self._aggregate_components_cost(config.root.components, cost_map)
        
        # Traverse Branches
        if config.branches:
            for branch in config.branches:
                self._accumulate_cost(
                    AssetCategories.CRAFTS.value, 
                    AssetInstances.STRUTS.value, 
                    branch.strut.id, 
                    cost_map
                )
                self._aggregate_components_cost(branch.components, cost_map)
                
        return [Cost(item=k, quantity=v) for k, v in cost_map.items()]
```

### Executive Summary & Architectural Evaluation

The revised scope focuses **Phase 09.05** strictly on **Bridges & Bifurcation**, deferring dynamic buoyancy to the backlog.

The user's architectural guidance regarding Bridges provides a critical breakthrough: **Bridges are Crafts, not Objects, and must decompose into constituent unit assets via `Decomposer`.**

---

### Architectural Analysis: Bridges as Decomposed Crafts

#### 1. Why Decomposed Crafts Beat "Stateful" Hitbox Mutation

Attempting to stretch hitboxes dynamically across a multiplier (`multiple.nx` or `multiple.ny`) would violate the foundational engine invariant:

> **"Code should never alter Asset Properties. Asset Properties are static and never change."**

If a single Bridge asset were stretched across 3 tiles:

* `asset.dimensions` and `asset.properties.hitboxes` would either need to be mutated at runtime or bypassed with dynamic state-level hitboxes.
* Narrow-phase collision routines, camera culling, spatial hashing, and shoreline occlusion checks would all require special branching logic to handle non-uniform asset scales.

By treating a deployed bridge declaration as a **virtual schema** that `Decomposer` unpacks into $N$ discrete unit `Asset` instances:

1. **Properties Remain 100% Immutable**: Each constituent bridge segment references the static `CraftProperties` of its orientation (`wood-bridge-horizontal` or `wood-bridge-vertical`), retaining fixed dimensions and local relative hitboxes.
2. **$O(1)$ Spatial Hashing & Collision Compatibility**: Each segment has its own Cartesian `Position`. Broad-phase grid insertion (`libs.core.math.space`) and narrow-phase AABB checks (`geometry.intersects`) process bridge segments like any standard entity with zero special-casing.
3. **Natural Cost Aggregation**: `Decomposer.cost()` already traverses composite structures. Sizing a bridge to $N$ segments scales the construction cost linearly ($N \times \text{Cost}$) during the `build` intention.

#### 2. Frame & Orientation Architecture

A bridge asset file contains both horizontal and vertical deck tiles arranged horizontally:

* **Frame 0 (Horizontal)**: $x \in [0, w)$, span oriented along the X-axis (crossing vertical rivers).
* **Frame 1 (Vertical)**: $x \in [w, 2w)$, span oriented along the Y-axis (crossing horizontal rivers).

To prevent frame indexing ambiguity:

* `CraftProperties` registers distinct IDs: `wood-bridge-horizontal` and `wood-bridge-vertical`.
* The `BridgeFrame` (or pre-indexed `IndexFrame`) maps:
* `wood-bridge-horizontal` $\to (0, 0, w, l)$
* `wood-bridge-vertical` $\to (w, 0, w, l)$


* When deployed with `multiple.nx > 1`, `Decomposer` instantiates $N$ horizontal segments spaced by $w$.
* When deployed with `multiple.ny > 1`, `Decomposer` instantiates $N$ vertical segments spaced by $l$.
* Simultaneous 2D multiples (`nx > 1 and ny > 1`) are prohibited; bridges are strictly 1D linear structures.

#### 3. Spatial Classification & Invariants

| Subsystem | Bridge Behavior | Enforcement |
| --- | --- | --- |
| **Mass & Physics** | Sensor ($m = -1$) | Excluded from elastic collision resolution. Excluded from `Board.weights()` ($m \ge 0$). |
| **Pathfinding (RRT)** | Passable Deck | Excluded from `Board.obstacles()`. NPCs pathfind directly across bridges. |
| **Fluid Propagation** | Non-occluding | Excluded from `Actuator._collect_obstacles()`. Water flows uninterrupted beneath decks. |
| **Shoreline Synthesis** | Non-occluding | Excluded from `Cartographer._detect_flank_occlusions()`. Natural shorelines generate beneath decks. |
| **Z-Sorting** | Above water/shores, below entities | `height = 0`, `depth = 1`. (Fluid: `depth = -1`, Shoreline: `depth = 0`, Walkers: $y + l > 0$). |

---

### Updated Task Board Backlog

```jinja2
#### Backlog: Phase 09.05 - Bridges & Bifurcation

**Overview**

Transition the fluid and geography mechanics from single-corridor raycasts to branched hydrological networks with downstream flank continuation, and implement procedural architectural bridge crafts that decompose into discrete static sensors, elevating entities over water corridors and shoreline thresholds without obstructing navigation or fluid flow.

##### Goal: Hydrological Network Bifurcation & Downstream Raycasting

Implement recursive stream branching in `Actuator` when an immovable obstacle ($m = 0$) is struck and $\text{flow} > 1$. Ensure child streams discharge strictly from the downstream face of the annular pool along its lateral flanks, eliminating spatial gaps and texture overdraw. Update `FluidState`, `FluidFrame`, `Board`, and `Cartographer` to index and render branched networks. Decouple `Actuator` from direct `Board` cache mutation.

##### Goal: Architectural Bridge Crafts & Decomposition Engine

Introduce `BRIDGES` under `AssetCategories.CRAFTS`. Define `BridgeState` utilizing a directional multiplier schema. Extend `Decomposer` to unpack bridge schemas into constituent unit `Asset` instances with sensor mass ($m = -1$) and explicit Z-ordering parameters (`height = 0, depth = 1`). Expose `Board.bridges(layer)` while strictly excluding bridges from `Board.obstacles()` and `Board.weights()`. Implement surface hierarchy evaluation in `fields.py` to intercept entities traversing bridges, suppressing submersion, splash particles, shoreline nudges, and current drift.

##### Tasks

**1. Task: Recursive Stream Bifurcation & Hydrodynamic Network Modeling**

*Objective*: Implement lateral flank discharge raycasting in `Actuator` and extend broad-phase spatial caching, shoreline synthesis, and frame key emission across all active branches.

- [ ] Subtask: Define `BranchCorridor` dataclass in `src/app/models/state/effects.py` and register `branches: List[BranchCorridor]` on `FluidState`.
- [ ] Subtask: Refactor `Actuator.propagate()` to compute downstream flank origins from the pool boundary ($pool.y + pool.l$ for `DOWN`, etc.) and raycast secondary child streams with `flow - 1`.
- [ ] Subtask: Decouple `Actuator` from `Board` cache mutation by removing `board.cache_fluid()` calls from `Actuator.propagate()`, delegating cache invalidation to `FluidMechanics`.
- [ ] Subtask: Update `Board._add_fluid_to_watermap()` to index parent corridors, annular pools, and all child branch corridors into `_cached_watermap`.
- [ ] Subtask: Update `Board._in_stream()` to evaluate candidate coordinates against active child branch corridor bounding boxes.
- [ ] Subtask: Update `Cartographer._collect_water_rectangles()` to compile primitive AABB tuples across all active branch corridors for contour analysis.
- [ ] Subtask: Update `FluidFrame.keys()` to emit full-tile keys and distal remainder slices for each active branch corridor relative to `state.position`.

**2. Task: Architectural Bridge Crafts & Decomposition Engine**

*Objective*: Implement static bridge assets as Crafts that decompose via `Decomposer` into discrete sensor units with static properties.

- [ ] Subtask: Register `BRIDGES = "bridges"` in `AssetInstances` enum (`src/app/config/enums.py`).
- [ ] Subtask: Add `bridges: Dict[str, CraftProperties]` to `CraftPropertyInstances` in `src/app/models/properties.py`.
- [ ] Subtask: Define `BridgeState` (containing `position: Position`, `multiple: Multiple`, `owner: Optional[str]`, `depth: int = 1`, `height: Optional[int] = 0`) in `src/app/models/state/crafts.py`.
- [ ] Subtask: Register `bridges` in `RecipeConfiguration.crafts` (`src/app/models/config/core.py`).
- [ ] Subtask: Implement `Decomposer.unpack_bridge(deployed_state: BridgeState) -> List[Asset]` to expand directed multipliers (`multiple.nx` or `multiple.ny`) into constituent unit assets with sequential names, offset positions, and static hitboxes.
- [ ] Subtask: Implement `Decomposer.cost_bridge(id: str, multiple: Multiple) -> List[Cost]` to calculate linear resource requirements ($N \times \text{cost}$).
- [ ] Subtask: Update hydration loaders and `Board` instantiation to unpack `crafts.bridges` via `Decomposer`.
- [ ] Subtask: Expose `Board.bridges(layer)` query method on `Board`, ensuring bridges are strictly excluded from `Board.obstacles()` and `Board.weights()`.

**3. Task: Surface Interception Hierarchy in Motion Fields**

*Objective*: Intercept entities traversing bridges in `fields.py` to suppress fluid immersion, current drift, and shoreline step-down nudges.

- [ ] Subtask: Update `fields.update()` to evaluate bridge surface interception at the top of the hierarchy prior to dynamic Rafts.
- [ ] Subtask: When intersecting a bridge, mark `on_surface = True`, set zero surface drift velocity ($\vec{v}_{\text{drift}} = \vec{0}$), clear `asset.state.mutators.triggers.submerged = False`, and bypass downstream shoreline edge crossing and fluid immersion passes.

```

---

### Deferred Backlog Item: Dynamic Buoyancy

Per the executive decision, dynamic buoyancy mechanics are preserved in the backlog:

```jinja2
#### Backlog: Hydrodynamic Buoyancy & Frictional Decoupling

**Overview** 

Generalize fluid interaction from hardcoded crate checks to property-driven dynamic flotation. Differentiate buoyant dynamic bodies (which float, drift with current velocity, and suppress ground friction) from non-buoyant dynamic bodies (which sink, resist drift, and maintain tile friction).

##### Goal: Property-Driven Buoyancy & Velocity Coupling

Incorporate declarative `buoyant: bool = False` into `ObjectProperties`. Update `fields.py` to inspect `asset.properties.buoyant` when applying fluid current vectors, reserving current velocity matching strictly for buoyant objects while allowing non-buoyant objects to sink without drift.

##### Goal: Submerged Frictional Decoupling

Refactor `frictive.py` so tile friction decay is suspended only when an asset is both submerged and buoyant. Ensure sunken non-buoyant objects continue to experience environmental friction decay against the underlying terrain tile.

##### Tasks

**1. Task: Property-Driven Buoyancy Integration**

*Objective*: Generalize hydrodynamic flotation across dynamic objects using `ObjectProperties.buoyant`.

- [ ] Subtask: Add `buoyant: bool = False` to `ObjectProperties` in `src/app/models/properties.py`.
- [ ] Subtask: Update default object configurations in `/src/assets/objects/main.yaml` (`wood-crate`, `wood-barrel` to `buoyant: True`; `iron-crate`, `stone-block` to `buoyant: False`).
- [ ] Subtask: Refactor `fields.py` to inspect `asset.properties.buoyant`, matching fluid velocity for buoyant objects while sinking non-buoyant objects without current acceleration.
- [ ] Subtask: Refactor `frictive.py` to condition friction suspension strictly on `asset.state.mutators.triggers.submerged and getattr(asset.properties, "buoyant", False)`.

```

---

### Bug Reports

```jinja2
##### Bug B012: Inconsistent Physical Weight Caching Across Board Mutations

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

```

```jinja2
##### Bug B013: Flank Discharge Coordinate Gap and Texture Overdraw in Proposed Bifurcation Raycasting

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

The task board's proposed discharge raycast coordinates for bifurcated fluid streams:

$$(pool.x - fw, pool.y) \quad \text{and} \quad (pool.x + pool.w, pool.y)$$

place secondary stream origins 1 tile ($fw$) outside the annular pool margin along the X-axis while starting at the upstream face of the pool ($pool.y$). For a stream flowing `DOWN`, this produces an unmeshed 1-tile gap at the pool flank and causes the secondary stream to travel parallel to the annular pool for length $pool.l$, creating severe texture overdraw and duplicate hitbox registrations.

**Proposed Remediation**

Update the bifurcation geometry calculation in `Actuator` so that discharge origins emanate from the downstream edge of the pool boundary ($pool.y + pool.l$ for `DOWN`, $pool.x + pool.w$ for `RIGHT`, $pool.y$ for `UP`, and $pool.x$ for `LEFT`), positioned flush at the lateral flanks ($pool.x$ and $pool.x + pool.w - fw$ for vertical streams).

```

---

### Documentation Drafts

#### Draft: Bridge Crafts & Decomposition Architecture

* **Page**: `docs/01-assets.md`
* **Heading**: `Crafts`

##### Drift

The crafts documentation specifies Struts, Decor, Forge, and Device, but lacks specifications for Bridges as multiplier-driven virtual crafts that decompose into discrete static sensors.

##### Update

```markdown
### Bridges

Bridges are static, passable Crafts that elevate characters and dynamic items over Fluid corridors, annular pools, and Shoreline margins without entering the `submerged` state.

**Decomposition & Structural Multipliers**

Rather than defining bespoke assets for every river span, Bridges are configured as unit assets (`wood-bridge-horizontal`, `wood-bridge-vertical`) and deployed via a 1D structural multiplier (`multiple.nx` or `multiple.ny`). 

During world hydration or dynamic execution of the `build` Intention, the `Decomposer` unpacks a `BridgeState` into a contiguous series of $N$ unit `Asset` instances:
* Each constituent segment receives an independent, absolute `Position` offset along the primary span axis.
* Each constituent segment references the base unit's static `CraftProperties`, preserving immutable dimensions and relative deck hitboxes.
* Construction cost scales linearly with span length ($N \times \text{Cost}$).

**Dynamics & Environmental Interception**

* Bridges are registered as Sensors ($m = -1$). They do not participate in momentum transfer or collision overlap resolution.
* Bridges are excluded from `Board.obstacles()` and `Board.weights()`, allowing `NavigationMechanics` (RRT) to pathfind across river crossings.
* In `MotionMechanics` (`fields.py`), intersecting a Bridge marks the entity as being on a surface:
  * Fluid immersion and current velocity drift are suppressed ($\vec{v}_{\text{drift}} = \vec{0}$).
  * Shoreline step-down nudges, ledge constraints, and splash particle emissions are bypassed.
  * `mutators.triggers.submerged` is cleared to `False`.

**Z-Ordering & Perspective**

Bridges declare an explicit `height: 0` and `depth: 1`. This guarantees that Bridge decks render above background Tiles, Fluids (`depth: -1`), and Shorelines (`depth: 0`), while allowing entities crossing the deck to sort above the bridge via dynamic geometric height ($y + l$).

**Frame: SingleFrame / IndexFrame**

* Indexes orientation deck tiles from the asset source.
* Emits `[(id, 0, 0)]` for each decomposed constituent segment.

**State: BridgeState (Deployment Schema)**

* `id: str`
* `name: Optional[str]`
* `layer: str`
* `position: Position`
* `multiple: Multiple` (`nx > 1` or `ny > 1`)
* `owner: Optional[str]`
* `depth: int = 1`
* `height: Optional[int] = 0`

```

---