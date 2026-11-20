# Swallowed OS Window Events & Sub-Tick Polling in `libs.core.input` and `Device`

1. **Ignored `SDL_QUIT` Events**: In `src/libs/core/input.pyx` (lines 20–26), `pump()` drains the SDL event queue with an empty body:

```cython
while SDL_PollEvent(&event):
    pass
```

Because `SDL_PollEvent` removes all OS window events from SDL's internal queue and discards them, `SDL_QUIT` (window close button, `Alt+F4`, or SIGINT window termination) is permanently discarded.

2. **Polling Inside the Sub-Step Accumulator Loop**: `Engine._play` (`src/app/game/engine.py`, line 109) calls `self.board.device.poll()` inside `while accumulator >= delta:`. In `Keyboard.poll` (`src/app/game/devices.py`, lines 64–106), edge-triggered intentions and menu triggers are resolved by comparing `current_dict.get(v) and not self._last_state.get(v)` and immediately overwriting `self._last_state = current_dict`. If `accumulator` executes two sub-steps in a single render frame, the edge transition is consumed on sub-step 1 and erased on sub-step 2; conversely, if a fast frame renders with `accumulator` less than `delta`, `sdl.pump()` is not called on that frame at all.




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




##### Review: Ontology Engine & Runtime Profile Analysis

###### Overview

An analysis of the runtime execution profile (`latest.pstats`, captured across **6,019 rendered frames** and **6,092 logic updates** / **5,447 active world ticks**, or ~100.3 seconds at 60 FPS) alongside the core codebase reveals that the Engine easily maintains its 60 FPS frame budget (**72.78%** of wall-clock time is spent in frame-pacing/idle), but exhibits several structural hotspots in the **25.85%** of wall-clock time dedicated to active execution:

| Subsystem | Wall-Clock % | Self % | Active Work Share (%) | Calls | Calls / Frame |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`Engine.start` Pacing (`sleep` + `time` + spin)** | **72.78%** | **72.07%** | *N/A (Idle/Spin)* | 15,979,892 | ~2,655 |
| **`Engine._render` (Total Rendering)** | **13.28%** | 0.03% | **51.37%** | 6,019 | 1.0 |
| ├─ `Screen._assemble` (World Culling & Sort) | 7.29% | **5.18%** | **28.20%** | 6,013 | 1.0 |
| │  └─ `Screen._in_viewport` | 1.02% | 0.58% | 3.95% | 617,989 | ~102.8 |
| └─ `Screen._widgets` (HUD / Menu Overlays) | 4.90% | 1.04% | **18.96%** | 6,636 | 1.1 |
|    └─ `WidgetFrame.keys` (`widgets:67:keys`) | 3.34% | 1.73% | 12.92% | 83,118 | ~13.8 |
| **`Engine._play` (Total Mechanics)** | **12.57%** | 0.06% | **48.63%** | 6,092 | 1.01 |
| ├─ `CollisionMechanics.update` | 5.91% | 1.25% | **22.86%** | 5,447 | 0.91 |
| │  ├─ `MaterialHitbox.elevations` (`crafts:64`) | 1.91% *(2.37% tot)* | 1.34% | 7.39% *(9.17% tot)* | 1,737,593 *(2.27M)* | ~319.0 |
| │  ├─ `SpatialMechanic.collisions` (`base:60`) | 1.85% | 0.48% | 7.16% | 81,896 | ~15.0 |
| │  └─ `MaterialHitbox.get` (`crafts:73`) | 0.92% *(1.28% tot)* | 0.81% | 3.56% *(4.95% tot)* | 501,124 *(698k)* | ~92.0 |
| └─ `MotionMechanics.update` (`fields.update`) | 1.92% | 0.81% | **7.43%** | 5,447 | 0.91 |
| **`enum.__get__` (Global Descriptor Overhead)** | **1.73%** | **1.25%** | **6.69%** | **7,685,348** | **~1,276.8** |

At a macro level, **rendering preparation in Python (`_render` at 13.28%) costs more CPU time than the entire game simulation (`_play` at 12.57%)**, and **static-environment queries inside `CollisionMechanics` (5.91%) and `Screen._widgets` (4.90%)** dominate the active frame budget despite Cython acceleration at the leaf nodes.

---

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

1. **Passable Craft Inclusion in `Board._cached_weights`**:
   * `CraftProperties` defaults to `mass: int = 0`. Consequently, decorative or passable surface crafts (e.g., `floors`, `flats`, `paths`, `corridors`) satisfy $m \ge 0$ (`predicates.is_weight`) and are indexed into `board.weights(layer)`.
   * Every tick, `CollisionMechanics.update` (and `fields.update`) iterates through all of these passable crafts and calls `w.hitbox.elevations(w.properties, w.state)` (**2.27 million calls**, **2.37%** of total runtime) just for `MaterialHitbox.elevations` to check `MaterialIndex().is_obstacle(state.blueprint)` and return `[]`.
   * Filtering passable `MaterialHitbox` crafts out of `_cached_weights` at board indexing time (or caching `elevations` on the asset/cache) would eliminate over **2 million Python calls** per 100 seconds.

2. **Uncached Per-Frame HUD / Overlay Resolution (`Screen._widgets`)**:
   * `Screen.interface` -> `Screen._widgets` consumes **4.90%** of total wall-clock time (**18.96% of active CPU time**)—nearly as much as `CollisionMechanics` (**5.91%**).
   * Unlike `PaneState` widgets which bake to a texture via `Screen.stamp`, non-pane overlay widgets (e.g., HUD meters, slots, buttons) execute `widget.frame.keys(widget.id, widget.state)` (**83,118 calls**, **3.34%**) and `registry.image(key)` on every single frame, even when the underlying widget state has not mutated.

3. **Serialization Contamination in `Board.serialize` (`src/app/game/board/core.py`)**:
   * `Board.serialize` filters out `WIDGETS`, non-persistent `TEMPORARY` effects, and `Equipment` sheets, but does not filter out procedurally synthesized `GEOGRAPHY` (`SHORELINES`) or hydrated reciprocal `Door` shadow projections (`DoorState.projection == LayerProjections.OUT.value`). Saving and reloading a board state will persist procedural/projected entities as static state entries.

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

##### Bug B001: Index Desynchronization & Out-of-Bounds Access in `SpatialMechanic.proximities`

**STATUS**: OPEN
**SEVERITY**: High

**Description**

In `src/app/game/logic/mechanics/spatial/base.py`, `SpatialMechanic.proximities` constructs `asset_map = dict(enumerate(assets))` using the enumeration index `i` ($0 \le i < N$), and passes `i` as the first element (`entity_id`) of `asset.primitive(i, hitboxes=[pad_hb])` appended to `primitive_data`. However, if any asset in `assets` fails the guard condition (`if not asset.state.mutators or not asset.state.mutators.parameters: continue`), that iteration is skipped, making `len(primitive_data) < len(assets)` while `data[0]` still holds the original index `i`.

When `physics.collisions(primitive_data, self.grid)` executes in `src/libs/core/math/physics.pyx`, it inserts `data[0]` (`i`) into `self.grid`, and then indexes `primitive_data[id_a]` and `primitive_data[id_b]` using those `entity_id` values:
1. Any `entity_id >= len(primitive_data)` raises an `IndexError: list index out of range`.
2. Any `entity_id < len(primitive_data)` occurring after a skipped element accesses the wrong asset's tuple in `primitive_data`, evaluating narrow-phase intersections with mismatched coordinates before mapping the result back to `asset_map[id_a]`.
3. Additionally, if `asset.state.mutators.parameters.action` is `None`, accessing `.radius` raises an `AttributeError`.

**Steps to Replicate** 

1. Instantiate a list of 3 `Asset` instances `[asset_0, asset_1, asset_2]` where `asset_0` has `asset_0.state.mutators = None`, and `asset_1`, `asset_2` have valid `mutators.parameters.action.radius` and overlapping positions.
2. Call `SpatialMechanic().proximities([asset_0, asset_1, asset_2])`.
3. `primitive_data` has length 2, containing `entity_id` values `1` and `2`.
4. `physics.collisions` queries the grid, receives candidate pair `(1, 2)`, and attempts to access `primitive_data[2]`, raising `IndexError: list index out of range`.

**Proposed Remeditation**

Maintain a contiguous local index `idx = len(primitive_data)` for `primitive_data` and `asset_map` (and guard `asset.state.mutators.parameters.action`), ensuring a 1-to-1 correspondence between `entity_id` and `primitive_data` indices:
* Assign `idx = len(primitive_data)`, map `asset_map[idx] = asset`, and append `asset.primitive(idx, hitboxes=[pad_hb])`.

---

##### Bug B002: Negative Crop Height & Corrupt Slicing on Submerged Composite Assets in `Screen._assemble`

**STATUS**: OPEN
**SEVERITY**: High

**Description**

In `src/app/game/screen.py` (`Screen._assemble`, lines 218–246), when an asset has `state.mutators.triggers.submerged == True`, `Frame.channels` emits a `ChannelTypes.SUBMERGE` directive with `split_y = properties.dimensions.l // 2` (e.g., `32` for a 64x64 `Sprite`). `Screen._assemble` then applies this `split_y` to **every** `(frame_key, ox, oy)` returned by `asset.frame.keys(asset.id, asset.state)`:
```python
rem_l = sl - split_y
active_assets.append((
    tex, sx, sy + split_y, sw, rem_l,
    dx, dy + split_y, dw, rem_l,
    r, g, b, a,
))
```
When a submerged `Sprite` has an active `Expression` cursor (which is superimposed via `SpriteFrame.keys` with a non-zero offset `(ox, oy)` and smaller dimensions, e.g., `16x16` where `sl < split_y`), `split_y` is neither offset by `oy` nor clamped to `[0, sl]`. Consequently, the upper slice crops out-of-bounds texture memory (`split_y > sl`) and stretches the expression icon to `split_y` pixels, while the lower slice computes a **negative** height (`rem_l = sl - split_y < 0`) passed to `SDL_RenderCopy`.

**Steps to Replicate** 

1. Place a `Sprite` (dimensions `64x64`, `split_y = 32`) in a `Fluid` stream so `state.mutators.triggers.submerged == True`.
2. Trigger an `Expression` bubble on the `Sprite` (e.g., `surprise` or `loquacity` with dimensions `16x16` or `32x32` at an overhead offset `oy < 0`).
3. Execute `Screen._assemble`: the expression frame is sliced using the Sprite's `split_y = 32`, producing corrupted rendering and `rem_l <= 0`.

**Proposed Remeditation**

Compute the local split offset relative to each frame's vertical offset `oy` (`local_split = split_y - oy`):
* If `local_split >= sl`: render the frame normally (entirely above the waterline).
* If `local_split <= 0`: render the entire frame with submerged RGBA modulation (entirely below the waterline).
* Otherwise (`0 < local_split < sl`): split into upper (`local_split`) and lower (`sl - local_split`) slices.

---

##### Bug B003: Texture Blend Mode Corruption in `render.construct` & Un-cleared `bg_canvas` in `Screen.reconstruct`

**STATUS**: OPEN
**SEVERITY**: Medium

**Description**

1. In `src/libs/graphics/render.pyx` (`construct`, line 325), every tile/primitive iteration executes:
   ```cython
   SDL_SetTextureBlendMode(tex.ptr, SDL_BLENDMODE_NONE)
   ```
   `construct` is used not only for `bg_canvas` (`ENVIRON` tiles), but also for `fg_canvas` (`CANOPY` tiles) and UI `Pane` 9-slice canvases in `Screen.stamp(widget)`. Setting `SDL_BLENDMODE_NONE` disables alpha blending when stamping canopy tiles or 9-slice borders onto transparent target canvases (causing overlapping canopy tiles to overwrite adjacent foliage with transparent black `(0, 0, 0, 0)`), and permanently leaves the shared `TexturePtr` in `Registry._textures` with `SDL_BLENDMODE_NONE`.
2. In `src/app/game/screen.py` (`Screen.reconstruct`, lines 473–482), `render.clear(self.fg_canvas)` is called prior to `render.construct`, but `render.clear(self.bg_canvas)` is omitted, leaving stale pixels on `bg_canvas` if any area is not fully overwritten.

**Steps to Replicate** 

1. Deploy two overlapping `CANOPY` tiles on a layer, or render a texture in `construct` that is subsequently drawn with alpha modulation in `render.render`.
2. During `Screen.__init__` or `Screen.reconstruct`, `render.construct(self.fg_canvas, fore_tiles)` sets `SDL_BLENDMODE_NONE` on the canopy texture, causing the second canopy tile's transparent bounding box to erase the overlapping portion of the first canopy tile on `fg_canvas`.

**Proposed Remeditation**

1. In `Screen.reconstruct`, call `render.clear(self.bg_canvas)` alongside `render.clear(self.fg_canvas)` (and in `Screen.stamp`, call `render.clear(tex)` before `render.construct`).
2. In `render.construct`, preserve `SDL_BLENDMODE_BLEND` for foreground/UI composition (or restore `SDL_SetTextureBlendMode(tex.ptr, SDL_BLENDMODE_BLEND)` after copying).

---

##### Bug B004: Outlined Text Glyph Misalignment & Missing Vertical Offset in `render.write`

**STATUS**: OPEN
**SEVERITY**: Medium

**Description**

In `src/libs/graphics/render.pyx` (`write`, lines 354–439):
1. When rendering outlined text (`font.outline_ptr != NULL and font.outline_width > 0`), `TTF_RenderUTF8_Blended_Wrapped` is called on the entire string `b_content` using `font.outline_ptr` (which has `TTF_SetFontOutline` applied), and the resulting surface is stamped once at `outline_rect.x = dst_rect.x - font.outline_width`. In `SDL2_ttf`, `TTF_SetFontOutline` increases the width and horizontal advance of **each individual glyph** by `2 * outline_width`. For a line of $N$ characters, the outlined surface is wider by $2 \cdot N \cdot \text{outline\_width}$ pixels, causing every character after the first to drift progressively further right relative to `text_surface` and causing multi-line text to wrap at different word boundaries.
2. `dst_rect.y = margin_px_h` omits the target crop offset `sy` (unlike `dst_rect.x`, which adds `sx`).

**Steps to Replicate** 

1. Configure a `Font` in `/src/assets/fonts/**/*.yaml` with `outline.width: 2` and render a multi-character string onto a `Pane` via `Screen.stamp`.
2. Observe that the outline aligns with the first character on the left, but shifts progressively to the right by `2 * outline_width` pixels per character across the string.

**Proposed Remeditation**

To outline wrapped text accurately in `SDL2_ttf`, either:
* Stamp `text_tex` (or `text_surface` rendered in `outline_color` using the base `font.ptr`) at 8-directional offsets $(\pm w, \pm w)$ behind the foreground `text_tex`, which guarantees identical glyph advances and word-wrapping bounds; or
* Render glyph-by-glyph using `TTF_GlyphMetrics` advances from the base font.
Additionally, set `dst_rect.y = sy + margin_px_h`.

---

##### Bug B005: Unclamped Camera Coordinates in `geometry.onscreen`

**STATUS**: OPEN
**SEVERITY**: Low

**Description**

In `src/libs/core/math/geometry.pyx` (`onscreen`, lines 60–71), camera coordinates are computed as:
```cython
cdef int cam_x = p_pos.x + (p_dim.w // 2) - (screen.w // 2)
cdef int cam_y = p_pos.y + (p_dim.l // 2) - (screen.l // 2)
```
Unlike `Screen.camera` in `src/app/game/screen.py` (lines 318–341), which clamps `cam_x` to `[0, boardsize.w - screensize.w]` and `cam_y` to `[0, boardsize.l - screensize.l]` (or centers layers smaller than the viewport), `geometry.onscreen` does not clamp to board boundaries. When the player (`p_pos`) is near any edge of the board (e.g., `p_pos.x = 0`), `Screen.camera` clamps `cam_x = 0` so the viewport displays `[0, screen.w]`, whereas `geometry.onscreen` evaluates `[ -screen.w // 2, screen.w // 2 ]`, falsely reporting visible entities in `[screen.w // 2, screen.w]` as offscreen.

**Steps to Replicate** 

1. Position the Player at `(0, 0)` on a board of size `1920x1080` with a `1280x720` screen viewport.
2. Place an Asset at `(800, 200)` (which is visible on screen since `Screen.camera` clamps `cam_x = 0`).
3. Call `geometry.onscreen(asset.pos, asset.dim, player.pos, player.dim, screen_dim)` — it returns `False` because `cam_x + screen.w` is computed as `-640 + 1280 = 640 < 800`.

**Proposed Remeditation**

Pass `board: Dimensions` (or the already-clamped camera `pov: Position` from `Screen.camera`) into `geometry.onscreen` so its viewport rectangle matches `Screen.camera`.

---

##### Bug B006: Procedural Shorelines & Projected Door Shadows Persisted in `Board.serialize`

**STATUS**: OPEN
**SEVERITY**: Medium

**Description**

In `src/app/game/board/core.py` (`Board.serialize`, lines 397–436), the serializer iterates over `self._assets` and excludes `WIDGETS`, non-persistent `TEMPORARY` effects, and `Equipment` sheets, but does not exclude:
1. Procedurally generated `GEOGRAPHY` assets (`AssetInstances.SHORELINES`), which are synthesized dynamically by `Cartographer` / `FluidMechanics`.
2. Reciprocal shadow footprints projected by `Doors` (`DoorState.projection == LayerProjections.OUT.value`), which are generated automatically during hydration.

Serializing a running board writes these runtime-synthesized entities into the state dump file, causing duplicate door projections and stale shoreline state entries upon reloading the saved slot.

**Steps to Replicate** 

1. Hydrate a board containing a `Door` (which projects a reciprocal `OUT` door onto `outlayer`) and `Fluids` (which synthesize `Shorelines`).
2. Call `board.serialize(world, slot)`.
3. Inspect the saved state YAML: both `geography.shorelines` and the reciprocal `OUT` door state are written to disk.

**Proposed Remeditation**

In `Board.serialize`, skip assets where `asset.category == AssetCategories.GEOGRAPHY.value` or where `asset.instance == AssetInstances.DOORS.value and getattr(asset.state, "projection", None) == LayerProjections.OUT.value`.








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

##### Draft: Mutator Charge Parameter

- **Page**: `docs/02-sprites.md`
- **Heading**: `###### Model: Mutators`

###### Drift

`docs/02-sprites.md` does not document the `parameters.charge` accumulator used to parameterize `attack` hold duration for projectile launch speed.

###### Update

```markdown
* `parameters.charge`: Tick accumulator tracking how long the `attack` Intention has been held prior to projectile release.
```

##### Draft: CombatMap Melee and Projectile Resolution

- **Page**: `docs/05-mechanics.md`
- **Heading**: `###### Map: Combat`

###### Drift

`###### Map: Combat` in `docs/05-mechanics.md` is currently an unpopulated `TODO` stub and does not specify either melee attackbox resolution or equipment release-frame projectile resolution.

###### Update

```markdown
###### Map: Combat

CombatMap bridges an attacking entity's current AnimationState and slotted Weapon Equipment to resolve either active melee Attackboxes or ranged Projectile emission parameters.

**Interface: Attack Hitbox Mapping**

* `attackboxes(state, equipment, elevation): returns List[Hitbox]`: Queries the slotted weapon's Hitbox component at the entity's active `<action>-<direction>-<frame>` key and elevation plane.

**Interface: Projectile Release Mapping**

* `projectile(state, equipment): returns Optional[Tuple[str, int]]`: Evaluates whether the slotted weapon configures a `projectile` ID and `release` frame matching the entity's current animation frame. When triggered on the entry tick of the `release` frame, calculates the initial scalar speed $s(S, n)$ from the attacker's strength $S$, held charge duration $n$, and the weapon's draw window $N_{\max} = \max(1, \text{release} \cdot \text{delay})$:

$$
\tau(n) = \min\left(1.0,\; \frac{n}{N_{\max}}\right), \qquad s(S, n) = \operatorname{round}\Big(\alpha S \big(1 + \tau(n)\big)\Big)
$$
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

##### Draft: AnimationMap Admissibility & CombatMap Separation

- **Page**: `docs/05-mechanics.md`
- **Heading**: `Modules: Maps` and `Dependency: Relations`

###### Drift

`docs/05-mechanics.md` currently leaves `Map: Combat` as `TODO`, lacks the `projectiles` entry under `Dependency: Relations`, and does not formalize the disjoint boundary between `AnimationMap` (Intentional-Spatial Space $\to$ Animation Space, including Equipment admissibility) and `CombatMap` (Active Combat State $\to$ Combat Resolution Geometry and Launch Parameters).

###### Update

```markdown
###### Dependency: Relations

Relations are static secondary indices compiled at initialization and injected into requesting Mechanics.

* `shorelines`: Compound index mapping `(Tile, Fluid, [Season])` keys to Shoreline Geography Asset IDs, compiled from Geography Properties.
* `materials`: Index mapping Blueprints and Asset Instances to obstacle classifications and rendering substrates, compiled from Materials Configuration.
* `projectiles`: Index mapping ranged Weapon keys to Projectile Cursor Asset IDs, compiled from Cursor Properties.

##### Modules

###### Modules: Maps

Maps are stateless domain projections translating Asset State, Equipment, and Relations into target domains consumed by Mechanics. Each Map owns a disjoint codomain.

###### Map: Animation

AnimationMap is the projection from Intentional and Spatial State into Animation Space:

$$
(\text{Intention} \times \text{Slots} \times \text{Equipment}) \longrightarrow \text{Action} \cup \{\bot\}
$$

$$
(\text{Position} \times \text{Target}) \longrightarrow \text{Direction}
$$

AnimationMap enforces Equipment admissibility prior to state commitment in Intentional Mechanics. Equipment-gated Intentions (`attack`, `mine`, `build`) project to the action declared by the corresponding slotted Weapon, Tool, or Utility, and evaluate to $\bot$ when the required Equipment slot is empty. Inadmissible transitions are rejected before Animation or Combat Mechanics execute.

###### Map: Combat

CombatMap projects an active, already-validated combat state into spatial and ballistic resolution primitives consumed by CombatMechanics:

* **Projectile Binding**: $(\text{Weapon} \times \text{ProjectileIndex}) \longrightarrow \text{Projectile} \cup \{\bot\}$. Partitions combat dispatch into ranged and melee modes independently of animation row layout.
* **Attackboxes**: $(\text{AnimationState} \times \text{Weapon} \times \text{Elevation}) \longrightarrow \mathcal{P}(\text{Hitbox})$. Resolves active melee strike geometry.
* **Release**: $(\text{AnimationState} \times \text{Weapon} \times \text{Elevation}) \longrightarrow (\text{Position} \times \text{Direction}) \cup \{\bot\}$. Evaluates the weapon's directional hitbox on the entry tick of its release frame to determine projectile spawn origin and heading.
* **Speed**: $(\text{Strength} \times \text{Charge} \times \text{ReleaseFrame} \times \text{Delay}) \longrightarrow \mathbb{Z}_{>0}$. Maps attacker strength $S$ and held draw duration $n$ to scalar launch speed $s(S, n)$:

$$
N_{\max} = \max(1,\; F_{\text{release}} \cdot \text{delay}), \qquad \tau(n) = \min\left(1.0,\; \frac{n}{N_{\max}}\right), \qquad s(S, n) = \operatorname{round}\Big(\alpha S \big(1 + \tau(n)\big)\Big)
$$
```

---

## 4. Bug Reports

##### Bug B-P0304-01: Dead Attackers Can Still Spawn Projectiles and Deal Melee Damage in `CombatMechanics`

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/game/logic/mechanics/spatial/combat.py`, `CombatMechanics.update()` collects attacking entities solely by checking `asset.state.intention == Intentions.ATTACK`, without checking `asset.state.mutators.triggers.dead`:

```python
attackers = [
    asset
    for asset in (
        board.instances(AssetInstances.PLAYERS, layer) +
        board.instances(AssetInstances.SPRITES, layer)
    )
    if asset.state.intention == Intentions.ATTACK
]
```

Similarly, `CombatMechanics._melee()` checks `target.state.mutators.triggers.dead` before applying damage, but never checks `attacker.state.mutators.triggers.dead`. As a result, a dead entity whose `intention` remains `Intentions.ATTACK` (either prior to `TransitionMechanics` / `RemoveMechanics` cleanup or when killed by another attacker earlier in the same batched melee pass) will still emit projectiles via `_project()` and inflict melee damage via `_melee()`.

**Steps to Replicate**

1. Set a Sprite or Player on layer `"0"` to `state.intention = Intentions.ATTACK`, `state.mutators.triggers.dead = True`, equipped with `"longbow"` at `frame = 9, tick = 0` (or `"sword"` at `frame = 3` overlapping a live target).
2. Execute `CombatMechanics().update(board, 0.016, bus, payload)`.
3. Observe that the dead entity still spawns an `"arrow"` onto the Board (or decrements the live target's health).

**Proposed Remediation**

Filter out dead attackers in `CombatMechanics.update()` (`if asset.state.intention == Intentions.ATTACK and not asset.state.mutators.triggers.dead`) and guard against mid-batch attacker death in `CombatMechanics._melee()` (`or attacker.state.mutators.triggers.dead`).

---

##### Bug B-P0304-02: `CursorProperties.weapon` Schema Mismatch Allows Unvalidated Weapon Bindings and Prevents Many-to-One Sharing

**STATUS**: OPEN
**SEVERITY**: LOW

**Description**

Per Phase 03.04 Specification §1, `CursorProperties` (`src/app/models/properties/assets.py`) should declare `weapons: List[Enumerated[WeaponPalette]] = field(default_factory=list)` and `rotation: int = 90` so that:
1. All weapon foreign keys are validated against `WeaponPalette` at boot via Pydantic `TypeAdapter`.
2. Multiple weapons (e.g., `shortbow` and `longbow`) can share a single projectile asset (`arrow`), while unbound projectiles (e.g., `cannonball`) default to `[]`.

Currently, `CursorProperties` defines `weapon: Optional[str] = None` and `rotation: Optional[int] = None`, `ProjectileIndex.from_properties()` reads singular `props.weapon`, and `src/assets/cursors/main.yaml` declares `cannonball.weapon: cannon`, which is a dangling weapon key absent from `src/assets/sheets/equipment/weapons/main.yaml`. Because `weapon` is an unvalidated `Optional[str]`, invalid or misspelled weapon references silently pass boot validation.

**Steps to Replicate**

1. Inspect `src/app/models/properties/assets.py` (`CursorProperties.weapon: Optional[str] = None`) and `src/assets/cursors/main.yaml` (`cannonball.weapon: cannon`).
2. Load properties via `Loader.load_properties()` and compile `ProjectileIndex.from_properties(properties.cursors.projectiles)`.
3. Observe that `ProjectileIndex.resolve("cannon")` returns `"cannonball"` even though `"cannon"` is neither in `WeaponPalette` nor defined in `src/assets/sheets/equipment/weapons/main.yaml`, and no mechanism exists to bind a second weapon to `"arrow"`.

**Proposed Remediation**

Update `CursorProperties` to `rotation: int = 90` and `weapons: List[Enumerated[WeaponPalette]] = field(default_factory=list)`, align `src/assets/cursors/main.yaml` (`arrow.weapons: [longbow]`, `bolt.weapons: [crossbow]`, `cannonball.weapons: []`), and iterate `for weapon_id in props.weapons:` inside `ProjectileIndex.from_properties()`. (If kept as-is until `cannon` is added as a weapon, update `test_projectiles.py` accordingly when migrating to `weapons`.)


