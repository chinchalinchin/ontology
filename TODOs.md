### Analysis: Code Review

##### Review: Collision Workflow (`app.assets.hitboxes`, `app.game.logic.mechanics.spatial`, `libs.core.math`)

###### Overview

The collision subsystem partitions spatial responsibility cleanly across three layers: stateless `HitboxSchema` strategies on `Asset` instances, broad-phase orchestration in `SpatialMechanic` / `CollisionMechanics`, and C-level broad/narrow-phase execution in `libs.core.math` (`space.pyx`, `geometry.pyx`, `physics.pyx`). However, several implementation defects, schema-to-code divergences, and broad-phase bounding assumptions degrade correctness and performance under edge conditions.

###### Review: Implementation

* **Ignored Elevation Parameter in Spatial Resolution**: `SpatialMechanic.collisions()`, `SpatialMechanic.constrain()`, `CollisionMechanics._boundary()`, and `CollisionMechanics._resolve()` accept an `elevation` parameter but invoke `asset.hitboxes` (which is pinned to `asset.elevation`) instead of `asset.hitbox.get(asset.properties, asset.state, elevation)`. This causes multi-elevation assets (`ElevatedHitbox`) and mismatched-elevation queries to evaluate against the wrong elevation plane.
* **Broad-Phase Insertion vs. Offset/Padded Hitboxes**: `physics.collisions()`, `physics.boundaries()`, and `physics.environment()` insert an entity into the `Space` hash grid using its base image bounds `(x, y, w, l)` (`data[1..4]`), while narrow-phase checks evaluate `data[5]` (`hitboxes`). In `SpatialMechanic.proximities()`, hitboxes are padded by `[-radius, +2 * radius]`, and in `SpatialMechanic.intersections()` by `[-2, +4]`. Similarly, `Signs` (`src/assets/objects/signs/main.yaml`) define hitboxes larger than `dimensions` (`l: 30` on a `24x24` plaque). Whenever two entities' padded or offset hitboxes overlap across a `64px` grid cell boundary while their unpadded base dimensions remain in separate cells, `Space.query()` fails to emit the candidate pair and the intersection is silently missed.
* **Integer Truncation in Overlap Separation (`physics.collide`)**: `shift_x1 = overlap_x * p1` and `shift_x2 = overlap_x * p2` are cast via `int(shift_x1)` and `int(shift_x2)`. Because C `int()` truncates toward zero, any 1-pixel overlap (`overlap_x == 1.0`) between two dynamic bodies ($m_1 > 0, m_2 > 0 \implies p_1 < 1, p_2 < 1$) truncates both shifts to `0`. The entities remain permanently overlapped while transferring/inverting velocities every tick.
* **Unchecked `Velocity` Dereference in `physics.avoid` Step 2**: In `src/libs/core/math/physics.pyx`, Step 1 of `avoid()` guards neighbor velocity access with `n.state.velocity.vx if n.state.velocity else 0.0` (lines 336–337), but Step 2 accesses `n.state.velocity.vx` and `n.state.velocity.vy` unconditionally (lines 397–398). If a neighbor Asset has `state.velocity = None` and Step 1 detects an obstacle cone conflict (`clear = False`), Step 2 raises an `AttributeError`.
* **Stair State Attribute Mismatch**: Documentation (`01-assets.md#craft-stairs`) and state data (`src/data/state/world-testbed/stairs/main.yaml`) specify `blueprint` (`stairs.state.blueprint`) for stair orientation, whereas `CollisionMechanics._traverse_stairs()` queries `stairs.state.direction`. Furthermore, `01-assets.md` specifies `Directions.DOWN` stair transitions and inverted `vx` signs compared to `_traverse_stairs()`, which notes `DOWN is impossible due to LPC perspective specification`.

###### Review: Quality

* **Redundant Condition in `CollisionMechanics._traverse_stairs**`: In `src/app/game/logic/mechanics/spatial/collision.py` (lines 89 and 96), `if direction_val == Directions.UP.value:` is checked twice in a nested block without intervening mutation.
* **Inaccurate Comment and Missing Guard in `SpatialMechanic.proximities**`: The comment on line 117 of `src/app/game/logic/mechanics/spatial/base.py` states `# Extract action radius safely, defaulting to 15 (1/2 grid cell)`, but the code performs no default fallback and directly evaluates `asset.state.mutators.parameters.action.radius`, which raises an `AttributeError` if `action` is `None`.
* **Docstring Signature Drift**: `01-assets.md` documents `Hitbox.get(properties, state, elevation, frame=None)`, whereas `HitboxSchema.get(self, properties, state, elevation)` in `src/app/assets/base.py` omits `frame`.
* **Duplicate Cython Directive**: `src/libs/core/math/geometry.pyx`, `physics.pyx`, and `space.pyx` declare `# cython: language_level=3` twice at the top of each file.
* **Test Fixture Violation in `test_physics.py**`: `test_physics_integrate` in `tests/unit/libs/core/math/test_physics.py` defines inline `DummyState` and `DummyAsset` classes instead of using the `mock_asset` fixture.

###### Review: Logic

* **Signed 32-Bit Overflow and Negative Modulo in `Space._hash**`: In `src/libs/core/math/space.pyx`:

```cython
cdef inline int _hash(self, int cx, int cy):
    return (abs(cx * 73856093 ^ cy * 19349663)) % self.num_buckets
```


Because `cx` and `cy` are signed 32-bit C `int` values, `cx * 73856093` overflows `INT_MAX` at `cx >= 30` (undefined behavior in C). Moreover, if the XOR expression evaluates to `INT_MIN` (`-2147483648`), `abs(INT_MIN)` remains negative in two's complement arithmetic, and C's `%` operator yields a negative bucket index `h < 0`, causing out-of-bounds memory corruption on `self.bucket_counts[h]`.
* **Sub-Pixel Accumulator Desynchronization on Collision**: `physics.integrate()` accumulates sub-pixel motion in `p.rx` and `p.ry`, but `physics.collide()` and `physics.constrain()` mutate `pos.x` and `pos.y` directly without zeroing `pos.rx` or `pos.ry` along the collision normal axis. A body pushed flush against a boundary can immediately re-penetrate by 1 pixel on the next integration tick from residual `rx`/`ry`.
* **Camera Culling Divergence (`geometry.onscreen` vs. `Screen.camera`)**: `geometry.onscreen()` computes `cam_x` and `cam_y` without clamping to `[0, boardsize - screensize]` or centering layers smaller than `screensize`, diverging from `Screen.camera()` and `Screen._assemble()`.

###### Review: Architecture

* **Inconsistent `max_entities` Allocation**: `SpatialMechanic.__init__` defaults to `max_entities: int = 2000`, but `CollisionMechanics.__init__` overrides the default to `max_entities: int = 200` (`num_buckets = 400`), increasing hash collisions in the primary physics mechanic.
* **Redundant Narrow-Phase Evaluations**: In `CollisionMechanics.update()`, `self.collisions(tier_weights, elevation=elevation)` already executes `geometry.intersects()` inside `physics.collisions()` to filter candidate pairs. `CollisionMechanics._resolve()` then immediately invokes `geometry.intersects()` a second time on the exact same pair to retrieve `(hb_a, hb_b)`. Similarly, `physics.boundaries()` runs `geometry.bounded()`, and `CollisionMechanics._boundary()` runs `geometry.bounded()` a second time. Returning `(id_a, id_b, hb_a, hb_b)` from `physics.collisions()` and `(asset_id, bound_id, hb)` from `physics.boundaries()` eliminates all duplicate narrow-phase passes.

###### Review: Optimization

* **Static-vs-Static Filtering in Phase 2 Collisions**: `board.weights(layer)` returns all assets with $m \ge 0$, including static structural Crafts (`struts`), `obstacles`, `chests`, `gates`, and `resources` ($m = 0$). In Phase 2 of `CollisionMechanics.update()`, all $m = 0$ entities are inserted into `Space`, generating candidate pairs and running `geometry.intersects()` twice for every pair of touching or overlapping static walls/struts on the board, only for `physics.collide()` to exit when `inv_total == 0`. Ignoring candidate pairs in `physics.collisions()` (or filtering before `_resolve()`) where both assets have `mass == 0` eliminates $O(N_{\text{static}}^2)$ narrow-phase overhead every frame.
* **Per-Frame Set/Tuple Allocations in `Space.query()**`: `Space.query()` allocates a Python `set()` (`seen`) and 2-tuples on the heap every call (`3x` per layer per frame across `constrain`, `collisions`, etc.). Maintaining a C-level generation counter array or sorting per-bucket pairs avoids Python set hashing in the inner loop.

---

### Bughunting: Bug Reports

##### Bug 001: Elevation Parameter Ignored in `SpatialMechanic` and `CollisionMechanics` Hitbox Resolution

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

`SpatialMechanic.collisions()`, `SpatialMechanic.constrain()`, `CollisionMechanics._boundary()`, and `CollisionMechanics._resolve()` accept an `elevation` parameter but resolve hitboxes via `asset.hitboxes`, which is hardcoded in `Asset.hitboxes` (`src/app/assets/base.py`) to query `self.hitbox.get(self.properties, self.state, self.elevation)`. As a result, passing an explicit `elevation` never filters out assets deployed on other elevations and never queries non-base tiers on multi-elevation assets (`ElevatedHitbox`).

**Steps to Replicate**

1. Instantiate two `crates` (`crate_a.elevation = 0`, `crate_b.elevation = 1`) at `Position(10, 10)`.
2. Execute `mechanics.collisions([crate_a, crate_b], elevation=0)`.
3. Observe `[(crate_a, crate_b)]` is returned instead of `[]`.

**Proposed Remeditation**

Replace `asset.hitboxes` with `asset.hitbox.get(asset.properties, asset.state, elevation)` in `SpatialMechanic.collisions()`, `SpatialMechanic.constrain()`, `CollisionMechanics._boundary()`, and `CollisionMechanics._resolve()` whenever `elevation is not None`.

---

##### Bug 002: Broad-Phase `Space` Grid Inserts Unpadded Asset Dimensions Instead of Active Hitbox Bounds

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

In `src/libs/core/math/physics.pyx`, `physics.collisions()`, `physics.boundaries()`, and `physics.environment()` insert entities into the `Space` hash grid using `data[1..4]` (`asset.state.position.x`, `asset.state.position.y`, `asset.dimensions.w`, `asset.dimensions.l`), ignoring the actual bounding extent of `data[5]` (`hitboxes`). In `SpatialMechanic.proximities()`, virtual hitboxes are padded outward by `radius` (`position = (-radius, -radius)`, `dimensions = (w + 2*radius, l + 2*radius)`). When two entities are separated across a `64px` grid cell boundary such that their base dimensions fall in disjoint cells (e.g., cell `1` and cell `2`) while their padded action-radius hitboxes overlap across the cell boundary, `Space.query()` fails to pair them and `proximities()` returns `[]`.

**Steps to Replicate**

1. Instantiate two `64x64` `sprites` (`action.radius = 25`) at `sprite_a.state.position = Position(50, 10)` (occupying `Space` cells `cx in {0, 1}`) and `sprite_b.state.position = Position(130, 10)` (occupying `Space` cells `cx in {2, 3}`).
2. Their padded action hitboxes span `[25, 139]` and `[105, 219]` (overlapping by `34px`).
3. Call `mechanics.proximities([sprite_a, sprite_b])` and observe `[]` is returned instead of `[(sprite_a, sprite_b)]`.

**Proposed Remeditation**

Compute the broad-phase insertion bounding box in `physics.collisions()` and `physics.environment()` from the union of the entity's active `hitboxes` (`data[5]`) when present, or pass the padded bounding coordinates `(x - radius, y - radius, w + 2 * radius, l + 2 * radius)` directly in the primitive tuple constructed by `SpatialMechanic.proximities()` and `SpatialMechanic.intersections()`.

---

##### Bug 003: Unchecked `None` Velocity Dereference in `physics.avoid` Candidate Sampling Loop

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/libs/core/math/physics.pyx` (`avoid()`), Step 1 checks `n.state.velocity.vx if n.state.velocity else 0.0` (lines 336–337), allowing neighbor `Asset` instances with `state.velocity = None` to be evaluated. However, Step 2 (lines 397–398) accesses `float(n.state.velocity.vx)` and `float(n.state.velocity.vy)` without checking `if n.state.velocity`. When a neighbor has `state.velocity = None` and lies inside the agent's velocity obstacle cone (`clear = False`), execution enters Step 2 and raises `AttributeError: 'NoneType' object has no attribute 'vx'`.

**Steps to Replicate**

1. Instantiate `sprite_a` at `Position(0, 0)` with `Velocity(50.0, 0.0)` and `sprite_b` at `Position(80, 0)` with `sprite_b.state.velocity = None`.
2. Call `physics.avoid(sprite_a, sprite_a.state.velocity, [sprite_b], 0.016)`.
3. Observe `AttributeError` at `src/libs/core/math/physics.pyx:397`.

**Proposed Remeditation**

Update lines 397–398 of `src/libs/core/math/physics.pyx` to match Step 1:

```cython
nvx = float(n.state.velocity.vx if n.state.velocity else 0.0)
nvy = float(n.state.velocity.vy if n.state.velocity else 0.0)

```

---

##### Bug 004: Sub-Pixel Integer Truncation in `physics.collide` Fails to Separate 1px Dynamic Overlaps

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/libs/core/math/physics.pyx` (`collide()`), inverse-mass proportional displacements `shift_x1 = overlap_x * p1` and `shift_x2 = overlap_x * p2` are truncated to integers via `int(shift_x1)` and `int(shift_x2)` before being applied to `pos1` and `pos2`. Whenever two dynamic bodies ($m_1 > 0, m_2 > 0 \implies p_1 \in (0, 1), p_2 \in (0, 1)$) overlap by `1.0` pixel (or `2.0` pixels with unequal masses such as $m_1 = 10, m_2 = 5$ where $2 \times \frac{1}{3} = 0.66$), `int(shift)` truncates to `0` for one or both bodies, leaving the hitboxes overlapping after resolution while still applying elastic velocity transfer.

**Steps to Replicate**

1. Instantiate two `crates` ($m_1 = 1, m_2 = 1$) with `32x32` hitboxes at `pos1 = Position(0, 0)` and `pos2 = Position(31, 0)` (`overlap_x = 1.0`).
2. Call `physics.collide(pos1, hb, Velocity(10.0, 0.0), 1.0, False, pos2, hb, Velocity(-10.0, 0.0), 1.0, False)`.
3. Observe `pos1.x == 0` and `pos2.x == 31` (zero spatial separation).

**Proposed Remeditation**

Use ceiling/rounding on the lighter body's shift or assign the integer remainder `int(overlap_x) - int(shift_x1)` to `shift_x2` so the total applied integer displacement always equals `int(overlap_x)` (and similarly for `overlap_y`).

---

##### Bug 005: Signed 32-Bit Integer Overflow and Negative Modulo in `Space._hash`

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/libs/core/math/space.pyx`, `_hash(self, int cx, int cy)` computes `(abs(cx * 73856093 ^ cy * 19349663)) % self.num_buckets` using signed 32-bit C `int` arithmetic. `cx * 73856093` overflows 32-bit signed `int` for `cx >= 30` ($30 \times 73856093 > 2^{31} - 1$). Furthermore, in C two's complement, `abs(INT_MIN)` evaluates to `INT_MIN` (negative), and C's `%` operator preserves the negative sign, yielding a negative bucket index `h < 0` that reads and writes before the start of `self.bucket_counts` and `self.bucket_data`.

**Proposed Remeditation**

Perform the hash multiplication and bitwise mask using `unsigned int`:

```cython
cdef inline int _hash(self, int cx, int cy) noexcept nogil:
    cdef unsigned int h = (<unsigned int>cx * 73856093u) ^ (<unsigned int>cy * 19349663u)
    return <int>(h % <unsigned int>self.num_buckets)

```