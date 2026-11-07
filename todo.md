
#### Refactor: Phase 10.06 - Sheet & Equipment Attackbox HitboxSchema

**Overview**

Resolve `@TODO(10-01)` (discovered in `01-assets.md` and `src/app/models/properties/assets.py` following completion of `Phase 10.01: Stage Hitboxes`). Induct `SheetProperties.attackboxes` into the `HitboxSchema` ECS component architecture so `CombatMechanics` queries active attack hitboxes through the unified `Asset.hitbox` interface rather than inspecting raw `SheetProperties.attackboxes` dictionaries and animation string keys directly.

##### Specification

For a `Sheet` asset (`Sprites`, `Players`, and slotted `Equipment`), an active attack footprint at macro-elevation $E$ during animation state $(a, d, f) = (\text{action}, \text{direction}, \text{frame})$ is resolved over the canonical key:

$$k(a, d, f) = \text{f"{a}-{d}-{f}"}$$

1. **Unarmed / Intrinsic Sheet Attackboxes**: Resolved from `properties.attackboxes.get(k(a, d, f), [])`.
2. **Slotted Equipment Attackboxes**: Resolved from the active weapon/tool `SheetProperties.attackboxes.get(k(a, d, f), [])` bound to the Sprite's `EquipmentState`.

##### Goals

###### Goal: Unify `Attackboxes` under `HitboxSchema`

Introduce a dedicated `SheetHitbox(StaticHitbox)` (or `combat` query method on `HitboxSchema`) that resolves frame-synchronized attack hitboxes using `state.animation` (`action`, `direction`, `frame`) and active `Equipment` properties, removing ad-hoc string concatenation from `CombatMechanics`.

##### Tasks

**1. Task: Induct `attackboxes` into `HitboxSchema` and Refactor `CombatMechanics**`

*Objective*: Migrate legacy `SheetProperties.attackboxes` lookups into `src/app/assets/hitboxes/` and update `CombatMechanics` to consume the unified interface.

* [] Subtask: Implement `SheetHitbox` in `src/app/assets/hitboxes/` to resolve frame-keyed `attackboxes` alongside static body `hitboxes`.
* [] Subtask: Register `SheetHitbox` on `sheets.sprites` and `sheets.players` in `src/data/config/recipes/main.yaml`.
* [] Subtask: Refactor `CombatMechanics` to query active attack footprints via the `HitboxSchema` interface and remove the legacy `# TODO: attackboxes need inducted into the new HitboxSchema ECS Architecture` marker in `src/app/models/properties/assets.py`.

---

##### Draft: Synchronize Widget Architecture & Multiplied Pane Specification

* **Page**: `docs/06-widgets.md`
* **Heading**: `##### Asset Specification`

###### Drift

`docs/06-widgets.md` contains an unconditional `!!! @TODO Documentation out of date (slightly, but still mostly accurate) and not formatted to new standards` marker and exhibits five concrete divergences from the codebase (`src/app/models/config/menus.py`, `src/app/models/state/assets/widgets.py`, `src/app/assets/frames/widgets.py`, `src/app/assets/animations/widgets.py`) and Phase 04.06:

1. **Layouts & Panes**: Lists `Overlay`, `Column`, `Row` instead of `Layouts` (`stack`, `dock`, `overlay`), types `margins` as `Tuple[int, int, int, int]` instead of `int`, and specifies `SingleFrame` instead of `PaneFrame` with `SurfaceMultiplier` canvas baking.
2. **Buttons (`TraversalAnimation`)**: Claims `TraversalAnimation` oscillates between `active` and `idle` each tick, whereas `src/app/assets/animations/widgets.py` assigns `state.animation.action = state.status`.
3. **Meters (`MeterState` & `MeterFrame`)**: Describes a two-frame `-empty` and `-filled` dynamic crop at draw time, whereas `MeterFrame.index()` pre-computes 100 discrete crop keys `f"{id}-{res}"` ($1 \le \text{res} \le 100$) and `MeterState` evaluates live closures (`reading_function`, `unit_function`).
4. **Pages (`DisplayState`) & Icons (`IconState`)**: Documents static value fields instead of the closure-backed `content_function` and `icon_function` properties hydrated by `Binder`.

###### Update

```markdown
##### Asset Specification

All Widget frames are organized in a single horizontal row in the Asset image file. The number of frames multiplied by the unit frame width (`dimensions.w`) equals the width of the image file.

**ScreenPosition**

- `ScreenPosition`:
  * `px: float`
  * `py: float`

Root `Pane` positions are configured as `ScreenPosition` percentages relative to `screensize` and converted into pixel `Position(int(px * screensize.w), int(py * screensize.l))` during `Layout.compute()`.

**Properties: WidgetProperties(AssetProperties)**

- `dimensions: Dimensions`: Unit frame dimensions `(w, l)`.
- `frames: Optional[List[str]]`: Ordered list of horizontal frame keys (used by `Icons`).
- `strategy: Optional[Enumerated[MultiplicationStrategies]]`: Multiplication strategy (`surface`, `perimeter`, `simple`) for expandable `Panes`.

###### Panes

**Taxonomy**

- `category: widgets`
- `instance: panes`

Panes are spatial and visual containers that organize child Widgets according to a declarative `layout` and `alignment`.

**Semantics: Layouts**

- `stack`: Vertical column of child Widgets along the Y-axis.
- `dock`: Horizontal row of child Widgets along the X-axis.
- `overlay`: Sagittal superimposition of child Widgets along the Z-axis.

**Semantics: Alignments**

- `start`: Children are aligned to the leading edge of the minor axis.
- `center`: Children are centered along the minor axis.
- `end`: Children are aligned to the trailing edge of the minor axis.

**Behavior: Bottom-Up Quantization & Canvas Baking**

Multiplied Panes (`strategy: surface`) partition their horizontal atlas strip into five unit tiles of size `(w, l)`: `north`, `south`, `east`, `west`, and `center`. During `Provider.unpack()`, `Layout.compute()` measures child footprints bottom-up and quantizes the required interior multiplicity $(n_x, n_y)$ via:

$$n_x = \max\!\left(0,\; \left\lceil \frac{W_{\text{req}} - 2w}{w} \right\rceil\right), \quad n_y = \max\!\left(0,\; \left\lceil \frac{L_{\text{req}} - 2l}{l} \right\rceil\right)$$

yielding total span $W = (n_x + 2)w,\; L = (n_y + 2)l$. `Provider._bake_pane()` stamps the projected `SurfaceMultiplier` tiles once onto `PaneState.canvas` via `render.construct()`, enabling `Screen._widgets()` to draw the entire Pane in a single `SDL_RenderCopy` call.

**State: PaneState(WidgetState)**

- `position: Position`
- `layout: Enumerated[Layouts] = Layouts.STACK.value`
- `alignment: Enumerated[Alignments] = Alignments.CENTER.value`
- `gap: Optional[int] = 0`
- `margins: Optional[int] = 0`
- `multiple: Optional[Multiple] = None`
- `span: Optional[Dimensions] = None`
- `canvas: Optional[TexturePtr] = None`

**Frame: PaneFrame**

- `index(id, properties)`: When `properties.strategy` is set, returns `{f"{id}-{part}": (i * w, 0, w, l)}` for `i, part` in `enumerate(["north", "south", "east", "west", "center"])`. Otherwise returns `{id: (0, 0, w, l)}`.
- `keys(id, state)`: Returns `[(id, 0, 0)]` (bypassed when `state.canvas` is pre-baked).

###### Buttons

**Taxonomy**

- `category: widgets`
- `instance: buttons`

Buttons are traversable Controls whose horizontal atlas frames are ordered by `Statuses`: `idle`, `active`, `selected`, `disabled`.

**State: TraversalState(WidgetState)**

- `position: Position`
- `status: Enumerated[Statuses] = Statuses.IDLE.value`
- `animation: AnimationState`

**Animation: TraversalAnimation**

- `animate(state, properties)`: Synchronizes `state.animation.action = state.status`.

**Frame: TraversalFrame**

- `index(id, properties)`: Maps `{f"{id}-idle": (0, 0, w, l), f"{id}-active": (w, 0, w, l), f"{id}-selected": (2*w, 0, w, l), f"{id}-disabled": (3*w, 0, w, l)}`.
- `keys(id, state)`: Returns `[(f"{id}-{state.animation.action}", 0, 0)]`.

###### Meters

**Taxonomy**

- `category: widgets`
- `instance: meters`

Meters render continuous ratios (`reading / unit`) by superimposing a cropped fill frame over an empty base frame.

**State: MeterState(WidgetState)**

- `position: Position`
- `reading_function: Callable[[], Union[int, float]]`
- `unit_function: Callable[[], Union[int, float]]`
- `animation: AnimationState`

**Animation: MeterAnimation**

- `animate(state, properties)`: Sets `state.animation.frame = max(0, min(100, int(round((state.reading / state.unit) * 100))))`.

**Frame: MeterFrame**

- `index(id, properties)`: Indexes `{f"{id}-empty": (0, 0, w, l)}` and discrete percentage crops `{f"{id}-{res}": (w, 0, int(w * (res / 100.0)), l)}` for `res` in `1..100`.
- `keys(id, state)`: Returns `[(f"{id}-empty", 0, 0), (f"{id}-{state.animation.frame}", 0, 0)]`.

###### Pages

**Taxonomy**

- `category: widgets`
- `instance: pages`

Pages rasterize wrapped typography onto an isolated `TexturePtr` target `canvas` via `Screen.stamp()`.

**State: DisplayState(WidgetState)**

- `content_function: Callable[[], Union[str, List[str]]]`
- `pageindex: int = 0`
- `pagesize: int = 1`
- `font: Enumerated[Fonts] = Fonts.DIALOGUE.value`
- `canvas: TexturePtr`

**Frame: SingleFrame**

- `index(id, properties)`: Returns `{id: (0, 0, w, l)}`.
- `keys(id, state)`: Returns `[(id, 0, 0)]`.

###### Icons

**Taxonomy**

- `category: widgets`
- `instance: icons`

**State: IconState(WidgetState)**

- `icon_function: Callable[[], str]`

**Frame: IndexFrame**

- `index(id, properties)`: Returns `{f"{id}-{frame}": (i * w, 0, w, l) for i, frame in enumerate(properties.frames)}`.
- `keys(id, state)`: Returns `[(f"{id}-{state.icon}", 0, 0)]` when `state.icon` is non-empty, else `[]`.

```

##### Draft: Remove Legacy Negative-Elevation Substrate Clamping Description

* **Page**: `docs/01-assets.md`
* **Heading**: `###### Concept: Appearance`

###### Drift

`docs/01-assets.md` contains `!!! @TODO(07-04)` (Phase 07.04 is marked `[x]` on the Task Board) noting that `Substrates` are no longer encoded as negative `elevation` values. However, the paragraph immediately following the note still states that during `CollisionMechanics` and Perimeter generation, all negative Substrates are collapsed into `elevation = 0` ($\text{elevation} \in [-\infty, 0] \to \text{elevation} = 0$). In the current architecture (`src/app/assets/base.py` and `src/app/game/screen.py`), `Asset.substrate` is a dedicated integer attribute (`Substrates.ENVIRON = -4` through `Substrates.STANDARD = 0`) occupying the secondary slot of `_sort`, while `Asset.elevation` is strictly non-negative ($\in \mathbb{Z}_{\ge 0}$).

###### Update

```markdown
**Substrates**

Certain Assets are assigned a dedicated intra-elevation `Substrate` ($\in \mathbb{Z}_{\le 0}$) to preserve coplanar rendering order within a macro-elevation tier $E \in \mathbb{Z}_{\ge 0}$. These values are hydrated onto `Asset.substrate` via `MaterialIndex` during asset instantiation:

--8<-- "static/md/asset-substrates.md"

Because `Asset.substrate` is decoupled from `Asset.elevation` as the secondary component of the render sort key `(elevation, substrate, ground_y, priority)`, surface and overlay assets (such as `crafts.struts.floors` on `Substrates.SURFACES = -2` or `crafts.bridges` on `Substrates.OVERLAYS = -1`) retain their true macro-elevation $E \ge 0$ for `CollisionMechanics`, `HitboxSchema.elevations()`, and perimeter contour evaluation without collapsing elevations.

```

---

##### Bug B017: MenuMechanics Focus Traversal Animation Action Desynchronization

**STATUS**: OPEN
**SEVERITY**: Low

**Description**

In `MenuMechanics.update()` (`src/app/game/logic/mechanics/core/menu.py`, lines 54–77), `widget.animation.animate(widget.state, widget.properties)` is executed *before* device traversal input is evaluated. When a directional `traversal` command shifts focus from `active_menu.focus` to `new_focus`, `MenuMechanics` updates `state.status = Statuses.IDLE.value` and `state.status = Statuses.ACTIVE.value` on the respective button widgets, but does **not** update `state.animation.action` (unlike `Provider._focus()` and `Provider._sync_collection_slots()`, which update both `state.status` and `state.animation.action`). Because `TraversalFrame.keys()` (`src/app/assets/frames/widgets.py`) indexes textures using `state.animation.action` rather than `state.status`, the rendered button states lag behind `active_menu.focus` by one tick during `Engine._render()`.

**Steps to Replicate**

1. Launch the Engine into `MainMenu` (`focus == "new-game"`).
2. Issue a single `Directions.DOWN` (`SOUTH`) traversal input payload.
3. Observe that after `MenuMechanics.update()` completes on that tick, `active_menu.focus` is `"load-game"` and `widgets["load-game"].state.status == "active"`, but `widgets["load-game"].state.animation.action` remains `"idle"` (and `widgets["new-game"].state.animation.action` remains `"active"`) when `Engine._render()` executes for that frame.

**Proposed Remeditation**

Synchronize `state.animation.action` alongside `state.status` during focus transitions in `MenuMechanics.update()` (or execute `widget.animation.animate()` after input interception):

```python
if direction in neighbors:
    new_focus = neighbors[direction]
    old_widget = active_menu.widgets[active_menu.focus]
    new_widget = active_menu.widgets[new_focus]
    old_widget.state.status = Statuses.IDLE.value
    old_widget.state.animation.action = Statuses.IDLE.value
    new_widget.state.status = Statuses.ACTIVE.value
    new_widget.state.animation.action = Statuses.ACTIVE.value
    active_menu.focus = new_focus

```

##### Bug B018: Screen._assemble Multi-Frame Channel Duplication and Missing Viewport Culling

**STATUS**: OPEN
**SEVERITY**: Medium

**Description**

In `Screen._assemble()` (`src/app/game/screen.py`, lines 124–181), the `# 2. Auxiliary Channel Tuples` loop (`for c_type, payload in channels:`) is nested *inside* `for frame_key, ox, oy in frame_keys:` and placed *outside* the camera viewport AABB culling guard. Consequently:

1. Any asset whose `Frame.keys()` emits $K > 1$ superimposed frame keys (such as a `Sprite` with slotted `Equipment` or an active `Expression` bubble) appends its `ChannelTypes.TINT` operation $K$ times per frame, compounding alpha-blended tint rectangles on top of the entity.
2. Off-screen assets that fail the viewport AABB culling check still emit `active_channels` primitives to `render.channel()`.

**Steps to Replicate**

1. Instantiate a `Sprite` with slotted equipment (`len(frame_keys) > 1`) and an active `ChannelTypes.TINT` directive.
2. Call `Screen._assemble()` and inspect `active_channels`.
3. Observe that the `TINT` tuple is duplicated once for every frame key in `frame_keys`, and continues to be emitted when the `Sprite` moves outside `(pov.x, pov.y, bounds.w, bounds.l)`.

**Proposed Remeditation**

Unindent the `for c_type, payload in channels:` loop in `Screen._assemble()` so it executes once per visible `asset` (gated by a boolean `is_visible` flag set when at least one `frame_key` passes viewport culling, or by culling `(asset.state.position.x + cx, asset.state.position.y + cy, cw, cl)` directly against `pov` and `bounds`).

##### Bug B019: Unreleased DisplayState and PaneState VRAM Target Canvases on Menu Termination

**STATUS**: OPEN
**SEVERITY**: Medium

**Description**

`Provider._page()` (`src/app/services/generators/menus/provider.py`, line 101) allocates an SDL target texture in GPU memory via `render.canvas(w, l)` for every `DisplayState` widget (`pages`) whenever a `Menu` is unpacked. Furthermore, `Provider._widget()` passes `widgets=widgets` into `Binder.binding()`, which stores a reference to the `widgets` dict inside `ApertureBinding` attached to `Widget.binding`, forming a reference cycle (`widgets` $\leftrightarrow$ `Widget` $\leftrightarrow$ `Binding`). When a modal menu is popped via `TerminalEvent` or wiped via `Board.clear()`, `render.destroy()` is never called on `widget.state.canvas`. Because of the reference cycle, `TexturePtr.__dealloc__` is deferred until cyclic garbage collection runs, leaking GPU target textures across repeated menu open/close cycles.

**Steps to Replicate**

1. Repeatedly open and close modal menus containing `pages` (or multiplied `panes` with `PaneState.canvas`), such as `inventory`, `dialogue`, or `options`.
2. Observe that `TerminalEventHandler.handle()` pops the `Menu` without calling `render.destroy(widget.state.canvas)` on `DisplayState` or `PaneState` instances.

**Proposed Remeditation**

In both `TerminalEventHandler.handle()` (when popping a `Menu`) and `Board.clear()` (before clearing `self.menus` and `self.overlays`), iterate over `menu.widgets.values()` and explicitly invoke `render.destroy(widget.state.canvas)` (setting `widget.state.canvas = None`) for any widget whose state holds a non-null `canvas`.