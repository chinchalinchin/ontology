#### 3. Documentation Updates 

###### Update

```markdown

- **Widgets (`docs/06-widgets.md` — `Menu: Data`)**:
  * **`pack`**: Displays two 2x4 grid Gizmos for `inventory.pack` (`materials`) and `inventory.sack` (`crops`) alongside the Craft Formulae column, which comprises a `crafts` filter strip Gizmo, a filtered formula grid Gizmo, and a recipe cost readout bound to `PackContext`.

```


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