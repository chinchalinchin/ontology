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

#### 3.1 Unclamped Fixed-Timestep Accumulator ("Spiral of Death") in `Engine.start`

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

#### 3.2 Swallowed OS Window Events & Sub-Tick Polling in `libs.core.input` and `Device`

1. **Ignored `SDL_QUIT` Events**: In `src/libs/core/input.pyx` (lines 20–26), `pump()` drains the SDL event queue with an empty body:
```cython
while SDL_PollEvent(&event):
    pass

```


Because `SDL_PollEvent` removes all OS window events from SDL's internal queue and discards them, `SDL_QUIT` (window close button, `Alt+F4`, or SIGINT window termination) is permanently discarded.
2. **Polling Inside the Sub-Step Accumulator Loop**: `Engine._play` (`src/app/game/engine.py`, line 109) calls `self.board.device.poll()` inside `while accumulator >= delta:`. In `Keyboard.poll` (`src/app/game/devices.py`, lines 64–106), edge-triggered intentions and menu triggers are resolved by comparing `current_dict.get(v) and not self._last_state.get(v)` and immediately overwriting `self._last_state = current_dict`. If `accumulator` executes two sub-steps in a single render frame, the edge transition is consumed on sub-step 1 and erased on sub-step 2; conversely, if a fast frame renders with `accumulator` less than `delta`, `sdl.pump()` is not called on that frame at all.

#### 3.3 `dataclasses.asdict` Serialization on Cython Extension Types in `Board.serialize`

In `src/app/game/board/core.py` (line 408), `Board.serialize` converts runtime states to dictionaries via `asdict(asset.state)`. However, `SheetState`, `ObjectState`, `CraftState`, etc., store Cython `cdef class` extension types (`libs.core.models.Position`, `Velocity`, `Dimensions`, `Multiple`) in their fields (`src/app/models/state/assets/sheets.py`, lines 130–131). Python's `dataclasses.asdict()` only unpacks standard Python `@dataclass` objects, lists, tuples, and dicts; for Cython `cdef class` instances, `asdict()` falls back to `copy.deepcopy(obj)`, leaving raw Cython extension instances in the output dict (or raising `TypeError` if `__reduce__`/`__deepcopy__` is not implemented on every `cdef class` in `libs.core.models`).

#### 3.4 Cross-Domain Enum Default Bug in `SelectTarget` and Off-Target Channel Rendering in `Screen.export_map`

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





### Architectural Grooming & Response to User Review I

#### 1. Inducting Equipment as Stateless `Asset`s on `Board.equipment`

In the current codebase, `Builder.build_board()` populates `EquipmentGroup` with raw `Dict[str, SheetProperties]` dictionaries (`self.context.properties.sheets.weapons`, etc.), while `Migrator` only instantiates `Asset` objects for stateful entities declared in `/src/data/state/<board-key>/**/*.yaml`. Because Equipment has `NoState` and is never deployed as an independent world entity, registering `hitbox: AttackHitbox` under `recipes.sheets.weapons` in the previous specification was a dead configuration path, and `CombatMap.attackboxes()` violated the ECS injection boundary by instantiating `AttackHitbox()` inline.

Storing stateless Equipment **`Asset`** instances in `Board.equipment` (`EquipmentGroup`) resolves this architectural split cleanly:

```mermaid
flowchart LR
    subgraph Bootstrap ["Builder.build_board()"]
        P["PropertiesSchema.sheets<br/>(weapons, tools, armor, shields, utilities)"]
        R["RecipeConfiguration.sheets<br/>(frame: StateFrame, hitbox: AttackHitbox | None)"]
        F["Factory / AssetFactory"]
        P --> F
        R --> F
        F --> EG["Board.equipment: EquipmentGroup<br/>Dict[str, Asset] (state=NoState)"]
    end

    subgraph Runtime ["Engine Loop"]
        EG -->|"weapon: Asset"| CM["CombatMap.attackboxes()<br/>weapon.hitbox.get(weapon.properties, state, elevation)"]
        EG -->|"weapon: Asset"| AM["AnimationMap.action()<br/>weapon.properties.actions"]
    end

```

##### Component-by-Component Implications

1. **`EquipmentGroup` (`src/app/models/groups.py`) & `Builder.build_board()` (`src/app/services/orchestration/builder.py`)**:
* Each field on `EquipmentGroup` (`armor`, `weapons`, `tools`, `utilities`, `shields`) transitions from `Dict[str, SheetProperties]` to `Dict[str, Asset]`.
* During `Builder.build_board()`, each equipment entry `(eq_id, eq_props)` is hydrated into an `Asset` using its corresponding `Recipe` from `self.context.configurations.recipes.sheets.<instance>`:
* `taxonomy = Taxonomy(id=eq_id, name=eq_id, category=AssetCategories.SHEETS.value, instance=inst_name)`
* `properties = eq_props` (`SheetProperties`)
* `state = NoState()`
* `frame = AssetFactory.frame(recipe.frame)` (`StateFrame`)
* `hitbox = AssetFactory.hitbox(recipe.hitbox)` (`AttackHitbox` for `weapons` and `tools`; `None` for `armor`, `shields`, and `utilities`)
* `animation = None`


* Registering `hitbox: AttackHitbox` in `src/data/config/recipes/main.yaml` for `sheets.weapons` and `sheets.tools` is now the actual mechanism that injects `AttackHitbox` onto each weapon and tool `Asset`.


2. **`CombatMap.attackboxes()` (`src/app/game/logic/modules/maps/combat.py`)**:
* `CombatMap` no longer imports or instantiates `AttackHitbox`. Instead, it retrieves the weapon `Asset` from `equipment.weapons.get(weapon_key)` (via `state.slots.equipment.weapon`) and delegates directly to the `Asset` interface:
```python
weapon_key = state.slots.equipment.weapon if state.slots and state.slots.equipment else None
weapon = equipment.weapons.get(weapon_key) if weapon_key else None
if not weapon or not weapon.hitbox:
    return []
resolved_elevation = (
    elevation if elevation is not None
    else (state.elevation if state.elevation is not None else 0)
)
return weapon.hitbox.get(weapon.properties, state, resolved_elevation)

```




3. **`AnimationMap` & Menu `Binder` Call Sites**:
* Any module reading equipment properties from `board.equipment` (such as `AnimationMap.action(state, equipment)` checking `weapon.properties.actions` instead of `weapon_props.actions`) must dereference `.properties` on the retrieved `Asset`.


4. **Implications for `SpriteFrame` (`src/app/assets/frames/sheets.py`)**:
* `Registry._index()` already iterates over `self.properties.sheets.<instance>` and `self.recipes.sheets.<instance>`, instantiating `AssetFactory.frame(recipe.frame)` (`StateFrame`) to populate `Registry._frames` with valid `<eq_id>-<action>-<direction>-<frame>` crop tuples. Hydrating Equipment as `Asset`s on `Board.equipment` does not alter `Registry._index()`.
* At render time, `Screen._assemble()` calls `asset.frame.keys(asset.id, asset.state)`. Because `Frame.keys(id, state)` only accepts `(id: str, state: AssetState)` and does not receive `board.equipment`, `SpriteFrame.keys()` only has access to the string identifiers in `state.slots.equipment` (`eq.armor`, `eq.utility`, `eq.tool`, `eq.weapon`, `eq.shield`).
* However, because every Equipment `Asset` uses `StateFrame` and `SpriteFrame` subclasses `StateFrame`, `SpriteFrame.keys()` can delegate key generation to `super().keys(eq_key, state)` (`StateFrame.keys(eq_key, state)`) rather than manually formatting strings with `settings.SEPARATOR.join(...)`.
* **Why `Screen._assemble()` Currently Suppresses `SheetState` Registry Misses**: Because `SpriteFrame.keys()` only sees the string `eq_key` on `state.slots.equipment` and cannot inspect `weapon.properties.actions`, it emits keys like `"sword-walk-down-0"` when a sword-wielding sprite is walking (`sword` only indexes `lpc-slash` rows in `Registry._frames`). `Screen._assemble()` catches the resulting `None` from `self.registry.image(frame_key)` and suppresses the warning via `if not isinstance(asset.state, SheetState): logger.warning(...)`.
* Keeping `state.slots.equipment` as string keys (`Enumerated[WeaponPalette]`, etc.) preserves clean YAML state serialization (`Board.serialize()`) and keeps `Frame.keys(id, state)` signature-compatible across all Asset categories.



---

#### 2. Analysis of the Projectile Rotation Strategy (Phase 03.04 Preparation)

To support arbitrary angular subdivisions $\Delta \theta \in (0, 360]$ (e.g., $\Delta \theta = 90^\circ$ for 4-direction arrows, $\Delta \theta = 45^\circ$ for 8-direction cannonballs, $\Delta \theta = 15^\circ$ for radial bursts) from a single canonical frame (authored facing `left` / $\theta_0 = 180^\circ$ or $\theta_0 = 0^\circ$), there are two distinct architectural places where texture rotation can occur: **Load-Time Atlas Synthesis in `Registry**` vs. **Per-Frame Rotation in `Screen` / `render.pyx**`.

```mermaid
flowchart TD
    subgraph RouteA ["Route A: Registry Load-Time Rotation (Recommended)"]
        A1["Single-Frame PNG (w x l)<br/>+ ProjectileProperties (delta: int)"] --> A2["ProjectileFrame.index(id, props)<br/>Maps f'{id}-{angle}' -> (k*S, 0, S, S)"]
        A2 --> A3["Registry._get_or_load_texture()<br/>Calls render.rotate(base_tex, delta)<br/>Stamps N rotated cells via SDL_RenderCopyEx"]
        A3 --> A4["Screen._assemble() & render.render()<br/>Unchanged 13-tuple SDL_RenderCopy"]
    end

    subgraph RouteB ["Route B: Render-Loop Runtime Rotation"]
        B1["Single-Frame PNG (w x l)<br/>SingleFrame.index()"] --> B2["Frame.keys() / Screen._assemble()<br/>Must pass dynamic angle in 14-tuple"]
        B2 --> B3["render.render()<br/>Calls SDL_RenderCopyEx every frame"]
    end

```

##### Comparative Trade-Off Analysis

| Architectural Dimension | Route A: Registry Load-Time Rotation (`render.rotate`) | Route B: Render-Loop Runtime Rotation (`render.render`) |
| --- | --- | --- |
| **`Frame.index()` & `Frame.keys()` Contract** | **Preserved**: `ProjectileFrame.index(id, properties)` generates `f"{id}-{angle}"` crop keys across $N = \lfloor 360 / \Delta\theta \rfloor$ cells. `ProjectileFrame.keys(id, state)` returns `[(f"{id}-{state.angle}", 0, 0)]`. | **Broken / Widened**: `Frame.keys(id, state)` must either widen its return signature to 4-tuples `(key, ox, oy, angle)` across *all* `Frame` classes, or `Screen._assemble()` must inspect `getattr(asset.state, 'angle', 0.0)`. |
| **`Screen._assemble()` & `render.render()**` | **Zero changes**: `Screen._assemble()` still emits the standard 13-element integer primitive `(tex, sx, sy, sw, sl, dx, dy, dw, dl, r, g, b, a)`, and `render.render()` executes standard `SDL_RenderCopy`. | **Invasive changes**: Every primitive tuple in `Screen._assemble()` expands to 14 elements; `render.render()` must unpack `angle` and invoke `SDL_RenderCopyEx` on every frame. Conflicts with horizontal texture slicing (`submerge_channel`). |
| **VRAM & Runtime Cost** | Allocates one synthesized strip texture of size $(N \cdot S) \times S$ in VRAM per projectile ID during `Registry` load/prewarm (identical to how `Registry._stack()` uses `render.compose()`). Zero per-frame rotation overhead. | Single $(w \times l)$ texture in VRAM, but incurs per-instance `SDL_RenderCopyEx` overhead on every tick (especially costly under `headless=True` software rendering where `SDL_RenderCopyEx` performs CPU surface rotation every frame). |
| **Alignment with Ontology Philosophy** | Matches `Registry._stack()` + `render.compose()`: static visual variations defined by `Properties` belong to **Frame space** (`Frame.index`), not ad-hoc renderer flags. | Violates `Frame` encapsulation by pushing orientation state out of `Frame.keys()` and into `Screen._assemble()`. |

##### Detailed Requirements to Adopt Route A (Registry Load-Time Rotation)

1. **Canvas Bounding & Non-Clipping Geometry**:
* If a projectile image has dimensions $(w, l)$ and is rotated by $\Delta\theta$ around its center $(w/2, l/2)$, its axis-aligned bounding box expands to:

$$w'(\Delta\theta) = \lceil w |\cos\Delta\theta| + l |\sin\Delta\theta| \rceil, \qquad l'(\Delta\theta) = \lceil w |\sin\Delta\theta| + l |\cos\Delta\theta| \rceil$$


* If the source PNG is authored on a square canvas $w = l = S$ (such as $32 \times 32$ or $64 \times 64$ with transparent margin around the projectile shaft so the sprite lies within diameter $S$), rotating around $(S/2, S/2)$ never clips at any angle $\Delta\theta$, and every cell in the generated horizontal atlas has uniform dimensions $(S, S)$ at crop offset $(k \cdot S, 0, S, S)$ for $k \in \{0, 1, \dots, \lfloor 360/\Delta\theta \rfloor - 1\}$.


2. **Cython SDL2 Addition in `src/libs/graphics/render.pyx` & `registry.pyx**`:
* Declare `SDL_Point`, `SDL_RendererFlip` (`SDL_FLIP_NONE = 0`), and `SDL_RenderCopyEx` in `render.pyx`:
```cython
cdef extern from "SDL2/SDL.h":
    ctypedef struct SDL_Point:
        int x
        int y
    ctypedef enum SDL_RendererFlip:
        SDL_FLIP_NONE = 0x00000000
        SDL_FLIP_HORIZONTAL = 0x00000001
        SDL_FLIP_VERTICAL = 0x00000002

    int SDL_RenderCopyEx(
        SDL_Renderer* renderer,
        SDL_Texture* texture,
        const SDL_Rect* srcrect,
        const SDL_Rect* dstrect,
        const double angle,
        const SDL_Point* center,
        const SDL_RendererFlip flip
    )

```


* Add a `rotate(TexturePtr base_ptr, int delta) -> TexturePtr` helper in `render.pyx` (analogous to `compose()`):
* Computes $N = 360 // \text{delta}$.
* Allocates `target = canvas(base_ptr.w * N, base_ptr.l, opaque=False)`.
* Sets render target to `target.ptr` and loops $k \in [0, N)$, calling `SDL_RenderCopyEx(_renderer, base_ptr.ptr, &c_src, &c_dst, k * delta, NULL, SDL_FLIP_NONE)` where `c_dst = {k * w, 0, w, l}`.


* In `Registry._get_or_load_texture()`, if an asset has a rotation `delta` configured in its properties, invoke `render.rotate(raw_tex, delta)` before caching in `self._textures[asset_key]`.


3. **Hitbox Rotation (`RotatedHitbox` or Pre-Computed Angle Map)**:
* Because Cython's `geometry.intersects` operates strictly on AABBs (`Hitbox(Position(x, y), Dimensions(w, l))`), a single base hitbox $H_0 = (x_0, y_0, w_0, l_0)$ defined in the canonical orientation ($\Delta\theta = 0^\circ$) with center offset $(h_{cx}, h_{cy}) = (x_0 + w_0/2 - W/2,\; y_0 + l_0/2 - L/2)$ relative to the frame center $(W/2, L/2)$ is rotated by $\Delta\theta = k \cdot \text{delta}$ into AABB $H(\Delta\theta)$:

$$\begin{pmatrix} h'_{cx} \\ h'_{cy} \end{pmatrix} = \begin{pmatrix} \cos\Delta\theta & -\sin\Delta\theta \\ \sin\Delta\theta & \cos\Delta\theta \end{pmatrix} \begin{pmatrix} h_{cx} \\ h_{cy} \end{pmatrix}$$


$$w'(\Delta\theta) = \max\Big(1,\; \text{round}\big(w_0 |\cos\Delta\theta| + l_0 |\sin\Delta\theta|\big)\Big), \qquad l'(\Delta\theta) = \max\Big(1,\; \text{round}\big(w_0 |\sin\Delta\theta| + l_0 |\cos\Delta\theta|\big)\Big)$$


$$x'(\Delta\theta) = \text{round}\left(\frac{W}{2} + h'_{cx} - \frac{w'(\Delta\theta)}{2}\right), \qquad y'(\Delta\theta) = \text{round}\left(\frac{L}{2} + h'_{cy} - \frac{l'(\Delta\theta)}{2}\right)$$


* At cardinal angles ($\Delta\theta \in \{0^\circ, 90^\circ, 180^\circ, 270^\circ\}$), this transformation is exact with zero AABB bloat. At oblique angles ($\Delta\theta = 45^\circ$), authoring the projectile's hitbox around the projectile head (where $w_0 \approx l_0$) keeps the rotated AABB tight across all directions.


4. **Decoupling Phase 06.03 from Phase 03.04**:
* In `CombatMechanics.update()`, the unfinished ranged stub (`if attacker.state.animation.frame == 0 and not attacker.state.mutators.triggers.executed: ... spawn_projectile(id="TODO", velocity="TODO")`) is what caused Task 3.2 in the previous plan to propose adding `executed: bool = False` to `MutatorTriggers`.
* As noted in your review, mutating `MutatorTriggers` to support a `"TODO"` stub makes no sense. In **Phase 06.03**, `CombatMechanics.update()` should simply skip `Actions.SHOOT` and `Actions.CAST` (removing the broken `"TODO"` block), while the full Projectile Rotation implementation is codified in **Phase 03.04: Projectiles**.



---

### Updated Task Board Backlog

#### Refactor: Phase 06.03 - Combat

**Overview**

Induct `Equipment` into the `Board` as stateless `Asset` instances injected via `Recipe` configurations (`StateFrame` and `AttackHitbox`), unify `SheetProperties.attackboxes` into `SheetProperties.hitboxes`, resolve the structural separation between a Sprite's physical hurtbox (`StaticHitbox`) and its equipped weapon reach (`AttackHitbox`), enforce discrete elevation partitioning in `CombatMechanics`, remove the broken ranged `"TODO"` stub from `CombatMechanics.update()`, and migrate `test_combat.py` to the live `world-testbed` fixture framework.

##### Specification

In the Asset Hierarchy, `Sprites` (and `Players`) are stateful `Sheet` Assets deployed onto the `Board`, whereas `Equipment` (`weapons`, `tools`, `armor`, `shields`, `utilities`) are stateless `Sheet` Assets (`state = NoState()`) hydrated into `Board.equipment` (`EquipmentGroup`) during `Builder.build_board()` and projected onto a wielding Sprite's state.

1. **Stateless Equipment `Asset` Hydration (`EquipmentGroup` & `Recipes`)**:
* `EquipmentGroup` stores `Dict[str, Asset]` for `armor`, `weapons`, `tools`, `utilities`, and `shields`.
* During `Builder.build_board()`, each equipment entry in `PropertiesSchema.sheets` is instantiated as an `Asset` using its `Recipe` in `src/data/config/recipes/main.yaml`:
* `sheets.weapons` and `sheets.tools` inject `frame: StateFrame` and `hitbox: AttackHitbox`.
* `sheets.armor`, `sheets.shields`, and `sheets.utilities` inject `frame: StateFrame` and `hitbox: null`.




2. **Dual Footprint Separation (`StaticHitbox` vs. `AttackHitbox`)**:
* **Body Footprint (`Hitbox`)**: Owned by the deployed `Sprite` or `Player` (`Asset`). Resolved via `StaticHitbox` from `sprite.properties.hitboxes` (`List[Hitbox]`). Governs physical obstacle collision (`CollisionMechanics`), RRT pathfinding anchors (`NavigationMechanics`), environmental interactions (`InteractionMechanics`), fluid immersion (`MotionMechanics`), and incoming damage reception (`CombatMechanics`).
* **Action Footprint (`Attackbox`)**: Owned by stateless `Equipment` `Asset`s (`weapons` and `tools`). Resolved via `weapon.hitbox.get(weapon.properties, sprite.state, elevation)` (`AttackHitbox`) from `weapon.properties.hitboxes` (`Dict[str, List[Hitbox]]`) projected against the wielding entity's `SheetState` (`state.animation` and `state.elevation`).


3. **Property Schema Unification (`SheetProperties`)**:
* Consolidate `attackboxes` into a single polymorphic `hitboxes` field on `SheetProperties`:



$$\text{SheetProperties.hitboxes} : \text{Optional}\Big[\text{Union}\big[\text{Dict}[\text{str}, \text{List}[\text{Hitbox}]],\; \text{List}[\text{Hitbox}]\big]\Big]$$

* Deployed character sheets (`sprites`, `players`, `pixies`) configure `hitboxes` as `List[Hitbox]` (interpreted by `StaticHitbox`).
* Stateless equipment sheets (`weapons`, `tools`) configure `hitboxes` as `Dict[str, List[Hitbox]]` keyed by `<action>-<direction>-<frame>` (interpreted by `AttackHitbox`).

4. **Stateless Projection Contract (`CombatMap`)**:
* `CombatMap.attackboxes(state, equipment, elevation)` resolves the active weapon key from `state.slots.equipment.weapon`, retrieves the stateless weapon `Asset` from `equipment.weapons`, and delegates geometric resolution to `weapon.hitbox.get(weapon.properties, state, resolved_elevation)`.



##### Architectural Analysis II

1. **Resolving the Recipe Injection Inconsistency via Stateless Equipment `Asset`s**:
Previously, `Builder.build_board()` passed raw `SheetProperties` dictionaries into `EquipmentGroup`, rendering `recipes.sheets.weapons` unused outside of `Registry._index()` and forcing `CombatMap` to instantiate `AttackHitbox()` directly. By constructing stateless `Asset` instances (`state=NoState()`) for `EquipmentGroup` in `Builder.build_board()`, `AttackHitbox` is injected once via `AssetFactory.hitbox(recipe.hitbox)` and accessed polymorphically via `weapon.hitbox.get(weapon.properties, state, elevation)`.
2. **Impact on `AnimationMap` and `SpriteFrame**`:
* In `AnimationMap.action(state, equipment)`, looking up a weapon or tool in `equipment.weapons` or `equipment.tools` now returns an `Asset`; action resolution accesses `weapon.properties.actions` instead of `weapon_props.actions`.
* In `SpriteFrame.keys(id, state)`, because `Frame.keys()` receives only `(id: str, state: SpriteState)` and `state.slots.equipment` stores equipment string keys, `SpriteFrame.keys()` delegates equipment key formatting to `super().keys(eq_key, state)` (`StateFrame.keys`).


3. **Fixing `state.slots.equipment` Lookup in `CombatMap**`:
`CombatMap.attackboxes()` currently queries `state.inventory.equipment.weapon` (which raises `AttributeError` because `equipment` was moved to `state.slots.equipment` in Phase 06.04) and uses `Optional[int]` without importing `Optional`. Updating `CombatMap` to read `state.slots.equipment.weapon` and call `weapon.hitbox.get(...)` fixes both defects.
4. **Elevation Partitioning & Removal of Broken Ranged Stub in `CombatMechanics**`:
* `CombatMechanics.update()` currently hashes all attackers and targets on a `layer` into `self.grid` regardless of `elevation`, allowing an attacker at $E = 0$ to strike a target at $E = 1$. Enforcing `attacker.elevation == target.elevation` isolates melee combat to coplanar entities.
* Ranged projectile spawning (`Actions.SHOOT`, `Actions.CAST`) is currently an unimplemented `"TODO"` stub that crashes on `attacker.state.mutators.triggers.executed`. Rather than polluting `MutatorTriggers` with an `executed` flag for a stub, ranged projectile spawning is deferred to **Phase 03.04: Projectiles**, and `CombatMechanics.update()` cleanly skips `Actions.SHOOT` and `Actions.CAST` during melee attacker collection.



##### User Review I

**Inconsistencies In The Current Spec**

There appears to be an inconsistency in the plan or a misunderstanding of the injection system, as the CombatMap is instantiating a AttackHitbox, but the Task list has it also being registered as a component injected via Recipes. Equipment is not instantiated in the game, so registering it in a Recipe in the current implementation achieves nothing.

However, rather than storing Equipment Properties on the Board, it might be better to store Equipment *Assets* on the Board that can be referenced. That way, CombatMap has access to the hitbox and properties through the Asset interface.

Adoption of this strategy, however, may have implications with respect to SpriteFrame, insofar that currently SpriteFrame manages the injection of EquipmentFrames.

**Projectile Implementation**

Application is at the point where Projectiles need to be codified. There are two routes, as I see:

* Atlasing Route: Different directions of the Projectile are atlased in an Asset file.
* Rotation Route: A Projectile Asset contains a single Frame in a single Direction (say: `left`). When it is indexed by the Registry, it's coordinates are rotated by a fixed amount.

Atlasing fixes the number of Directions a Projectile can be fired. However, rotation allows for an arbitary division of degrees, e.g. arrows can fire in four directions (degree delta = 90) and cannonballs can fire in eight directions (degree delta = 45). However, rotation may require substantial changes in the rendering interface, so there are trade offs.

Do an analysis of what would be required to adopt the rotation strategy.

##### Goals

###### Goal: Unify `SheetProperties.hitboxes` and YAML Definitions

Replace `attackboxes` with `hitboxes` on `SheetProperties` in `src/app/models/properties/assets.py` so both character sheets (`List[Hitbox]`) and equipment sheets (`Dict[str, List[Hitbox]]`) share a single property field:

```python
# src/app/models/properties/assets.py
@dataclass(slots=True)
class SheetProperties(AssetProperties):
    stack: List[str] = field(default_factory=list)
    mass: int = 1
    actions: Union[
        str,
        Dict[Enumerated[Actions], Action]
    ] = field(default_factory=dict)
    hitboxes: Optional[Union[
        Dict[str, List[Hitbox]],
        List[Hitbox]
    ]] = field(default_factory=list)

```

Update `src/assets/sheets/equipment/weapons/main.yaml` and `src/assets/sheets/equipment/tools/main.yaml` to replace `attackboxes` with `hitboxes`.

###### Goal: Hydrate Stateless Equipment `Asset`s into `EquipmentGroup`

Update `EquipmentGroup` (`src/app/models/groups.py`) to hold `Dict[str, Asset]` and update `Builder.build_board()` (`src/app/services/orchestration/builder.py`) to construct stateless `Asset` objects (`state=NoState()`) for `armor`, `weapons`, `tools`, `utilities`, and `shields` using `recipes.sheets`:

```python
# src/app/models/groups.py
@dataclass(slots=True)
class EquipmentGroup:
    armor: Dict[str, Asset] = field(default_factory=dict)
    weapons: Dict[str, Asset] = field(default_factory=dict)
    tools: Dict[str, Asset] = field(default_factory=dict)
    utilities: Dict[str, Asset] = field(default_factory=dict)
    shields: Dict[str, Asset] = field(default_factory=dict)

```

###### Goal: Delegate `CombatMap.attackboxes` to the Weapon `Asset` Interface

Update `CombatMap.attackboxes` to resolve the equipped weapon from `state.slots.equipment.weapon` and invoke `weapon.hitbox.get(weapon.properties, state, resolved_elevation)` through the `Asset` interface:

```python
# src/app/game/logic/modules/maps/combat.py
from typing import List, Optional
from app.models.groups import EquipmentGroup
from app.models.state import SheetState
from libs.core.models import Hitbox

class CombatMap:
    @staticmethod
    def attackboxes(
        state: SheetState,
        equipment: EquipmentGroup,
        elevation: Optional[int] = None
    ) -> List[Hitbox]:
        weapon_key = state.slots.equipment.weapon
        weapon = equipment.weapons.get(weapon_key) if weapon_key else None
        if not weapon or not weapon.hitbox:
            return []
        resolved_elevation = (
            elevation if elevation is not None
            else (state.elevation if state.elevation is not None else 0)
        )
        return weapon.hitbox.get(weapon.properties, state, resolved_elevation)

```

###### Goal: Enforce Elevation Isolation and Clean Up `CombatMechanics.update()`

Remove the unfinished ranged `"TODO"` block from `CombatMechanics.update()` (deferring ranged projectile spawning to Phase 03.04) and enforce discrete elevation isolation (`attacker.elevation == target.elevation`) during melee collision resolution:

```python
# src/app/game/logic/mechanics/spatial/combat.py
for attacker in attackers:
    if attacker.state.animation.action in (
        Actions.SHOOT.value,
        Actions.CAST.value,
    ):
        continue

    attackboxes = CombatMap.attackboxes(attacker.state, board.equipment, attacker.elevation)
    if attackboxes:
        melee_attackers.append((attacker, attackboxes))

```

###### Goal: Induct `test_combat.py` into the Live Fixture Framework

Remove all `_create_*` helper functions, `MagicMock` instances, and monkeypatched `mock_board` lambdas from `tests/unit/app/game/logic/mechanics/spatial/test_combat.py`. Execute all combat tests against `mock_mechanic(Mechanics.COMBAT.value)`, `mock_board`, `mock_bus`, and `mock_payload`.

##### Tasks

**1. Task: Unify `SheetProperties.hitboxes` and Equipment YAML Assets**

*Objective*: Consolidate `attackboxes` into `hitboxes` on `SheetProperties` and update all Equipment YAML definitions.

* [] Subtask: Update `SheetProperties` in `src/app/models/properties/assets.py` so `hitboxes` accepts `Optional[Union[Dict[str, List[Hitbox]], List[Hitbox]]]` and remove the legacy `attackboxes` field.
* [] Subtask: Replace `attackboxes` with `hitboxes` (and remove duplicate `hitboxes: null` keys) in `src/assets/sheets/equipment/weapons/main.yaml` and `src/assets/sheets/equipment/tools/main.yaml`.

**2. Task: Hydrate Stateless Equipment `Asset`s in `EquipmentGroup` and `Builder**`

*Objective*: Store stateless `Asset` instances in `Board.equipment` (`EquipmentGroup`) injected via `recipes/main.yaml` and update all `board.equipment` consumers.

* [] Subtask: Register `hitbox: AttackHitbox` for `sheets.weapons` and `sheets.tools` in `src/data/config/recipes/main.yaml`.
* [] Subtask: Update `EquipmentGroup` in `src/app/models/groups.py` to type `armor`, `weapons`, `tools`, `utilities`, and `shields` as `Dict[str, Asset]`.
* [] Subtask: Update `Builder.build_board()` in `src/app/services/orchestration/builder.py` to instantiate stateless `Asset` objects (`state=NoState()`) for each equipment dictionary using `AssetFactory` and `self.context.configurations.recipes.sheets`.
* [] Subtask: Update `AnimationMap` (and any Menu `Binder` / controller call sites) that access `board.equipment` to read `.properties` from the retrieved Equipment `Asset`, and simplify `SpriteFrame.keys()` in `src/app/assets/frames/sheets.py` to delegate equipment key formatting to `super().keys(eq_key, state)`.

**3. Task: Wire `CombatMap` and Harden `CombatMechanics**`

*Objective*: Route `CombatMap.attackboxes()` through `weapon.hitbox.get()`, enforce elevation isolation in `CombatMechanics.update()`, and remove the broken ranged stub.

* [] Subtask: Fix `CombatMap.attackboxes()` in `src/app/game/logic/modules/maps/combat.py` to import `Optional`, read `state.slots.equipment.weapon`, and delegate hitbox lookup to `weapon.hitbox.get(weapon.properties, state, resolved_elevation)`.
* [] Subtask: Remove the unimplemented ranged `"TODO"` block in `CombatMechanics.update()` (`src/app/game/logic/mechanics/spatial/combat.py`), skip `Actions.SHOOT` and `Actions.CAST` in melee resolution, remove the defensive `getattr(target.state, 'mutators', None)` check, and enforce `attacker.elevation == target.elevation` on colliding pairs.
* [] Subtask: Add unit tests for `AttackHitbox.elevations()` and `AttackHitbox.get()` and update `tests/unit/app/game/logic/modules/maps/test_combat_maps.py` to test against stateless Equipment `Asset`s.

**4. Task: Refactor `test_combat.py` to Use `world-testbed` Fixtures**

*Objective*: Replace all ad-hoc asset builders and `MagicMock` overrides in `tests/unit/app/game/logic/mechanics/spatial/test_combat.py` with live `mock_board` and `mock_mechanic` fixtures.

* [] Subtask: Remove `_create_player_attacker`, `_create_sprite_target`, `_create_reactable_target`, and `_create_equipment` from `tests/unit/app/game/logic/mechanics/spatial/test_combat.py`.
* [] Subtask: Refactor `test_combat_mechanics_melee_resolution`, `test_combat_mechanics_lethal_blow`, `test_combat_mechanics_reactable_trigger`, `test_combat_mechanics_inactive_attackbox_filtered`, and `test_combat_mechanics_unarmed_bypasses_melee` to query `mock_board.player()`, `mock_board.instances(AssetInstances.SPRITES.value, "0")`, and `mock_board.instances(AssetInstances.REACTABLES.value, "0")`.
* [] Subtask: Add `test_combat_mechanics_elevation_isolation` to verify that an attacker at `elevation = 0` cannot damage an overlapping target at `elevation = 1`.

---

### Proposed Backlog Entry: Phase 03.04 - Projectiles

To codify the Rotation Route analyzed above into the backlog for **Phase 03.04**, here is the structured Phase specification following the Backlog Template (`with(not grooming)`):

#### Refactor: Phase 03.04 - Projectiles

**Overview**

Codify `Projectiles` (`cursors.projectiles`) using the Registry Load-Time Rotation strategy (`ProjectileFrame`, `RotatedHitbox`, and `render.rotate`), allowing a single canonical projectile texture frame to be quantized into arbitrary angular increments ($\Delta\theta \in (0, 360]$) in VRAM without modifying the 60 Hz `Screen._assemble()` / `render.render()` pipeline. Wire ranged combat spawning in `CombatMechanics` and trajectory/impact resolution in `ProjectileMechanics`.

##### Specification

1. **Angular Partitioning (`CursorProperties`)**:
* Extend `CursorProperties` (`src/app/models/properties/assets.py`) with `delta: int = 90` (degrees per discrete rotational step, where $360 \bmod \text{delta} == 0$) and `speed: int = 200`.
* The discrete set of valid projectile angles is $\Theta = \{ k \cdot \text{delta} \mid 0 \le k < 360 // \text{delta} \}$.


2. **Load-Time Texture Strip Synthesis (`ProjectileFrame` & `Registry`)**:
* Authored projectile `.png` files contain a single canonical frame of square dimensions $(S, S)$ oriented at $\theta = 0^\circ$ (or canonical `left`).
* `ProjectileFrame.index(id, properties)` maps each discrete angle key `f"{id}-{angle}"` ($\text{angle} = k \cdot \text{delta}$) to crop coordinate $(k \cdot S, 0, S, S)$.
* `Registry._get_or_load_texture()` detects `delta` on projectile properties and invokes `render.rotate(raw_tex, delta)`, which allocates a target `TexturePtr` of dimensions $(N \cdot S, S)$ where $N = 360 // \text{delta}$ and stamps the base texture $N$ times via `SDL_RenderCopyEx`.
* `ProjectileFrame.keys(id, state)` projects `state.angle` directly to `[(f"{id}-{state.angle}", 0, 0)]`.


3. **Rotated AABB Hitbox Projection (`RotatedHitbox`)**:
* `RotatedHitbox.get(properties, state, elevation)` rotates each base `Hitbox` in `properties.hitboxes` by $\Delta\theta = \text{state.angle}$ around the frame center $(S/2, S/2)$:



$$\begin{pmatrix} h'_{cx} \\ h'_{cy} \end{pmatrix} = \begin{pmatrix} \cos\Delta\theta & -\sin\Delta\theta \\ \sin\Delta\theta & \cos\Delta\theta \end{pmatrix} \begin{pmatrix} h_{cx} \\ h_{cy} \end{pmatrix}$$

$$w'(\Delta\theta) = \max\Big(1,\; \text{round}\big(w_0 |\cos\Delta\theta| + l_0 |\sin\Delta\theta|\big)\Big), \qquad l'(\Delta\theta) = \max\Big(1,\; \text{round}\big(w_0 |\sin\Delta\theta| + l_0 |\cos\Delta\theta|\big)\Big)$$

##### Goals

###### Goal: Implement `render.rotate` in Cython SDL2 Bindings

Expose `SDL_RenderCopyEx` in `src/libs/graphics/render.pyx` and implement `rotate(TexturePtr base_ptr, int delta) -> TexturePtr` to pre-bake rotated projectile frames into a single horizontal `TexturePtr` strip during Registry texture loading.

###### Goal: Implement `ProjectileFrame` and `RotatedHitbox`

Create `ProjectileFrame` (`src/app/assets/frames/cursors.py`) and `RotatedHitbox` (`src/app/assets/hitboxes/cursors.py`) and register them under `recipes.cursors.projectiles` in `src/data/config/recipes/main.yaml`.

###### Goal: Wire Ranged Spawning in `Cradle` and Impact Resolution in `ProjectileMechanics`

Update `Cradle.spawn_projectile()` to quantize launch angles to `properties.delta`, compute initial `Velocity(vx, vy)`, and instantiate the projectile `Asset` at the attacker's `elevation`. Update `ProjectileMechanics` to integrate trajectories, enforce elevation-isolated impact detection, apply damage, and garbage-collect expired projectiles.

##### Tasks

**1. Task: Add Cython `render.rotate` and Registry Load-Time Rotation**

*Objective*: Synthesize rotated texture strips in VRAM during `Registry` texture loading.

* [] Subtask: Declare `SDL_Point`, `SDL_RendererFlip`, and `SDL_RenderCopyEx` in `src/libs/graphics/render.pyx` and implement `rotate(TexturePtr base_ptr, int delta) -> TexturePtr`.
* [] Subtask: Update `CursorProperties` in `src/app/models/properties/assets.py` to include `delta: Optional[int] = None` and `speed: int = 200`, and update `MotorState` (`src/app/models/state/assets/cursors.py`) to include `angle: int = 0`.
* [] Subtask: Update `Registry._get_or_load_texture()` in `src/libs/graphics/registry.pyx` to invoke `render.rotate()` when loading a projectile texture with a configured `delta`.

**2. Task: Implement `ProjectileFrame` and `RotatedHitbox**`

*Objective*: Index rotated projectile frame crops and transform base AABB hitboxes by `state.angle`.

* [] Subtask: Implement `ProjectileFrame` in `src/app/assets/frames/cursors.py` to index `f"{id}-{k * delta}"` crops and resolve `[(f"{id}-{state.angle}", 0, 0)]` in `keys()`.
* [] Subtask: Implement `RotatedHitbox` in `src/app/assets/hitboxes/cursors.py` to project base `properties.hitboxes` around the frame center by `state.angle` at the projectile's `elevation`.
* [] Subtask: Register `ProjectileFrame` and `RotatedHitbox` under `cursors.projectiles` in `src/data/config/recipes/main.yaml`.

**3. Task: Implement `Cradle.spawn_projectile`, `CombatMechanics` Ranged Trigger, and `ProjectileMechanics**`

*Objective*: Complete the end-to-end lifecycle of ranged projectiles from release frame to target impact or boundary removal.

* [] Subtask: Update `Cradle.spawn_projectile()` to quantize direction/target vectors onto the nearest multiple of `properties.delta` and populate `MotorState`.
* [] Subtask: Wire ranged projectile spawning in `CombatMechanics.update()` on the release frame of `Actions.SHOOT`.
* [] Subtask: Update `ProjectileMechanics.update()` to evaluate elevation-partitioned intersections against targets and obstacles and queue impacted or out-of-bounds projectiles for removal.

---

### Bug Reports

##### Bug 001: `CombatMap.attackboxes` Raises `NameError` on Import and `AttributeError` on Equipment Slot Lookup

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

In `src/app/game/logic/modules/maps/combat.py`, two defects prevent `CombatMap.attackboxes()` from executing:

1. Line 12 imports `from typing import List` without `Optional` (and without `from __future__ import annotations`), causing `elevation: Optional[int] = None` on line 25 to raise `NameError: name 'Optional' is not defined` at import time.
2. Line 27 accesses `state.inventory.equipment.weapon`. Following Phase 06.04 (`Inventory`), active equipment is stored on `state.slots.equipment` (`Slots`), whereas `state.inventory` (`Inventory`) only holds unequipped storage containers (`bag`, `belt`, `sheathe`, `pouch`, `pack`, `sack`). Calling `CombatMap.attackboxes()` raises `AttributeError: 'Inventory' object has no attribute 'equipment'`.

**Steps to Replicate**

1. Import `CombatMap` from `app.game.logic.modules.maps.combat` (raises `NameError` unless `Optional` is imported).
2. Pass a hydrated `SpriteState` or `SheetState` and `board.equipment` to `CombatMap.attackboxes(state, board.equipment)`.
3. Observe `AttributeError: 'Inventory' object has no attribute 'equipment'` on line 27.

**Proposed Remeditation**

Import `Optional` from `typing`, resolve `weapon_key` via `state.slots.equipment.weapon`, and delegate hitbox retrieval to the weapon `Asset` (`weapon.hitbox.get(weapon.properties, state, resolved_elevation)`).

##### Bug 002: `SheetProperties` Declares `attackboxes` Instead of `hitboxes`, Silently Dropping Sprite Hitboxes

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

In `src/app/models/properties/assets.py` (lines 117–128), `SheetProperties` still defines `attackboxes` and omits `hitboxes`. However, `src/assets/sheets/sprites/main.yaml` configures physical hurtboxes under the `hitboxes:` key for `player`, `jasilynn`, and `archaxes`. When `Loader.load_properties()` validates `SheetProperties` via Pydantic `TypeAdapter`, the `hitboxes` key in `sprites/main.yaml` is silently ignored, leaving `sprite.properties` without a `hitboxes` attribute when `StaticHitbox.get()` queries it.

**Steps to Replicate**

1. Load properties via `Loader.load_properties()`.
2. Inspect `properties.sheets.sprites["player"]`.
3. Observe that `hasattr(properties.sheets.sprites["player"], "hitboxes")` is `False` and the configured hitbox in `src/assets/sheets/sprites/main.yaml` was discarded.

**Proposed Remeditation**

Rename `attackboxes` to `hitboxes: Optional[Union[Dict[str, List[Hitbox]], List[Hitbox]]] = field(default_factory=list)` on `SheetProperties` in `src/app/models/properties/assets.py`, and replace `attackboxes` with `hitboxes` in `src/assets/sheets/equipment/weapons/main.yaml` and `src/assets/sheets/equipment/tools/main.yaml`.

##### Bug 003: Unfinished Ranged Combat Stub in `CombatMechanics.update` Crashes on `Actions.SHOOT` and `Actions.CAST`

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

In `src/app/game/logic/mechanics/spatial/combat.py` (lines 76–88), when an entity in `Intentions.ATTACK` has `state.animation.action` equal to `Actions.SHOOT.value` or `Actions.CAST.value`, execution enters an unfinished ranged combat block that accesses `attacker.state.mutators.triggers.executed`. Because `MutatorTriggers` (`src/app/models/state/core.py`) does not define `executed`, an `AttributeError` is raised at `frame == 0` (and at `frame != 0`).

**Steps to Replicate**

1. Set a deployed Sprite or Player state to `intention = Intentions.ATTACK.value` with `animation.action = Actions.CAST.value` (unarmed) or `Actions.SHOOT.value` (`longbow`).
2. Execute `CombatMechanics().update(board, delta, bus, payload)`.
3. Observe `AttributeError: 'MutatorTriggers' object has no attribute 'executed'`.

**Proposed Remeditation**

Remove the unfinished ranged combat `"TODO"` block from `CombatMechanics.update()` and skip `Actions.SHOOT.value` and `Actions.CAST.value` during melee attacker resolution until **Phase 03.04: Projectiles** is implemented.

---

### Documentation Updates

*(Note: The `@TODO(06-03)` markers in `docs/04-intentions.md` under `Goal: Category` (`resource`) and `Workflow Component: Cognition` (`doors`) concern Goal semantics for **Phase 06.02: Goals**, which has not yet been started on the Task Board.)*

##### Draft: Sheet Hitboxes, Stateless Equipment Assets, and Substrate Sort Keys

* **Page**: `docs/01-assets.md`
* **Heading**: `##### Assets: Overview -> ###### Concept: Appearance` & `##### Assets: Categories -> ###### Category: Sheets`

###### Drift

1. Under `###### Concept: Appearance -> **Substrates**`, `@TODO(07-03)` notes that the paragraph claiming negative substrates are collapsed into `elevation = 0` during `CollisionMechanics` is obsolete: `substrate` ($\le 0$) and `elevation` ($\ge 0$) are now independent attributes on `Asset` forming the first two components of `sort_key(A) = (elevation, substrate, ground, priority)`.
2. Under `###### Category: Sheets -> **Hitbox: Attackboxes**` (`@TODO(06-03)`), `**Properties: SheetProperties**`, and `###### Sheet: Equipment`, the documentation still lists `attackboxes` as a separate field on `SheetProperties`, uses the legacy `get(properties, state, frame)` signature on `StaticHitbox`, and states that Equipment only has Properties (whereas Equipment is now hydrated into `Board.equipment` as stateless `Asset`s with injected `SheetProperties`, `StateFrame`, and `AttackHitbox`).

###### Update

```markdown
**Substrates**

Certain Assets have a dedicated Substrate (`asset.substrate` $\in \mathbb{Z}_{\le 0}$) to preserve intra-elevation rendering order within a macro-elevation tier $E \in \mathbb{Z}_{\ge 0}$. These values are hydrated onto the Asset directly via [MaterialIndex](./appendices/01-schemas.md#configuration-materials) during [hydration](./12-architecture.md#phase-2-hydration) and occupy the secondary slot of the render sort key `(elevation, substrate, ground, priority)`. Physical collision and boundary resolution operate strictly on `asset.elevation` via `HitboxSchema.elevations()`, independent of `asset.substrate`.

--8<-- "static/md/asset-substrates.md"

```

```markdown
**Hitbox: StaticHitbox & AttackHitbox**

Sheet Assets utilize a unified polymorphic `hitboxes` property on `SheetProperties` interpreted by the `HitboxSchema` injected via their [Recipe](./appendices/01-schemas.md#configuration-recipes):

- **Deployed Character Sheets (`sprites`, `players`, `pixies`)**: Configure `hitboxes` as `List[Hitbox]` representing the entity's physical body footprint. Injected with `StaticHitbox`:
  * `elevations(properties, state): returns [max(0, state.elevation or 0)]`
  * `get(properties, state, elevation): returns properties.hitboxes if elevation == max(0, state.elevation or 0) else []`
- **Stateless Equipment Sheets (`weapons`, `tools`)**: Configure `hitboxes` as `Dict[str, List[Hitbox]]` mapped to canonical `<action>-<direction>-<frame>` keys (where `settings.SEPARATOR = "-"`). Injected with `AttackHitbox`:
  * `elevations(properties, state): returns [max(0, state.elevation or 0)]`
  * `get(properties, state, elevation): returns properties.hitboxes.get(f"{state.animation.action}-{state.animation.direction}-{state.animation.frame}", []) if elevation == max(0, state.elevation or 0) else []`

**Properties: SheetProperties(AssetProperties)**

- `dimensions: Dimensions`
- `stack: List[str]`
- `hitboxes: Optional[Union[Dict[str, List[Hitbox]], List[Hitbox]]]`
- `actions: Union[str, Dict[Enumerated[Actions], Action]]`
- `mass: int = 1`

###### Sheet: Equipment

- Equipment: Weapons, Utilities, Tools, Armor, Shields

Equipment is a group of stateless Asset Instances within the Category of Sheets (`EquipmentGroup`) hydrated onto `Board.equipment` during `Builder.build_board()`. Because Equipment rendering and action hitboxes depend on the wielding Sprite's `SheetState`, Equipment Assets are instantiated with `state = NoState()`, `animation = None`, `frame = StateFrame()`, and (for `weapons` and `tools`) `hitbox = AttackHitbox()`.

```

##### Draft: Equipment Slot Paths and Stateless Equipment Assets on `Board`

* **Page**: `docs/02-sprites.md`
* **Heading**: `##### Specification: Sprites -> ###### Equipment: Frame` & `###### Equipment: Animation`

###### Drift

In `docs/02-sprites.md`, `###### Equipment: Frame` refers to `sprite.state.inventory.equipment` in prose (while the YAML snippet below it uses `slots.equipment`), and `###### Equipment: Animation` states that `Board.equipment` stores raw `Equipment Properties` rather than stateless Equipment `Asset`s.

###### Update

```markdown
###### Equipment: Frame

Equipment is hydrated onto `Board.equipment` (`EquipmentGroup`) as stateless Sheet `Asset`s (`state = NoState()`). Because Equipment does not possess its own deployment state in `/src/data/state/<board-key>/**`, it is not deployed onto Board layers by the Migrator. Instead, Equipment Frame keys are projected dynamically by `SpriteFrame.keys()` when a Sprite or Player has Equipment slotted in `state.slots.equipment`:

``` yaml
# /src/data/state/<board-key>/sheets.sprites.state.slots: 
equipment:
    armor: leather
    tool: shovel
    utility: lantern
    shield: buckler
    weapon: dagger

```

###### Equipment: Animation

When Equipment is configured in the Sheet Property index file, the Equipment `Asset`'s `properties.actions` dictionary determines which Actions in a Sprite's state are enterable from animated Intentions (`attack`, `mine`) via `AnimationMap.action(sprite.state, board.equipment)` and which `<action>-<direction>-<frame>` hitboxes are projected during combat via `CombatMap.attackboxes(sprite.state, board.equipment, sprite.elevation)`.

!!! note "Equipment Assets" Stateless Equipment `Asset` instances (bundling `SheetProperties`, `StateFrame`, and `AttackHitbox`) are stored in `Board.equipment`, *not* on the Sprite Asset.

```

##### Draft: Elevation-Partitioned Collision Pipeline in `CollisionMechanics`

- **Page**: `docs/05-mechanics.md`
- **Heading**: `###### Spatial Mechanic: CollisionMechanics`

###### Drift

Marked with `!!! @TODO Out of date.` (`phase = None`). The section does not document the 3-phase elevation-partitioned pipeline introduced in Phases 07.02–07.03 (Phase 0 stair incline transitions, Phase 1 ground-tier $E = 0$ perimeter constraint solving allowing un-walled ledge drops at $E > 0$, and Phase 2 per-elevation solid-body collision and momentum resolution with airborne `falling` exclusion). Additionally, the `SpatialMechanics` base summary above it omits the `elevation` parameter on `collisions(assets, elevation=None)`.

###### Update

```markdown
###### Spatial Mechanic: CollisionMechanics

`CollisionMechanics` resolves topological elevation transitions, environmental perimeter constraints, and solid-body elastic collisions across three deterministic phases per active layer. Airborne entities (`state.mutators.triggers.falling == True`) are excluded from all three phases so freefall kinematics execute unobstructed across elevation planes.

1. **Phase 0 — Incline Traversal (`_traverse_stairs`)**:
   * Strictly prior to elevation tier partitioning, dynamic entities intersecting `crafts.stairs` evaluate directional velocity against the stair's `state.blueprint` (`left`, `right`, `down`) and mutate `asset.state.elevation += ±stairs.state.delta`.
   * Executing Phase 0 first guarantees that elevation transitions take effect within the current frame's broad-phase spatial hash.

2. **Phase 1 — Environmental Perimeter Constraints ($E = 0$)**:
   * Queries `self.constrain(weights_at_e0, boundaries, elevation=0)` via `physics.boundaries` and resolves overlaps via `physics.constrain`.
   * Perimeter hulls are enforced strictly at base terrain (`elevation == 0`), allowing dynamic entities at elevated tiers ($E > 0$) to walk off un-walled platform ledges into gravitational freefall.

3. **Phase 2 — Elevation-Partitioned Solid Collisions & Momentum Transfer**:
   * Non-falling weights (`board.weights(layer, elevation=tier)`) are partitioned by discrete elevation tier $E \in \mathbb{Z}_{\ge 0}$, ensuring entities only collide with obstacles and bodies whose `HitboxSchema.elevations()` includes tier $E$.
   * Overlapping pairs returned by `self.collisions(tier_weights, elevation=tier)` are resolved via `physics.collide`:
     * **Spatial Separation**: Overlapping bodies shift apart along the minimum penetration axis proportional to their inverse mass ratios ($p_i = \frac{1/m_i}{1/m_1 + 1/m_2}$). Static bodies ($m = 0$) absorb $0\%$ of the shift ($1/m \to 0$), forcing dynamic bodies ($m > 0$) to absorb $100\%$ of the displacement.
     * **1D Elastic Momentum Transfer**: Post-separation velocities update via conservation of momentum:

$$
v_{1f} = \frac{v_1(m_1 - m_2) + 2m_2v_2}{m_1 + m_2}, \qquad v_{2f} = \frac{v_2(m_2 - m_1) + 2m_1v_1}{m_1 + m_2}
$$

     * **Player Kinematic Exemption**: The Player retains positive dynamic mass ($m > 0$) during spatial separation—halting against static walls ($m = 0$) and pushing movable Crates ($m > 0$)—but passes `is_kinematic = True` to `physics.collide` to bypass elastic velocity bounce.

```



















##### Math: Paths

- Address: `libs.core.math.paths`

Given a start coordinate $\mathbf{s} = (s_x, s_y)$, a target coordinate $\mathbf{t} = (t_x, t_y)$, a step size $\delta > 0$, an iteration limit $N_{\max}$, and a set of obstacle rectangles $\mathcal{O}$ (inflated in configuration space by the navigating entity's hitbox half-dimensions and clearance radius), pathfinding constructs a collision-free trajectory from $\mathbf{s}$ to $\mathbf{t}$ via a Rapidly-exploring Random Tree (RRT):

1. **Search Window Partitioning**:
   Define a padded search domain enclosing $\mathbf{s}$ and $\mathbf{t}$ with margin $\mathbf{m} = (0.2|t_x - s_x| + 2\delta,\; 0.2|t_y - s_y| + 2\delta)$:

$$
[x_{\min}, x_{\max}] = [\min(s_x, t_x) - m_x,\; \max(s_x, t_x) + m_x], \qquad [y_{\min}, y_{\max}] = [\min(s_y, t_y) - m_y,\; \max(s_y, t_y) + m_y]
$$

   If $x_{\min} < 0$ or $y_{\min} < 0$, the negative offset is added to the corresponding upper bound and the lower bound is clamped to $0$. The active obstacle set is restricted to $\mathcal{O}_{\text{local}} = \{R \in \mathcal{O} \mid R \cap ([x_{\min}, x_{\max}] \times [y_{\min}, y_{\max}]) \neq \emptyset\}$.

2. **Goal-Biased Tree Expansion**:
   Initialize a tree $\mathcal{T} = (V, E)$ rooted at $\mathbf{v}_0 = \mathbf{s}$. For up to $N_{\max}$ iterations:
   - **Sampling**: Draw $u, u_x, u_y \sim \mathcal{U}(0, 1)$ with goal bias $p_{\text{goal}} = 0.05$:

$$
\mathbf{q} = \begin{cases} \mathbf{t} & \text{if } u \le p_{\text{goal}} \\ \big(x_{\min} + u_x(x_{\max} - x_{\min}),\; y_{\min} + u_y(y_{\max} - y_{\min})\big) & \text{otherwise} \end{cases}
$$

   - **Nearest Neighbor**: Select the tree vertex $\mathbf{v}_{\text{near}} \in V$ minimizing Euclidean distance to $\mathbf{q}$:

$$
\mathbf{v}_{\text{near}} = \arg\min_{\mathbf{v} \in V} \|\mathbf{v} - \mathbf{q}\|_2
$$

   - **Clamped Steering**: Step from $\mathbf{v}_{\text{near}}$ toward $\mathbf{q}$ by distance $d = \min(\delta, \|\mathbf{q} - \mathbf{v}_{\text{near}}\|_2)$ along angle $\theta = \operatorname{atan2}(q_y - v_{\text{near},y},\; q_x - v_{\text{near},x})$:

$$
\mathbf{v}_{\text{new}} = \mathbf{v}_{\text{near}} + d\begin{pmatrix} \cos\theta \\ \sin\theta \end{pmatrix}
$$

   - **Edge Validation & Termination**: If the segment $\overline{\mathbf{v}_{\text{near}}\mathbf{v}_{\text{new}}}$ is unobstructed across $\mathcal{O}_{\text{local}}$, add $\mathbf{v}_{\text{new}}$ to $V$ with parent $\mathbf{v}_{\text{near}}$. If $\mathbf{v}_{\text{new}} = \mathbf{t}$, or if $\|\mathbf{t} - \mathbf{v}_{\text{new}}\|_2 \le \delta$ and $\overline{\mathbf{v}_{\text{new}}\mathbf{t}}$ is unobstructed, append $\mathbf{t}$ to $\mathcal{T}$ and terminate exploration.

3. **Backtracing & String-Pulling Pruning**:
   Traverse parent links from $\mathbf{t}$ to $\mathbf{v}_0$ and reverse the sequence to form the unpruned chain $\mathbf{p}_0, \mathbf{p}_1, \dots, \mathbf{p}_k$ ($\mathbf{p}_0 = \mathbf{s}$, $\mathbf{p}_k = \mathbf{t}$). Redundant intermediate vertices are collapsed via greedy line-of-sight string-pulling:
   - From current anchor index $i$ (initialized to $0$), select the largest index $j \in (i, k]$ for which $\overline{\mathbf{p}_i\mathbf{p}_j}$ is unobstructed across $\mathcal{O}_{\text{local}}$ (defaulting to $j = i + 1$ if no further vertex has line of sight).
   - Emit $\mathbf{p}_j$, advance $i \leftarrow j$, and repeat until $i = k$.

##### Math: Space

- Address: `libs.core.math.space`

To avoid $O(N^2)$ pairwise comparisons over $N$ entities, the plane is partitioned into a uniform grid of cell size $C > 0$ mapped across $M$ hash buckets:

1. **Grid Discretization**:
   An entity with bounding box $[x, x + w] \times [y, y + l]$ covers the integer cell coordinates:

$$
c_x \in \left[\left\lfloor \frac{x}{C} \right\rfloor,\; \left\lfloor \frac{x + w}{C} \right\rfloor\right], \qquad c_y \in \left[\left\lfloor \frac{y}{C} \right\rfloor,\; \left\lfloor \frac{y + l}{C} \right\rfloor\right]
$$

2. **Spatial Hashing**:
   Each covered cell $(c_x, c_y)$ maps to a 1D bucket index $h(c_x, c_y) \in \{0, \dots, M - 1\}$ via multiplicative prime hashing:

$$
h(c_x, c_y) = (c_x \cdot p_1 \oplus c_y \cdot p_2) \bmod M
$$

   where $p_1, p_2$ are large coprime integers. The entity identifier is inserted into each bucket its bounding box intersects.

3. **Candidate Pair Generation**:
   Iterating through populated buckets yields unique unordered pairs $(i, j)$ with $i < j$ that share at least one spatial bucket, forming the broad-phase candidate set for narrow-phase evaluation.

##### Math: Physics

- Address: `libs.core.math.physics`

This module governs collision detection, minimum-translation separation, elastic momentum transfer, boundary constraints, locomotion steering, friction decay, and numerical integration:

1. **Two-Phase Collision Pipeline**:
   - **Broad Phase**: Entities are hashed into the uniform spatial grid by their bounding footprints to produce candidate pairs $(A_1, A_2)$.
   - **Narrow Phase**: Candidate pairs are evaluated for intersection across their offset hitboxes $\mathcal{H}(A_1) \cap \mathcal{H}(A_2) \neq \emptyset$.

2. **Minimum Translation Vector & Inverse-Mass Separation**:
   For two intersecting hitboxes $H_1 = [x_1, x_1 + w_1] \times [y_1, y_1 + l_1]$ and $H_2 = [x_2, x_2 + w_2] \times [y_2, y_2 + l_2]$ with centers $\mathbf{c}_1, \mathbf{c}_2$, the axial overlap depths are:

$$
\delta_x = \frac{w_1 + w_2}{2} - |c_{1,x} - c_{2,x}|, \qquad \delta_y = \frac{l_1 + l_2}{2} - |c_{1,y} - c_{2,y}|
$$

   Separation occurs along the axis of minimum penetration $\delta = \min(\delta_x, \delta_y)$ with unit normal $\hat{\mathbf{n}}$. Define each body's inverse mass $\mu_i$ such that static obstacles ($m_i = 0$) have $\mu_i = 0$ ($m_i \to \infty$) and dynamic bodies ($m_i > 0$) have $\mu_i = 1 / m_i$. For $\mu_{\text{total}} = \mu_1 + \mu_2 > 0$, each body is displaced in proportion to its inverse mass share:

$$
\Delta \mathbf{r}_1 = -\delta \left(\frac{\mu_1}{\mu_{\text{total}}}\right) \hat{\mathbf{n}}, \qquad \Delta \mathbf{r}_2 = +\delta \left(\frac{\mu_2}{\mu_{\text{total}}}\right) \hat{\mathbf{n}}
$$

3. **One-Dimensional Elastic Momentum Transfer**:
   Along the collision normal, post-separation velocities $(v_{1f}, v_{2f})$ follow conservation of momentum and kinetic energy:

$$
v_{1f} = \frac{v_1(m_1 - m_2) + 2m_2 v_2}{m_1 + m_2}, \qquad v_{2f} = \frac{v_2(m_2 - m_1) + 2m_1 v_1}{m_1 + m_2}
$$

   Against a static body ($m_2 = 0 \implies m_2 \to \infty$), the dynamic body's normal velocity inverts ($v_{1f} = -v_1$). Kinematic entities participate in inverse-mass spatial separation using their nominal mass $m_1 > 0$, but bypass velocity reassignment.

4. **Boundary Hull Constraints**:
   Environmental perimeters act as directed barriers with $\mu_{\text{bound}} = 0$. When an entity's hitbox penetrates a boundary segment, the entity is displaced out of the overlap along the boundary normal by penetration depth $\delta$ and its normal velocity component is inverted.

5. **Locomotion Kinematics & Steering Dynamics**:
   - **Direct Kinematics**: Given directional input vector $\mathbf{d}_{\text{input}}$ and speed $s$, non-active axes snap to $0$ and the velocity vector is normalized to magnitude $s$:

$$
\mathbf{v} = \begin{cases} s \dfrac{\mathbf{d}_{\text{input}}}{\|\mathbf{d}_{\text{input}}\|_2} & \text{if } \|\mathbf{d}_{\text{input}}\|_2 > 0 \\ \mathbf{0} & \text{otherwise} \end{cases}
$$

   - **Autonomous Steering Dynamics**: Given position $\mathbf{r} = (x, y)$, target $\mathbf{t} = (t_x, t_y)$, impulse $a$, and maximum speed $s$, let $\mathbf{d} = \mathbf{t} - \mathbf{r}$ and $\hat{\mathbf{d}} = \mathbf{d} / \|\mathbf{d}\|_2$. Velocity accelerates along $\hat{\mathbf{d}}$ and is clamped to $s$:

$$
\mathbf{v}' = \mathbf{v} + a \hat{\mathbf{d}}, \qquad \mathbf{v}_{n+1} = \min\left(1,\; \frac{s}{\|\mathbf{v}'\|_2}\right)\mathbf{v}'
$$

     If $\|\mathbf{d}\|_2$ lies within the single-tick arrival threshold, velocity snaps to the remaining displacement to prevent oscillation.

6. **Linear Friction Decay**:
   For an entity with velocity $\mathbf{v}_n$ traversing a surface with friction coefficient $\mu_f \ge 0$ over timestep $\Delta t$, speed decays linearly to a lower bound of $0$:

$$
s_{n+1} = \max\big(0,\; \|\mathbf{v}_n\|_2 - \mu_f \Delta t\big), \qquad \mathbf{v}_{n+1} = \begin{cases} \dfrac{s_{n+1}}{\|\mathbf{v}_n\|_2}\mathbf{v}_n & \text{if } \|\mathbf{v}_n\|_2 > 0 \\ \mathbf{0} & \text{otherwise} \end{cases}
$$

7. **Symplectic Euler Integration with Sub-Pixel Accumulation**:
   Because positions $(x_n, y_n) \in \mathbb{Z}^2$ are discrete integers while velocities $(v_x, v_y) \in \mathbb{R}^2$ and timesteps $\Delta t \in \mathbb{R}_{>0}$ are continuous, fractional sub-pixel remainders $(r_x, r_y) \in (-1, 1)$ are accumulated across frames:

$$
\begin{aligned}
\tilde{r}_x &= r_{x,n} + v_x \Delta t, & \Delta x &= \operatorname{trunc}(\tilde{r}_x), & x_{n+1} &= x_n + \Delta x, & r_{x,n+1} &= \tilde{r}_x - \Delta x \\
\tilde{r}_y &= r_{y,n} + v_y \Delta t, & \Delta y &= \operatorname{trunc}(\tilde{r}_y), & y_{n+1} &= y_n + \Delta y, & r_{y,n+1} &= \tilde{r}_y - \Delta y
\end{aligned}
$$