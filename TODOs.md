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