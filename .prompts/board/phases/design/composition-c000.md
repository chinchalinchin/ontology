#### Design: Composition C000 - Castle Dawn

* **Purpose**: Testing Gravity and Elevation in Phase 07.03.
* **Description**: 

### 4. Codebase Bug Reports

##### Bug B018: Stairs Only Emit Hitboxes at Base Elevation Preventing Descent

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

In `app/assets/hitboxes/crafts.py`, `MaterialHitbox.elevations()` and `MaterialHitbox.get()` only emit hitboxes at `target_e = max(0, state.elevation)`. When a Sprite ascends a `steps` asset (`StairState`) from `elevation = 0` with `delta = 1`, the Sprite's elevation becomes `1`. Because the stair's `MaterialHitbox` returns `[]` for `elevation = 1`, the Sprite can no longer intersect the stair sensor at `elevation = 1` to descend back to `elevation = 0` (and in `Ontology Docs: Assets`, the descent velocity condition for `up` and `down` stairs also typos `vx` instead of `vy`).

**Steps to Replicate**

1. Deploy a `steps` Craft (`elevation = 0, delta = 1, blueprint = 'up'`) leading to an `elevation = 1` surface.
2. Move a Sprite north (`vy` less than `0`) onto `steps` so its `elevation` transitions from `0` to `1`.
3. Move the Sprite south (`vy` greater than `0`) onto `steps` from `elevation = 1` and observe that `steps.hitbox.get(properties, state, elevation=1)` returns `[]`, preventing descent.

**Proposed Remeditation**

In `MaterialHitbox.elevations()` and `MaterialHitbox.get()` (or a dedicated `StairHitbox` schema), include both endpoints of `StairState` transitions (`base_e` and `base_e + state.delta`):

```python
if isinstance(state, StairState):
    base_e = max(0, state.elevation if state.elevation is not None else 0)
    return [base_e, max(0, base_e + state.delta)]
```

##### Bug B019: Decomposer `anchor(parent)` Double-Counts Branch `pseudo_y`

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `app/services/generators/game/decomposer.py`, `_resolve_anchor()` computes `self_y = self_state.position.y`, which for a component of a branch strut is already expressed in the local coordinate frame of `parent` (where the parent strut's local origin is `y = 0`). However, when `target_ref == "parent"`, `_resolve_anchor()` sets `target_y = parent_context.get("pseudo_y", 0)` instead of `0`. This shifts the computed `anchor` of every component using `anchor(parent)` inside a branch strut by `parent.pseudo_y`, corrupting its `ground_y` sort order whenever `parent.pseudo_y != 0`.

**Steps to Replicate**

1. Define a Composition branch whose `strut` has `position: { x: 0, y: 200 }` and `dimensions.l = 96`.
2. Add a child component on that branch with `position: { x: 0, y: 48 }`, `dimensions.l = 48`, and `anchor: anchor(parent)`.
3. Unpack the Composition via `Decomposer.unpack()` and observe that `component.state.anchor` resolves to `200` instead of `0`, yielding `ground_y = 596` instead of `396`.

**Proposed Remeditation**

In `Decomposer._resolve_anchor()`, set `target_y = 0` when `target_ref == "parent"` (since `self_y` is already relative to `parent`), and when `target_ref == "root"` on a same-layer branch component, account for `parent_context.get("pseudo_y", 0)` in the child's offset from `root`.

##### Bug B020: Decomposer `_multiply_expansion` and `_multiply_perimeter` Overwrite `state.anchor`

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `app/services/generators/game/decomposer.py`, `_multiply_simple()` preserves `base_anchor = int(state.anchor or 0)`, but `_multiply_expansion()` sets `seg_anchor = int(base_ground - (seg_y + l))` and `_multiply_perimeter()` sets `north_anchor = int(north_bottom - l)` (and `0` for `south`, `east`, `west`) without adding `int(state.anchor or 0)`. Any explicit `anchor` or `anchor(...)` macro configured on `columns` (`pillar`, `tower`) or `enclosures` (`palisade`) is discarded during multiplication.

**Steps to Replicate**

1. Configure a `pillar` or `tower` component in a Composition with a non-zero `anchor` (e.g., `anchor: 32` or `anchor: anchor(parent)`).
2. Unpack via `Decomposer.multiply()` and inspect the spawned `crowns`, `shafts`, and `bases` units.
3. Observe that `state.anchor` on the parent state was ignored rather than added to each segment's `seg_anchor`.

**Proposed Remeditation**

In `_multiply_expansion()` and `_multiply_perimeter()`, compute `base_anchor = int(state.anchor or 0)` and add `base_anchor` to the segment anchor passed to `self._spawn_unit()`.

##### Bug B021: `Decomposer._hydrate_state` Fails to Namespace `SwitchState.link`

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

When `Decomposer._hydrate_state()` unpacks components in a Composition, it rewrites each component's `name` to `<base_inst>-<parent_name>-<comp_name>-<inc>` (e.g., `gate-strut-castle-foundation-1-atrium-main-gate-1`). However, `_hydrate_state()` does not transform the `link` attribute on `SwitchState` (`Gate` and `Plate` assets), leaving `state.link` as the raw pseudo-state string (`atrium-main-gate`). Consequently, plates and gates unpacked from a Composition cannot resolve their linked target on the `Board`.

**Steps to Replicate**

1. Add a `Plate` (`link: my-gate`) and a `Gate` (`name: my-gate`) to a Composition.
2. Unpack the Composition onto the `Board`.
3. Observe that the `Gate` is named `gate-strut-<root>-1-my-gate-1`, while `plate.state.link` remains `'my-gate'`, causing lookup of the linked gate to fail.

**Proposed Remeditation**

In `Decomposer._unpack_components()`, resolve `SwitchState.link` against `scope_lookup` (or across a composition-wide component name map) and format `kwargs["link"]` using the target component's hydrated `<base_inst>-<parent_name>-<target_name>-<inc>` nomenclature.

##### Bug B022: `SwitchHitbox` Disables `Plate` Sensor Collisions Once Activated

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `app/assets/hitboxes/objects.py` (and `Ontology Docs: Assets`), `SwitchHitbox.get()` returns `[]` whenever `state.switch` is `True`. While this is intended for `Gates` (which become passable when open), assigning `SwitchHitbox` to `Plates` (`mass = -1` sensors) causes a `Plate` to lose all hitboxes the moment `state.switch` becomes `True`, preventing it from ever detecting subsequent collisions to toggle back off.

**Steps to Replicate**

1. Deploy a `stone-switch` Plate (`mass = -1`) with `SwitchHitbox` and `switch = False`.
2. Intersect the Plate with a Sprite so `plate.state.switch` flips to `True` (or deploy it with `switch = True`).
3. Call `plate.hitboxes` (`SwitchHitbox.get()`) and observe that it returns `[]`, permanently disabling collision detection for the sensor.

**Proposed Remeditation**

Assign `StaticHitbox` (instead of `SwitchHitbox`) to `objects.plates` in `src/data/config/recipes/main.yaml` so sensor plates retain their detection footprint in both switch states while `mass: -1` bypasses physical collision resolution.