* **Per-Call List and Tuple Allocations in `predicates.in_pool` and `predicates.in_stream`**:
    * `in_pool()` allocates a single-element list `[(pool.x, pool.y, pool.x + pool.w, pool.y + pool.l)]` on every call just to invoke `geometry.inside()` for a 4-integer comparison.
    * `in_stream()` rebuilds `aabbs: List[Tuple[int, int, int, int]]` from `fluid.state.source` and `fluid.state.branches` on every `Board.fluid()` lookup (`60 Hz` per moving entity), even though `Actuator.propagate()` already compiles the active stream and pool geometry onto `fluid.state.hitboxes`.

---

## Documentation

##### Draft: NavigationMechanics Minkowski Inflation, Elevation Hitboxes, and Corner Waypoint Gating

* **Page**: `docs/05-mechanics.md`
* **Heading**: `###### Intentional Mechanic: NavigationMechanics`

###### Drift

`docs/05-mechanics.md` describes `NavigationMechanics` as raycasting against raw layer obstacles and popping waypoints unconditionally upon entering proximal range. It omits Minkowski obstacle inflation (`NavigationMechanics.padding()`), elevation-specific hitbox resolution (`asset.hitbox.get()`), line-of-sight gating to `vertices[1]` before popping intermediate corner waypoints, and offset-adjusted `goal_target` assignment.

###### Update

```markdown
###### Intentional Mechanic: NavigationMechanics

NavigationMechanics acts as the Sprite's tactical navigator, bridging strategic Goals with physical locomotion:

1. **Goal Verification**: Verifies Goal exists and Intention belongs to NavigationIntentions. Clears Trajectory and yields if false.
2. **Anchor & Padding Resolution**: Computes sensory footprints using `NavigationMechanics.anchor()` and calculates Minkowski inflation half-extents `(half_w + squeeze, half_l + squeeze)` via `NavigationMechanics.padding()` using the Sprite's hitbox half-dimensions and `mutators.parameters.squeeze.radius`.
3. **Obstacle Extraction & Line-of-Sight Check**: Extracts weight hitboxes at the Sprite's discrete `elevation` tier via `asset.hitbox.get(properties, state, elevation)` alongside tier perimeter boundaries, inflating each AABB by `(pad_x, pad_y)`. Raycasts a line-of-sight segment from `anchor` to `target` using `geometry.los()`.
4. **Path Maintenance**:
   * **Clear LOS**: Clears Trajectory and sets `trajectory.target` to the footprint-adjusted `goal_target` coordinate (`target - offset`).
   * **Occluded LOS**: If Trajectory is empty and `cooldown == 0`, executes `Planner.plan()` against the Minkowski-inflated obstacles, converts vertices to canvas origin coordinates by subtracting anchor displacement, and populates `trajectory.vertices`. Sets `trajectory.target` to `vertices[0]`.
   * **Dynamic Invalidation**: If active intermediate segments lose line-of-sight due to a moving dynamic Asset, invalidates the queue and replans immediately.
5. **Waypoint Arrival**: When the entity arrives within `mutators.parameters.action.radius` of `trajectory.target`, verifies line-of-sight to `vertices[1]` (if `len(vertices) > 1`) before popping `vertices[0]` so corner waypoints are not discarded prior to clearing the corner. When `vertices` is exhausted, sets `trajectory.target` to `goal_target`.
6. **Stall & Cooldown Handling**: When Navigation cannot resolve a collision-free path, sets `stalled = True` and initializes `cooldown = settings.PATH_RETRY_INTERVAL` to prevent per-frame re-planning thrash.

```

##### Draft: RRT Clamped Steering, Search-Space Culling, and Greedy String-Pulling

* **Page**: `docs/12-architecture.md`
* **Heading**: `###### Math: Paths`

###### Drift

`docs/12-architecture.md` states that `libs.core.math.paths` ingests all obstacles into `RRTObstacle*` and performs "fixed-distance trigonometric node steering", omitting the search-window broad-phase obstacle culling, the clamped step distance `fminf(step_size, hypotf(dx, dy))` in `_steer()`, and the `nogil` greedy raycast string-pulling pass (`_prune_path()`).

###### Update

```markdown
###### Math: Paths

- Address: `libs.core.math.paths`

This module implements the Rapidly-exploring Random Tree (RRT) pathfinding algorithm in pure C memory.

- **Broad-Phase Culling & Memory Management**: Computes an AABB search window around `(sx, sy)` and `(tx, ty)` padded by `20% + 2 * step_size` (with origin fallback clamping), packing only intersecting obstacles into a contiguous `RRTObstacle*` buffer via `malloc()`. Allocates `RRTNode*` and integer index buffers (`path_buf`, `forward_buf`, `pruned_buf`) sized to `max_iter + 2`, freeing all buffers synchronously in a `try...finally` block.
- **Tree Representation**: Nodes are represented as flat `RRTNode` structs containing coordinate values and an integer `parent_idx`, eliminating object pointer chasing and heap fragmentation.
- **Inner Loop (`nogil`)**: Releases the Python GIL during tree exploration. Executes 5% goal-biased continuous coordinate sampling, $O(N)$ nearest-neighbor distance minimization, distance-clamped trigonometric steering (`fminf(step_size, hypotf(dx, dy))`) via `atan2f()`, `cosf()`, and `sinf()`, and line-of-sight segment verification via `c_punctures`.
- **String-Pulling & Path Reconstruction**: Backtraces the `parent_idx` chain from `target_idx` to the root node, reverses the index chain into `forward_buf`, and executes a `nogil` greedy raycast string-pulling pass (`_prune_path`) to collapse redundant intermediate vertices before re-acquiring the GIL to instantiate Python `Position` models.

```

##### Draft: Mutator Triggers Schema and Squeeze Parameter Specification

* **Page**: `docs/02-sprites.md`
* **Heading**: `###### Model: Mutators`

###### Drift

In `docs/02-sprites.md`, `Fields: Triggers` lists `trigger.action` (which does not exist on `MutatorTriggers` in `src/app/models/state/core.py`), refers to `frightened` as `triggers.fear`, and omits `triggers.falling`. Additionally, `parameters.squeeze.radius` is described without noting its role in Minkowski obstacle inflation during `NavigationMechanics.padding()`.

###### Update

```markdown
**Fields: Triggers**

- `triggers.animated`: Triggered if a Sprite is currently able to animate, i.e. alter its AnimationState. When this Mutator trigger is false, the Sprite does not receive animation updates from the game loop.
- `triggers.dead`: Triggered if a Sprite dies (`meters.health.current == 0`).
- `triggers.frightened`: Triggered for the logical disjunction of the following conditions:
  * Triggered if Sprite's health dips below `fear.limit`.
  * Triggered if Sprite is surrounded by more than `fear.enemy` enemies within the pixel distance of `fear.radius`.
- `triggers.submerged`: Triggered when the entity's footprint intersects an active Fluid stream or pool without being aboard a Raft or Bridge. When active, `Screen.draw` renders a semi-transparent water tint over the lower half of the Sprite, and `Cradle` dispatches a temporary `splash` effect.
- `triggers.falling`: Triggered when an entity at elevation $E > 0$ steps off its supporting substrate into gravitational freefall.
- `triggers.vision`: Triggered if a Sprite is within visible distance of its Goal.

**Fields: Parameters**

- `parameters.fear`:
  * `radius`: Radius of separation within which the Sprite triggers the `triggers.frightened` mutator. Measured in pixels.
  * `limit`: Percentage of health below which Sprite triggers the `triggers.frightened` mutator.
  * `enemy`: Number of enemies within `parameters.fear.radius` that must be present to trigger the `triggers.frightened` mutator.
- `parameters.vision`:
  * `radius`: Radius of separation within which the Sprite triggers the `triggers.vision` mutator. Measured in pixels.
- `parameters.action`:
  * `radius`: Radius of separation used for proximity interaction checks and waypoint arrival thresholds. Measured in pixels.
- `parameters.squeeze`:
  * `radius`: Clearance buffer radius added to the Sprite's hitbox half-dimensions `(hb.w / 2 + squeeze.radius, hb.l / 2 + squeeze.radius)` in `NavigationMechanics.padding()` to Minkowski-inflate obstacle and perimeter AABBs during line-of-sight and RRT pathfinding.
- `parameters.descension`:
  * Sub-tier vertical freefall accumulator tracking pixel displacement toward `settings.TIER_DROP_DISTANCE`.
- `parameters.hand`:
  * Active hand (`left` or `right`) parameterizing the `use` Intention to resolve the corresponding item in `slots.grip`.

```

##### Draft: Sheet AttackHitbox ECS Component Implementation

* **Page**: `docs/01-assets.md`
* **Heading**: `###### Category: Sheets`

###### Drift

Under `**Hitbox: Attackboxes**` in `docs/01-assets.md`, a `@TODO(06-03)` note states that `Attackboxes` are a legacy hitbox implementation not yet migrated to the `HitboxSchema` component interface. In `src/app/assets/hitboxes/sheets.py`, `AttackHitbox(HitboxSchema)` is implemented and resolves frame-keyed attackboxes at the entity's elevation tier.

###### Update

```markdown
**Hitbox: AttackHitbox**

An Attackbox is a directional, frame-keyed hitbox unique to Sheet Assets. `AttackHitbox(HitboxSchema)` resolves active attackboxes at the Sheet's deployed elevation tier (`max(0, state.elevation)`) by joining `<action>-<direction>-<frame>` with `settings.SEPARATOR` (`"-"`) and querying `properties.attackboxes`. Attackboxes are evaluated during [CombatMechanics](./05-mechanics.md#spatial-mechanic-combatmechanics) to detect weapon and unarmed strike intersections.

- `elevations(properties, state): returns [max(0, state.elevation if state.elevation is not None else 0)]`
- `get(properties, state, elevation): returns properties.attackboxes.get(f"{state.animation.action}-{state.animation.direction}-{state.animation.frame}", []) if max(0, elevation) == max(0, state.elevation or 0) else []`

```

## Bughunting

##### Bug B036: `NavigationMechanics.update` Dereferences `board.player().name` Inside the Sprite Loop Without a `None` Guard

**STATUS**: OPEN
**SEVERITY**: LOW

**Description**

In `src/app/game/logic/mechanics/intentional/navigation.py` (`NavigationMechanics.update`, lines 311–316), `board.player().name` is evaluated on every iteration of `for sprite in board.instances(AssetInstances.SPRITES.value):`. Because `Board.player()` returns `Optional[Asset]` (`None` when no player instance is deployed on the board), calling `mechanic.update()` on a playerless board raises `AttributeError: 'NoneType' object has no attribute 'name'`.

**Steps to Replicate**

1. Remove the player asset from `mock_board` via `mock_board.remove([mock_board.player()])`.
2. Call `navigation_mechanic.update(mock_board, 0.016, mock_bus, mock_payload())`.
3. Observe `AttributeError: 'NoneType' object has no attribute 'name'`.

**Proposed Remeditation**

Resolve `player = board.player()` once prior to the loop in `NavigationMechanics.update()` and check `if player and sprite.name == player.name: continue`.