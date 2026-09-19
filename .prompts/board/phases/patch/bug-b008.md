##### Bug B008: Open Gate Obstruction

**STATUS**: OPEN
**SEVERITY**: Medium

**Description**

`Board.obstacles()` retrieves all gates via `self._cached_instances.get(layer, {}).get(AssetInstances.GATES.value, [])` without checking their `state.switch` value. In the engine specification, an open gate (`switch == True`) has no physical hitboxes and allows entities to pass freely. Including open gates in `Board.obstacles()` causes pathfinding algorithms (`NavigationMechanics`) and line-of-sight checks to treat open passages as solid barriers.

**Steps to Replicate**

1. Deploy a gate linked to a pressure plate on Layer `0`.
2. Trigger the plate so `gate.state.switch = True`.
3. Call `board.obstacles('0')`.
4. Observe that the open gate is still returned in the obstacle list.

**Proposed Remediation**

Filter gates in `Board.obstacles()` by switch state:

```python
gates = [
    g for g in self._cached_instances.get(layer, {}).get(AssetInstances.GATES.value, [])
    if not getattr(g.state, "switch", False)
]
```