
##### Draft: Resolve Post-07.04 Substrate vs. Elevation Documentation Drift

- **Page**: `docs/01-assets.md`
- **Heading**: `###### Concept: Appearance` (`**Substrates**`)

###### Drift

Flagged by `@TODO(07-04)` (where Phase 07.04 is `[x]` Closed/Implemented). The documentation states:
`During CollisionMechanics and Perimeter generation, all negative Substrates are collapsed into elevation = 0, i.e. elevation \in [-\infty, 0] \to elevation = 0, in order that all Assets on these Substrates may participate in collisions at elevation = 0.`
Following Phase 07.04, `substrate` ($\in \mathbb{Z}_{\le 0}$) and `elevation` ($\in \mathbb{Z}_{\ge 0}$) are orthogonal attributes on `Asset` (`asset.substrate` vs. `asset.elevation`), and `Screen._sort` sorts by `(asset.elevation, asset.substrate, ground_y, asset.properties.priority)`. Substrates are no longer stored as negative values on `state.elevation`, though `Board.weights`, `Board.obstacles`, and `HitboxSchema.elevations` still clamp `max(0, elevation)` as a safeguard.

###### Update

```markdown
**Substrates**

Certain Assets are assigned a dedicated intra-elevation `substrate` ($\in \mathbb{Z}_{\le 0}$) to preserve the fidelity of their rendering order within a macro-elevation tier $E \in \mathbb{Z}_{\ge 0}$. These values are hydrated onto the Asset (`asset.substrate`) via [MaterialIndex](./appendices/01-schemas.md#configuration-materials) during [hydration](./12-architecture.md#phase-2-hydration):

--8<-- "static/md/asset-substrates.md"

Because `substrate` is an independent secondary component of the rendering sort key `(elevation, substrate, ground_y, priority)`, Assets rendered on negative intra-elevation substrates (such as `Bridges` on `Substrates.OVERLAYS = -1` or `Shorelines` on `Substrates.SURFACES = -2`) retain their true topological `elevation` ($E \ge 0$) for spatial queries and collision partitioning.

```

##### Draft: Update Sheet Attackboxes Documentation for `HitboxSchema` ECS Component

* **Page**: `docs/01-assets.md`
* **Heading**: `###### Category: Sheets` (`**Hitbox: Attackboxes**`)

###### Drift

Flagged by `@TODO(10-01)` (where Phase 10.01 is `[x]` Closed/Implemented). The section states that `Attackboxes` have not yet been migrated to the `HitboxSchema` component architecture and lists `StaticHitbox` with the legacy 3-argument signature `get(properties, state, frame)`. In `src/app/assets/hitboxes/sheets.py`, `AttackHitbox(HitboxSchema)` implements the 4-argument `get(properties, state, elevation, frame)` interface.

###### Update

```markdown
**Hitbox: AttackHitbox**

An Attackbox is a directional, frame-keyed hitbox unique to Sheet Assets. It is mapped in `SheetProperties.attackboxes` to a canonical `<action>-<direction>-<frame>` key and resolved dynamically via the `AttackHitbox` (`HitboxSchema`) component during [CombatMechanics](./05-mechanics.md#spatial-mechanic-collisionmechanics).

- `elevations(properties, state)`: returns `[max(0, state.elevation if state.elevation is not None else 0)]`
- `get(properties, state, elevation, frame)`: resolves active `Hitbox` list for the current animation frame at the requested `elevation`.

```


### Formal Assumptions

To evaluate the *Ontology* codebase against enterprise software engineering and real-time simulation standards, this analysis proceeds from four formal assumptions derived from the project's documented design (`docs/00-overview.md`, `docs/01-assets.md`, `docs/12-architecture.md`) and standard software architecture principles:

1. **Strict Layered Decoupling (Hexagonal / Clean Architecture)**: Domain models (`app.models`), the in-memory state database (`app.game.board`), and declarative state bindings (`app.game.menus.bindings`) must remain independent of hardware I/O and C-level rendering subsystems (`libs.graphics.render`, `libs.core.input`).
2. **Component Polymorphism over Type Switching**: Per `docs/01-assets.md` (*Overview: Architecture*), entity behavior is defined by injected strategy components (`Frame`, `Animation`, `HitboxSchema`) and data models (`AssetProperties`, `AssetState`). Core engine loops must operate on the unified `Asset` interface without branching on concrete `isinstance` state checks or hardcoded asset IDs.
3. **Real-Time Complexity & Zero-Allocation Inner Loop**: Per `docs/12-architecture.md` (*Specification: Cython Libraries*), the 60 Hz (`1.0 / settings.TARGET_FPS`) loop must minimize per-frame Python heap allocations (strings, tuples, lists) and bound algorithmic complexity to visible/active working sets rather than total layer populations.
4. **Deterministic State Lifecycle & Serialization Integrity**: Component initialization, event queue draining, and state serialization (`Board.serialize`) must be total, cycle-safe, and free of temporal coupling.

---

### 1. Architectural & Organizational Violations

#### 1.1 Hardware & VRAM Coupling in the State Database and Models

The rendering abstraction boundary (`Screen` $\to$ `libs.graphics.render`) is breached by both the domain state models and the `Board` database:

* **VRAM Pointers Stored in Domain State**: `PaneState` (`src/app/models/state/assets/widgets.py`, line 81) stores `canvas: Any = None`, which at runtime holds a Cython `TexturePtr` wrapping a raw `SDL_Texture*` GPU allocation (`src/app/game/screen.py`, line 269).
* **Duplicate VRAM Teardown Across Layers**: Because `PaneState` holds a hardware pointer, `src/app/game/board/core.py` imports `libs.graphics.render as render` (line 59) and manually destroys GPU textures inside `Board.clear()` (lines 363–369):
```python
for menu in self.menus + self.overlays:
    if menu.widgets:
        for widget in menu.widgets.values():
            if isinstance(widget.state, PaneState) and widget.state.canvas is not None:
                render.destroy(widget.state.canvas)
                widget.state.canvas = None

```


This duplicates `Screen.release(menu)` (`src/app/game/screen.py`, lines 289–296). Consequently, the database layer (`Board`) has a hard compile-time and runtime dependency on the SDL2 Cython rendering module.
* **SDL Font Measurement Inside Data Bindings**: `src/app/game/menus/bindings/text.py` imports `libs.graphics.render as render` (line 40) to call `render.measure(test_line, font)` inside `paginate()` (lines 67, 81). As noted in the file's own comment (lines 34–39), this couples declarative data binding to an active SDL2 TTF context. Furthermore, both `LibraryBinding.bind` (line 136) and `TextBinding.bind` (line 167) ignore the `font=widget.state.font` keyword argument passed by `Provider._bind_pane` (`src/app/services/generators/menus/provider.py`, line 155) and hardcode `self.registry.font("dialogue")`.
* **Remediation**: Store widget canvas `TexturePtr` instances in a renderer-owned dictionary (`Screen._widget_canvases: Dict[str, TexturePtr]`) keyed by `widget.name`, and pass a callable text-measurement interface (or execute pagination inside `Screen.stamp`) so `Board`, `PaneState`, and `Binding` have zero dependencies on `libs.graphics.render`.

#### 1.2 Erosion of ECS Polymorphism via `isinstance` and ID Branching

Although `Asset` (`src/app/assets/base.py`, line 139) is designed as a uniform component container, core systems bypass its strategy interfaces:

* **`Screen` Inspects Concrete State Types**: `Screen._assemble` (`src/app/game/screen.py`, line 157) checks `if not isinstance(asset.state, SheetState):` to suppress missing frame warnings for sparse equipment sheets. `Screen._widgets`, `Screen.stamp`, `Screen.bake`, and `Screen.release` (lines 213, 224, 250, 286, 294) repeatedly check `isinstance(widget.state, PaneState)`.
* **`Widget` Subclasses `Asset` to Override `dimensions**`: `src/app/game/menus/core.py` (lines 37–49) defines `class Widget(Asset)` solely to attach `binding` and branch on `if isinstance(self.state, PaneState): return self.state.span`.
* **Hardcoded Entity IDs and `getattr` Guards in Sheet Components**:
* `SpriteFrame.keys` (`src/app/assets/frames/sheets.py`, line 103) checks `if id != RequiredAssets.PLAYER.value and state.psyche.expression:`.
* `SpriteAnimation.animate` (`src/app/assets/animations/sheets.py`, line 32) is type-annotated for `state: SpriteState`, yet uses `if getattr(state, 'psyche', None) is None: return state` because `Player` is hydrated with `SheetState` (which lacks `psyche`) while sharing `SpriteAnimation` and `SpriteFrame`.
* Meanwhile, `SheetState` (`src/app/models/state/assets/sheets.py`, lines 128–136) bundles `intention`, `character`, `inventory`, `meters`, and `goal` onto the base class for all `Sheets`, forcing `Pixies` (`docs/01-assets.md`, *Sheet: Pixies*) to inherit full character/inventory structures if they use `SheetState`.


* **Remediation**: Separate `SheetState` (strictly `position`, `velocity`, `animation`), `CharacterState(SheetState)` (adding `character`, `slots`, `inventory`, `meters`, `intention`, `goal` for `Player`), and `SpriteState(CharacterState)` (adding `psyche`, `memory`, `trajectory`). Give `Player` and `Sprite` distinct `Frame` and `Animation` recipes (or let `PlayerFrame` be `SpriteFrame` without expression overlays and `SpriteFrame` subclass `PlayerFrame`), eliminating `getattr` and `id != "player"` checks.

#### 1.3 Temporal Coupling and Encapsulation Leaks in `Board`

* **Nullable Late-Bound Dependencies Violating Type Annotations**: In `src/app/game/board/core.py` (lines 69–77), `plot: PlotState`, `device: Device`, and `cradle: Cradle` are annotated as non-optional, while `self.materializer` is unannotated. In `Board.__init__` (lines 90–95), all five are initialized to `None` and mutated later via setter methods (`set_device`, `set_cradle`, `set_plot`, `set_migrator`). Any mechanic or handler invoked before all setters run encounters `AttributeError` on `None`.
* **11 Private Cache Structures Exposed on `Board**`: Lines 111–155 of `src/app/game/board/core.py` expose `_cached_categories`, `_cached_instances`, `_cached_layers`, `_cached_renderables`, `_cached_weights`, `_cached_tilemap`, `_cached_fluidmap`, `_cached_characters`, `_all_categories`, `_all_instances`, and `_shorelines` directly from `self._cache`. External callers inspecting these properties bypass `Board`'s query API and couple directly to `Cache` implementation details.

---

### 2. Algorithmic & Runtime Inefficiencies (60 Hz Loop)

#### 2.1 Unculled Heap Allocations, Registry Lookups, and Full-Layer Sorting in `Screen._assemble`

In `src/app/game/screen.py` (`_assemble`, lines 126–205), the rendering pipeline executes operations in the following order every frame (60 Hz):

1. `self.board.renderables(player.state.layer)` (`src/app/game/engine.py`, line 127) returns the cached list of **all** non-tile assets on the active layer (`src/app/game/board/core.py`, line 276).
2. `assets.sort(key=self._sort)` (line 138) sorts the **entire layer's asset list** in-place ($O(N_{\text{layer}} \log N_{\text{layer}})$), mutating the list stored inside `Board._cache.cached_renderables[layer]`.
3. For **every** asset on the layer (lines 140–154), the loop calls `asset.frame.keys(asset.id, asset.state)`, `asset.frame.channels(...)`, and `self.registry.image(frame_key)` **before** checking whether the asset is inside the camera viewport (lines 171–174).

**Impact**:
In `StateFrame.keys` and `SpriteFrame.keys` (`src/app/assets/frames/sheets.py`, lines 46–51, 88–107), every call to `keys()` executes `settings.SEPARATOR.join([...])` and allocates a new list of tuples on the Python heap. If a layer contains $2,000$ assets and only $40$ are within the camera viewport (`pov`, `bounds`), the engine performs $2,000$ sort key evaluations, $2,000+$ dynamic string concatenations, list allocations, and `Registry.image()` dictionary lookups per frame ($120,000+$ allocations per second) only to discard $98\%$ of them at line 171.

**Remediation**:
Perform broad-phase camera AABB culling **first** using `asset.state.position` and `asset.dimensions` (with a constant margin $M$ for expression offsets), collect only the visible subset $V$ ($\vert{}V\vert{} \ll N_{\text{layer}}$), sort $V$ into a local list without mutating `Board._cache`, and invoke `asset.frame.keys()`, `asset.frame.channels()`, and `self.registry.image()` exclusively on $a \in V$:

$$\text{Complexity}_{\text{frame}}: \quad O(N_{\text{layer}} \log N_{\text{layer}}) + N_{\text{layer}} \cdot C_{\text{alloc}} \;\longrightarrow\; O(N_{\text{layer}}) + O(\vert{}V\vert{} \log \vert{}V\vert{}) + \vert{}V\vert{} \cdot C_{\text{alloc}}$$

#### 2.2 $O(N)$ Linear Scans for Unique Entity Lookups and Layer Dimensions in `Board`

* **`Board.asset(name, layer)` (`src/app/game/board/core.py`, lines 222–224)**:
```python
def asset(self, name: str, layer: Optional[str] = None) -> Optional[Asset]:
    search_list = self.renderables(layer) if layer else self._assets
    return next((a for a in search_list if a.name == name), None)

```


Although `asset.name` is globally unique across a deployed `Board` (`docs/01-assets.md`, *Hierarchy: Taxonomy*), `board.asset(name)` performs an $O(N)$ linear scan. Worse, when `layer` is specified, it searches `self.renderables(layer)`, which excludes `AssetCategories.TILES`—meaning `board.asset(tile_name, layer="main")` always returns `None`. Indexing `assets_by_name: Dict[str, Asset]` inside `Cache` reduces `board.asset(name)` to $O(1)$.
* **`Board.size(layer)` (`src/app/game/board/core.py`, lines 296–323)**:
Iterates over every asset on the layer in $O(N)$ on each invocation to compute `max_w` and `max_l`, rather than caching layer dimensions in `Cache` during `index_batch` / `evict_batch`.

---

### 3. Correctness & Reliability Defects

#### 3.1 `Engine._drain` Drops Queued Events on Missing Handler and Lacks Cycle Bounding

In `src/app/game/engine.py` (lines 92–104):

```python
def _drain(self) -> None:
    while self.bus:
        event = self.bus.popleft()
        handler = self.handlers.get(type(event))
        if not handler:
            logger.warning(f"No Event Handler registered for type: {type(event)}")
            return 
        handler.handle(event, self.data)

```

1. **Queue Stall on `return**`: Line 101 uses `return` instead of `continue`. If an unmapped event type is pushed to `self.bus`, `_drain()` aborts immediately, leaving all valid events behind it unprocessed in the queue until the next frame tick.
2. **Unbounded Synchronous Cascading**: Because `self.data.bus` is `self.bus`, any `handler.handle(event, self.data)` that appends a new `Event` extends the active `while self.bus:` loop in the same tick. If two handlers mutually trigger events, `_drain()` enters an infinite loop. Draining a bounded tick snapshot (`for _ in range(len(self.bus)):`) guarantees termination within each tick.

#### 3.2 Unclamped Fixed-Timestep Accumulator ("Spiral of Death") in `Engine.start`

In `src/app/game/engine.py` (lines 173–182):

```python
current_time = self.time()
frame_time = current_time - last_time
last_time = current_time
accumulator += frame_time

while accumulator >= delta:
    self._play(delta)
    self._drain()
    accumulator -= delta

```

`frame_time` has no upper bound. If the OS window manager blocks the process (e.g., dragging the window title bar, workspace switching, or a breakpoint) for $5\text{ seconds}$, `accumulator` spikes to $5.0\text{ s}$ and executes $300$ consecutive `_play(delta)` ticks without rendering or sleeping. Clamping `frame_time = min(current_time - last_time, settings.MAX_FRAME_TIME)` (typically $0.25\text{ s}$) prevents accumulator runaway.

#### 3.3 Swallowed OS Window Events & Sub-Tick Polling in `libs.core.input` and `Device`

1. **Ignored `SDL_QUIT` Events**: In `src/libs/core/input.pyx` (lines 20–26), `pump()` drains the SDL event queue with an empty body:
```cython
while SDL_PollEvent(&event):
    pass

```


Because `SDL_PollEvent` removes all OS window events from SDL's internal queue and discards them, `SDL_QUIT` (window close button, `Alt+F4`, or SIGINT window termination) is permanently discarded.
2. **Polling Inside the Sub-Step Accumulator Loop**: `Engine._play` (`src/app/game/engine.py`, line 109) calls `self.board.device.poll()` inside `while accumulator >= delta:`. In `Keyboard.poll` (`src/app/game/devices.py`, lines 64–106), edge-triggered intentions and menu triggers are resolved by comparing `current_dict.get(v) and not self._last_state.get(v)` and immediately overwriting `self._last_state = current_dict`. If `accumulator` executes two sub-steps in a single render frame, the edge transition is consumed on sub-step 1 and erased on sub-step 2; conversely, if a fast frame renders with `accumulator` less than `delta`, `sdl.pump()` is not called on that frame at all.

#### 3.4 `dataclasses.asdict` Serialization on Cython Extension Types in `Board.serialize`

In `src/app/game/board/core.py` (line 408), `Board.serialize` converts runtime states to dictionaries via `asdict(asset.state)`. However, `SheetState`, `ObjectState`, `CraftState`, etc., store Cython `cdef class` extension types (`libs.core.models.Position`, `Velocity`, `Dimensions`, `Multiple`) in their fields (`src/app/models/state/assets/sheets.py`, lines 130–131). Python's `dataclasses.asdict()` only unpacks standard Python `@dataclass` objects, lists, tuples, and dicts; for Cython `cdef class` instances, `asdict()` falls back to `copy.deepcopy(obj)`, leaving raw Cython extension instances in the output dict (or raising `TypeError` if `__reduce__`/`__deepcopy__` is not implemented on every `cdef class` in `libs.core.models`).

#### 3.5 Cross-Domain Enum Default Bug in `SelectTarget` and Off-Target Channel Rendering in `Screen.export_map`

* **Invalid Default Enum Type on `SelectTarget**`: In `src/app/models/config/menus.py` (line 87):
```python
@dataclass(slots=True, frozen=True)
class SelectTarget:
    selection: Enumerated[Selections] = Statuses.IDLE.value

```


`selection` is validated against `Enumerated[Selections]`, but its default value is `Statuses.IDLE.value` (`"idle"`), which is a `Statuses` enum value rather than a `Selections` enum value. Additionally, `from app.models.adapters import Enumerated` is imported twice in `src/app/models/config/menus.py` (lines 34 and 39).
* **Channel Operations Drawn to Default Viewport Instead of `full_target` in `Screen.export_map**`: In `src/app/game/screen.py` (lines 398–411), `render.render(..., target=full_target)` renders the map onto the temporary offscreen texture `full_target`, but the subsequent line `render.channel(active_channels, pov.x, pov.y)` (line 411) omits `target=full_target`, causing auxiliary tint channels to render onto the screen backbuffer rather than the exported map texture.

---

### Summary Matrix

| Category | Location | Architectural / Technical Issue | Severity | Primary Fix |
| --- | --- | --- | --- | --- |
| **Layering / Coupling** | `board/core.py:59,368`<br>

<br>`bindings/text.py:40`<br>

<br>`state/assets/widgets.py:81` | `Board`, `PaneState`, and `TextBinding` directly depend on Cython SDL2 `libs.graphics.render` and hold GPU `TexturePtr` pointers. | **High** | Move `canvas` `TexturePtr` storage into `Screen`; inject a measurement callback or paginate inside `Screen.stamp`. |
| **60 Hz Render Performance** | `screen.py:138-174` | `Screen._assemble` sorts the entire layer in-place (mutating `Board._cache`) and runs `frame.keys()` string joins + `Registry.image()` lookups for all off-screen assets *before* camera culling. | **High** | Cull by `asset.state.position` and `asset.dimensions` *before* sorting and *before* invoking `frame.keys()` and `registry.image()`. |
| **ECS Polymorphism** | `screen.py:157,213`<br>

<br>`frames/sheets.py:103`<br>

<br>`animations/sheets.py:32` | Core loops branch on `isinstance(state, ...)`, `getattr(state, 'psyche', None)`, and `id != "player"`, violating the `Asset` strategy abstraction. | **Medium** | Split `SheetState` $\to$ `CharacterState` $\to$ `SpriteState`; assign dedicated `PlayerFrame` / `PlayerAnimation` recipes. |
| **Event Bus Safety** | `engine.py:92-104` | `_drain()` uses `return` instead of `continue` on missing handlers (stalling the queue) and loops `while self.bus:` without bounding tick depth. | **Medium** | Replace `return` with `continue`; iterate over a fixed tick snapshot `for _ in range(len(self.bus)):`. |
| **Loop Stability & OS Input** | `engine.py:109,174-182`<br>

<br>`libs/core/input.pyx:20-26` | Unclamped `frame_time` risks accumulator "spiral of death"; `input.pump()` discards `SDL_QUIT` events. | **Medium** | Clamp `frame_time` to `MAX_FRAME_TIME`; surface `SDL_QUIT` from `input.pump()` to `Engine.stop()`. |
| **Database & Serialization** | `board/core.py:222,296,408` | `Board.asset()` and `Board.size()` run in $O(N)$ (`asset()` also misses `Tiles` when `layer` is passed); `serialize()` runs `asdict()` over Cython `cdef` types. | **Medium** | Index `assets_by_name` and layer bounds in `Cache`; convert Cython `Position`/`Velocity` explicitly during serialization. |
| **Type & Render Bugs** | `config/menus.py:87`<br>

<br>`bindings/text.py:136,167`<br>

<br>`screen.py:411` | `SelectTarget.selection` defaults to `Statuses.IDLE`; `LibraryBinding`/`TextBinding` hardcode `"dialogue"` font; `export_map` omits `target=full_target` on `render.channel`. | **Low** | Default `SelectTarget.selection` to a valid `Selections` member; use `font` kwarg in `text.py`; pass `target=full_target` to `render.channel`. |

---

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