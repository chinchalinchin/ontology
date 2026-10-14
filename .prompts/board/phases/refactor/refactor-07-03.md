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
* Taking the horizontal ground run of one unit tile as the adjacent leg ($\Delta y = U = 32\text{ px}$), the vertical leg opposite $\theta = 60^\circ$ (the screen-space $+y$ height of one elevation tier) is:

$$\Delta y_{\text{tier}} = U \cdot \tan(60^\circ) = 32\sqrt{3} \approx 55.43\text{ px}$$

* Equivalently, taking the line-of-sight hypotenuse across a two-tile sprite frame ($L_{\text{LOS}} = 2U = 64\text{ px}$) yields the same opposite vertical leg:

$$\Delta y_{\text{tier}} = L_{\text{LOS}} \cdot \sin(60^\circ) = 64 \cdot \frac{\sqrt{3}}{2} = 32\sqrt{3} \approx 55.43\text{ px}$$

Under this formulation, gravity is purely a property of the topological elevation planes $E \in \mathbb{Z}$: every $\Delta y_{\text{tier}} = U \tan(\theta)$ pixels of vertical freefall transitions the entity down one discrete elevation plane ($E \to E - 1$), where support is re-evaluated immediately.

##### Specification

| Component / System | State / Field / Method | Responsibility |
| --- | --- | --- |
| **`settings.py`** | `PERSPECTIVE_ANGLE_DEG = 60.0, TIER_DROP_DISTANCE = int(TILE_HASH_SIZE * math.tan(math.radians(60.0))), GRAVITY_ACCELERATION = 400.0, TERMINAL_VELOCITY = 350.0` | Computes the per-tier vertical drop ($\approx 55\text{ px}$) from the LPC $60^\circ$ camera triangle and defines freefall kinematics. |
| **`MutatorTriggers`** | `falling: bool = False` | Flags an entity as airborne and subject to gravitational acceleration. |
| **`Mutators` / State** | `fall_distance: float = 0.0` | Accumulates downward $+Y$ pixel displacement during freefall to trigger discrete $E \to E - 1$ tier transitions at each $\Delta y_{\text{tier}}$ interval. |
| **`MotionModules`** | `kinematic`, `motive`, `frictive` | Suppresses voluntary input velocity clamping, NPC steering, and tile friction decay while `falling == True`. |
| **`fields.py`** | `_update_gravity(l_assets, board, layer, delta, grid)` | Evaluates substrate support at $E > 0$, integrates $v_y \mathrel{+}= g \cdot \Delta t$, steps $E \to E - 1$ per $\Delta y_{\text{tier}}$, and halts freefall upon reaching a supported tier ($E \ge 0$). |
| **`CollisionMechanics`** | `update()` | Restricts Phase 1 perimeter containment to `elevation == 0` so entities can cross un-walled ledges at $E > 0$, and bypasses Phase 2 solid collisions only while `falling == True`. |

##### Architectural Analysis I

1. **Decoupling Gravity from Lower-Elevation Hitboxes**
Elevations $E \in \mathbb{Z}$ are topological planes rather than attributes of obstacle hitboxes. By deriving $\Delta y_{\text{tier}} = U \tan(\theta)$ from the camera projection angle ($\theta = 60^\circ$) and unit grid scale ($U = 32\text{ px}$), the vertical distance required to transition from plane $E$ to plane $E - 1$ is invariant across all Asset categories.
2. **Multi-Tier Step-Down & Intermediate Landing ($E_n \to E_{n-1}$)**
In `castle-atrium-layer-3`, `platform-04` is deployed at `Position(0, 0)` with `elevation = 1` (walkable deck at $E = 2$, $y \in [0, 111]$), directly above `platform-01` at `Position(0, 136)` with `elevation = 0` (walkable deck at $E = 1$, $y \in [136, 247]$).
* When an entity at $E = 2$ steps South off `platform-04` ($y > 111$), it is unsupported at $E = 2$ and enters freefall (`falling = True`).
* After descending $\Delta y_{\text{tier}} \approx 55\text{ px}$ ($y \approx 166$), `fall_distance >= TIER_DROP_DISTANCE` triggers $E: 2 \to 1$ and decrements `fall_distance -= TIER_DROP_DISTANCE`.
* The engine immediately checks support at the new tier $E = 1$. Because $(x, 166)$ lies inside `platform-01`'s $E = 1$ surface ($y \in [136, 247]$), the entity lands on $E = 1$ (`falling = False`, `vy = 0.0`) without falling to $E = 0$.
* Conversely, if the entity steps off an $E = 2$ ledge into open space with no $E = 1$ substrate below, the support check at $E = 1$ returns `False`; the entity retains its downward velocity $v_y$ and falls an additional $\Delta y_{\text{tier}}$ until it reaches $E = 0$.


3. **Coplanar Overlap Resolution on Landing**
While `falling == True`, the entity is between discrete elevation planes and bypasses `CollisionMechanics`. The moment `falling` transitions to `False` on a supported tier $E$, the entity re-enters `CollisionMechanics` at tier $E$, where any minor coplanar hitbox overlap at the landing coordinate is resolved via standard inverse-mass separation (`physics.collide`).

##### Goals

###### Goal: Elevated Substrate Support Evaluation

An entity at elevation $E > 0$ is supported if its footprint intersects any walkable substrate occupying tier $E$ on the active layer (`Platforms` projecting a tier at $E$, `Stairs` spanning $E$, or walkable sensor `Struts` deployed at $E$):

```python
def _extract_tier_support_primitives(
    board: Board,
    layer: str,
    elevation: int
) -> List[Tuple]:
    """
    Extracts broad-phase C-grid primitives for all walkable substrates
    at discrete elevation tier E > 0.
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

###### Goal: Trigonometric Tier Stepping & Multi-Elevation Freefall

In `fields.py`, `_update_gravity` evaluates support per tier, integrates downward gravitational acceleration, and steps $E \to E - 1$ whenever accumulated vertical displacement crosses `settings.TIER_DROP_DISTANCE`:

```python
def _is_supported_at_tier(
    asset: Asset,
    elevation: int,
    support_cache: Dict[int, List[Tuple]],
    board: Board,
    layer: str,
    grid: Space
) -> bool:
    """
    Returns True if the asset is supported at the given elevation tier.
    Tier 0 (base terrain) is unconditionally supported.
    """
    if elevation <= 0:
        return True
    if elevation not in support_cache:
        support_cache[elevation] = _extract_tier_support_primitives(board, layer, elevation)
    support_prims = support_cache[elevation]
    if not support_prims:
        return False
    return bool(physics.environment([asset.primitive(0)], support_prims, grid))


def _update_gravity(
    l_assets: List[Asset],
    board: Board,
    layer: str,
    delta: float,
    grid: Space
) -> set[int]:
    """
    Evaluates elevated support, accelerates unsupported entities downward (+Y),
    and decrements elevation E -> E - 1 per geometric TIER_DROP_DISTANCE.
    """
    falling_indices: set[int] = set()
    support_cache: Dict[int, List[Tuple]] = {}

    for i, asset in enumerate(l_assets):
        if asset.elevation <= 0 and not asset.state.mutators.triggers.falling:
            continue

        is_falling = asset.state.mutators.triggers.falling

        # 1. Check if entity at E > 0 has stepped off its supporting substrate
        if not is_falling:
            if not _is_supported_at_tier(asset, asset.elevation, support_cache, board, layer, grid):
                asset.state.mutators.triggers.falling = True
                asset.state.mutators.fall_distance = 0.0
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
        dy = asset.state.velocity.vy * delta
        asset.state.mutators.fall_distance += dy

        # 3. Step down discrete elevation tiers (E -> E - 1) per TIER_DROP_DISTANCE
        while (
            asset.state.mutators.fall_distance >= settings.TIER_DROP_DISTANCE
            and asset.elevation > 0
        ):
            asset.state.mutators.fall_distance -= settings.TIER_DROP_DISTANCE
            asset.elevation -= 1

            # Re-evaluate support at the newly reached elevation plane
            if _is_supported_at_tier(asset, asset.elevation, support_cache, board, layer, grid):
                asset.state.mutators.triggers.falling = False
                asset.state.mutators.fall_distance = 0.0
                asset.state.velocity.vy = 0.0
                break

        if asset.state.mutators.triggers.falling:
            falling_indices.add(i)

    return falling_indices

```

##### Tasks

**1. Task: Trigonometric Gravity Constants & Freefall State**

*Objective*: Define perspective-derived gravitational constants in `settings.py` and add freefall state tracking to `Mutators`.

* [ ] Subtask: Add `PERSPECTIVE_ANGLE_DEG = 60.0`, `TIER_DROP_DISTANCE = int(TILE_HASH_SIZE * math.tan(math.radians(PERSPECTIVE_ANGLE_DEG)))`, `GRAVITY_ACCELERATION = 400.0`, and `TERMINAL_VELOCITY = 350.0` to `src/app/config/settings.py`.
* [ ] Subtask: Add `falling: bool = False` to `MutatorTriggers` and `fall_distance: float = 0.0` to `Mutators` in `src/app/models/state/core.py`.

**2. Task: Locomotion & Friction Suppression During Freefall**

*Objective*: Prevent voluntary input polling, NPC steering, and tile friction decay from overriding gravitational velocity while an entity is airborne.

* [ ] Subtask: Gate `kinematic.update()` in `src/app/game/logic/modules/motion/kinematic.py` to skip entities with `asset.state.mutators.triggers.falling == True`.
* [ ] Subtask: Gate `motive.update()` in `src/app/game/logic/modules/motion/motive.py` to skip entities with `asset.state.mutators.triggers.falling == True`.
* [ ] Subtask: Gate `frictive.update()` in `src/app/game/logic/modules/motion/frictive.py` to skip entities with `asset.state.mutators.triggers.falling == True`.

**3. Task: Geometric Gravity Field & Multi-Tier Landing Resolution**

*Objective*: Implement elevated substrate support detection and trigonometric tier-stepped freefall in `fields.py`.

* [ ] Subtask: Implement `_extract_tier_support_primitives()` and `_is_supported_at_tier()` in `src/app/game/logic/modules/motion/fields.py`.
* [ ] Subtask: Implement `_update_gravity()` in `src/app/game/logic/modules/motion/fields.py` to trigger freefall when unsupported at $E > 0$, accumulate `fall_distance`, decrement `asset.elevation` every `TIER_DROP_DISTANCE` pixels, and halt freefall as soon as `_is_supported_at_tier()` succeeds at the new elevation $E \ge 0$.
* [ ] Subtask: Exclude `falling_indices` from subsequent bridge, shoreline, and fluid field passes in `fields.update()`.

**4. Task: CollisionMechanics Ledge & Airborne Integration**

*Objective*: Allow dynamic entities to cross un-walled elevated ledges and bypass solid collisions while airborne.

* [ ] Subtask: Restrict Phase 1 `CollisionMechanics._boundary` enforcement in `src/app/game/logic/mechanics/spatial/collision.py` to `elevation == 0` so `board.perimeters` at $E > 0$ remain available to `NavigationMechanics` without trapping dynamic bodies on open ledges.
* [ ] Subtask: Filter entities with `w.state.mutators.triggers.falling == True` out of Phase 0 stair traversal and Phase 2 solid collision resolution in `CollisionMechanics.update()`.

**5. Task: Multi-Tier Gravity Regression Suite**

*Objective*: Verify trigonometric drop distance, intermediate elevation landing ($E = 2 \to 1$), and ground landing ($E = 1 \to 0$).

* [ ] Subtask: Add unit test in `tests/unit/app/game/logic/test_gravity.py` verifying an unsupported entity at $E = 1$ falls exactly `TIER_DROP_DISTANCE` ($\lfloor 32 \tan 60^\circ \rfloor = 55\text{ px}$) before transitioning to $E = 0$ and clearing `falling`.
* [ ] Subtask: Add unit test verifying an entity stepping off an $E = 2$ platform onto an underlying $E = 1$ platform transitions $E: 2 \to 1$ after `TIER_DROP_DISTANCE` pixels and lands at $E = 1$ without dropping to $E = 0$.
* [ ] Subtask: Add unit test verifying an entity stepping off an $E = 2$ platform with no $E = 1$ support underneath falls continuously through $E = 1$ and lands at $E = 0$ after $2 \times \text{TIER\_DROP\_DISTANCE}$ pixels.