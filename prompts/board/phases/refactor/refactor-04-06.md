#### Refactor: Phase 04.06 - Pane Generation

**Overview**

Decouple UI `Pane` assets from fixed-dimension textures (`dark`, `dark-small`, `dark-thin`, etc.) by inducting `Panes` into the multiplication architecture established in Phase 07.04. Enable `Panes` to expand to arbitrary dimensions (bounded below by the asset's minimum unit perimeter) using perimeter-capped multiplication and bottom-up child layout measurement.

##### Specification

A multiplied `Pane` of unit cell dimensions $(w, l)$ and interior multiplicity $(n_x, n_y) \in \mathbb{Z}_{\ge 0}^2$ spans a total bounding box of:

$$W(n_x) = (n_x + 2) \cdot w, \quad L(n_y) = (n_y + 2) \cdot l$$

1. **Minimum Dimensions Constraint**:
Setting $n_x = 0, n_y = 0$ yields the minimum valid footprint $W_{\min} = 2w,\; L_{\min} = 2l$, where the `north`/`south` and `west`/`east` caps meet and superimpose at the four corners without interior shaft segments.
2. **Quantization of Arbitrary Target Dimensions**:
Given a target content bounding box $(W_{\text{req}}, L_{\text{req}})$ (derived either from explicit `PaneParameters.dimensions` or from the measured bounding box of child widgets plus `2 * margins`), the integer multiplicity $(n_x, n_y)$ is resolved via clamped ceiling division:

$$n_x = \max\!\left(0,\; \left\lceil \frac{W_{\text{req}} - 2w}{w} \right\rceil\right), \quad n_y = \max\!\left(0,\; \left\lceil \frac{L_{\text{req}} - 2l}{l} \right\rceil\right)$$

3. **Topological Partitions (Perimeter + Interior Fill)**:
* **Horizontal Caps (`north`, `south`)**: Placed across $i_x \in [0, n_x + 1]$ at $(i_x \cdot w,\; 0)$ and $(i_x \cdot w,\; (n_y + 1) \cdot l)$.
* **Vertical Caps (`west`, `east`)**: Placed across $i_y \in [0, n_y + 1]$ at $(0,\; i_y \cdot l)$ and $((n_x + 1) \cdot w,\; i_y \cdot l)$, superimposing over `north` and `south` at the four corners $(0, 0)$, $((n_x + 1)w, 0)$, $(0, (n_y + 1)l)$, and $((n_x + 1)w, (n_y + 1)l)$ to form corner joints without dedicated corner sprites.
* **Interior Surface (`center` / `fill`)**: Placed across $i_x \in [1, n_x],\; i_y \in [1, n_y]$ (or tiled across the full $[0, n_x + 1] \times [0, n_y + 1]$ background plane beneath the perimeter caps) whenever $n_x \ge 1$ and $n_y \ge 1$.



##### Architectural Analysis I

###### 1. Can the Existing Multiplication Strategies Be Utilized?

The existing `Multipliers` (`SimpleMultiplier`, `OrientedMultiplier`, `ExpansionMultiplier`, `PerimeterMultiplier` in `app.game.logic.modules.multipliers`) implement the exact coordinate stepping required for `Panes`, but **cannot be invoked directly as-is** due to three architectural divergences between world `Crafts` and UI `Panes`:

1. **Multi-Entity Instantiation vs. Single-Widget Identity**:
* `PerimeterMultiplier.multiply()` calls `self._unit(...)` to instantiate $2(n_x + n_y + 4)$ separate `Asset` instances on the `Board`. `Struts` require separate `Asset` instances because each world segment has an independent `Hitbox` for `CollisionMechanics` and an independent `ground_y` (`anchor`) for 2.5D Painter's Algorithm sorting (`Screen._sort`) against dynamic `Sprites`.
* Conversely, a `Pane` in `Menu.widgets` **must remain a single `Widget` instance** keyed by `pane.name`:
* `Layout.compute()` queries `widgets[pane.name]` to resolve child alignments and mutates `pane.state.position` *after* `Provider._unpack_pane()` completes.
* `CollectionState` Gizmos store state on the root `Pane` (`menu.widgets[selector]`), which `ApertureBinding` and `InventoryController` query in $O(1)$ by `pane.name`.
* `Panes` do not participate in world collisions or `Screen._sort`; they render flat on a single plane behind their children via `Screen.interface()`.




2. **Hollow Enclosure vs. Filled Backdrop**:
* `PerimeterMultiplier` generates a **hollow** boundary: for $n_x \ge 1, n_y \ge 1$, no segments are placed in the interior domain $[1, n_x] \times [1, n_y]$. While a fence or wall enclosure on the `Board` encloses open terrain, a `Pane` is an opaque backdrop. Using `PerimeterMultiplier` alone leaves a rectangular hole in the center of every menu whenever $n_x \ge 1$ and $n_y \ge 1$.
* A `Pane` therefore requires a **composite (`simple` + `perimeter`)** or **filled-perimeter (`surface`)** strategy: a base fill across the interior $[1, n_x] \times [1, n_y]$ (or full $[0, n_x + 1] \times [0, n_y + 1]$ footprint) combined with the `PerimeterMultiplier` border pass.


3. **Coupling to `CraftState` and `MaterialIndex` Substrates**:
* `Multiplier._unit` assumes `state` is a `CraftState` with `material`, `blueprint`, `layer`, `elevation`, and queries `self.materials.substrate(instance, blueprint)`.



**Resolution**: Refactor `Multiplier` subclasses to separate **pure topological coordinate generation** (`project(w, l, nx, ny, ...) -> List[Tuple[str, int, int, int]]` yielding `(partition_key, ox, oy, anchor_delta)` and `span(w, l, nx, ny) -> Dimensions`) from **world `Asset` instantiation** (`multiply(...) -> List[Asset]`).

* `Decomposer.multiply()` calls `multiply()` to emit world `Asset` lists for `Crafts`.
* `CompositionCompiler._compute_span()` calls `Multiplier.span()` instead of duplicating strategy span formulas.
* `Provider` / `PaneFrame` calls `project()` to obtain relative tile offsets `(part_key, ox, oy)` for a single `Pane` `Widget`.

###### 2. Dependency Injection & Hydration Pipeline Analysis

Tracing the DI pipeline (`Builder` $\to$ `Orchestrator` $\to$ `Provider` $\to$ `Layout` $\to$ `Screen`) reveals three pipeline bottlenecks that must be resolved:

1. **Missing `MaterialIndex` / Strategy Injection in `Provider**`:
* In `app.services.orchestration.builder`, `Decomposer` is injected with `MaterialIndex`, whereas `Provider` only receives `(recipes.widgets, properties.widgets, binder, fabricator)`. If `Panes` declare blueprint schemas (or multiplication strategies) and optional `Material` palettes (e.g., unifying `dark`, `neutral`, `light` into a single `pane` atlas indexed over `Chromatics`), `Provider` must receive `MaterialIndex` (or the compiled strategy index).


2. **Phase Ordering Inversion Between `Provider._unpack_pane` and `Layout.compute**`:
* Currently in `Provider.unpack()`:
* **Phase 1**: `_expand()` expands `Gizmos` into `MenuNode` trees, computing static pixel `Dimensions` on `PaneParameters`.
* **Phase 2**: `_unpack_pane()` instantiates `Widget` objects and overrides `props.dimensions` if `params.dimensions` was explicitly set.
* **Phase 3**: `Layout.compute()` walks the tree, reads `widget.dimensions`, and assigns `widget.state.position`.


* Under this ordering, if a `Pane` in YAML omits explicit `dimensions` / `multiple`, Phase 2 instantiates it with its raw unit tile size $(w, l)$ before `Layout` has measured its children!
* **Pipeline Fix**: Split `Layout.compute()` into a **Bottom-Up Measurement & Quantization Pass** (computing required `(nx, ny)` and quantized `span` `Dimensions((nx + 2) * w, (ny + 2) * l)` for every `Pane` based on its children's sizes, `gap`, and `margins`) followed by the **Top-Down Positioning Pass**.


3. **60 Hz Rendering Overhead (`Frame.keys` vs. `render.construct` Canvas Baking)**:
* A $320 \times 256\text{ px}$ menu built from $16 \times 16\text{ px}$ unit tiles ($n_x = 18, n_y = 14$) comprises $(20 \times 16) + 2(18 + 14 + 4) = 392$ tile primitives.
* Pushing 392 tuples per pane across the Python-to-Cython boundary in `Screen._widgets()` on every frame at 60 Hz creates avoidable inner-loop overhead.
* Instead, just as `Screen._prerender()` bakes multiplied `Tiles` onto `bg_canvas` via `render.construct()` and `Provider._page()` allocates a `TexturePtr` `canvas` for `DisplayState`, `Provider` (or `Layout`) can bake a multiplied `Pane`'s tiles once onto a `PaneState.canvas: TexturePtr` via `render.construct()` at menu instantiation time. At runtime, `Screen._widgets()` draws the entire multiplied `Pane` in a **single** `SDL_RenderCopy` call.



##### Goals

###### Goal: Decouple Topology Generation from Entity Instantiation in `Multipliers`

Extract pure geometric projection and span calculation methods onto the `Multiplier` hierarchy so both world `Crafts` (`Decomposer`), compile-time macro evaluation (`CompositionCompiler`), and UI `Panes` (`Provider` / `Layout`) share a single mathematical implementation:

```python
class Multiplier(ABC):
    @abstractmethod
    def span(self, w: int, l: int, nx: int, ny: int, blueprint: Optional[str] = None) -> Dimensions:
        """Returns the total bounding Dimensions of the multiplied footprint."""
        pass

    @abstractmethod
    def project(
        self,
        w: int,
        l: int,
        nx: int,
        ny: int,
        blueprint: Optional[str] = None,
        base_anchor: int = 0,
        hitboxes: Optional[Dict[str, List[Hitbox]]] = None
    ) -> List[Tuple[str, int, int, int]]:
        """
        Emits relative placement primitives: (blueprint_part, offset_x, offset_y, seg_anchor).
        """
        pass

```

Introduce `SurfaceMultiplier(PerimeterMultiplier)` (registered under `MultiplicationStrategies.SURFACE = "surface"`), which first tiles a `center` (or `fill`) partition across the interior $[1, n_x] \times [1, n_y]$ via `SimpleMultiplier` offsets and then appends the `PerimeterMultiplier` caps (`north`, `south`, `east`, `west`) across $[0, n_x + 1]$ and $[0, n_y + 1]$.

###### Goal: Induct `Panes` into Multiplied Schemas & `PaneState`

Extend `WidgetProperties` (or introduce `PaneProperties(WidgetProperties)`) and `PaneParameters` / `PaneState` to support multiplication:

```python
@dataclass(slots=True, frozen=True)
class PaneParameters:
    layout: Enumerated[Layouts] = Layouts.STACK.value
    alignment: Enumerated[Alignments] = Alignments.START.value
    gap: int = 0
    margins: int = 0
    position: Optional[ScreenPosition] = None
    dimensions: Optional[Dimensions] = None
    multiple: Optional[Multiple] = None
    font: Optional[str] = None
    children: List[MenuNode] = field(default_factory=list)


@dataclass(slots=True)
class PaneState(WidgetState):
    layout: Enumerated[Layouts] = Layouts.STACK.value
    alignment: Enumerated[Alignments] = Alignments.CENTER.value
    gap: int = 0
    margins: int = 0
    multiple: Optional[Multiple] = None
    span: Optional[Dimensions] = None
    canvas: Any = None

```

###### Goal: Bottom-Up Auto-Sizing & Quantization in `Layout`

Update `Layout.compute()` to resolve `Pane` dimensions in two passes:

1. **Pass 1 (Post-Order Measurement & Quantization)**:
* Recursively measure child `MenuNode` footprints.
* For a `STACK` pane, required content size is:

$$W_{\text{req}} = \max_{c}(c.w) + 2m, \quad L_{\text{req}} = \sum_{c} c.l + \text{gap} \cdot \max(0, \vert{}C\vert{} - 1) + 2m$$


* For a `DOCK` pane, required content size is:

$$W_{\text{req}} = \sum_{c} c.w + \text{gap} \cdot \max(0, \vert{}C\vert{} - 1) + 2m, \quad L_{\text{req}} = \max_{c}(c.l) + 2m$$


* If the `Pane` asset uses a multiplication strategy (`surface` / `perimeter`), quantize $(W_{\text{req}}, L_{\text{req}})$ into $n_x = \max(0, \lceil (W_{\text{req}} - 2w) / w \rceil)$ and $n_y = \max(0, \lceil (L_{\text{req}} - 2l) / l \rceil)$, setting `pane.state.multiple = Multiple(nx, ny)` and `pane.state.span = Dimensions((nx + 2) * w, (ny + 2) * l)`.


2. **Pass 2 (Pre-Order Coordinate Assignment & Canvas Baking)**:
* Position parent panes and children using the quantized `pane.state.span` so centered/aligned children sit symmetrically within the quantized perimeter.



###### Goal: Pre-Baked `PaneState.canvas` Rendering & Teardown

During menu unpacking, construct a single `TexturePtr` target canvas (`render.canvas(span.w, span.l)`) for each multiplied `Pane` and stamp its projected `(part_key, ox, oy)` primitives in a single Cython `render.construct(canvas, primitives)` call. Update `Screen._widgets()` to render `PaneState.canvas` directly (mirroring `DisplayState.canvas`) and ensure `TerminalEventHandler` / `Board.clear()` explicitly calls `render.destroy()` on both `DisplayState.canvas` and `PaneState.canvas`.

##### Tasks

**1. Task: Refactor `Multipliers` to Separate Geometry Projection from Entity Instantiation**

*Objective*: Decouple coordinate/partition math from `Craft` asset hydration so `Multipliers` can be shared across `CompositionCompiler`, `Decomposer`, and `Provider`.

* [] Subtask: Add abstract `span(w, l, nx, ny, blueprint)` and `project(w, l, nx, ny, blueprint, base_anchor, hitboxes)` methods to `Multiplier` in `src/app/game/logic/modules/multipliers/base.py`.
* [] Subtask: Implement `span()` and `project()` on `SimpleMultiplier`, `OrientedMultiplier`, `ExpansionMultiplier`, and `PerimeterMultiplier`, refactoring `multiply()` to iterate over `self.project(...)` and invoke `self._unit(...)`.
* [] Subtask: Implement `SurfaceMultiplier(PerimeterMultiplier)` (and add `SURFACE = "surface"` to `MultiplicationStrategies` in `src/app/static/semantics.py`) combining interior `center` fill across $[1, n_x] \times [1, n_y]$ with outer perimeter caps (`north`, `south`, `east`, `west`).
* [] Subtask: Replace duplicate span logic in `CompositionCompiler._compute_span` (`src/app/static/macros/compositions.py`) with a call to the corresponding `Multiplier.span()`.

**2. Task: Extend Widget Models, Frames, and Semantics for Multiplied Panes**

*Objective*: Update configuration, property, and state schemas to represent multiplied `Panes` and index their partition frames in `Registry`.

* [] Subtask: Add `multiple: Optional[Multiple] = None` to `PaneParameters` (`src/app/models/config/menus.py`) and `multiple: Optional[Multiple] = None`, `span: Optional[Dimensions] = None`, `canvas: Any = None` to `PaneState` (`src/app/models/state/assets/widgets.py`).
* [] Subtask: Add `strategy: Optional[Enumerated[MultiplicationStrategies]] = None` (or `blueprints`) to `WidgetProperties` (`src/app/models/properties/assets.py`).
* [] Subtask: Implement `PaneFrame(Frame)` in `src/app/assets/frames/widgets.py` to index partition frames (`north`, `south`, `east`, `west`, `center`) for multiplied panes while preserving single-frame fallback for static/transparent panes.
* [] Subtask: Update `AssetW.dimensions` property (`src/app/assets/base.py` or `Widget` in `src/app/game/menus/core.py`) to return `self.state.span` when present on `PaneState`, falling back to `self.properties.dimensions`.

**3. Task: Upgrade `Layout`, `Fabricator`, and `Provider` for Bottom-Up Auto-Sizing and Canvas Baking**

*Objective*: Automatically calculate `(nx, ny)` from child widget bounds or explicit parameters and bake multiplied pane textures once per menu instantiation.

* [] Subtask: Inject `MaterialIndex` (or strategy map) into `Provider` in `src/app/services/orchestration/builder.py` and `src/app/services/generators/menus/provider.py`.
* [] Subtask: Refactor `Layout.compute()` (`src/app/game/menus/modules/layout.py`) to execute a bottom-up post-order pass that measures child footprints, quantizes `PaneState.multiple` and `PaneState.span` via ceiling division ($n_x = \max(0, \lceil(W_{\text{req}} - 2w)/w\rceil)$), and then executes the top-down coordinate placement pass.
* [] Subtask: Remove hardcoded `dimensions` overrides in `Fabricator._collection` (`src/app/services/generators/menus/fabricator.py`) and `src/data/config/menus/*.yaml` where bottom-up auto-sizing applies.
* [] Subtask: Add `_bake_pane(widget)` to `Provider` (invoking `render.canvas` and `render.construct` over `Multiplier.project` tuples) and update `Screen._widgets()` (`src/app/game/screen.py`) to draw `PaneState.canvas` in a single `superimpose` primitive.
* [] Subtask: Add explicit `render.destroy()` cleanup for `PaneState.canvas` and `DisplayState.canvas` when menus close in `TerminalEventHandler.handle` (`src/app/game/menus/handlers/terminal.py`) and `Board.clear()` (`src/app/game/board/core.py`).

**4. Task: Re-Atlas Pane Assets and Consolidate `menus/*.yaml**`

*Objective*: Replace fixed-size pane variants (`dark`, `dark-small`, `dark-thin`, `neutral`, `neutral-small`, `light`, `light-small`) with multiplied base pane assets and verify with unit tests.

* [] Subtask: Re-atlas `dark`, `neutral`, and `light` pane `.png` files in `src/assets/widgets/panes/` into unit tiles (`north`, `south`, `east`, `west`, `center`) and update `src/assets/widgets/main.yaml`.
* [] Subtask: Update `main.yaml`, `pause.yaml`, `options.yaml`, `dialogue.yaml`, `text.yaml`, `inventory.yaml`, and `view.yaml` in `src/data/config/menus/` to reference the unified multiplied pane IDs (`dark`, `neutral`, `light`).
* [] Subtask: Add unit tests under `tests/unit/app/` verifying `SurfaceMultiplier.project()`, `SurfaceMultiplier.span()`, minimum dimension clamping ($n_x = 0, n_y = 0 \implies 2w \times 2l$), and `Layout.compute()` bottom-up quantization.