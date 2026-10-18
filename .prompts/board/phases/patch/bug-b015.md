
##### Bug B016: Decomposer Macro Scope

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

In `src/app/services/generators/game/decomposer.py`, `Decomposer._resolve_anchor()` and `Decomposer._unpack_components()` exhibit two coupled defects when evaluating `anchor(...)` macros:

1. `_unpack_components()` builds `scope_lookup` exclusively from sibling components inside `node.components` and omits the parent `node.strut` (and `root.strut`) raw names. Referencing the parent strut by name (as documented in `03-compositions.md`, e.g., `anchor: anchor(house-exterior)` or `anchor: anchor(house-interior)`) fails lookup, logs a warning, and defaults `anchor` to `0`.
2. When `anchor(parent)` is used on a branch or root strut that declares a non-zero `position.y` (`pseudo_y != 0`), `_resolve_anchor()` sets `target_y = parent_context.get("pseudo_y", 0)`. Because `self_state.position.y` (`self_y`) is already expressed in the parent strut's local frame of reference (where the parent's top edge is at `y = 0`) and `parent.position.y` is subsequently added to `self_state.position.y` during coordinate hydration, adding `pseudo_y` to `target_y` double-counts the parent's vertical offset and shifts the child's `ground_y` baseline by `parent.pseudo_y`.

**Steps to Replicate**

1. Define a Composition branch whose `strut` has `name: house-interior` and `position: { x: 10, y: 10 }` (`l = 96`), and a child Door with `position: { x: 20, y: 20 }` (`l = 48`).
2. Set `anchor: anchor(house-interior)` on the Door and call `Decomposer.unpack()`. Observe warning `Unable to resolve anchor target 'house-interior'` and `door.state.anchor == 0`.
3. Change the Door to `anchor: anchor(parent)` and call `Decomposer.unpack()`. Observe `door.state.anchor == 38` (`ground_y = 30 + 48 + 38 = 116`) instead of `28` (`ground_y = 10 + 96 = 106`).

**Proposed Remeditation**

In `Decomposer._resolve_anchor()`, set `target_y = 0` for `target_ref == "parent"`, and also allow `target_ref == parent_context.get("raw_name")` (or register the parent strut's un-suffixed name in `parent_context["raw_name"]`):

```python
if target_ref == "parent" or target_ref == parent_context.get("raw_name"):
    target_y = 0
    target_l = parent_context.get("length", 0)

```