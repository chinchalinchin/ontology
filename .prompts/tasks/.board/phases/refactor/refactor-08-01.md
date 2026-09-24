
#### Refactor: Phase 08.01 - Obstacle Geometry

**Overview**

Refactor the spatial queries and sensory representations connecting `CognitionMechanics` to the Cython geometry and RRT pathfinding subsystems. Ensure path generation accurately reflects physical hitboxes rather than texture canvas bounds, and stabilize the automaton when targets are temporarily or permanently unreachable.

##### Goal: Physical Obstacle Projection

Extract obstacle bounding boxes strictly from asset collision hitboxes rather than top-level rendering dimensions.

```python
def obstacles(layer: str, board: Board, exclude: list) -> list:
    rects = []
    for asset in board.weights(layer):
        if asset.name in exclude:
            continue
        for hb in asset.hitboxes:
            rects.append((
                asset.state.position.x + hb.position.x,
                asset.state.position.y + hb.position.y,
                hb.dimensions.w,
                hb.dimensions.l,
            ))
    for bound in board.perimeters.get(layer, []):
        rects.append((
            bound.position.x,
            bound.position.y,
            bound.dimensions.w,
            bound.dimensions.l,
        ))
    return rects

```

##### Goal: Footprint Sensory Anchoring

Anchor line-of-sight raycasts and RRT start/end coordinates to the entity's physical footprint center rather than the top-left canvas coordinate.

```python
def anchor(asset: Asset) -> Position:
    hbs = asset.hitboxes
    if not hbs:
        return Position(
            x=asset.state.position.x + asset.dimensions.w // 2,
            y=asset.state.position.y + asset.dimensions.l // 2,
        )
    hb = hbs[0]
    return Position(
        x=asset.state.position.x + hb.position.x + hb.dimensions.w // 2,
        y=asset.state.position.y + hb.position.y + hb.dimensions.l // 2,
    )

```

##### Goal: Pathfinding Failure Recovery

Prevent the two-tick thrashing loop between `find` and `idle` when RRT cannot find a path.

```python
# If RRT fails to connect:
CognitionMechanics.log_goal(sprite, verb="unreachable")
sprite.state.memory.unreachable[goal.name] = (
    current_tick + settings.PATH_RETRY_INTERVAL
)
sprite.state.goal = None

```

##### Tasks

**1. Task: Hitbox-Accurate Obstacle Extraction**

*Objective*: Ensure pathfinding obstacle lists accurately represent physical collision boundaries.

* [x] Subtask: Refactor `CognitionMechanics.obstacles()` to iterate over `asset.hitboxes` for all entities returned by `board.weights(layer)`.
* [x] Subtask: Verify `obstacles()` computes absolute world coordinates by summing `asset.state.position` and `hitbox.position`.
* [x] Subtask: Add unit tests in `tests/unit/test_app_game_logic_mechanics_intentional_cognition.py` verifying multi-hitbox and offset-hitbox assets produce multiple discrete obstacle tuples.

**2. Task: Sensory Anchor Utilities**

*Objective*: Eliminate perspective bias in spatial raycasts.

* [x] Subtask: Add an `anchor()` helper in `app/game/logic/mechanics/modules/paths/` (or `CognitionMechanics`) to compute the physical footprint center of any Asset.
* [x] Subtask: Update `CognitionMechanics._plan()` to pass footprint anchors as `start` and `target` to `geometry.los()` and `Planner`.
* [x] Subtask: In `CognitionMechanics.path()`, offset generated RRT waypoints by the sprite's anchor displacement so `sprite.state.position` is steered such that the hitbox follows the path.

**3. Task: Categorical Dispatch Optimization in `_track**`

*Objective*: Prevent spurious per-tick re-planning on existing paths and static objects.

* [x] Subtask: In `CognitionMechanics._track()`, ensure active waypoints (`name.startswith(settings.RRT_PATH_PREFIX)`) only run invalidation checks (`_scrap()`) and bypass `_plan()`.
* [x] Subtask: Gate `_plan()` for `OBJECT` and `POSITION` goals behind an initial acquisition check or active obstruction detection.

**4. Task: Unreachable Target Backoff**

*Objective*: Stabilize the automaton when a target is obstructed.

* [!] Subtask: Add an unreachable/dormant tracking mechanism in `SpriteState.memory` to prevent `_remember()` from immediately popping goals that failed RRT.
* [!] Subtask: Ensure that upon path failure, control falls through to `idle -> wander` until sensory conditions change or the retry timeout expires.