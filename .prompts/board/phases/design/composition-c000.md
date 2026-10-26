#### Design: Composition C000 - Castle Dawn

* **Purpose**: Testing Gravity and Elevation in Phase 07.03.
* **Description**: 

### 4. Codebase Bug Reports

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