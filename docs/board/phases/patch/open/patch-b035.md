##### Bug B035: `Screen.stamp` Does Not Clear `PaneState.canvas` Prior to Re-Stamping Transparent Text Panes

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/game/screen.py` (`Screen.stamp`, lines 253–295), when a `PaneState` widget is re-stamped (e.g., via `UpdateEventHandler` when scrolling dialogue or updating dynamic text), `Screen.stamp` invokes `render.construct(tex, primitives)` under the assumption `# 1. Clear target canvas and stamp 9-slice background (if any)`. However, `render.construct` in `src/libs/graphics/render.pyx` does not clear `target` before iterating over `tiles`. When `widget.id == "transparent"`, `primitives` is empty (`[]`), making `render.construct(tex, [])` a complete no-op. Subsequent `render.write(...)` calls blend new text directly over the previous text pixels on `widget.state.canvas`, and clearing text to `""` leaves the old text permanently visible.

**Steps to Replicate**

1. Instantiate a `Pane` widget with `id="transparent"` and initial text content `"First Page"`.
2. Call `screen.stamp(widget)` to allocate `widget.state.canvas` and rasterize `"First Page"`.
3. Dispatch an `UpdateEvent(widget=widget, content="Second Page")` (or call `screen.stamp(widget, "Second Page")`).
4. Inspect `widget.state.canvas`: `render.clear` is never called on `tex` and `render.construct(tex, [])` performs no operations, leaving `"First Page"` baked underneath `"Second Page"`.

**Proposed Remeditation**

Invoke `render.clear(tex)` in `Screen.stamp` prior to calling `render.construct(tex, primitives)` (or clear `target` inside `render.construct`).
