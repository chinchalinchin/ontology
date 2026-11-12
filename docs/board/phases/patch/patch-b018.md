##### Bug B018: Library Binding Font Desynchronization

**STATUS**: OPEN

**SEVERITY**: MEDIUM

**Description**

In `src/app/game/menus/bindings/text.py`, both `LibraryBinding.bind()` and `TextBinding.bind()` hardcode `font = self.registry.font("dialogue")`. Neither binding captures or applies the lexical `font` passed in `**kwargs` from `Provider._unpack_pane()`. In addition, `Provider._bake_pane()` calls `widget.binding.bind(w=w, l=l)` without supplying `font=widget.state.font`. When a menu pane specifies an alternative font (`font: menu` or `font: title`), `paginate()` calculates line wrapping and page boundaries using the dimensions of `"dialogue"`, while `_bake_pane()` rasterizes glyphs using `widget.state.font`. This desynchronization causes text clipping, premature wrapping, or canvas overflow.

**Steps to Replicate**

1. Configure a menu pane in YAML declaring `font: title` with a bound `TextBinding`.
2. Provide a string whose length causes line wrapping.
3. Call `Provider.unpack()` and inspect `widget.state.canvas`.
4. Observe that `paginate()` breaks lines based on `"dialogue"` character widths instead of `"title"` character widths.

**Proposed Remeditation**

1. Update `LibraryBinding` and `TextBinding` in `src/app/game/menus/bindings/text.py` to capture `font` in `__init__` or accept `font` in `bind(w, l, font=None)`.
2. Update `Provider._bake_pane()` in `src/app/services/generators/menus/provider.py` to pass `font=widget.state.font` into `widget.binding.bind(w=w, l=l, font=widget.state.font)`.
