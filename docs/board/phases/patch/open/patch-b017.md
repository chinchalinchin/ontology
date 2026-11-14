##### Bug B017: Stair Target Elevations Omitted by `Perimeter.generate` When Unoccupied by Weights

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `Perimeter.generate` (`src/app/services/generators/game/perimeter.py`, lines 98–104), candidate elevation tiers are derived exclusively from `board.weights(layer)`:

```python
weights = board.weights(layer)
elevations = {
    max(0, e)
    for w in weights
    for e in w.hitbox.elevations(w.properties, w.state)
} | {0}

```

Because `Stairs` (`AssetInstances.STAIRS`) are configured as sensors (`mass = -1`), they are excluded from `board.weights(layer)`. If a layer contains a stair incline transitioning to `base_e + delta` (such as `test-stairs` on layer `'0'` transitioning to `elevation = 1`), and no `m >= 0` weight currently occupies that upper tier at hydration time, `Perimeter.generate` never evaluates `cls.extract(board, layer, elevation=1)`, leaving `board.perimeters[layer][1]` unpopulated.

**Steps to Replicate**

1. Hydrate `world-testbed` where `test-stairs` is on layer `'0'` with `elevation = 0` and `delta = 1`, and all weights on layer `'0'` are at `elevation = 0`.
2. Call `Perimeter.generate(board, "0")`.
3. Observe that `1 not in perimeters`, even though `Perimeter.extract(board, "0", elevation=1)` returns `[(1000, 100, 1032, 196)]`.

**Proposed Remeditation**

Union the target elevations of `board.instances(AssetInstances.STAIRS.value, layer)` (`max(0, (s.state.elevation or 0) + s.state.delta)`) into the `elevations` set in `Perimeter.generate`.