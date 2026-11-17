#### Refactor: Phase 01.02 - Render Decoupling

**Overview** 

Eliminate all direct imports and runtime couplings to `libs.graphics.render` and Cython `TexturePtr` allocations from `Board`, `PaneState`, and `app.game.menus.bindings.text`. Dynamic widget canvas textures (`_canvases`) and text measurement will be owned and lifecycle-managed centrally by the Cython `Registry` singleton (`src/libs/graphics/registry.pyx`), ensuring multi-layer (`Screen`) compatibility, unified VRAM teardown, and zero SDL rendering dependencies inside domain models or data bindings.

##### Bug 038: Hardware & VRAM Coupling in the State Database and Models

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

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

##### Specification

1. **Centralized Widget Canvas Cache (`Registry` & `Screen`)**:
   * Remove `canvas: Any = None` from `PaneState` (`src/app/models/state/assets/widgets.py`).
   * Add `cdef public dict _canvases` to `Registry` (`src/libs/graphics/registry.pyx`) to store dynamic widget `TexturePtr` buffers keyed by `widget.name`.
   * Expose canvas lifecycle methods on `Registry`:
     * `canvas(self, str key, int w, int l, bint opaque=False) -> TexturePtr`: Returns the cached `TexturePtr` for `key` if present (and matching dimensions), or allocates and caches a new `render.canvas(w, l, opaque)`.
     * `get_canvas(self, str key) -> TexturePtr`: Retrieves the cached `TexturePtr` for `key`, or `None`.
     * `destroy_canvas(self, str key) -> void`: Destroys the `SDL_Texture*` via `render.destroy()` and removes `key` from `self._canvases`.
   * Update `Registry.clear()` to iterate over `self._canvases.values()`, destroy any remaining `SDL_Texture*` pointers, and clear `self._canvases`.
   * Update `Screen.stamp()`, `Screen._widgets()`, and `Screen.release()` (`src/app/game/screen.py`) to delegate widget canvas creation, lookup, and teardown to `self.registry`. Convert `Screen.release(self, menu: Menu)` from a `@staticmethod` to an instance method using `self.registry.destroy_canvas(widget.name)`.
   * Update `TerminalEventHandler.handle()` (`src/app/game/menus/handlers/terminal.py`) to invoke `screen.release(menu)` whenever a modal menu is popped from `data.board.menus`.
2. **Database Decoupling (`Board`)**:
   * Remove `import libs.graphics.render as render` and `from app.models.state import PaneState` from `src/app/game/board/core.py`.
   * Remove the manual `render.destroy(widget.state.canvas)` loop from `Board.clear()`.
3. **Typography Measurement & Font Resolution (`Registry` & `text.py`)**:
   * Bind `TTF_SizeUTF8` in `src/libs/graphics/registry.pyx` and expose `measure(self, str content) -> tuple` directly on `TTFFont` (or `registry.measure(font_key, content)`).
   * Remove `import libs.graphics.render as render` from `src/app/game/menus/bindings/text.py` and update `paginate()` to call `font.measure(test_line)`.
   * Update `LibraryBinding.bind()` and `TextBinding.bind()` in `src/app/game/menus/bindings/text.py` to resolve `font_key = kwargs.get("font", Fonts.DIALOGUE.value)` instead of hardcoding `"dialogue"`.

##### Architectural Analysis I

* **VRAM Lifecycle across Layer Transitions**: In `Engine._render()`, the active `Screen` is selected via `self.screens[player.state.layer]`. Meanwhile, `board.overlays` (such as the `VIEW` HUD) and `board.menus` are stored on `Board` and rendered by whichever `Screen` is currently active. Because all `Screen` instances share the same underlying SDL `_renderer` singleton, storing `_widget_canvases: Dict[str, TexturePtr]` as a class-level dictionary on `Screen` (or clearing/releasing via `Screen.release(menu)` in `Screen.destroy()`) guarantees that HUD and modal menu canvases remain accessible even when the player traverses a `Door` onto a new layer.
* **Preserving Synchronous Pagination**: `ScrollController` mutates `PaneState.pageindex` via `scrollup()` / `scrolldown()`, which check `self.more()` (`self.pageindex < self._pagecount - 1`). Keeping `paginate()` inside `src/app/game/menus/bindings/text.py`—backed by `font.measure()` on the `TTFFont` object retrieved from `self.registry.font(font_key)`—preserves lazy pagination and `PaneState._pagecount` semantics while completely removing `libs.graphics.render` from the binding layer.

##### User Review I

Rather than managing the `_widget_canvases` on the Python wrapper as a class level dictionary, why not store them on the Cython-level Registry and have the Screen retrieve them via an interface? Does it make any difference from a performance perspective?

##### Architectural Analysis II

###### Performance Comparison: `Screen` (Python) vs. `Registry` (Cython)

From a **performance perspective**, storing widget canvases in `Registry` (Cython `cdef dict`) vs. `Screen` (Python `dict`) makes **virtually zero measurable difference**:

1. **Both Use `PyDict_GetItem` Under the Hood**: Even in Cython, a `cdef dict _canvases` is still a standard Python `dict` C-struct (`PyDictObject`). Looking up a string key (`widget.name`) in `Registry` executes the exact same hash table lookup as `self._canvases.get(widget.name)` in Python.
2. **Low Cardinality**: `Screen._widgets()` only runs for active HUD overlays and open modal menus—typically **5 to 30 widgets per frame**, with only **1 to 5 of those being `PaneState` canvases**. A Python dict lookup takes ~30–40 nanoseconds; 5 lookups per frame equals ~150 nanoseconds (0.00015 ms out of a 16.67 ms 60 FPS frame budget).
3. **Crossing the Cython Boundary Still Happens Once**: Regardless of where the `TexturePtr` is cached, `Screen._widgets()` builds the `primitives` list in Python and passes the batch once per menu into `render.superimpose(primitives)`.

###### Comparison: Where Does It *Make Sense*?

While performance is identical, storing widget canvases in **`Registry` (`libs.graphics.registry.pyx`)** is **architecturally superior** to storing them on `Screen` for four reasons specific to Ontology's design:

**1. Multi-Screen / Multi-Layer Topology (`Engine.screens`)**

In `Engine`, `self.screens` is a `Dict[str, Screen]`—there is **one `Screen` instance per Board Layer** (e.g., `overworld`, `interior`), whereas **`Registry` is a true application-wide singleton** shared across all `Screen` instances (`screen.registry`).

* `board.overlays` (the HUD) and `board.menus` live on `Board`, which is layer-agnostic.
* When the Player walks through a `Door` from Layer A to Layer B, `Engine._render()` switches from `self.screens["layer_a"]` to `self.screens["layer_b"]`.
* If widget canvases were stored as instance attributes on `Screen`, Layer B's `Screen` would not have the HUD canvas that was baked on Layer A's `Screen` during `TerminalEventHandler` (unless `_widget_canvases` was made a mutated class-level global on `Screen`).
* Because every `Screen` already holds a reference to the same `self.registry`, putting `_canvases` in `Registry` naturally makes baked UI textures available across all layers without class-variable hacks.

**2. Unified VRAM Ownership & Teardown (`Registry.clear()`)**

`Registry` already owns the lifecycle of all other dynamically composited `TexturePtr` objects in VRAM (such as virtualized Sheet `stack` textures composed via `render.compose()` in `_get_or_load_texture`).
* When `Engine.stop()` runs, it calls `self.registry.clear()`.
* If `Registry` owns `_canvases`, `Registry.clear()` can deterministically `SDL_DestroyTexture` every active widget canvas in C alongside `_textures` and `_fonts`, guaranteeing zero VRAM leaks on shutdown even if a modal menu or overlay was left open on `Board`.

**3. Uniformity in `Screen._widgets()`**

In `Screen._widgets()`, every non-canvas widget resolves its texture via `self.registry.image(key)`. If `Registry` manages dynamic widget canvases (e.g., via `registry.canvas(name, w, l)`, `registry.get_canvas(name)`, `registry.release_canvas(name)`), `Screen` remains a pure stateless coordinator between `Board` assets and `Registry`/`render`:

* `Screen.stamp(widget)` asks `self.registry` for the widget's canvas texture (allocating via `render.canvas(w, l)` if absent) and stamps the 9-slice + text onto it.
* `Screen._widgets(menus)` queries `self.registry.get_canvas(widget.name)` for `PaneState` widgets, falling back to `self.registry.image(key)` for standard frame keys.
* `Screen.release(menu)` simply calls `self.registry.release_canvas(widget.name)` for each widget in `menu.widgets`.

**4. Solving the `TTFFont` Measurement Coupling at the Same Layer**

In **Bug 038**, the second half of the problem is that `LibraryBinding` and `TextBinding` already receive `self.registry: Registry`, **not** `Screen`.

* Because `Registry` already binds `SDL2/SDL_ttf.h` and holds the `TTFFont` instances, adding `registry.measure(font_key: str, text: str) -> tuple` (or `TTFFont.measure(text)`) directly on `Registry` lets `LibraryBinding` and `TextBinding` paginate text using only `self.registry`—which they already have injected—with zero imports of `libs.graphics.render`.

###### Summary Recommendation

| Criteria | `Screen` (Python `dict`) | `Registry` (Cython `cdef dict`) |
| :--- | :--- | :--- |
| **Lookup Performance** | ~35 ns / widget (negligible) | ~30 ns / widget (negligible) |
| **Multi-Layer (`Door`) Safe?** | Only if stored as a class-level dict | **Yes** (`Registry` is a shared singleton) |
| **Centralized VRAM Teardown** | Split between `Screen` and `Registry` | **Unified** inside `Registry.clear()` |
| **Text Measurement (`Bug 038`)** | Requires passing `Screen` or callback to `Binder` | **Already injected** into `Binder` / `Binding` |

**Verdict**: Put the widget canvas cache (and font measurement helper) in **`Registry` (`libs.graphics.registry.pyx`)**, with `Screen.stamp()`, `Screen._widgets()`, and `Screen.release()` delegating canvas retrieval and destruction to `self.registry`.

##### Goals

###### Goal: Centralize Widget Canvas VRAM in `Registry` and Delegate from `Screen`

Manage widget canvas `TexturePtr` allocations inside `Registry._canvases` and remove `PaneState.canvas`:

```cython
# src/libs/graphics/registry.pyx
cdef class Registry:
    cdef public dict _textures
    cdef public dict _canvases
    ...

    def canvas(self, str key, int w, int l, bint opaque=False) -> TexturePtr:
        cdef TexturePtr tex = self._canvases.get(key, None)
        if tex is not None and tex.ptr != NULL and tex.w == w and tex.l == l:
            return tex
        if tex is not None:
            render.destroy(tex)
        tex = render.canvas(w, l, opaque=opaque)
        self._canvases[key] = tex
        return tex

    def get_canvas(self, str key) -> TexturePtr:
        return self._canvases.get(key, None)

    cpdef void destroy_canvas(self, str key):
        cdef TexturePtr tex = self._canvases.pop(key, None)
        if tex is not None:
            render.destroy(tex)
```

```python
# src/app/game/screen.py
    def release(self, menu: Menu) -> None:
        """Explicitly destroys hardware canvas textures held by a Menu's panes."""
        if not menu.widgets:
            return
        for widget in menu.widgets.values():
            if isinstance(widget.state, PaneState):
                self.registry.destroy_canvas(widget.name)
```

###### Goal: Decouple `Board` from `libs.graphics.render`

Strip all SDL rendering imports and texture destruction loops from `src/app/game/board/core.py`:

```python
# src/app/game/board/core.py
    def clear(self) -> None:
        self.loaded = False
        self.paused = False
        self._assets.clear()
        self._cache.clear()
        self.menus.clear()
        self.overlays.clear()
        self.perimeters.clear()
        self._moisture_fields.clear()
```

###### Goal: Expose `TTFFont.measure` in `Registry` and Honor Configured Fonts in Bindings

Provide `measure(self, str content) -> tuple` on `TTFFont` and resolve the bound pane's configured font in `LibraryBinding` and `TextBinding`:

```cython
# src/libs/graphics/registry.pyx
cdef class TTFFont:
    ...
    def measure(self, str content) -> tuple:
        if self.ptr == NULL:
            return (0, 0)
        cdef int w = 0, h = 0
        cdef bytes b_content = content.encode('utf-8')
        TTF_SizeUTF8(self.ptr, b_content, &w, &h)
        return (w, h)
```

```python
# src/app/game/menus/bindings/text.py
def bind(self, **kwargs) -> Tuple[Callable, ...]:
    w, l = kwargs.get("w", 0), kwargs.get("l", 0)
    font_key = kwargs.get("font", Fonts.DIALOGUE.value)

    def content_function():
        if self._cached_pages is not None:
            return self._cached_pages

        raw = self._deref(self._content_ref, self.target.content)
        font = self.registry.font(font_key) if self.registry else None

        self._cached_pages = paginate(str(raw), font, w, l)
        return self._cached_pages

    return content_function
```

##### Tasks

**1. Task: Centralize Widget Canvas Lifecycle in `Registry` and `Screen`**

*Objective*: Remove `canvas` from `PaneState` and manage all widget canvas `TexturePtr` instances inside `Registry._canvases`.

* [] Subtask: Remove `canvas: Any = None` from `PaneState` in `src/app/models/state/assets/widgets.py`.
* [] Subtask: Add `cdef public dict _canvases` to `Registry` in `src/libs/graphics/registry.pyx` and implement `canvas(key, w, l, opaque=False)`, `get_canvas(key)`, `destroy_canvas(key)`, and teardown cleanup inside `Registry.clear()`.
* [] Subtask: Update `Screen.stamp()`, `Screen._widgets()`, and `Screen.release()` in `src/app/game/screen.py` to allocate, retrieve, and destroy widget canvases through `self.registry`.
* [] Subtask: Update `TerminalEventHandler.handle()` in `src/app/game/menus/handlers/terminal.py` to invoke `screen.release(menu)` on every popped modal menu.
* [] Subtask: Remove `import libs.graphics.render as render`, `from app.models.state import PaneState`, and the manual canvas destruction loop from `Board.clear()` in `src/app/game/board/core.py`.

**2. Task: Move Font Measurement to `Registry` (`TTFFont`) and Fix Binding Font Resolution**

*Objective*: Remove `libs.graphics.render` from `src/app/game/menus/bindings/text.py` and respect the `font` parameter passed by `Provider._bind_pane()`.

* [] Subtask: Declare `int TTF_SizeUTF8(TTF_Font* font, const char* text, int* w, int* h)` in `src/libs/graphics/registry.pyx` and implement `TTFFont.measure(self, str content) -> tuple` (delegating `render.measure` to `font.measure` for compatibility if needed).
* [] Subtask: Update `paginate()` in `src/app/game/menus/bindings/text.py` to call `font.measure(test_line)` and remove `import libs.graphics.render as render`.
* [] Subtask: Update `LibraryBinding.bind()` and `TextBinding.bind()` in `src/app/game/menus/bindings/text.py` to resolve `font_key = kwargs.get("font", Fonts.DIALOGUE.value)` instead of hardcoding `"dialogue"`.
* [!: Dependent on Prior Task Completion] Subtask: Recompile Cython extensions and update unit tests and documentation (`docs/06-widgets.md`, `docs/12-architecture.md`) to reflect `Registry`-owned widget canvases and `TTFFont.measure`.