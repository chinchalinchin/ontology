#### Refactor: Phase 03.06 : Perimeter Containment

**Overview** 

Resolves **Bug NEW-02** and **Bug B053 (Item 3)** by restoring directed outward normals across `geometry.contours` -> `Boundary` -> `physics.constrain`, correcting the 1px north/west interior contour encroachment, reordering `CollisionMechanics` boundary clamping after Phase 2 collisions, and separating walkable floor hulls from visual canopies and interior solid obstacles in `Perimeter.extract`.

##### Specification

1. **Contour Placement (Outside Walkable Union)**: Given walkable union $\mathcal{U} = \bigcup_i [x_{i,\min}, x_{i,\max}) \times [y_{i,\min}, y_{i,\max})$, 1px perimeter segments sit strictly outside $\mathcal{U}$:
   * `Directions.LEFT`: `(x - 1, y1, 1, y2 - y1, Directions.LEFT)` — outward normal $(-1, 0)$, inward push $(+1, 0)$.
   * `Directions.RIGHT`: `(x, y1, 1, y2 - y1, Directions.RIGHT)` — outward normal $(+1, 0)$, inward push $(-1, 0)$.
   * `Directions.UP`: `(x1, y - 1, x2 - x1, 1, Directions.UP)` — outward normal $(0, -1)$, inward push $(0, +1)$.
   * `Directions.DOWN`: `(x1, y, x2 - x1, 1, Directions.DOWN)` — outward normal $(0, +1)$, inward push $(0, -1)$.
2. **Directed Half-Plane Containment (`physics.constrain`)**: When an entity hitbox `[hx1, hx2) x [hy1, hy2)` intersects a directed boundary `B`:
   * Displacement pushes strictly along the **inward normal** (never outward, regardless of center crossover):
     * `LEFT`: `pos.x += (b_x + b_w) - hx1`
     * `RIGHT`: `pos.x -= hx2 - b_x`
     * `UP`: `pos.y += (b_y + b_l) - hy1`
     * `DOWN`: `pos.y -= hy2 - b_y`
   * Velocity reflection only triggers when velocity points outward (`v · n_out > 0`), and `pos.rx` / `pos.ry` is cleared on the clamped axis.
3. **Walkable Substrate Extraction (`Perimeter.extract`)**:
   * **Tier 0 ($E = 0$)**: Union strictly over `AssetInstances.ENVIRON` tiles (excludes overhead `CANOPY` tiles and interior solid `OBJECTS`/`CRAFTS` already enforced by Phase 2 collisions).
   * **Elevated Tiers ($E > 0$)**: Union strictly over walkable substrates matching `Field: Gravity` support — elevated `STAIRS` ($e_{\text{base}} + \Delta e = E$), elevated `BRIDGES` ($e_{\text{base}} = E$), and non-obstacle `STRUTS` ($e_{\text{base}} = E$ and $\neg \text{MaterialIndex.is\_obstacle}(\text{blueprint})$) — so `NavigationMechanics` retains accurate elevated ledge boundaries while `CollisionMechanics` continues skipping $E > 0$ clamping to permit freefall.
4. **Collision Phase Order**: In `CollisionMechanics.update`, execute Phase 0 (Stairs) -> Phase 1 (Body-vs-Body Collisions) -> Phase 2 (Tier-0 Perimeter Containment) so body separation cannot push entities across perimeter hulls.

##### Architectural Analysis I

Fixing this cleanly requires coordinated breaking changes across both Cython struct layouts and Python domain services (no backwards-compatibility shims):

* **`libs.core.models.Boundary` (`models.pxd` / `models.pyx`)**: Must gain a C-level normal/direction field (e.g., `cdef public int nx, ny` or `cdef public str orientation` mapped to unit int normals `nx, ny` at construction to avoid string comparisons in `physics.constrain`).
* **`libs.core.math.geometry` (`geometry.pyx`)**: Shifting `entries_v` (`x - 1`) and `entries_h` (`y - 1`) places left/top boundaries at `-1` for origin-aligned maps. `Space.insert` handles negative integers safely via unsigned hash wrap; verify `NavigationMechanics._project` (`navigation.py:456`) still projects inward into `[0, max_w]` when inflated `[-1 - pad_x, pad_x)` overlaps `x = 0`.
* **`SpatialMechanic.constrain` & `physics.boundaries`**: The primitive boundary tuple schema `(i, x, y, w, l)` and `physics.constrain` signature must carry `(nx, ny)` (or `Boundary`) directly into the C solver.
* **`Perimeter.extract` & `MaterialIndex`**: Excluding obstacle `STRUTS` at $E > 0$ requires injecting or passing `MaterialIndex` into `Perimeter` (from `Migrator` / `Board`), avoiding any new global `MaterialIndex()` calls.

##### Goals

###### Goal: Preserve Directed Normals End-to-End

```python
# Boundary model (Cython cdef class in models.pxd / models.pyx)
cdef class Boundary:
    cdef public Position position
    cdef public Dimensions dimensions
    cdef public int nx  # Outward unit normal X in {-1, 0, 1}
    cdef public int ny  # Outward unit normal Y in {-1, 0, 1}

# physics.constrain (directed containment)
if nx < 0:    # LEFT wall -> push right (+x)
    shift = (b_x + b_w) - (pos.x + hb.position.x)
    if shift > 0: pos.x += shift; pos.rx = 0.0
    if vel is not None and not is_kinematic and vel.vx < 0: vel.vx = -vel.vx
elif nx > 0:  # RIGHT wall -> push left (-x)
    shift = (pos.x + hb.position.x + hb.dimensions.w) - b_x
    if shift > 0: pos.x -= shift; pos.rx = 0.0
    if vel is not None and not is_kinematic and vel.vx > 0: vel.vx = -vel.vx
# Symmetric handling for ny < 0 (UP) and ny > 0 (DOWN)
```

###### Goal: Decouple Walkable Hulls from Visual Canopy and Interior Blockers

Ensure `Perimeter.extract` represents strictly the *playable surface exterior* for each elevation tier: `ENVIRON` only at $E = 0$, and `{walkable STRUTS, STAIRS, BRIDGES}` at $E > 0$, removing the redundant and lossy static-object union pass.

##### Tasks

**1. Task: Extend `Boundary` and Fix Contour Edge Alignment**

*Objective*: Carry outward unit normals from `geometry.contours` through `Boundary` and place all four contour edges outside the walkable union.

* [] Subtask: Add outward normal fields (`nx`, `ny`) or `orientation` to `Boundary` in `src/libs/core/models.pxd` and `src/libs/core/models.pyx` and update all `Boundary(...)` call sites and unit tests.
* [] Subtask: Update `geometry.contours` in `src/libs/core/math/geometry.pyx` to offset `entries_v` to `x - 1` and `entries_h` to `y - 1` so left/top 1px segments sit outside the walkable footprint.
* [] Subtask: Update `Perimeter.generate` in `src/app/services/generators/game/perimeter.py` to map the 5th contour tuple element (`orientation`) into `Boundary` outward normals instead of discarding it via `*_`.

**2. Task: Implement Directed Half-Plane Containment & Reorder Collision Phases**

*Objective*: Prevent boundary ejection and post-collision perimeter tunneling.

* [] Subtask: Update `physics.constrain` in `src/libs/core/math/physics.pyx` to accept outward normal `(nx, ny)`, clamp overlap strictly inward, guard velocity reflection by outward motion (`v · n_out > 0`), and clear `pos.rx` / `pos.ry`.
* [] Subtask: Update `CollisionMechanics._boundary` to pass `boundary.nx, boundary.ny` to `physics.constrain`.
* [] Subtask: Reorder `CollisionMechanics.update` so Tier-0 perimeter containment executes *after* body-vs-body collisions, preventing Phase 2 separation from pushing entities out of bounds.

**3. Task: Clean Walkable Substrate Extraction in `Perimeter.extract`**

*Objective*: Resolve B053.3 while preserving elevated ledge perimeters for `NavigationMechanics`.

* [] Subtask: Remove `AssetInstances.CANOPY` from Tier-0 extraction in `Perimeter.extract` so overhead canopies do not inflate walkable bounds.
* [] Subtask: Remove Step 3's absorption of interior `OBJECTS` and obstacle `CRAFTS` into the contour union; restrict Step 2 ($E > 0$) to walkable `STRUTS` (via `MaterialIndex.is_obstacle`), `STAIRS`, and `BRIDGES` (scaling by `multiple`).
* [] Subtask: Add unit and integration tests covering corner pushing against Tier-0 perimeters, negative-edge projection in `NavigationMechanics._project`, and elevated platform + bridge navigation perimeters.