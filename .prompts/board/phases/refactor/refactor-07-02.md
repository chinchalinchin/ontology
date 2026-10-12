#### Refactor: Phase 07.02: Platforms & Elevated Hitboxes

**Current Focus**: Synthesizing drafts into a unified task list for Phase 07.02.

**Overview**

This phase establishes `platforms` as a first-class `Crafts` asset instance in the Asset Hierarchy and introduces the `ElevatedHitbox` strategy component. It extends physical collision primitives and query pipelines to support multi-tier structures that span vertical elevation planes (e.g., cliff margins, raised terraces, and stage foundations). Rather than splitting raised architecture into decoupled facade walls and floor decks, unified platform entities project tier-specific physical constraints dynamically across both base and summit tiers.

**Summary***

In a discrete elevation architecture ($\text{elevation} \in \mathbb{Z}$), an elevated structure (such as a raised terrace, stage, or platform deck) has dual physical obligations:

1. **Sub-Tier Obstructor ($E$):** At its base elevation $E$, it presents a vertical facade wall that must obstruct dynamic entities moving on the lower plane (e.g., stopping a player walking north on the ground from clipping into the foundation).
2. **Super-Tier Substrate & Perimeter ($E + 1$):** At its upper elevation $E + 1$, it acts as a walkable surface deck that bounds entities traversing its surface (e.g., preventing a player on the terrace from walking off the unrailed edges without taking stairs).

Under a single-hitbox, single-elevation model, achieving this requires deploying two distinct assets for every single platform: an upright facade `Strut` at elevation $0$ ($m = 0$) and a floor deck `Strut` at elevation $1$ ($m = -1$). This clutters the board state, creates namespace bloat in compositions, and forces artificial synchronizations between independent assets that logically represent a single physical structure.

Just as `StageHitbox` dynamically derives hitboxes from an entity's biological `stage` and `OrientedHitbox` derives hitboxes from directional orientation, an **`ElevatedHitbox`** component fulfills the Entity-Component-System contract:

* **The Archetype:** `category: crafts`, `instance: platforms`.
* **The Flyweight Strategy:** `frame: SingleFrame`, `animation: NoAnimation`, `hitbox: ElevatedHitbox`.
* **The Property Schema:** `CraftProperties.hitboxes` typed as `Dict[int, List[Hitbox]]`, where keys represent relative elevation offsets ($0 = \text{base facade}$, $1 = \text{upper perimeter/deck constraints}$).

When `Board.weights(layer, elevation)` and `CollisionMechanics` evaluate physical bodies for tier $E$, `ElevatedHitbox` resolves the specific hitboxes assigned to tier $E$, allowing a single platform asset to cleanly participate across multiple elevation tiers simultaneously.

---

VERSION 1: Produced directly after Phase 07 implementation.

---

##### Specification

1. **Asset Taxonomy & Recipe Registration (`crafts.platforms`)**:
    * Register `AssetInstances.PLATFORMS.value` under `AssetCategories.CRAFTS.value`.
    * Configure recipe mapping in `recipes.yaml` binding `platforms` to `SingleFrame`, `NoAnimation`, and `ElevatedHitbox`.
    * Register `crafts.platforms` in `PropertiesSchema`, `StateSchema`, and `Decomposer`.
    * Implement `PlatformState(AssetState)` (`position`, `elevation: int = 1`, `owner`).
2. **Hitbox Schema & Data Structure (`ElevatedHitbox`)**:
    * Introduce `ElevatedHitbox(HitboxSchema)` in `app.assets.hitboxes.crafts`.
    * Update `CraftProperties.hitboxes` schema to accept relative tier-indexed hitboxes: `Dict[int, List[Hitbox]]`, where key `0` denotes the base tier facade boundary and key `1` denotes the summit tier edge constraints.
    * `Asset.hitboxes` delegates to `ElevatedHitbox.get()`, accepting an optional `elevation: Optional[int]` context to resolve tier-specific footprints.
3. **Multi-Tier Spatial Partitioning & Query Expansion**:
    * Add `span: Tuple[int, int]` property to `Asset` (derived from `(self.elevation, self.elevation + max(properties.hitboxes.keys()))` for platforms, and `(self.elevation, self.elevation)` for standard assets).
    * Update `Board.weights(layer, elevation)` and `Board.obstacles(layer, elevation)` to evaluate whether target `elevation` falls within an asset's `span`.
    * Update spatial broad-phase grids to index multi-tier platforms into all relevant elevation buckets.
4. **Environmental Boundary & Perimeter Synthesis**:
    * Refactor `Perimeter.extract(board, layer, elevation)` to query `ElevatedHitbox` primitives corresponding specifically to the evaluated `elevation`.
    * Facade hitboxes on relative tier `0` fold into lower-tier boundary perimeters; perimeter constraints on relative tier `1` fold into upper-tier boundary perimeters.
5. **Collision & Constraint Resolution (`CollisionMechanics`)**:
    * `CollisionMechanics.update()` queries tier-specific hitboxes during Phase 1 (`constrain`) and Phase 2 (`resolve`), ensuring dynamic bodies on tier $E$ only collide against the platform's tier-$E$ physical footprint.

##### Architectural Analysis I

In the current engine, `CollisionMechanics` partitions physical weights by discrete elevation:

$$
\text{CanCollide}(A, B) \iff A.\text{elevation} == B.\text{elevation}
$$

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
    def span(self) -> Tuple[int, int]:
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

* [ ] Subtask: Update `Board.weights(layer, elevation)` to filter assets by `span`.
* [ ] Subtask: Update `Board.obstacles(layer, elevation)` to filter assets by `span`.
* [ ] Subtask: Update `Cache.index_batch()` to insert multi-tier platform references across all spanned elevation buckets.

**4. Task: Collision & Perimeter Mechanics Integration**

*Objective*: Isolate tier-specific hitboxes during collision resolution and boundary generation.

* [ ] Subtask: Update `Perimeter.extract()` to query platform hitboxes corresponding specifically to the evaluated `elevation`.
* [ ] Subtask: Update `CollisionMechanics.update()` to pass the current loop `elevation` into `asset.primitive()` and `asset.hitboxes` queries.
* [ ] Subtask: Update `CollisionMechanics._resolve()` and `_boundary()` to ensure narrow-phase collision checks unpack hitboxes matching the active tier.

**5. Task: Test Bed Migration & Multi-Tier Physics Regression Suite**

*Objective*: Verify multi-tier obstacle blocking, deck containment, and stair transition mechanics.

* [!: Conditional on User Acceptance of Previous Tasks] Subtask: Add unit tests in `test_collision.py` asserting a player at elevation 0 is obstructed by a platform's tier 0 facade.
* [!: Conditional on User Acceptance of Previous Tasks] Subtask: Add unit tests in `test_collision.py` asserting a player at elevation 1 traverses the platform deck unhindered by the tier 0 facade.
* [!: Conditional on User Acceptance of Previous Tasks] Subtask: Add integration tests verifying a player traversing stairs from elevation 0 to 1 successfully transitions from front-facade collision to top-deck containment.

---

VERSION 2: Produced after Phase 07.01 refactor, without reference to VERSION 1.

---

##### Specification

1. **Data Models & Taxonomy (`crafts.platforms`)**:

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

* [ ] Subtask: Update `Perimeter.extract` to include platform deck bounds as walkable substrate rectangles for $E \ge 1$.
* [!: User Task] Subtask: Verify `Perimeter.generate` produces distinct closed boundary contours for Tier 0 and Tier 1.

**4. Task: Elevation-Aware Navigation & Mechanics Integration**

*Objective*: Ensure NPC navigation and broad-phase physics respect platform tiers.

* [ ] Subtask: Update `NavigationMechanics` to filter line-of-sight raycasts and obstacle hulls using `sprite.elevation`.
* [!: Conditional on User Acceptance of Previous Tasks] Subtask: Add unit tests verifying ground-level entities at $E = 0$ collide with platform facades while elevated entities at $E = 1$ traverse the deck.
* [!: Conditional on User Acceptance of Previous Tasks] Subtask: Add integration tests verifying an entity can climb stairs, traverse a platform deck at $E = 1$, and descend via stairs back to $E = 0$.


---

##### User Review

- Version 1 gets this correct: ElevatedHitbox indices have to be *relative to the deployed state* of the Platform. If a Platform is deployed on `elevation = 2` with elevated hitbox indices of `0` and `1`, then the hitboxes are resolved on `2` and `3`, i.e. the elevation of a Platform's hitbox is the sum of their elevation index and the Platform's base elevation.
- Version 1 alters the Hitbox interface to achieve this relative reference. While the Hitbox interface is relatively new (Phase 07, 09), I am always hesitant to change an interface to suit a particuLar instance of that interface. Tis seems undesirable and moreover, the result of misunderstanding the meaning of the interface; I am not sure the Hitbox interface should say *which* Hitbox is the hitbox that governs a collision. That information is only available once the collision occurs. The interface is meant to be a schematization of how to access hitboxes from the Asset's internal data structures. 
    - Code smell: The duck-typing on the Asset `@property span` is undesirable and evidence of a deeper ambiguity in the specification. The hitbox interface is supposed to determine the structure of the Hitbox. Putting conditionals that re-determine the structure is redundant and poor design. 
- Version 2 does not differentiates between the *deployed* elevation of the Platform and the *relative* elevation of the Platform. In Version 2's implementation of ElevatedHitbox, it assumes the hitbox can retrieved via `state.elevation`, implying the elevation of the Platform can change; however, the elevation of a Platform does not change. It should have a `state.elevation` and a `state.delta` to formalize the distinction between where it sits and how high it rises.  
    - Incorrect: Platforms cannot resolve their own hitboxes because they are dependent on the Asset that is colliding with the Platform, i.e. an external state.
- It seems as though the resolution of hitbox elevations with respect to the assets colliding with them should occur at the CollisionMechanics and Perimeter levels.