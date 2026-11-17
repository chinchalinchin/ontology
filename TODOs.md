# Hardware & VRAM Coupling in the State Database and Models

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


---


# Erosion of ECS Polymorphism via `isinstance` and ID Branching

Although `Asset` (`src/app/assets/base.py`, line 139) is designed as a uniform component container, core systems bypass its strategy interfaces:

* **`Screen` Inspects Concrete State Types**: `Screen._assemble` (`src/app/game/screen.py`, line 157) checks `if not isinstance(asset.state, SheetState):` to suppress missing frame warnings for sparse equipment sheets. `Screen._widgets`, `Screen.stamp`, `Screen.bake`, and `Screen.release` (lines 213, 224, 250, 286, 294) repeatedly check `isinstance(widget.state, PaneState)`.

* **`Widget` Subclasses `Asset` to Override `dimensions`**: `src/app/game/menus/core.py` (lines 37–49) defines `class Widget(Asset)` solely to attach `binding` and branch on `if isinstance(self.state, PaneState): return self.state.span`.

* **Hardcoded Entity IDs and `getattr` Guards in Sheet Components**:
  * `SpriteFrame.keys` (`src/app/assets/frames/sheets.py`, line 103) checks `if id != RequiredAssets.PLAYER.value and state.psyche.expression:`.
  * `SpriteAnimation.animate` (`src/app/assets/animations/sheets.py`, line 32) is type-annotated for `state: SpriteState`, yet uses `if getattr(state, 'psyche', None) is None: return state` because `Player` is hydrated with `SheetState` (which lacks `psyche`) while sharing `SpriteAnimation` and `SpriteFrame`.
  * Meanwhile, `SheetState` (`src/app/models/state/assets/sheets.py`, lines 128–136) bundles `intention`, `character`, `inventory`, `meters`, and `goal` onto the base class for all `Sheets`, forcing `Pixies` (`docs/01-assets.md`, *Sheet: Pixies*) to inherit full character/inventory structures if they use `SheetState`.

* **Remediation**: Separate `SheetState` (strictly `position`, `velocity`, `animation`), `CharacterState(SheetState)` (adding `character`, `slots`, `inventory`, `meters`, `intention`, `goal` for `Player`), and `SpriteState(CharacterState)` (adding `psyche`, `memory`, `trajectory`). Give `Player` and `Sprite` distinct `Frame` and `Animation` recipes (or let `PlayerFrame` be `SpriteFrame` without expression overlays and `SpriteFrame` subclass `PlayerFrame`), eliminating `getattr` and `id != "player"` checks.


---


# Temporal Coupling and Encapsulation Leaks in `Board`

* **Nullable Late-Bound Dependencies Violating Type Annotations**: In `src/app/game/board/core.py` (lines 69–77), `plot: PlotState`, `device: Device`, and `cradle: Cradle` are annotated as non-optional, while `self.materializer` is unannotated. In `Board.__init__` (lines 90–95), all five are initialized to `None` and mutated later via setter methods (`set_device`, `set_cradle`, `set_plot`, `set_migrator`). Any mechanic or handler invoked before all setters run encounters `AttributeError` on `None`.
* **11 Private Cache Structures Exposed on `Board**`: Lines 111–155 of `src/app/game/board/core.py` expose `_cached_categories`, `_cached_instances`, `_cached_layers`, `_cached_renderables`, `_cached_weights`, `_cached_tilemap`, `_cached_fluidmap`, `_cached_characters`, `_all_categories`, `_all_instances`, and `_shorelines` directly from `self._cache`. External callers inspecting these properties bypass `Board`'s query API and couple directly to `Cache` implementation details.


---


# Unculled Heap Allocations, Registry Lookups, and Full-Layer Sorting in `Screen._assemble`

In `src/app/game/screen.py` (`_assemble`, lines 126–205), the rendering pipeline executes operations in the following order every frame (60 Hz):

1. `self.board.renderables(player.state.layer)` (`src/app/game/engine.py`, line 127) returns the cached list of **all** non-tile assets on the active layer (`src/app/game/board/core.py`, line 276).
2. `assets.sort(key=self._sort)` (line 138) sorts the **entire layer's asset list** in-place ($O(N_{\text{layer}} \log N_{\text{layer}})$), mutating the list stored inside `Board._cache.cached_renderables[layer]`.
3. For **every** asset on the layer (lines 140–154), the loop calls `asset.frame.keys(asset.id, asset.state)`, `asset.frame.channels(...)`, and `self.registry.image(frame_key)` **before** checking whether the asset is inside the camera viewport (lines 171–174).

**Impact**:

In `StateFrame.keys` and `SpriteFrame.keys` (`src/app/assets/frames/sheets.py`, lines 46–51, 88–107), every call to `keys()` executes `settings.SEPARATOR.join([...])` and allocates a new list of tuples on the Python heap. If a layer contains $2,000$ assets and only $40$ are within the camera viewport (`pov`, `bounds`), the engine performs $2,000$ sort key evaluations, $2,000+$ dynamic string concatenations, list allocations, and `Registry.image()` dictionary lookups per frame ($120,000+$ allocations per second) only to discard $98\%$ of them at line 171.

**Remediation**:

Perform broad-phase camera AABB culling **first** using `asset.state.position` and `asset.dimensions` (with a constant margin $M$ for expression offsets), collect only the visible subset $V$ ($\vert{}V\vert{} \ll N_{\text{layer}}$), sort $V$ into a local list without mutating `Board._cache`, and invoke `asset.frame.keys()`, `asset.frame.channels()`, and `self.registry.image()` exclusively on $a \in V$:

$$\text{Complexity}_{\text{frame}}: \quad O(N_{\text{layer}} \log N_{\text{layer}}) + N_{\text{layer}} \cdot C_{\text{alloc}} \;\longrightarrow\; O(N_{\text{layer}}) + O(\vert{}V\vert{} \log \vert{}V\vert{}) + \vert{}V\vert{} \cdot C_{\text{alloc}}$$


---


# $O(N)$ Linear Scans for Unique Entity Lookups and Layer Dimensions in `Board`

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


# Unclamped Fixed-Timestep Accumulator ("Spiral of Death") in `Engine.start`

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


----


# Swallowed OS Window Events & Sub-Tick Polling in `libs.core.input` and `Device`

1. **Ignored `SDL_QUIT` Events**: In `src/libs/core/input.pyx` (lines 20–26), `pump()` drains the SDL event queue with an empty body:

```cython
while SDL_PollEvent(&event):
    pass
```

Because `SDL_PollEvent` removes all OS window events from SDL's internal queue and discards them, `SDL_QUIT` (window close button, `Alt+F4`, or SIGINT window termination) is permanently discarded.

2. **Polling Inside the Sub-Step Accumulator Loop**: `Engine._play` (`src/app/game/engine.py`, line 109) calls `self.board.device.poll()` inside `while accumulator >= delta:`. In `Keyboard.poll` (`src/app/game/devices.py`, lines 64–106), edge-triggered intentions and menu triggers are resolved by comparing `current_dict.get(v) and not self._last_state.get(v)` and immediately overwriting `self._last_state = current_dict`. If `accumulator` executes two sub-steps in a single render frame, the edge transition is consumed on sub-step 1 and erased on sub-step 2; conversely, if a fast frame renders with `accumulator` less than `delta`, `sdl.pump()` is not called on that frame at all.


---


# `dataclasses.asdict` Serialization on Cython Extension Types in `Board.serialize`

In `src/app/game/board/core.py` (line 408), `Board.serialize` converts runtime states to dictionaries via `asdict(asset.state)`. However, `SheetState`, `ObjectState`, `CraftState`, etc., store Cython `cdef class` extension types (`libs.core.models.Position`, `Velocity`, `Dimensions`, `Multiple`) in their fields (`src/app/models/state/assets/sheets.py`, lines 130–131). Python's `dataclasses.asdict()` only unpacks standard Python `@dataclass` objects, lists, tuples, and dicts; for Cython `cdef class` instances, `asdict()` falls back to `copy.deepcopy(obj)`, leaving raw Cython extension instances in the output dict (or raising `TypeError` if `__reduce__`/`__deepcopy__` is not implemented on every `cdef class` in `libs.core.models`).


---


# Cross-Domain Enum Default Bug in `SelectTarget` and Off-Target Channel Rendering in `Screen.export_map`

* **Invalid Default Enum Type on `SelectTarget**`: In `src/app/models/config/menus.py` (line 87):
```python
@dataclass(slots=True, frozen=True)
class SelectTarget:
    selection: Enumerated[Selections] = Statuses.IDLE.value

```


`selection` is validated against `Enumerated[Selections]`, but its default value is `Statuses.IDLE.value` (`"idle"`), which is a `Statuses` enum value rather than a `Selections` enum value. Additionally, `from app.models.adapters import Enumerated` is imported twice in `src/app/models/config/menus.py` (lines 34 and 39).
* **Channel Operations Drawn to Default Viewport Instead of `full_target` in `Screen.export_map**`: In `src/app/game/screen.py` (lines 398–411), `render.render(..., target=full_target)` renders the map onto the temporary offscreen texture `full_target`, but the subsequent line `render.channel(active_channels, pov.x, pov.y)` (line 411) omits `target=full_target`, causing auxiliary tint channels to render onto the screen backbuffer rather than the exported map texture.


---


* **Per-Call List and Tuple Allocations in `predicates.in_pool` and `predicates.in_stream`**:
    * `in_pool()` allocates a single-element list `[(pool.x, pool.y, pool.x + pool.w, pool.y + pool.l)]` on every call just to invoke `geometry.inside()` for a 4-integer comparison.
    * `in_stream()` rebuilds `aabbs: List[Tuple[int, int, int, int]]` from `fluid.state.source` and `fluid.state.branches` on every `Board.fluid()` lookup (`60 Hz` per moving entity), even though `Actuator.propagate()` already compiles the active stream and pool geometry onto `fluid.state.hitboxes`.


#### 3. Documentation Updates

##### Draft: MaterialIndex Substrate Lookup & Pack Menu Context

* **Page**: `docs/03-compositions.md` & `docs/06-widgets.md`
* **Heading**: `Service: Materializer` / `Menu: Data`

###### Drift

1. In `docs/03-compositions.md`, `Decomposer` hydration documents late-binding for `bind(root.*)` and `bind(parent.*)` attributes (`layer`, `owner`), but omits `material` injection required by parameterized Armature compositions (`bind(root.material)`).
2. In `docs/06-widgets.md`, `Menu: Data` item 3 (`Equipment, Pouch & Pack`) describes `pack` as displaying two 2x4 grid Gizmos alongside the Craft Formulae pane using `InventoryContext`, without specifying the filter strip or ledger context fields required for crafting.

###### Update

```markdown
- **Compositions (`docs/03-compositions.md` — `Decomposer: Hydration`)**:
  * **Root Context Attributes**: At deployment, `root_context` exposes `id`, `name`, `layer`, `owner`, `position`, `elevation`, `material`, and `blueprint` from the deployed `PropertyState`, allowing parameterized Armatures to resolve `bind(root.material)` across root and branch Struts.

- **Widgets (`docs/06-widgets.md` — `Menu: Data`)**:
  * **`pack`**: Displays two 2x4 grid Gizmos for `inventory.pack` (`materials`) and `inventory.sack` (`crops`) alongside the Craft Formulae column, which comprises a `crafts` filter strip Gizmo, a filtered formula grid Gizmo, and a recipe cost readout bound to `PackContext`.

```

---

#### 4. Bug Reports

##### Bug 07-06-A: `Decomposer.unpack` Omits `material` and `blueprint` from `root_context`

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

In `src/app/services/generators/game/decomposer.py`, `Decomposer.unpack(deployed_state: PropertyState)` constructs `root_context` with only `id`, `name`, `layer`, `owner`, `position`, and `elevation`. When an Armature composition omits `material` on `root.strut` and declares `material: bind(root.material)` on component or branch struts, `CompositionCompiler` defers the macro string to deployment time, where `Decomposer._resolve_bind` fails to resolve `bind(root.material)` because `material` is absent from `root_context`.

**Steps to Replicate**

1. Define an Armature composition with `root.strut` omitting `material` and a component strut declaring `material: bind(root.material)`.
2. Call `decomposer.unpack(PropertyState(id="armature/house/home", material="granite", ...))`.
3. Inspect the hydrated child strut's `state.material`; it remains the literal string `"bind(root.material)"` instead of `"granite"`.

**Proposed Remediation**

Include `"material": deployed_state.material` and `"blueprint": deployed_state.blueprint` in `root_context` inside `Decomposer.unpack()`, and ensure `root.strut` inherits `deployed_state.material` when its own `material` field is `None`.

---

##### Bug 07-06-B: `MenuMechanics` Prevents Focusing `DISABLED` Slots in Craft Formulae

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/game/logic/mechanics/core/menu.py`, `MenuMechanics._resolve_neighbor` enforces `neighbor.state.status != Statuses.DISABLED.value` before moving `menu.focus`. While appropriate for vacant inventory slots in `equipment` and `pouch`, applying `Statuses.DISABLED` to unaffordable recipes in the Craft Formulae grid prevents the player from traversing onto those slots to inspect their required material costs.

**Proposed Remediation**

Either introduce a dedicated `Statuses` / visual state distinction for unaffordable-but-inspectable recipes, or allow `MenuMechanics` / `CraftController` to traverse onto occupied Craft Formulae slots regardless of affordability while gating execution inside `CraftController.select()`.