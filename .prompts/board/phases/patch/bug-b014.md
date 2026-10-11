##### Bug B014: Stair Railing Hitbox Traversal Block

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

In `src/app/game/logic/mechanics/spatial/collision.py`, `CollisionMechanics.update()` validates mover-stair overlap via:

```python
geometry.intersects(
    mover.state.position, mover.dimensions, mover.hitboxes,
    stair.state.position, stair.dimensions, stair.hitboxes
)
```

Because `stairs.yaml` populates `hitboxes` exclusively with side railings ($w=1, l=53$), characters walking along the center of the stairs or stepping onto the upper/lower landings never intersect `stair.hitboxes`. `_traverse_stairs()` is never called, leaving characters trapped on their originating elevation tier.

**Steps to Replicate**

1. Place `stairs-stone` at position `(100, 100)` with `direction: up`.
2. Move a player sprite to `(116, 150)` (centered between left and right railings).
3. Walk along the vertical axis from $y=190$ to $y=100$.
4. Observe that `geometry.intersects()` returns `None`, and `player.state.elevation` remains `0`.

**Proposed Remediation**

Evaluate stair sensor overlap using the full dimensional footprint of the staircase rather than railing hitboxes:

```python
stair_hb = Hitbox(Position(0, 0), stair.dimensions)
if geometry.intersects(
    mover.state.position, mover.dimensions, mover.hitboxes,
    stair.state.position, stair.dimensions, [stair_hb]
):
    self._traverse_stairs(mover, stair)
```

###### Analysis

Instantiating `Hitbox` and `Position` extension objects inside the 60 Hz collision update loop directly violates the engine's core architectural principle of **Zero Heap Allocation in the Inner Loop**.

If a board contains $M$ dynamic movers and $S$ staircases, executing:

```python
stair_hb = Hitbox(Position(0, 0), stair.dimensions)
```

generates $2 \times M \times S$ heap allocations per frame. Over continuous execution, this introduces unnecessary memory fragmentation and triggers the Python garbage collector, inducing frame-time spikes.

#### Zero-Allocation Alternatives

1. **Pre-Cached Sensor Hitbox on `StairProperties` / `StairState**`:

Rather than dynamic instantiation, the unified sensor footprint can be allocated once during bootstrap:

```python
# Evaluated once during flyweight/recipe construction
stair.properties.sensor_hitbox = [Hitbox(Position(0, 0), stair.properties.dimensions)]
```

2. **Primitive AABB Comparison in Cython**:
    
Because sensor intersection merely asks whether the mover's hitboxes intersect the stair's dimensional rectangle $(x, y, w, l)$, this check can be offloaded to `libs.core.math.geometry` without wrapping the stair's bounds in a `Hitbox` instance. A C-level function can test mover hitboxes directly against the primitive integer bounds $(b_x, b_y, b_w, b_l)$, identical to how `geometry.bounded()` operates for environmental boundaries.

