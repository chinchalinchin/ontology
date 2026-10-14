#### Refactor: Phase 07.03: Gravity

**Overview**

Introduces a gravitational environmental field within `MotionMechanics` (`fields.py`) that governs vertical freefall when dynamic entities ($m > 0$) leave elevated support surfaces ($E > 0$). While falling, an entity accelerates downward ($+Y$) under constant gravitational acceleration $g$, bypasses standard coplanar collision resolution, and treats lower-elevation obstacle hitboxes ($e < E$) as inverted retention spans—continuing its descent until the lower-tier hitboxes release its footprint onto a valid lower substrate.

##### Specification

| Component / System | State / Field / Method | Responsibility |
| --- | --- | --- |
| **`MutatorTriggers`** | `falling: bool = False` | Tracks whether an entity is currently in airborne freefall. |
| **`MutatorParameters`** | `fall_floor: float = 0.0` (or `fall` state) | Tracks the minimum world-$Y$ landing threshold when stepping laterally off an elevated edge with no lower hitbox directly underneath. |
| **`settings.py`** | `GRAVITY_ACCELERATION = 400.0, TERMINAL_VELOCITY = 350.0, TIER_DROP_HEIGHT = 32` | Defines gravitational acceleration ($px/s^2$), maximum downward speed ($px/s$), and minimum vertical pixel span per elevation tier. |
| **`MotionModules`** | `kinematic`, `motive`, `frictive` | Suppresses voluntary locomotion, AI waypoint steering, and tile friction decay while `state.mutators.triggers.falling == True`. |
| **`fields.py`** | `_update_gravity(l_assets, board, layer, delta, grid)` | Evaluates elevated support containment, triggers `falling`, integrates $v_y \mathrel{+}= g \cdot \Delta t$, and resolves inverted hitbox span release. |
| **`CollisionMechanics`** | `update()` | Bypass Phase 1 elevated perimeter constraints (`elevation > 0`) so entities can cross open ledges, and exclude `falling` entities from Phase 2 solid collision resolution. |

##### Architectural Analysis I

1. **Support Surface vs. Facade Span (The 2.5D Projection Paradox)**
In 2.5D oblique projection, a single multi-tier `Platform` (e.g., `platform-marble`, `Dimensions(96, 111)`) embeds both its upper walkable deck and its lower vertical cliff facade (`Tier 0` hitbox: `Position(0, 32), Dimensions(96, 79)`) inside the same 2D bounding box:
* **Stacked Compositions (`Layer: 0` Castle Roof)**: An elevated `Strut` (`floor-horizontal-stone` at $E = 1$) sits above a base `Strut` (`wall-up-stone` at $E = 0$). Leaving the $E = 1$ `Strut`'s bounding box places the entity directly over the $E = 0$ wall's hitbox, which naturally acts as the vertical fall span until the bottom of the wall releases the entity.
* **Single-Asset Platforms (`castle-atrium-layer-3`)**: Because a `Platform` is deployed at base elevation $E_{\text{base}} = 0$ and projects its deck to $E = 1$, its `Tier 0` hitbox (`y: [168, 247]`) occupies the lower `79px` of its own `Dimensions(96, 111)` (`y: [136, 247]`).
* If an entity walks **South** off the platform (`y > 247`), its top hitbox edge (`py + hb.y`) only clears `y = 247` at `py = 213`.
* If an entity walks **East or West** off the side of the platform (`x > 96` or `x < 0` at `py = 160`), there is **no `Tier 0` hitbox** in the empty space beside the platform. If release depended solely on non-intersection with lower-tier hitboxes, an entity stepping laterally off a cliff into open air would land instantaneously on the very first frame (`\Delta y = 0`).
* **Resolution**: Falling termination requires satisfying **both** conditions:
1. **Minimum Tier Drop**: The entity's ground contact point (`foot_y = pos.y + dim.l`) must descend at least `TIER_DROP_HEIGHT` pixels below the elevation departure coordinate (or below the host platform's upper deck baseline).
2. **Inverted Hitbox Release**: The entity's physical hitboxes (`asset.hitbox.get(..., target_e)`) must have zero AABB intersections with all lower-elevation obstacle hitboxes (`board.weights(layer, elevation=target_e)` where `mass == 0`).






2. **Locomotion & Friction Clamping in `MotionMechanics**`
In `MotionMechanics.update()`, `kinematic.update()`, `motive.update()`, and `frictive.update()` execute *prior* to `fields.update()`:
* `physics.kinematics()` resets `vel.vy = 0.0` whenever vertical input is neutral and clamps `|vel|` to `character.speed` (`100.0`) when input is active.
* `frictive.update()` decays crate velocity via `physics.friction()`.
* Without gating these three modules by `not asset.state.mutators.triggers.falling`, `kinematic.update()` will overwrite gravitational acceleration every tick, preventing $v_y$ from accumulating.


3. **Elevated Perimeters vs. Open Ledges in `CollisionMechanics**`
In `Phase 07.02`, `Perimeter.extract()` generates closed boundary contours around `PLATFORMS` and `STAIRS` at `elevation > 0`, and `CollisionMechanics.update()` Phase 1 constrains all dynamic entities inside those contours.
* If `CollisionMechanics` enforces `perimeters` at `elevation > 0`, invisible boundary walls block entities from ever walking or being pushed off an elevated platform edge.
* **Resolution**: Retain `board.perimeters[layer][elevation]` for `NavigationMechanics` (so NPCs do not pathfind off cliffs during RRT/LOS planning), but restrict `CollisionMechanics` Phase 1 boundary enforcement to `elevation == 0` (the outer world canvas boundary). Walled platform edges (such as `platform-marble`'s North parapet at Tier `1`: `Position(0, 0), Dimensions(96, 8)`) remain enforced by Phase 2 hitbox collisions at `elevation = 1`, while un-hitboxed platform edges become true open drop-offs.


4. **Painter's Algorithm Integrity During Freefall**
While `falling == True`, keeping `asset.elevation` at its departure tier $E$ (or stepping down $E \to E - 1$ only as each tier's hitboxes release the entity) ensures the Primary Sort Key in `Screen._sort` (`asset.elevation > obstacle.elevation`) renders the falling body strictly in front of the lower-elevation wall/platform facade it is descending across.

##### Goals

###### Goal: Elevated Support Resolution & Trigger Activation

An entity at `asset.elevation > 0` is supported at tier $E = \text{asset.elevation}$ if its footprint intersects any of the following support primitives on the active `layer`:

1. **`Platforms`**: Where $E > \text{platform.elevation}$ and $E \in \text{platform.hitbox.elevations(platform.properties, platform.state)}`.
2. **`Stairs`**: Where $\text{stair.elevation} < E \le \text{stair.elevation} + \text{stair.state.delta}$ (evaluated against the stair's tread hitboxes).
3. **`Struts`**: Where $\text{strut.elevation} == E$ and `strut.properties.mass == -1` (walkable elevated floor substrates such as `floor-horizontal-stone` or elevated `floor-area-*`).

```python
def _extract_elevated_support_primitives(
    board: Board,
    layer: str,
    elevation: int
) -> List[Tuple]:
    """
    Builds C-grid field primitives for all surfaces capable of supporting
    a dynamic body at the given elevation tier (E > 0).
    """
    primitives: List[Tuple] = []
    idx = 0
    for craft in board.categories(AssetCategories.CRAFTS.value, layer):
        inst = craft.taxonomy.instance
        base_e = craft.elevation

        if inst == AssetInstances.PLATFORMS.value:
            if elevation > base_e and elevation in craft.hitbox.elevations(craft.properties, craft.state):
                primitives.append((
                    idx,
                    craft.state.position.x,
                    craft.state.position.y,
                    craft.dimensions.w,
                    craft.dimensions.l,
                    []
                ))
                idx += 1

        elif inst == AssetInstances.STAIRS.value:
            if base_e < elevation <= base_e + craft.state.delta:
                sx, sy = craft.state.position.x, craft.state.position.y
                for hb in craft.hitboxes:
                    primitives.append((
                        idx,
                        sx + hb.position.x,
                        sy + hb.position.y,
                        hb.dimensions.w,
                        hb.dimensions.l,
                        [hb]
                    ))
                    idx += 1

        elif inst == AssetInstances.STRUTS.value:
            if base_e == elevation and getattr(craft.properties, "mass", 0) < 0:
                primitives.append((
                    idx,
                    craft.state.position.x,
                    craft.state.position.y,
                    craft.dimensions.w,
                    craft.dimensions.l,
                    []
                ))
                idx += 1

    return primitives

```

###### Goal: Gravitational Acceleration & Inverted Hitbox Span Release

When an entity at $E > 0$ fails the support check (or is already `falling`), `_update_gravity` accelerates it downward and checks whether the lower tier ($E - 1$) hitboxes have released it:

```python
def _update_gravity(
    l_assets: List[Asset],
    board: Board,
    layer: str,
    delta: float,
    grid: Space
) -> set[int]:
    """
    Applies downward gravitational acceleration to unsupported elevated entities
    and resolves landing via inverted lower-elevation hitbox release.
    Returns indices of falling assets to exclude from surface/fluid passes.
    """
    falling_indices: set[int] = set()
    elevated_groups: Dict[int, List[Tuple[int, Asset]]] = {}

    for i, asset in enumerate(l_assets):
        if asset.elevation > 0 or asset.state.mutators.triggers.falling:
            elevated_groups.setdefault(asset.elevation, []).append((i, asset))

    if not elevated_groups:
        return falling_indices

    for elevation, group in elevated_groups.items():
        if elevation <= 0:
            for i, asset in group:
                asset.state.mutators.triggers.falling = False
            continue

        support_prims = _extract_elevated_support_primitives(board, layer, elevation)
        group_prims = [asset.primitive(sub_i) for sub_i, (_, asset) in enumerate(group)]

        supported_sub_indices: set[int] = set()
        if support_prims:
            matches = physics.environment(group_prims, support_prims, grid)
            for sub_i, _ in matches:
                supported_sub_indices.add(sub_i)

        target_e = max(0, elevation - 1)
        lower_obstacles = [
            w for w in board.weights(layer, elevation=target_e)
            if getattr(w.properties, "mass", 0) == 0
        ]
        lower_obs_prims = [
            w.primitive(
                idx,
                hitboxes=w.hitbox.get(w.properties, w.state, target_e, w.frame)
            )
            for idx, w in enumerate(lower_obstacles)
        ]

        for sub_i, (orig_i, asset) in enumerate(group):
            is_falling = asset.state.mutators.triggers.falling

            if not is_falling and sub_i not in supported_sub_indices:
                asset.state.mutators.triggers.falling = True
                asset.state.velocity.vx = 0.0
                asset.state.velocity.vy = max(0.0, asset.state.velocity.vy)
                is_falling = True

            if not is_falling:
                continue

            falling_indices.add(orig_i)

            # 1. Constant downward acceleration (+Y)
            asset.state.velocity.vx = 0.0
            asset.state.velocity.vy = min(
                settings.TERMINAL_VELOCITY,
                asset.state.velocity.vy + (settings.GRAVITY_ACCELERATION * delta)
            )

            # 2. Inverted Hitbox Check: Retain in freefall while intersecting lower-tier obstacles
            retained_by_span = False
            if lower_obs_prims:
                probe = [
                    asset.primitive(
                        0,
                        hitboxes=asset.hitbox.get(asset.properties, asset.state, target_e, asset.frame)
                    )
                ]
                if physics.collisions(probe + [
                    (idx + 1, p[1], p[2], p[3], p[4], p[5])
                    for idx, p in enumerate(lower_obs_prims)
                ], grid):
                    retained_by_span = True

            # 3. Release onto target elevation when clear of lower-tier obstacle span
            if not retained_by_span:
                asset.elevation = target_e
                if target_e == 0 or sub_i in supported_sub_indices:
                    asset.state.mutators.triggers.falling = False
                    asset.state.velocity.vy = 0.0

    return falling_indices

```

##### Tasks

**1. Task: State Triggers & Gravity Configuration Constants**

*Objective*: Register the `falling` trigger on `MutatorTriggers` and define gravitational constants in `settings.py`.

* [ ] Subtask: Add `falling: bool = False` to `MutatorTriggers` in `src/app/models/state/core.py`.
* [ ] Subtask: Add `GRAVITY_ACCELERATION`, `TERMINAL_VELOCITY`, and `TIER_DROP_HEIGHT` constants to `src/app/config/settings.py`.

**2. Task: Locomotion & Friction Suppression During Freefall**

*Objective*: Prevent input polling, NPC steering, and tile friction from overwriting vertical freefall velocity.

* [ ] Subtask: Update `kinematic.update()` in `src/app/game/logic/modules/motion/kinematic.py` to skip entities with `asset.state.mutators.triggers.falling == True`.
* [ ] Subtask: Update `motive.update()` in `src/app/game/logic/modules/motion/motive.py` to skip entities with `asset.state.mutators.triggers.falling == True`.
* [ ] Subtask: Update `frictive.update()` in `src/app/game/logic/modules/motion/frictive.py` to skip entities with `asset.state.mutators.triggers.falling == True`.

**3. Task: Gravity Field & Inverted Hitbox Span Resolution**

*Objective*: Implement elevated support detection, downward gravitational acceleration, and lower-tier hitbox release in `fields.py`.

* [ ] Subtask: Implement `_extract_elevated_support_primitives(board, layer, elevation)` in `src/app/game/logic/modules/motion/fields.py` covering `Platforms`, `Stairs`, and elevated sensor `Struts`.
* [ ] Subtask: Implement `_update_gravity()` in `src/app/game/logic/modules/motion/fields.py` to transition unsupported entities at `elevation > 0` into `falling`, integrate `vy += GRAVITY_ACCELERATION * delta`, and evaluate lower-elevation obstacle hitbox retention using `Space` broad-phase and `geometry.intersects` narrow-phase checks.
* [ ] Subtask: Filter `falling_indices` out of the subsequent bridge, shoreline, and fluid passes in `fields.update()` until the entity lands on `elevation == 0`.

**4. Task: CollisionMechanics Freefall & Ledge Integration**

*Objective*: Allow dynamic entities on elevated tiers to cross un-walled drop-off ledges and bypass solid collision resolution while falling.

* [ ] Subtask: Update `CollisionMechanics.update()` in `src/app/game/logic/mechanics/spatial/collision.py` to exclude entities with `w.state.mutators.triggers.falling == True` from Phase 0 stair transitions, Phase 1 boundary constraints, and Phase 2 solid collision resolution.
* [ ] Subtask: Restrict Phase 1 `CollisionMechanics._boundary` constraint solving to `elevation == 0` (preserving `board.perimeters[layer][elevation]` for `NavigationMechanics` LOS/RRT queries while allowing physical entities to walk or be pushed off open elevated ledges).

**5. Task: Gravity & Freefall Regression Suite**

*Objective*: Verify freefall initiation, inverted hitbox span traversal, and landing resolution across unit and integration tests.

* [ ] Subtask: Add unit test in `tests/unit/app/game/logic/test_gravity.py` asserting an entity stepping off an elevated `Platform` or `Strut` sets `mutators.triggers.falling = True` and accelerates in $+Y$.
* [ ] Subtask: Add unit test asserting a falling entity overlapping a Tier `0` platform/wall hitbox remains at `elevation = 1` with `falling = True` until its hitbox clears the southern edge of the Tier `0` hitbox.
* [ ] Subtask: Add unit test asserting landing on `elevation = 0` resets `falling = False`, zeroes `velocity.vy`, and restores normal `Tier 0` collision obstruction.