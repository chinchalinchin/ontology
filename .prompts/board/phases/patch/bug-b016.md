##### Bug B017: Decomposer Elevation Inheritance

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/services/generators/game/decomposer.py`, `Decomposer._hydrate_state()` inherits `layer` and `owner` from `parent_context` when omitted (`None`) on a child `AssetState`, but never inherits `elevation`. Furthermore, in `_unpack_node()` (line 274):

```python
if is_root:
    root_context["elevation"] = strut_state.elevation

```

Because `node.strut.elevation` defaults to `None` in `CompositionConfiguration`, `strut_state.elevation` remains `None` and overwrites `root_context["elevation"]` (which held `deployed_state.elevation`), causing compositions deployed at non-zero elevations to lose their deployed elevation across both the root strut and child components.

**Steps to Replicate**

1. Deploy any Composition in a state YAML with `elevation: 2`.
2. Unpack via `Decomposer.unpack(deployed_state)`.
3. Inspect the resulting root Strut and component `state.elevation` values; all assets with `elevation: None` in their PseudoState resolve to `state.elevation = None` (`0`) instead of `2`.

**Proposed Remeditation**

In `Decomposer._hydrate_state()`, inherit `elevation` from `parent_context` when `kwargs.get('elevation') is None`:

```python
if 'elevation' in kwargs and kwargs['elevation'] is None:
    kwargs['elevation'] = parent_context.get('elevation', 0)

```