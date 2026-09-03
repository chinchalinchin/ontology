##### Bug B003: Painter's Algorithm String Exception

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

Phase 05.05 tasked a fix for the `Screen.draw()` height sorting crash, noting that late-bound string references in `a.state.height` (e.g., `"parent.depth"`) cause `TypeError` exceptions during `list.sort()`. The specified fix required a runtime guard to catch strings if the `Decomposer` failed to resolve them.

The implemented lambda function in `Screen.draw` is:
`a.state.height if getattr(a.state, 'height', None) is not None else ...`

This lambda only checks if the height is `not None`. If the `Decomposer` passes a late-binding string to the renderer, `is not None` evaluates to `True`, and the string is passed into the Cython sorting tuple. Python will immediately throw a `TypeError: '<' not supported between instances of 'str' and 'int'` when comparing it against a standard asset's Y-coordinate.

**Steps to Replicate**

1. Hydrate a Board containing a `Composition` (e.g., a Door bound to a Strut) where the child asset has `state.height = "parent.height"`.
2. Skip or bypass the `Decomposer`'s string-to-int mutation phase.
3. Allow the Engine to reach the `_render()` phase.
4. `Screen.draw()` will crash the game loop during `assets.sort()`.