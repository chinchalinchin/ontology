#### Refactor: Phase 07.02: Platforms & Elevated Hitboxes

**Overview**

Establishes Platforms as a Craft Asset and introduces the `ElevatedHitbox` component. Rather than splitting raised architecture into decoupled Assets, Platform utilize elevation-specific hitboxes.

A Platform has two responsibilities:

1. **Base Hitbox($E$):** At its base elevation $E$, its hitbox obstructs dynamic Assets moving on the same elevation.
2. **Elevated Hitbox($E + 1$):** At its upper elevation $E + 1$, it acts as a walkable area that bounds Assets traversing its surface.

| Architecture / Component | Implementations / Classes | `elevations(properties, state)` | `get(properties, state, elevation, frame=None)` |
| --- | --- | --- | --- |
| **Interface Contract** | `HitboxSchema` | `List[int]` | `List[Hitbox]` |
| **Single-Tier Body** | `StaticHitbox`, `DirectedHitbox`, `OrientedHitbox` | `[state.elevation]` | `hitboxes if elevation == state.elevation else []` |
| **Multi-Tier Architecture** | `ElevatedHitbox` | `[state.elevation + k for k in properties.hitboxes.keys()]` | `properties.hitboxes.get(elevation - state.elevation, [])` |

* `elevation: int` answers *at which vertical layer* the collision is occurring.
* `frame: Optional[Frame]` answers *which animation frame* governs the hitbox footprint.

##### Tasks

**1. Task: HitboxSchema Clean Interface Break**

*Objective*: Redefine `HitboxSchema` with `elevations()` and `get(properties, state, elevation, frame)` and update all existing strategies.

* [x] Subtask: Update `HitboxSchema` abstract methods in `src/app/assets/base.py`.
* [x] Subtask: Refactor `StaticHitbox`, `DynamicHitbox`, `OrientedHitbox`, `DirectedHitbox`, and `NoHitbox` in `src/app/assets/hitboxes/core.py`.
* [x] Subtask: Update `Asset.hitboxes` in `src/app/assets/base.py` to forward `self.elevation` and `self.frame`.

**2. Task: Platform Taxonomy, Schemas & Recipes**

*Objective*: Register platforms in configuration enums, schemas, and recipes.

* [x] Subtask: Add `AssetInstances.PLATFORMS` to `src/app/config/enums.py`.
* [x] Subtask: Implement `PlatformState` in `src/app/models/state/assets/crafts.py`.
* [x] Subtask: Update `CraftProperties.hitboxes` in `src/app/models/properties.py` to accept `Dict[int, List[Hitbox]]`.
* [x] Subtask: Bind `platforms` to `SingleFrame`, `NoAnimation`, and `ElevatedHitbox` in `recipes.yaml`.
* [x] Subtask: Create `src/assets/crafts/platforms/main.yaml` defining platform presets with dual-tier hitboxes (`0` and `1`).

**3. Task: ElevatedHitbox Strategy Implementation**

*Objective*: Implement the `ElevatedHitbox` component.

* [x] Subtask: Implement `ElevatedHitbox` in `src/app/assets/hitboxes/crafts.py` executing `elevation - state.elevation` relative resolution while honoring the updated interface signature.

**4. Task: Board Query Filtering & Cache Sync**

*Objective*: Filter multi-tier assets polymorphically in `Board`.

* [x] Subtask: Update `Board.weights(layer, elevation)` in `src/app/game/board/core.py` to filter via `elevation in w.hitbox.elevations(w.properties, w.state)`.
* [x] Subtask: Update `Board.obstacles(layer, elevation)` in `src/app/game/board/core.py` to filter via `elevation in o.hitbox.elevations(o.properties, o.state)`.

**5. Task: Collision Mechanics & Perimeter Integration**

*Objective*: Partition collision passes and generate walkable elevated deck contours.

* [x] Subtask: Update `SpatialMechanic.collisions()` and `constrain()` in `src/app/game/logic/mechanics/spatial/base.py` to accept `elevation: Optional[int] = None` and forward it to `asset.hitbox.get()`.
* [x] Subtask: Update `CollisionMechanics.update()` to bucket multi-tier weights into `weights_by_elevation` via `w.hitbox.elevations(w.properties, w.state)`.
* [x] Subtask: Update `CollisionMechanics._boundary()` and `_resolve()` to query hitboxes at the active loop `elevation`.
* [x] Subtask: Update `Perimeter.extract()` in `src/app/services/generators/game/perimeter.py` to synthesize walkable substrate bounds from platform decks when $E > \text{platform.state.elevation}$ and $E \in \text{platform.hitbox.elevations()}$.

**6. Task: Multi-Tier Collision Regression Suite**

*Objective*: Verify obstacle obstruction, deck traversal, and attackbox integrity across elevation planes.

* [x] Subtask: Add unit test in `tests/test_collision.py` asserting an entity at $E = 0$ is obstructed by a platform's tier 0 facade.
* [x] Subtask: Add unit test in `tests/test_collision.py` asserting an entity at $E = 1$ traverses the platform deck unhindered by the tier 0 facade.
* [x] Subtask: Add integration test verifying stair ascent from $E = 0$ to $E = 1$ transitions an entity from facade obstruction to deck containment.

**7. User Acceptance Session**

*Objective*: Debug live execution of the game engine.

* [ ] Subtask: Debug the [User Session](#view-session).