#### Refactor: Phase 07.02: Platforms & Elevated Hitboxes

**Overview**

This phase establishes `platforms` as a first-class `Crafts` asset instance in the Asset Hierarchy and introduces the `ElevatedHitbox` strategy component. It extends physical collision primitives and query pipelines to support multi-tier structures that span vertical elevation planes (e.g., cliff margins, raised terraces, and stage foundations). Rather than splitting raised architecture into decoupled facade walls and floor decks, unified platform entities project tier-specific physical constraints dynamically across both base and summit tiers.

**Summary***

In a discrete elevation architecture ($\text{elevation} \in \mathbb{Z}$), an elevated structure (such as a raised terrace, stage, or platform deck) has dual physical obligations:

1. **Sub-Tier Obstructor ($E$):** At its base elevation $E$, it presents a vertical facade wall that must obstruct dynamic entities moving on the lower plane (e.g., stopping a player walking north on the ground from clipping into the foundation).
2. **Super-Tier Substrate & Perimeter ($E + 1$):** At its upper elevation $E + 1$, it acts as a walkable surface deck that bounds entities traversing its surface (e.g., preventing a player on the terrace from walking off the unrailed edges without taking stairs).

Under a single-hitbox, single-elevation model, achieving this requires deploying two distinct assets for every single platform: an upright facade `Strut` at elevation $0$ ($m = 0$) and a floor deck `Strut` at elevation $1$ ($m = -1$). This clutters the board state, creates namespace bloat in compositions, and forces artificial synchronizations between independent assets that logically represent a single physical structure.

Just as `StageHitbox` dynamically derives hitboxes from an entity's biological `stage` and `OrientedHitbox` derives hitboxes from directional orientation, an **`ElevatedHitbox`** (or `TieredHitbox`) component fulfills the Entity-Component-System contract:

* **The Archetype:** `category: crafts`, `instance: platforms`.
* **The Flyweight Strategy:** `frame: SingleFrame`, `animation: NoAnimation`, `hitbox: ElevatedHitbox`.
* **The Property Schema:** `CraftProperties.hitboxes` typed as `Dict[int, List[Hitbox]]`, where keys represent relative elevation offsets ($0 = \text{base facade}$, $1 = \text{upper perimeter/deck constraints}$).

When `Board.weights(layer, elevation)` and `CollisionMechanics` evaluate physical bodies for tier $E$, `ElevatedHitbox` resolves the specific hitboxes assigned to tier $E$, allowing a single platform asset to cleanly participate across multiple elevation tiers simultaneously.

##### Specification

1. **Asset Taxonomy & Recipe Registration (`crafts.platforms`)**:
    * Register `AssetInstances.PLATFORMS.value` under `AssetCategories.CRAFTS.value`.
    * Configure recipe mapping in `recipes.yaml` binding `platforms` to `SingleFrame`, `NoAnimation`, and `ElevatedHitbox`.
    * Register `crafts.platforms` in `PropertiesSchema`, `StateSchema`, and `Decomposer`.

2. **Hitbox Schema & Data Structure (`ElevatedHitbox`)**:
    * Introduce `ElevatedHitbox(HitboxSchema)` in `app.assets.hitboxes.crafts`.
    * Update `CraftProperties.hitboxes` schema to accept relative tier-indexed hitboxes: `Dict[int, List[Hitbox]]`, where key `0` denotes the base tier facade boundary and key `1` denotes the summit tier edge constraints.
    * `Asset.hitboxes` delegates to `ElevatedHitbox.get()`, accepting an optional `elevation: Optional[int]` context to resolve tier-specific footprints.

3. **Multi-Tier Spatial Partitioning & Query Expansion**:
    * Add `elevation_span: Tuple[int, int]` property to `Asset` (derived from `(self.elevation, self.elevation + max(properties.hitboxes.keys()))` for platforms, and `(self.elevation, self.elevation)` for standard assets).
    * Update `Board.weights(layer, elevation)` and `Board.obstacles(layer, elevation)` to evaluate whether target `elevation` falls within an asset's `elevation_span`.
    * Update spatial broad-phase grids to index multi-tier platforms into all relevant elevation buckets.

4. **Environmental Boundary & Perimeter Synthesis**:
    * Refactor `Perimeter.extract(board, layer, elevation)` to query `ElevatedHitbox` primitives corresponding specifically to the evaluated `elevation`.
    * Facade hitboxes on relative tier `0` fold into lower-tier boundary perimeters; perimeter constraints on relative tier `1` fold into upper-tier boundary perimeters.

5. **Collision & Constraint Resolution (`CollisionMechanics`)**:
    * `CollisionMechanics.update()` queries tier-specific hitboxes during Phase 1 (`constrain`) and Phase 2 (`resolve`), ensuring dynamic bodies on tier $E$ only collide against the platform's tier-$E$ physical footprint.

##### Architectural Analysis I

In the current engine, `CollisionMechanics` partitions physical weights by discrete elevation:

$$\text{CanCollide}(A, B) \iff A.\text{elevation} == B.\text{elevation}$$

While this eliminates cross-tier collision bleeding between independent entities, it fails for vertical structures that connect tiers. If a platform deck resides at `elevation: 1`, a character walking on `elevation: 0` is completely ignored by the platform during broad-phase filtering, allowing the character to walk straight through the platform's vertical foundation.

Decoupling the asset into two independent struts (a facade wall at 0 and a deck at 1) introduces several points of failure:

* Composition blueprints must declare duplicate structures and synchronize position offsets manually.
* Deconstruction or building mechanics (e.g., `build` or `mine` intentions) would require two distinct atomic actions to place or destroy a single logical platform.
* RRT pathfinding in `NavigationMechanics` evaluates the facade as an obstacle while evaluating the deck as empty space, complicating multi-tier waypoint planning.

Introducing `ElevatedHitbox` solves this via behavioral polymorphism:

```
                      +-----------------------------+
                      |   Platform Deck (Tier 1)    |  <-- Hitboxes[1]: Deck perimeter
                      +-----------------------------+
                      |   Platform Facade (Tier 0)  |  <-- Hitboxes[0]: Facade wall
+---------------------+-----------------------------+
| Ground Plane (Tier 0)                             |
+---------------------------------------------------+

```

* When `CollisionMechanics` processes Tier 0, the platform provides `Hitboxes[0]`. Dynamic bodies on the ground collide with the foundation.
* When `CollisionMechanics` processes Tier 1, the platform provides `Hitboxes[1]`. Dynamic bodies that climbed stairs to Tier 1 walk across the deck and are bounded by the deck edges.
* Memory overhead is negligible: `ElevatedHitbox` is a stateless singleton, and `Hitbox` primitives are stored as contiguous C structs.

##### Goals

###### Goal: ElevatedHitbox Behavioral Component

Implement the `ElevatedHitbox` strategy to extract relative tier-mapped hitboxes based on query context.

```python
# app/assets/hitboxes/crafts.py
class ElevatedHitbox(HitboxSchema):
    """
    Resolves multi-tier collision footprints from CraftProperties.hitboxes.
    Maps relative tier keys (0 for base facade, 1 for summit boundary)
    to physical Cython Hitbox models.
    """
    def get(
        self,
        properties: CraftProperties,
        state: AssetState,
        frame: Optional[Frame] = None,
        elevation: Optional[int] = None
    ) -> List[Hitbox]:
        if not properties.hitboxes or not isinstance(properties.hitboxes, dict):
            return []
        
        base_elevation = state.elevation if state.elevation is not None else 0
        target_tier = (elevation - base_elevation) if elevation is not None else 0
        return properties.hitboxes.get(target_tier, []) or []

```

###### Goal: Elevation Span Retrieval & Board Query Expansion

Update `Asset` and `Board` to query physical weights and obstacles across multi-elevation spans.

```python
# app/assets/base.py
class Asset:
    # ...
    @property
    def elevation_span(self) -> Tuple[int, int]:
        """Returns (min_elevation, max_elevation) spanned by this entity."""
        base_e = self.elevation
        if self.taxonomy.instance == AssetInstances.PLATFORMS.value:
            if isinstance(self.properties.hitboxes, dict) and self.properties.hitboxes:
                max_delta = max(self.properties.hitboxes.keys())
                return (base_e, base_e + max_delta)
        return (base_e, base_e)

# app/game/board/core.py
    def weights(self, layer: Optional[str] = None, elevation: Optional[int] = None) -> List[Asset]:
        weights = self._cache.get_weights(layer) if layer is not None else [
            a for a in self._assets if predicates.is_weight(a)
        ]
        if elevation is not None:
            target_e = max(0, elevation)
            return [
                w for w in weights 
                if w.elevation_span[0] <= target_e <= w.elevation_span[1]
            ]
        return weights

```

###### Goal: Platform Craft Schema Specification

Define schema for `crafts.platforms` supporting tiered hitboxes and deck calibration.

```yaml
# src/assets/crafts/platforms/main.yaml
crafts:
  platforms:
    platform-marble:
      dimensions:
        w: 96
        l: 111
      mass: 0
      cost:
        - item: marble
          quantity: 23
      hitboxes:
        # Tier 0 (Base facade wall blocking ground-level movement)
        0:
          - position: { x: 0, y: 32 }
            dimensions: { w: 96, l: 79 }
        # Tier 1 (Summit deck boundary constraints / railings)
        1:
          - position: { x: 0, y: 0 }
            dimensions: { w: 96, l: 8 }

```

##### Tasks

**1. Task: Models & Hitbox Schema Implementation**

*Objective*: Implement `ElevatedHitbox` and expand property models to accommodate relative tier-indexed hitboxes.

* [ ] Subtask: Implement `ElevatedHitbox(HitboxSchema)` in `src/app/assets/hitboxes/crafts.py`.
* [ ] Subtask: Update `CraftProperties` in `src/app/models/properties.py` to type `hitboxes: Optional[Union[Dict[int, List[Hitbox]], Dict[str, List[Hitbox]], List[Hitbox]]]`.
* [ ] Subtask: Add `elevation_span` property to `Asset` in `src/app/assets/base.py`.
* [ ] Subtask: Update `Asset.primitive()` to accept an explicit `elevation` argument to forward to `self.hitbox.get()`.

**2. Task: Platform Instance & Recipe Registration**

*Objective*: Integrate `platforms` into the Asset Hierarchy, recipe pipelines, and configuration schemas.

* [ ] Subtask: Add `AssetInstances.PLATFORMS` to `app.config.enums.AssetInstances`.
* [ ] Subtask: Create `src/assets/crafts/platforms/main.yaml` and migrate `platform-marble` from struts to platforms.
* [ ] Subtask: Register recipe mapping in `recipes.yaml` binding `platforms` to `SingleFrame`, `NoAnimation`, and `ElevatedHitbox`.
* [ ] Subtask: Update `PropertiesSchema`, `StateSchema`, and `Decomposer` to recognize `crafts.platforms`.

**3. Task: Spatial Partitioning & Board Query Refactoring**

*Objective*: Ensure spatial hash caching, `Board.weights()`, and `Board.obstacles()` index and return multi-tier assets across their full elevation span.

* [ ] Subtask: Update `Board.weights(layer, elevation)` to filter assets by `elevation_span`.
* [ ] Subtask: Update `Board.obstacles(layer, elevation)` to filter assets by `elevation_span`.
* [ ] Subtask: Update `Cache.index_batch()` to insert multi-tier platform references across all spanned elevation buckets.

**4. Task: Collision & Perimeter Mechanics Integration**

*Objective*: Isolate tier-specific hitboxes during collision resolution and boundary generation.

* [ ] Subtask: Update `Perimeter.extract()` to query platform hitboxes corresponding specifically to the evaluated `elevation`.
* [ ] Subtask: Update `CollisionMechanics.update()` to pass the current loop `elevation` into `asset.primitive()` and `asset.hitboxes` queries.
* [ ] Subtask: Update `CollisionMechanics._resolve()` and `_boundary()` to ensure narrow-phase collision checks unpack hitboxes matching the active tier.

**5. Task: Test Bed Migration & Multi-Tier Physics Regression Suite**

*Objective*: Verify multi-tier obstacle blocking, deck containment, and stair transition mechanics.

* [ ] Subtask: Add unit tests in `test_collision.py` asserting a player at elevation 0 is obstructed by a platform's tier 0 facade.
* [ ] Subtask: Add unit tests in `test_collision.py` asserting a player at elevation 1 traverses the platform deck unhindered by the tier 0 facade.
* [ ] Subtask: Add integration tests verifying a player traversing stairs from elevation 0 to 1 successfully transitions from front-facade collision to top-deck containment.

---

The completion of **Phase 07.01: Elevation Sorting** marks an architectural watershed for *Ontology*. The game engine's core philosophy is **simulation and emergence at all costs**—the premise that dynamic behavior must never be hard-scripted, but must emerge naturally from an initial world configuration evolving according to mathematical and physical invariants.

In a top-down 2D simulation, faking verticality via arbitrary coordinate hacks (such as legacy `height` offsets, imperative `depth` overrides, and string-binding patches) fundamentally compromises that philosophy. Those hacks created non-physical exceptions in collision pipelines, caused sorting jitter, and made inclined planes impossible to navigate without bespoke scripts.

By formalizing a discrete 2.5D topological manifold—where $Z$-space is represented by discrete elevation integer tiers ($E \in \mathbb{Z}$), draw order is derived deterministically through lexicographical sorting, and spatial mechanics partition physical interactions by elevation—Phase 07.01 restores physical consistency to the simulation. Entities do not need scripted state machines to climb a hill or traverse an overpass; they simply obey spatial kinematics across topological transitions.

Below is the formal architectural review, bug diagnosis, documentation audit, and subsequent phase backlog grooming.

---

#### Review: Phase 07.01 - Elevation Sorting

##### Overview

Phase 07.01 deprecated the legacy `height` attribute, renamed `depth` to `elevation`, established discrete negative integer tiers for terrain substrates, expanded the Painter's Algorithm to a 3-key lexicographical sort $(E, \text{ground\_y}, \text{priority})$, registered `crafts.stairs` as an inclined sensor entity, and partitioned broad/narrow-phase physical collisions by discrete elevation tiers.

##### Review: Implementation

* **Topological Incline Traversal**: `CollisionMechanics._traverse_stairs` successfully replaces naive bounding-box leading edges with centered foot-anchor projection ($f_x = x + \lfloor w/2 \rfloor, f_y = y + l$). Normalizing tread progress and gating elevation mutation on directional velocity vectors ($v_y < 0 / v_y > 0, v_x < 0 / v_x > 0$) prevents premature tier switching when an entity grazes stair edges.
* **Lexicographical Screen Sorting**: `Screen._sort` evaluates `(asset.elevation, ground_y, asset.properties.priority)`. Upright entities, substrate layers, and surface apertures sort deterministically without runtime string coercion or fallback branches.
* **Two-Pass Macro Resolution**: `Decomposer` introduces scope indexing to resolve `anchor(target)` directives down to concrete integer offsets before ECS instantiation, allowing wall fixtures to align with host facade baselines without manual asset offset tuning.

##### Review: Quality

* **Docstring Drift in Hitbox Schemas**: `app.assets.hitboxes.crafts.ElevatedHitbox` contains a copy-paste docstring from `StageHitbox` referencing *"biological/geological stage-indexed hitboxes from ResourceProperties"*. Furthermore, `OrientedHitbox` and `DirectedHitbox` in `app.assets.hitboxes.core` possess empty docstrings.
* **Redundant Taxonomy Predicates**: In `CollisionMechanics.update`, dynamic body filtering retains redundant checks:
```python
if getattr(w.properties, 'mass', 0) > 0 or w.taxonomy.instance == AssetInstances.PLAYERS.value:

```


Since `SheetProperties` defaults to `mass: int = 1` and the player is configured as a dynamic body ($m > 0$), checking `taxonomy.instance == AssetInstances.PLAYERS.value` violates the ECS principle of decoupling behavior from categorical taxonomy.
* **Enum Equality Style Discrepancy**: In `CollisionMechanics._resolve`, lines 144–145 compare `asset_a.taxonomy.instance == AssetInstances.PLAYERS` directly against the enum rather than using `.value`, whereas line 118 in `_boundary` uses `AssetInstances.PLAYERS.value`.

##### Review: Logic

* **Sensor Body Boundary Ingestion Defect**: In `Perimeter.extract`, static architecture is filtered using:
```python
mass = getattr(obj.properties, 'mass', 0)
if mass > 0 or obj.taxonomy.instance in (
    AssetInstances.CRATES.value,
    AssetInstances.CHESTS.value,
    AssetInstances.RAFTS.value
):
    continue

```


Sensor entities (such as stairs, pressure plates, and bridges) define `mass: int = -1`. The condition `mass > 0` evaluates to `False`, causing `Perimeter.extract` to treat sensor bodies as static architecture ($m = 0$) and appending their outer dimensions to `rects`. Consequently, `geometry.contours` bakes the entire bounding box of stair treads and floor switches into the impassable perimeter hull, physically locking characters out of incline traversal (the underlying cause of Bug B014).
* **Zero-Velocity Incline Stalling**: In `_traverse_stairs`, elevation mutation requires non-zero directional velocity (`vy < 0`, `vy > 0`, etc.). If an entity is pushed onto a stair sensor or comes to a complete rest ($v = 0$) within the transition threshold before switching tiers, their elevation remains unchanged. While this prevents edge grazing jitter, voluntary locomotion must be resumed in the original direction to trigger the shift.
* **Substrate Elevation Query Parity**: `Board.weights` and `Board.obstacles` map negative substrate elevations ($\le 0$) to Tier 0. However, `Board.categories` and `Board.instances` evaluate strict equality (`a.elevation == elevation`). Querying `board.categories('crafts', layer, elevation=0)` excludes default bridges because their substrate elevation is `-1`.

##### Review: Architecture

* **Pathfinding Disconnect on Multi-Tier Networks**: `CollisionMechanics` partitions physical collisions by elevation, but `NavigationMechanics` (RRT pathfinding) still extracts obstacle hitboxes in 2D space without elevation filtering. An NPC pathfinding on elevation 1 currently treats ground-level obstacles at elevation 0 as obstructions if they share screen coordinates $(x, y)$. Path planning must become elevation-aware.
* **Two-Pass Macro Scope Limits**: `Decomposer._resolve_anchor` indexes sibling components within the same strut branch. However, forward references across separate branches of the same composition macro cannot be resolved if the target branch is traversed later in the tree.

##### Review: Optimization

* **Unindexed Stair Sensor Checks**: In `CollisionMechanics.update`, stair detection executes an unindexed nested loop across all stairs and dynamic movers:
```python
for stair in stairs:
    for mover in movers:
        if geometry.intersects(...): self._traverse_stairs(mover, stair)

```


This incurs an $O(S \times M)$ overhead in Python and invokes the `stair.hitboxes` property repeatedly every frame. Sensor candidate evaluation should be offloaded to `SpatialMechanic.grid` (`Space.query`) or Cython `physics.environment`.
* **Per-Frame Sorting Allocations**: In `Screen.draw()`, `assets.sort(key=self._sort)` creates a 3-tuple `(elevation, ground_y, priority)` for every rendered asset on every frame at 60 Hz. Moving the sorting comparator into a Cython sort key or maintaining an insertion-sorted linked list in `BoardCache` will reduce inner-loop garbage collection pressure.

---


#### Refactor: Phase 07.02: Platforms & Elevated Hitbox

**Overview**

Phase 07.02 builds upon the elevation tier architecture by introducing `crafts.platforms`—static multi-tier structures that provide elevated, walkable surfaces ($E = 1$). To achieve physical consistency without 3D swept volumes, platforms introduce `ElevatedHitbox`: a dual-hitbox model where the front facade acts as a solid physical obstacle to entities on the ground tier ($E = 0$), while the deck surface acts as a traversable substrate for entities on the elevated tier ($E = 1$). In addition, boundary generation and tactical pathfinding are updated to support multi-tier environments.

##### Specification

1. **Data Models & Taxonomy (`crafts.platforms`)**:

* Register `AssetInstances.PLATFORMS` under `AssetCategories.CRAFTS.value`.
* Implement `PlatformProperties` ($w, l, \text{cost}, \text{hitboxes}$) where `hitboxes` maps discrete elevations to collision footprints:

```yaml
hitboxes:
  0: # Facade wall blocking ground level
    - position: { x: 0, y: 16 }
      dimensions: { w: 64, l: 48 }
  1: # Deck perimeter railing or edge constraints on elevated level
    - position: { x: 0, y: 0 }
      dimensions: { w: 64, l: 16 }

```

* Implement `PlatformState(AssetState)` (`position`, `elevation: int = 1`, `owner`).


2. **Hitbox Strategy (`ElevatedHitbox`)**:

* Implement `ElevatedHitbox(HitboxSchema)` in `app.assets.hitboxes.crafts`.
* Resolves active physical hitboxes dynamically based on querying entity elevation:

$$
\text{hitboxes}(A, E_{\text{query}}) = A.\text{properties.hitboxes}.get(E_{\text{query}}, [])
$$


3. **Multi-Tier Boundary Partitioning (`Perimeter`)**:

* `Perimeter.extract` parses platforms per elevation:
* At $E = 0$: Platform facade hitboxes are added to boundary obstacle hulls.
* At $E = 1$: Platform deck rectangles are treated as traversable substrates (analogous to $E = 0$ floorboards), synthesizing walkable contours for elevated tiers.

4. **Elevation-Aware Pathfinding (`NavigationMechanics`)**:
    
* `NavigationMechanics` filters `board.obstacles(layer, elevation=sprite.elevation)` and `board.perimeters[layer][sprite.elevation]`, allowing RRT to navigate open deck space on elevation 1 without false occlusions from elevation 0 architecture.

##### Architectural Analysis I

In a flat 2D projection, an elevated platform represents two distinct physical spaces occupying the same $(x, y)$ screen footprint:

1. The vertical wall/facade rising from the ground plane.
2. The walkable floor deck suspended at elevation 1.

Attempting to model this with a single static hitbox creates an unsolvable paradox: if the platform is solid, entities cannot walk on the deck; if the platform is passable, entities walk through the front facade wall on the ground.

By utilizing `ElevatedHitbox` and partitioning `CollisionMechanics` by discrete elevation tiers:

* A player at $E = 0$ colliding with the platform matches the facade hitbox at tier 0 ($m = 0$), halting at the wall.
* A player who ascends via stairs to $E = 1$ matches the platform at tier 1. The facade wall no longer exists in their collision partition; they walk freely across the deck and are constrained only by deck railings at $E = 1$.

##### Goals

###### Goal: Platform Properties & State Schema Definition

Establish declarative platform configurations and Pydantic schema validation.

```python
# app/models/state/assets/crafts.py
@dataclass(slots=True)
class PlatformState(AssetState):
    position: Optional[Position] = None
    elevation: int = 1
    owner: Optional[str] = None

```

```yaml
# src/assets/crafts/struts/platforms.yaml
crafts:
  platforms:
    platform-wood:
      dimensions: { w: 64, l: 64 }
      mass: 0
      priority: -1
      cost:
        - item: wood
          quantity: 20
      hitboxes:
        0:
          - position: { x: 0, y: 32 }
            dimensions: { w: 64, l: 32 }
        1: []

```

###### Goal: ElevatedHitbox Resolution Strategy

Implement dynamic tier-indexed hitbox retrieval in `app.assets.hitboxes.crafts.ElevatedHitbox`.

```python
# app/assets/hitboxes/crafts.py
class ElevatedHitbox(HitboxSchema):
    """
    Resolves physical obstacle hitboxes dynamically based on entity elevation.
    """
    def get(
        self,
        properties: CraftProperties,
        state: AssetState,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        if not properties.hitboxes:
            return []
        if isinstance(properties.hitboxes, dict):
            return properties.hitboxes.get(state.elevation, []) or []
        return properties.hitboxes

```

###### Goal: Elevated Deck Substrate Synthesis in Perimeter

Extend `Perimeter.extract` so platform decks form the walkable hull for $E \ge 1$.

```python
# app/services/generators/game/perimeter.py
if elevation > 0:
    platforms = board.instances(AssetInstances.PLATFORMS.value, layer, elevation=elevation)
    for plat in platforms:
        x1 = int(plat.state.position.x)
        y1 = int(plat.state.position.y)
        rects.append((x1, y1, x1 + plat.dimensions.w, y1 + plat.dimensions.l))

```

##### Tasks

**1. Task: Models & Schema Configuration**

*Objective*: Register platforms across property schemas, state schemas, and recipes.

* [ ] Subtask: Add `AssetInstances.PLATFORMS` to `app.config.enums.AssetInstances`.
* [ ] Subtask: Create `src/assets/crafts/struts/platforms.yaml` with calibrated costs and dual-tier hitboxes.
* [ ] Subtask: Update `CraftProperties` to validate tier-indexed hitbox dictionaries (`Dict[int, List[Hitbox]]`).
* [ ] Subtask: Bind `platforms` recipe to `SingleFrame`, `NoAnimation`, and `ElevatedHitbox` in `recipes.yaml`.

**2. Task: ElevatedHitbox & Asset Pipeline Integration**

*Objective*: Implement and verify tier-filtered hitbox extraction.

* [ ] Subtask: Implement `ElevatedHitbox` in `src/app/assets/hitboxes/crafts.py` and fix the legacy docstring.
* [ ] Subtask: Update `Asset.hitboxes` to allow passing an optional evaluation elevation tier for cross-tier sensor testing.

**3. Task: Multi-Tier Perimeter Synthesis**

*Objective*: Generate accurate walkable contours and boundary hulls for elevated tiers.

* [ ] Subtask: Resolve Bug B014 by explicitly excluding sensor bodies ($m < 0$) from static architecture extraction in `Perimeter.extract`.
* [ ] Subtask: Update `Perimeter.extract` to include platform deck bounds as walkable substrate rectangles for $E \ge 1$.
* [ ] Subtask: Verify `Perimeter.generate` produces distinct closed boundary contours for Tier 0 and Tier 1.

**4. Task: Elevation-Aware Navigation & Mechanics Integration**

*Objective*: Ensure NPC navigation and broad-phase physics respect platform tiers.

* [ ] Subtask: Update `NavigationMechanics` to filter line-of-sight raycasts and obstacle hulls using `sprite.elevation`.
* [ ] Subtask: Add unit tests verifying ground-level entities at $E = 0$ collide with platform facades while elevated entities at $E = 1$ traverse the deck.
* [ ] Subtask: Add integration tests verifying an entity can climb stairs, traverse a platform deck at $E = 1$, and descend via stairs back to $E = 0$.