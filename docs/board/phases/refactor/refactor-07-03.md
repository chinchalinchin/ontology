#### Refactor: Phase 07.03: Gravity

**Overview** 

Establishes a geometric gravitational field in `MotionMechanics` (`fields.py`) derived from the LPC $60^\circ$ orthographic projection triangle. When a dynamic Asset ($m > 0$) at elevation $E > 0$ is no longer supported by an elevated substrate at tier $E$, it enters freefall (`falling = True`) and accelerates downward ($+Y$). For every $\Delta y_{\text{tier}} = U \tan(60^\circ)$ pixels of vertical descent, the engine decrements the entity's elevation by one discrete tier ($E \to E - 1$) and re-evaluates substrate support at the new tier—allowing entities to fall from $E = 3$ onto $E = 2$ (or any intermediate tier $E > 0$) without coupling gravity to lower-tier Asset hitboxes.

According to the *Liberated Pixel Cup Style Guide* (OpenGameArt.org, dual-licensed CC-BY-SA 3.0 / GPLv3), LPC assets are authored to two spatial specifications:

1. **Base Grid Quantum ($U$):** $32 \times 32\text{ px}$ unit tiles (with $16 \times 16\text{ px}$ sub-tiles).
2. **Camera Angle ($\theta$):** Top-down **orthographic projection** at a pitch angle of $\theta = 60^\circ$ ($\frac{\pi}{3}\text{ rad}$) relative to the horizontal ground plane.

##### Prior Analysis

Let world space be parameterized by $(X, Y, Z)$, where $(X, Y)$ spans the horizontal ground plane ($E = 0$) and $Z \ge 0$ is the vertical elevation axis perpendicular to the ground plane:

1. **Assumption 1 (Orthographic Parallelism):** Camera rays are parallel and intersect the horizontal ground plane $(X, Y)$ at a constant inclination angle $\theta = 60^\circ$.
2. **Assumption 2 (Right Triangle Formation):** For a point at discrete elevation tier $E$ dropping by $\Delta E = 1$ tier to $E - 1$, the vertical elevation leg ($\Delta z$), the horizontal ground leg ($\Delta y$), and the camera line-of-sight ray ($L_{\text{LOS}}$) form a right triangle $\triangle$ with right angle at the base of the vertical leg and acute angle $\theta = 60^\circ$ at the ground intercept:

$$\tan(\theta) = \frac{\Delta z}{\Delta y}, \qquad \sin(\theta) = \frac{\Delta z}{L_{\text{LOS}}}, \qquad \cos(\theta) = \frac{\Delta y}{L_{\text{LOS}}}$$

3. **Deduction of Per-Tier Screen Drop ($\Delta y_{\text{tier}}$):**

- Taking the horizontal ground run of one unit tile as the adjacent leg ($\Delta y = U = 32\text{ px}$), the vertical leg opposite $\theta = 60^\circ$ (the screen-space $+y$ height of one elevation tier) is:

$$\Delta y_{\text{tier}} = U \cdot \tan(60^\circ) = 32\sqrt{3} \approx 55.43\text{ px}$$

- Equivalently, taking the line-of-sight hypotenuse across a two-tile sprite frame ($L_{\text{LOS}} = 2U = 64\text{ px}$) yields the same opposite vertical leg:

$$\Delta y_{\text{tier}} = L_{\text{LOS}} \cdot \sin(60^\circ) = 64 \cdot \frac{\sqrt{3}}{2} = 32\sqrt{3} \approx 55.43\text{ px}$$

Under this formulation, gravity is purely a property of the topological elevation planes $E \in \mathbb{Z}$: every $\Delta y_{\text{tier}} = U \tan(\theta)$ pixels of vertical freefall transitions the entity down one discrete elevation plane ($E \to E - 1$), where support is re-evaluated immediately.

##### Specification

| Component / System | State / Field / Method | Responsibility |
| --- | --- | --- |
| **`settings.py`** | `PERSPECTIVE_ANGLE_DEG = 60.0, TIER_DROP_DISTANCE = int(TILE_HASH_SIZE * math.tan(math.radians(60.0))), GRAVITY_ACCELERATION = 400.0, TERMINAL_VELOCITY = 350.0` | Computes the per-tier vertical drop ($\lfloor 32\sqrt{3} \rfloor = 55\text{ px}$) from the LPC $60^\circ$ camera triangle and defines freefall kinematics. |
| **`MutatorTriggers`** | `falling: bool = False` | Flags an entity as airborne and subject to gravitational acceleration. |
| **`Mutators` / State** | `descension: float = 0.0` | Accumulates downward $+Y$ pixel displacement during freefall to trigger discrete $E \to E - 1$ tier transitions at each $\Delta y_{\text{tier}}$ interval. |
| **`MotionModules` & `NavigationMechanics`** | `kinematic`, `motive`, `frictive`, `navigation` | Suppresses voluntary input velocity clamping, NPC steering (prior to idle velocity zeroing), tile friction decay, and RRT pathfinding while `falling == True`. |
| **`fields.py`** | `_update_gravity(l_assets, board, layer, delta)` | Executes at Step 0 of `fields.update()`. Evaluates substrate support at $E > 0$ via Cython `geometry.occluded`, integrates $v_y \mathrel{+}= g \cdot \Delta t$, steps $E \to E - 1$ per $\Delta y_{\text{tier}}$ with exact landing remainder clamping, and halts freefall upon reaching a supported tier ($E \ge 0$). |
| **`CollisionMechanics`** | `update()` | Restricts Phase 1 perimeter containment to `elevation == 0` so entities can cross un-walled ledges at $E > 0$, and bypasses Phase 0 stair traversal and Phase 2 solid collisions while `falling == True`. |

##### Architectural Analysis I

1. **Decoupling Gravity from Lower-Elevation Hitboxes**: Elevations $E \in \mathbb{Z}$ are topological planes rather than attributes of obstacle hitboxes. By deriving $\Delta y_{\text{tier}} = U \tan(\theta)$ from the camera projection angle ($\theta = 60^\circ$) and unit grid scale ($U = 32\text{ px}$), the vertical distance required to transition from plane $E$ to plane $E - 1$ is invariant across all Asset categories.
2. **Multi-Tier Step-Down & Intermediate Landing ($E_n \to E_{n-1}$)**: In `castle-atrium-layer-3`, `platform-04` is deployed at `Position(0, 0)` with `elevation = 1` (walkable deck at $E = 2$, $y \in [0, 111]$), directly above `platform-01` at `Position(0, 136)` with `elevation = 0` (walkable deck at $E = 1$, $y \in [136, 247]$).
   * When an entity at $E = 2$ steps South off `platform-04` ($y > 111$), it is unsupported at $E = 2$ and enters freefall (`falling = True`).
   * After descending $\Delta y_{\text{tier}} = 55\text{ px}$ ($y \approx 166$), `descension >= TIER_DROP_DISTANCE` triggers $E: 2 \to 1$ and decrements `descension -= TIER_DROP_DISTANCE`.
   * The engine immediately checks support at the new tier $E = 1$. Because $(x, 166)$ lies inside `platform-01`'s $E = 1$ surface ($y \in [136, 247]$), the entity lands on $E = 1$ (`falling = False`, `vy = 0.0`) without falling to $E = 0$.
   * Conversely, if the entity steps off an $E = 2$ ledge into open space with no $E = 1$ substrate below, the support check at $E = 1$ returns `False`; the entity retains its downward velocity $v_y$ and falls an additional $\Delta y_{\text{tier}}$ until it reaches $E = 0$.
3. **Coplanar Overlap Resolution on Landing**: While `falling == True`, the entity is between discrete elevation planes and bypasses `CollisionMechanics`. The moment `falling` transitions to `False` on a supported tier $E$, the entity re-enters `CollisionMechanics` at tier $E$, where any minor coplanar hitbox overlap at the landing coordinate is resolved via standard inverse-mass separation (`physics.collide`).

##### Architectural Analysis II

1. **Path to Deprecating `Platforms` Without Per-Frame Footprint Generation**:
   * In Ontology's Composition model, elevated structures consist of supporting `Struts` (`walls`, `columns`, `enclosures`) at $E - 1$, walkable surface `Struts` (`flats`, `floors`, `paths`, `corridors`) or `Bridges` at $E > 0$, and `Stairs` spanning $[E - 1, E]$.
   * To prevent entities at $E = 0$ from walking "underneath" solid elevated surfaces at $E > 0$ while still permitting hollow overpasses (`Bridges`), no per-frame footprint generation is needed: static `Struts` never move during the game loop. Walkable surface `Struts` (`not MaterialIndex().is_obstacle(blueprint)`) deployed at $E > 0$ emit `[]` at $e_{\text{query}} = E$ (walkable deck) and can project their static bounding box onto lower tiers $0 \le e_{\text{query}} < E$ in `MaterialHitbox` (solid mass below), while `Bridges` use `NoHitbox` so entities at $E = 0$ pass underneath freely.
2. **Zero-Allocation Support Evaluation via `geometry.occluded` (Eliminating `physics.environment` Overhead)**:
   * Invoking `physics.environment([asset.primitive(0)], support_prims, grid)` per elevated entity resets and scans all 4,000 buckets of the Cython `Space` grid every call.
   * Instead, `_extract_tier_support_aabbs(board, layer, elevation)` extracts raw 4-integer AABB tuples `(ox, oy, ow, ol)` for static walkable substrates at tier $E$ (`Platforms`, full-tread `Stairs` bounding boxes, `Bridges`, and passable surface `Struts`), and `_is_supported_at_tier` delegates directly to Cython's zero-allocation `geometry.occluded(qx, qy, qw, ql, support_aabbs)` (`src/libs/core/math/geometry.pyx:270`).
3. **Full-Tread `Stairs` Support**:
   * `Stairs` hitboxes (`craft.hitboxes`) define lateral side railings rather than the walkable tread between them, and `CollisionMechanics._traverse_stairs` promotes an ascending entity's elevation to `e_top` at `tread_progress <= 0.85` (near the bottom of the incline). Therefore, `Stairs` must contribute their full bounding footprint `(sx, sy, craft.dimensions.w, craft.dimensions.l)` to the support AABBs for all tiers $E \in [e_{\text{base}} + 1, e_{\text{base}} + \Delta e]$ so entities climbing or descending stairs are never flagged as unsupported mid-incline.
4. **Synchronizing `descension` with `physics.integrate` via Remainder Clamping**:
   * Because `fields.update()` executes prior to `physics.integrate()`, zeroing `velocity.vy` upon reaching `TIER_DROP_DISTANCE` before `physics.integrate()` runs would rob the entity of its final frame of vertical displacement, while allowing `physics.integrate()` to apply an unclamped `dy` would overshoot `TIER_DROP_DISTANCE`.
   * When `descension + dy >= TIER_DROP_DISTANCE`, `_update_gravity` computes the exact pixel remainder $\Delta y_{\text{rem}} = \text{TIER\_DROP\_DISTANCE} - \text{fall\_distance}$ and advances `position.y` to the exact geometric intercept of plane $E - 1$ prior to evaluating `_is_supported_at_tier`. If supported at $E - 1$, `velocity.vy` and `position.ry` are zeroed so `physics.integrate()` preserves the exact $k \times \text{TIER\_DROP\_DISTANCE}$ landing coordinate; if unsupported, the entity retains `velocity.vy` and integrates seamlessly across the intermediate plane.

##### Goals

###### Goal: Elevated Substrate Support Evaluation

An entity at elevation $E > 0$ is supported if its physical footprint intersects any walkable substrate occupying tier $E$ on the active layer (`Platforms` projecting a tier at $E$, `Stairs` spanning $E$, `Bridges` at $E$, or passable surface `Struts` deployed at $E$), evaluated via Cython's zero-allocation `geometry.occluded`:

```python
def _extract_tier_support_aabbs(
    board: Board,
    layer: str,
    elevation: int
) -> List[Tuple[int, int, int, int]]:
    """
    Extracts primitive (x, y, w, l) AABB tuples for all walkable substrates
    at discrete elevation tier E > 0.
    """
    aabbs: List[Tuple[int, int, int, int]] = []
    for craft in board.categories(AssetCategories.CRAFTS.value, layer):
        inst = craft.taxonomy.instance
        base_e = craft.elevation

        # TODO: remove: platforms are deprecated.
        if inst == AssetInstances.PLATFORMS.value:
            if elevation > base_e and elevation in craft.hitbox.elevations(craft.properties, craft.state):
                aabbs.append((
                    int(craft.state.position.x),
                    int(craft.state.position.y),
                    int(craft.dimensions.w),
                    int(craft.dimensions.l)
                ))

        elif inst == AssetInstances.STAIRS.value:
            # Use full stair tread bounds so ascending/descending entities remain supported
            if base_e < elevation <= base_e + craft.state.delta:
                aabbs.append((
                    int(craft.state.position.x),
                    int(craft.state.position.y),
                    int(craft.dimensions.w),
                    int(craft.dimensions.l)
                ))

        elif inst == AssetInstances.BRIDGES.value:
            if base_e == elevation:
                aabbs.append((
                    int(craft.state.position.x),
                    int(craft.state.position.y),
                    int(craft.dimensions.w),
                    int(craft.dimensions.l)
                ))

        elif inst == AssetInstances.STRUTS.value:
            # Support both sensor struts (mass < 0) and passable surface blueprints at tier E
            if base_e == elevation and (
                getattr(craft.properties, "mass", 0) < 0
                or not craft.hitbox.elevations(craft.properties, craft.state)
            ):
                aabbs.append((
                    int(craft.state.position.x),
                    int(craft.state.position.y),
                    int(craft.dimensions.w),
                    int(craft.dimensions.l)
                ))

    return aabbs


def _is_supported_at_tier(
    asset: Asset,
    elevation: int,
    support_cache: Dict[int, List[Tuple[int, int, int, int]]],
    board: Board,
    layer: str
) -> bool:
    """
    Returns True if any active hitbox (or bounding box) of the asset overlaps
    a walkable substrate AABB at the given elevation tier.
    Tier 0 (base terrain) is unconditionally supported.
    """
    if elevation <= 0:
        return True
    if elevation not in support_cache:
        support_cache[elevation] = _extract_tier_support_aabbs(board, layer, elevation)
    support_aabbs = support_cache[elevation]
    if not support_aabbs:
        return False

    ax = int(asset.state.position.x)
    ay = int(asset.state.position.y)
    hbs = asset.hitbox.get(asset.properties, asset.state, asset.elevation, asset.frame)
    if hbs:
        for hb in hbs:
            if geometry.occluded(
                ax + hb.position.x,
                ay + hb.position.y,
                hb.dimensions.w,
                hb.dimensions.l,
                support_aabbs
            ):
                return True
        return False

    return bool(
        geometry.occluded(ax, ay, asset.dimensions.w, asset.dimensions.l, support_aabbs)
    )

```

###### Goal: Trigonometric Tier Stepping & Multi-Elevation Freefall

In `fields.py`, `_update_gravity` executes at Step 0 of `fields.update()`, integrates downward gravitational acceleration, steps $E \to E - 1$ per `settings.TIER_DROP_DISTANCE`, and clamps landing displacement so entities land at exact $\Delta y_{\text{tier}}$ multiples:

```python
def _update_gravity(
    l_assets: List[Asset],
    board: Board,
    layer: str,
    delta: float
) -> set[int]:
    """
    Evaluates elevated support, accelerates unsupported entities downward (+Y),
    and decrements elevation E -> E - 1 per geometric TIER_DROP_DISTANCE.
    """
    falling_indices: set[int] = set()
    support_cache: Dict[int, List[Tuple[int, int, int, int]]] = {}

    for i, asset in enumerate(l_assets):
        if asset.elevation <= 0 and not asset.state.mutators.triggers.falling:
            continue

        is_falling = asset.state.mutators.triggers.falling

        # 1. Check if entity at E > 0 has stepped off its supporting substrate
        if not is_falling:
            if not _is_supported_at_tier(asset, asset.elevation, support_cache, board, layer):
                asset.state.mutators.triggers.falling = True
                asset.state.mutators.descension = 0.0
                asset.state.position.ry = 0.0
                asset.state.velocity.vx = 0.0
                asset.state.velocity.vy = max(0.0, asset.state.velocity.vy)
                is_falling = True

        if not is_falling:
            continue

        # 2. Integrate constant gravitational acceleration (+Y)
        asset.state.velocity.vx = 0.0
        asset.state.velocity.vy = min(
            settings.TERMINAL_VELOCITY,
            asset.state.velocity.vy + (settings.GRAVITY_ACCELERATION * delta)
        )

        # Compute integer vertical step matching physics.integrate sub-pixel accumulation
        total_ry = asset.state.position.ry + (asset.state.velocity.vy * delta)
        step_y = int(total_ry)
        rem_to_tier = int(settings.TIER_DROP_DISTANCE - asset.state.mutators.descension)

        # 3. Evaluate discrete tier transitions (E -> E - 1)
        if step_y >= rem_to_tier and asset.elevation > 0:
            # Advance to exact geometric intercept of plane E - 1 to test landing support
            orig_y = asset.state.position.y
            asset.state.position.y = orig_y + rem_to_tier
            asset.elevation -= 1

            if _is_supported_at_tier(asset, asset.elevation, support_cache, board, layer):
                # Landed on supported plane E - 1: clamp exact drop and zero velocity
                asset.state.mutators.triggers.falling = False
                asset.state.mutators.descension = 0.0
                asset.state.position.ry = 0.0
                asset.state.velocity.vy = 0.0
            else:
                # Unsupported at intermediate plane: restore y for full physics.integrate step
                asset.state.position.y = orig_y
                asset.state.mutators.descension = float(step_y - rem_to_tier)
                falling_indices.add(i)
        else:
            asset.state.mutators.descension += float(step_y)
            falling_indices.add(i)

    return falling_indices

```

##### Tasks

**1. Task: Trigonometric Gravity Constants & Freefall State**

*Objective*: Define perspective-derived gravitational constants in `settings.py` and add freefall state tracking to `Mutators`.

* [x] Subtask: Add `PERSPECTIVE_ANGLE_DEG = 60.0`, `TIER_DROP_DISTANCE = int(TILE_HASH_SIZE * math.tan(math.radians(PERSPECTIVE_ANGLE_DEG)))`, `GRAVITY_ACCELERATION = 400.0`, and `TERMINAL_VELOCITY = 350.0` to `src/app/static/settings.py`.
* [x] Subtask: Add `falling: bool = False` to `MutatorTriggers` and `descension: float = 0.0` to `Mutators` in `src/app/models/state/core.py`.

**2. Task: Locomotion, Friction & Navigation Suppression During Freefall**

*Objective*: Prevent voluntary input polling, NPC steering, idle velocity zeroing, tile friction decay, and RRT pathfinding from overriding gravitational velocity or thrashing while an entity is airborne.

* [ ] Subtask: Gate `kinematic.update()` in `src/app/game/logic/modules/motion/kinematic.py` at the top of the loop to skip entities with `player.state.mutators.triggers.falling == True`.
* [ ] Subtask: Gate `motive.update()` in `src/app/game/logic/modules/motion/motive.py` at the very top of the loop (strictly before the `if not sprite.state.goal` velocity reset) to skip entities with `sprite.state.mutators.triggers.falling == True`.
* [ ] Subtask: Gate `frictive.update()` in `src/app/game/logic/modules/motion/frictive.py` at the top of the loop to skip entities with `asset.state.mutators.triggers.falling == True`.
* [ ] Subtask: Gate `NavigationMechanics._navigate()` in `src/app/game/logic/mechanics/intentional/navigation.py` to skip path maintenance when `sprite.state.mutators.triggers.falling == True`.

**3. Task: Geometric Gravity Field & Multi-Tier Landing Resolution**

*Objective*: Implement zero-allocation elevated substrate support detection and trigonometric tier-stepped freefall in `fields.py`.

* [ ] Subtask: Implement `_extract_tier_support_aabbs()` and `_is_supported_at_tier()` using `geometry.occluded` in `src/app/game/logic/modules/motion/fields.py`, covering `Platforms`, full-tread `Stairs`, `Bridges`, and passable surface `Struts`.
* [ ] Subtask: Implement `_update_gravity()` at Step 0 of the per-layer loop in `src/app/game/logic/modules/motion/fields.py` to trigger freefall when unsupported at $E > 0$, accumulate integer drop displacement synchronized with `position.ry`, clamp landing steps to exact `TIER_DROP_DISTANCE` multiples, and halt freefall when `_is_supported_at_tier()` succeeds at $E \ge 0$.
* [ ] Subtask: Filter `falling_indices` out of subsequent bridge/raft, shoreline, and fluid passes in `fields.update()`, while allowing entities that landed at $E = 0$ on the current tick (`falling == False`) to proceed immediately into surface and fluid evaluation.

**4. Task: CollisionMechanics Ledge & Airborne Integration**

*Objective*: Allow dynamic entities to cross un-walled elevated ledges and bypass solid collisions while airborne.

* [ ] Subtask: Restrict Phase 1 `CollisionMechanics._boundary` enforcement in `src/app/game/logic/mechanics/spatial/collision.py` to `elevation == 0` so `board.perimeters` at $E > 0$ remain available to `NavigationMechanics` without trapping dynamic bodies on open ledges.
* [ ] Subtask: Filter entities with `w.state.mutators.triggers.falling == True` out of Phase 0 stair traversal (`movers`) and Phase 2 solid collision resolution (`tier_weights`) in `CollisionMechanics.update()`.

**5. Task: Multi-Tier Gravity Regression Suite**

*Objective*: Verify trigonometric drop distance, stair ascent support, intermediate elevation landing ($E = 2 \to 1$), and ground landing ($E = 1 \to 0$).

* [!: Dependent on User Acceptance Testing] Subtask: Add unit test in `tests/unit/app/game/logic/test_gravity.py` verifying an unsupported entity at $E = 1$ falls exactly `TIER_DROP_DISTANCE` ($\lfloor 32 \tan 60^\circ \rfloor = 55\text{ px}$) before transitioning to $E = 0$ and clearing `falling`.
* [!: Dependent on User Acceptance Testing] Subtask: Add unit test verifying an entity stepping off an $E = 2$ platform onto an underlying $E = 1$ platform transitions $E: 2 \to 1$ after `TIER_DROP_DISTANCE` pixels and lands at $E = 1$ without dropping to $E = 0$.
* [!: Dependent on User Acceptance Testing] Subtask: Add unit test verifying an entity stepping off an $E = 2$ platform with no $E = 1$ support underneath falls continuously through $E = 1$ and lands at $E = 0$ after $2 \times \text{TIER\_DROP\_DISTANCE}$ (`110 px`).
* [!: Dependent on User Acceptance Testing] Subtask: Add unit test verifying an entity ascending `Stairs` from $E = 0 \to 1$ remains supported by the stair tread bounding box after `_traverse_stairs` transitions its elevation to $E = 1$.