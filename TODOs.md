# Swallowed OS Window Events & Sub-Tick Polling in `libs.core.input` and `Device`

1. **Ignored `SDL_QUIT` Events**: In `src/libs/core/input.pyx` (lines 20–26), `pump()` drains the SDL event queue with an empty body:

```cython
while SDL_PollEvent(&event):
    pass
```

Because `SDL_PollEvent` removes all OS window events from SDL's internal queue and discards them, `SDL_QUIT` (window close button, `Alt+F4`, or SIGINT window termination) is permanently discarded.

2. **Polling Inside the Sub-Step Accumulator Loop**: `Engine._play` (`src/app/game/engine.py`, line 109) calls `self.board.device.poll()` inside `while accumulator >= delta:`. In `Keyboard.poll` (`src/app/game/devices.py`, lines 64–106), edge-triggered intentions and menu triggers are resolved by comparing `current_dict.get(v) and not self._last_state.get(v)` and immediately overwriting `self._last_state = current_dict`. If `accumulator` executes two sub-steps in a single render frame, the edge transition is consumed on sub-step 1 and erased on sub-step 2; conversely, if a fast frame renders with `accumulator` less than `delta`, `sdl.pump()` is not called on that frame at all.



#### 3. Documentation Updates

###### Update

```markdown

- **Widgets (`docs/06-widgets.md` — `Menu: Data`)**:
  * **`pack`**: Displays two 2x4 grid Gizmos for `inventory.pack` (`materials`) and `inventory.sack` (`crops`) alongside the Craft Formulae column, which comprises a `crafts` filter strip Gizmo, a filtered formula grid Gizmo, and a recipe cost readout bound to `PackContext`.

```

---

#### 4. Bug Reports

##### Bug 07-06-B: `MenuMechanics` Prevents Focusing `DISABLED` Slots in Craft Formulae

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/game/logic/mechanics/core/menu.py`, `MenuMechanics._resolve_neighbor` enforces `neighbor.state.status != Statuses.DISABLED.value` before moving `menu.focus`. While appropriate for vacant inventory slots in `equipment` and `pouch`, applying `Statuses.DISABLED` to unaffordable recipes in the Craft Formulae grid prevents the player from traversing onto those slots to inspect their required material costs.

**Proposed Remediation**

Either introduce a dedicated `Statuses` / visual state distinction for unaffordable-but-inspectable recipes, or allow `MenuMechanics` / `CraftController` to traverse onto occupied Craft Formulae slots regardless of affordability while gating execution inside `CraftController.select()`.


###### Review: Logic

1. **All-Layer Physics Execution vs. Single-Layer Rendering**:
   * In `CollisionMechanics.update`, the outer loop iterates over `for layer in board.layers():`, running stair traversal, elevation partitioning, perimeter constraints, and broad/narrow-phase collision resolution across **every layer in the Board** on every tick.
   * Because `81,896` calls to `SpatialMechanic.collisions` occur across `5,447` world ticks, `CollisionMechanics` is executing an average of **15.04 elevation-tier collision passes per tick** across all layers.

2. **Static-vs-Static Broad/Narrow-Phase Evaluation in `CollisionMechanics`**:
   * `board.weights(layer)` returns all assets with $m \ge 0$, which includes both dynamic bodies ($m > 0$) and all static bodies ($m = 0$: walls, buildings, obstacle struts, resources, chests, etc.).
   * In Phase 2 of `CollisionMechanics.update`, all `tier_weights` (dominated by static $m = 0$ assets) are passed to `self.collisions(tier_weights, elevation=elevation)`.
   * `physics.collisions` inserts all static and dynamic hitboxes into `Space`, queries all overlapping cell pairs (including **static-vs-static** pairs), and runs `geometry.intersects` on them.
   * For every intersecting pair, `_resolve` re-fetches hitboxes and calls `geometry.intersects` a **second time**, only for `physics.collide` to compute `inv_m1 = 0.0`, `inv_m2 = 0.0`, `inv_total = 0.0` and no-op on static-vs-static pairs.
   * Additionally, `geometry.intersects` returns only the **first** intersecting `(hb1, hb2)` tuple (`return (hb1, hb2)`). If a dynamic entity simultaneously overlaps two hitboxes of a compound asset (e.g., an L-shaped enclosure or multi-hitbox fluid/shoreline), only the first hitbox is resolved per tick.

3. **Perimeter Union Collapse in `Perimeter.extract` (`src/app/services/generators/game/perimeter.py`)**:
   * `Perimeter.extract` collects rectangles for Tier 0 `ENVIRON` and `CANOPY` tiles (Step 1) and then appends static `OBJECTS` and `CRAFTS` rectangles (Step 3) into the same `rects` list passed to `geometry.contours(rects)`.
   * Because `geometry.contours` computes the outer boundary of the **union** $\bigcup_i R_i$ via interval merging (`merge()`), any static object or craft situated *inside* the bounding footprint of the background `ENVIRON` tiles is completely absorbed into the tile interval and produces zero contour edges. Conversely, including `CANOPY` tiles in Step 1 expands the walkable Tier 0 perimeter out to overhead tree/roof canopies.
   * Furthermore, `Perimeter.generate` computes `perimeters_by_tier` for all elevations $E > 0$ (including Step 2 for elevated stairs), but `CollisionMechanics.update` restricts Phase 1 to `if elevation == 0:`, leaving elevated perimeters unused by collision constraints.

---

###### Review: Architecture

2. **Uncached Per-Frame HUD / Overlay Resolution (`Screen._widgets`)**:
   * `Screen.interface` -> `Screen._widgets` consumes **4.90%** of total wall-clock time (**18.96% of active CPU time**)—nearly as much as `CollisionMechanics` (**5.91%**).
   * Unlike `PaneState` widgets which bake to a texture via `Screen.stamp`, non-pane overlay widgets (e.g., HUD meters, slots, buttons) execute `widget.frame.keys(widget.id, widget.state)` (**83,118 calls**, **3.34%**) and `registry.image(key)` on every single frame, even when the underlying widget state has not mutated.

---

###### Review: Optimization

1. **Move `Screen._assemble` Culling, Sorting, and Tuple Packing to Cython (`5.18%` self-time -> `<0.5%`)**:
   * `Screen._assemble` is the single largest Python self-time hotspot in the entire application (**5.18%** wall-clock, or **20.04% of active CPU time**).
   * Currently, `_assemble` iterates over every asset on the layer in Python, calls `_in_viewport` (617,989 times), sorts `visible` using a Python `@staticmethod` key (`Screen._sort`), calls `frame.keys` and `frame.channels`, queries `registry.image`, and allocates new 13-element tuples every frame.
   * **Remediation**:
     1. Maintain a dirty-flagged `_frame_keys` / `_sort_key` cache on `Asset` (invalidated only when `position.y`, `elevation`, `animation.frame`, or `mutators` change).
     2. Move the viewport AABB cull and render-list assembly into `libs.graphics.render` (Cython), operating directly on C-level attributes.

2. **Separate Static ($m = 0$) and Dynamic ($m > 0$) Bodies in `CollisionMechanics` & `Space`**:
   * In `CollisionMechanics.update`, static weights ($m = 0$) never collide with one another.
   * **Remediation**:
     1. Exclude passable crafts (`not MaterialIndex().is_obstacle(blueprint)`) from `Board._cached_weights` during `Cache.index_batch`.
     2. Use the existing asymmetric query pattern (similar to `physics.boundaries` / `physics.environment`) where only dynamic bodies ($m > 0$) initiate queries against static bodies ($m = 0$), and return the intersecting `(hb_a, hb_b)` directly from `physics.collisions` so `_resolve` does not re-execute `geometry.intersects`.

3. **Dirty-Flag HUD Overlays & Eliminate `Enum.value` in `WidgetFrame.keys` (`4.90%` -> `<0.3%`)**:
   * Cache the compiled `primitives` list for `board.overlays` on `Screen` (or cache `widget.frame.keys` per widget) and rebuild only when an `UpdateEvent` or state mutation occurs.
   * Replace repeated `Enum.value` lookups inside `src/app/assets/frames/widgets.py` with pre-bound string constants or `StrEnum`.

4. **Replace `time.sleep(0)` Spin Loop in `Engine.start`**:
   * Replace the `while (self.time() - current_time) < delta: time.sleep(0)` loop (or reduce `settings.SPIN_RATE` and use a pure `pass` spin over a sub-millisecond window `< 0.2ms` with a local `perf_counter = time.perf_counter` binding) to eliminate ~8 million `time.sleep(0)` and `self.time()` calls per 100 seconds.

---


##### Draft: Cursor Properties, Projectile Frame, and Rotated Hitbox Specification

- **Page**: `docs/01-assets.md`
- **Heading**: `###### Cursor: Projectiles`

###### Drift

`docs/01-assets.md` currently specifies `SingleFrame` and no `Hitbox` for `Projectiles`, omits `rotation` on `CursorProperties`, and omits `position`, `angle`, `speed`, and `owner` on `MotorState`.

###### Update

```markdown
###### Cursor: Projectiles

Projectiles are spawned on the `release` frame of ranged [Equipment](./02-sprites.md#equipment) with an initial coordinate, quantized launch angle, and scalar speed, following a linear trajectory until impacting an obstacle or target hitbox or exceeding their range.

**Properties: CursorProperties(AssetProperties)**

* `frames: List[str]`
* `rotation: int = 90`: Angular step $\Delta\theta \in (0, 360]$ partitioning the $360^\circ$ rotation space into $N = 360 // \text{rotation}$ discrete frames.
* `hitboxes: List[Hitbox]`

**Animation: None**

N/A

**Frame: ProjectileFrame**

* `keys(id, state): returns [ (f"{id}-{state.angle}", 0, 0) ]`
* `index(id, properties): returns { f"{id}-{k * properties.rotation}": (k * properties.dimensions.w, 0, properties.dimensions.w, properties.dimensions.l) for k in range(360 // properties.rotation) }`

**Hitbox: RotatedHitbox**

Projects each static base Hitbox $(x_0, y_0, w_0, l_0)$ in `properties.hitboxes` around the frame center $(c_x, c_y) = (W / 2, L / 2)$ by $\Delta\theta = \text{state.angle}$:

$$
h_{cx} = \left(x_0 + \frac{w_0}{2}\right) - c_x, \qquad h_{cy} = \left(y_0 + \frac{l_0}{2}\right) - c_y
$$

$$
\begin{pmatrix} h'_{cx} \\ h'_{cy} \end{pmatrix} = \begin{pmatrix} \cos\Delta\theta & -\sin\Delta\theta \\ \sin\Delta\theta & \cos\Delta\theta \end{pmatrix} \begin{pmatrix} h_{cx} \\ h_{cy} \end{pmatrix}
$$

$$
w'(\Delta\theta) = \max\Big(1,\; \operatorname{round}\big(w_0 |\cos\Delta\theta| + l_0 |\sin\Delta\theta|\big)\Big), \qquad l'(\Delta\theta) = \max\Big(1,\; \operatorname{round}\big(w_0 |\sin\Delta\theta| + l_0 |\cos\Delta\theta|\big)\Big)
$$

$$
x'(\Delta\theta) = \operatorname{round}\left(c_x + h'_{cx} - \frac{w'(\Delta\theta)}{2}\right), \qquad y'(\Delta\theta) = \operatorname{round}\left(c_y + h'_{cy} - \frac{l'(\Delta\theta)}{2}\right)
$$

**State: MotorState(AssetState)**

* `position: Position`
* `initial: Position`
* `velocity: Velocity`
* `angle: int = 0`
* `speed: int = 200`
* `owner: Optional[str] = None`
```

---

# Documentation Updates

##### Draft: Cursor Projectiles Specification

- **Page**: `docs/01-assets.md`
- **Heading**: `Cursor: Projectiles`

###### Drift

`docs/01-assets.md` still specifies Projectiles as using `SingleFrame` and a minimal `MotorState` containing only `initial` and `velocity`. Under Phase 03.04, Projectiles partition a single canonical $\theta = 0^\circ$ asset into discrete rotational frames spaced by an angular increment $\Delta\theta$, transform their bounding hitboxes by their active heading $\theta$, and carry relational foreign keys binding them to the Weapons that emit them.

###### Update

```markdown
###### Cursor: Projectiles

Projectiles are autonomous Cursor Assets spawned on the release frame of ranged combat Actions. A Projectile Asset file contains a single canonical frame oriented at $\theta = 0^\circ$ ($+x$, `right`) and is partitioned into discrete angular frames spaced by its rotational increment $\Delta\theta$ (where $360 \bmod \Delta\theta = 0$):

$$
\Theta = \{ k \cdot \Delta\theta \mid 0 \le k < 360 / \Delta\theta \}
$$

Because Projectiles depend on the Weapons that emit them, each Projectile declares the set of Weapons bound to it in its Properties. During initialization, these bindings are inverted into a relational index mapping each ranged Weapon to its emitted Projectile.

**Properties: CursorProperties(AssetProperties)**

* `rotation: int`: Discrete angular increment $\Delta\theta$ in degrees ($360 \bmod \Delta\theta = 0$).
* `weapons: List[WeaponPalette]`: Weapon keys bound to this Projectile.
* `hitboxes: Optional[List[Hitbox]]`: Canonical AABB footprint at $\theta = 0^\circ$.

**Animation: None**

N/A

**Frame: ProjectileFrame**

Partitions the horizontal strip across $\Theta$ and projects `state.angle` directly onto its corresponding rotated frame.

**Hitbox: RotatedHitbox**

Rotates each canonical hitbox $(x_0, y_0, w_0, l_0)$ clockwise by $\theta = \text{state.angle}$ around the frame center $(W/2, L/2)$, yielding the enclosing axis-aligned bounding box $(x'(\theta), y'(\theta), w'(\theta), l'(\theta))$ at the Projectile's elevation.

**State: MotorState(AssetState)**

* `position: Position`: Active world coordinate.
* `initial: Position`: Spawn origin coordinate used for range expiration.
* `velocity: Velocity`: Constant linear trajectory vector.
* `angle: int`: Quantized heading $\theta \in \Theta$.
* `speed: int`: Scalar launch speed encoding attacker strength and draw duration.
* `owner: Optional[str]`: Deploying entity `name`, excluded from impact resolution.
```

---


### Backlog Entry (B039.1 — Board Temporal Coupling & Late-Bound Dependencies)

#### Refactor: Eliminate Late-Bound Service Setters and Temporal Coupling on `Board`

**Overview**

While the immediate annotation mismatches on `Board` (`plot`, `device`, `cradle`, `materializer`) have been corrected to `Optional[...]`, `Board.__init__` still initializes its core runtime collaborators (`device`, `cradle`, `migrator`, `materializer`, `plot`) to `None` and relies on external callers (`Orchestrator`, `Migrator`, event handlers, and test fixtures) invoking mutable setter methods in an undocumented order. Eliminating this temporal coupling spans multiple orchestration and service layers outside the immediate `Board` patch boundary and warrants a dedicated refactoring pass.

##### Specification

Separate **Boot-Time Collaborators** (always present once `Board` is constructed in Phase 1: `device`, `cradle`, `migrator`, and `materializer` if active) from **Hydrated World State** (loaded/reset in Phase 2: `plot`, `calendar`, `assets`, `perimeters`, `overlays`).

* **Constructor Injection**: `Device` and `Cradle` (which depend only on `configurations` / `spawnables`, not a live `Board` instance) must be injected directly into `Board.__init__`.
* **Circular Dependency Resolution**: If `Migrator` requires a `Board` reference (or vice versa), invert the dependency so `Engine` / `LoadController` / `StateEventHandler` owns `Migrator` (or passes `board` into `migrator.step(board)`), eliminating `Board.migrator` and `Board.set_migrator()` altogether.
* **Orphaned Attribute Audit**: Audit `self.materializer` across the entire codebase; either inject it strictly as a typed component or remove it if unused.
* **Non-Optional `PlotState`**: Default `self.plot = PlotState()` (matching `self.calendar = CalendarState()`) and update `Board.serialize()` to emit `Shortcuts.PLOTS` only when `self.plot.current is not None or self.plot.previous`.

##### Goals

###### Goal: Construct `Board` in a Valid, Non-Null Boot State

Every `Board` returned by `Orchestrator` should hold non-optional, ready-to-use `device` and `cradle` collaborators so `Engine._play()` (`self.board.device.poll()`) and `Cartographer` / `CombatMechanics` (`board.cradle`) cannot fail with `AttributeError` on `None`.

###### Goal: Decouple `Migrator` Lifecycle from `Board`

`Board` is the in-memory world database, whereas `Migrator` is an orchestration service that hydrates `Board`. Moving `Migrator` ownership to `EventData` / `Engine` (or passing `board` to `Migrator` methods) breaks the `Board <-> Migrator` cycle and removes `set_migrator`.

##### Tasks

**1. Task: Audit `Board` Collaborator Wiring and Remove Dead Attributes**

*Objective*: Map every caller of `set_device`, `set_cradle`, `set_plot`, `set_migrator`, and `board.materializer` across `app.services.orchestration`, `app.game.menus`, and `tests/`.

* [ ] Subtask: Verify whether `board.materializer` is referenced anywhere in `src/` or `tests/`; schedule removal or strict typing.
* [ ] Subtask: Trace whether `Cradle` or `Device` holds a back-reference to `Board`, and break any accidental reverse coupling.

**2. Task: Refactor `Board.__init__` and `Orchestrator` for Constructor Injection**

*Objective*: Inject mandatory Phase 1 collaborators at construction and eliminate mutable setter methods.

* [ ] Subtask: Update `Board.__init__` to accept `device: Device` and `cradle: Cradle` directly, removing `set_device` and `set_cradle`.
* [ ] Subtask: Default `Board.plot` to `PlotState()` and guard `Board.serialize()` on non-empty plot state (`self.plot.current is not None or self.plot.previous`).
* [ ] Subtask: Move `Migrator` ownership out of `Board` into `EventData` / `LoadController` (or pass `board` per step), removing `Board.migrator` and `set_migrator`.
* [ ] Subtask: Update `Orchestrator`, `StateEventHandler`, `LoadController`, and `tests/unit/conftest.py` fixtures to construct `Board` with the new signature.


---