##### Bug B011: Stream and Annular Pool Texture Overdraw

**STATUS**: CLOSED
**SEVERITY**: MEDIUM

**Description**

When a fluid stream encounters an obstacle and generates an annular pool, `Actuator._partition_pool` creates a top flank hitbox extending from $y = o_y - \text{flow} \cdot f_l$ to $y = o_y$. Concurrently, `Actuator.pump` sets `stream_length = oy - fy`, projecting stream corridor tiles all the way to $o_y$.

In `FluidFrame.keys`, full-tile keys are emitted along the stream corridor from $f_y$ to $o_y$, and the pool iteration subsequently emits full-tile keys across the top flank from $o_y - \text{flow} \cdot f_l$ to $o_y$. The stream corridor column within this band receives two identical overlapping texture blits on the same frame, doubling alpha-blended opacity and causing visual stuttering.

**Proposed Remediation**

In `Actuator.pump`, truncate the active stream length at the outer edge of the annular pool boundary rather than the obstacle face:

```python
if pool_bounds and flow > 0:
    if direction == Directions.DOWN.value:
        stream_length = max(0, pool_bounds.y - fy)
    elif direction == Directions.UP.value:
        stream_length = max(0, fy - (pool_bounds.y + pool_bounds.l))
    elif direction == Directions.RIGHT.value:
        stream_length = max(0, pool_bounds.x - fx)
    elif direction == Directions.LEFT.value:
        stream_length = max(0, fx - (pool_bounds.x + pool_bounds.w))
```

##### Post Phase 09.03 Assessment

In the current codebase, Bug B011 remains present and active.

###### Why the Bug Persists

1. **Raycast vs. Pool Calculation in `Actuator.propagate` (`src/app/services/generators/game/actuator.py`)**: `geometry.raycast()` returns `stream_length` as the distance from the emitter origin $(f_x, f_y)$ to the obstacle surface $(o_x, o_y)$ (e.g., $o_y - f_y = 599\text{px}$). `Actuator._partition_pool()` then expands an annular pool of radius $\text{flow} \times \text{dim}$ around the obstacle, setting `pool.y = 512` ($88\text{px}$ upstream of the obstacle face at $y = 600$).
2. **Dual Emission in `FluidFrame.keys` (`src/app/assets/frames/effects.py`)**:
* **Stream Pass**: Emits full-tile and slice keys along `state.length` from $y = f_y$ all the way to $y = o_y$ ($y \in [1, 600]$).
* **Pool Pass**: Emits tiles across the entire pool bounding box ($x \in [0, 192], y \in [512, 736]$).
3. **Resulting Overdraw**: For the column where the stream enters the pool ($x \in [70, 102], y \in [512, 600]$), `FluidFrame.keys` emits identical tile keys twice in the same frame. Because water assets utilize alpha blending, this doubles texture opacity along the entry corridor, creating a discolored, saturated visual artifact.

##### Architectural Review of the Proposed Remediation

The core remediation strategy in Bug B010 is geometrically and architecturally sound, but requires three adjustments to align with the current architecture:

1. **Relocation from `pump()` to `propagate()**`: Following the Phase 09.03 refactor, `Actuator.pump()` is merely a pass-through to `Actuator.propagate()`. The truncation logic must reside directly inside `Actuator.propagate()`.
2. **Hitbox Construction Sequencing**: Currently in `propagate()`, `_build_stream_hitbox()` is called *before* `_partition_pool()`. If `stream_length` is truncated after hitbox creation, `fluid.state.hitboxes[0]` will still extend to the obstacle face while `fluid.state.length` stops at the pool. `_build_stream_hitbox()` must be constructed **after** truncating `stream_length`.
3. **Downstream Safety**:
    * **`Cartographer` / Sweep-Line**: In `Cartographer._collect_water_rectangles()`, the corridor rectangle ends at $y = \text{pool.y}$ and the pool rectangle begins at $y = \text{pool.y}$. In `geometry.contours()`, the abutting edges at $y = \text{pool.y}$ span $x \in [f_x, f_x + f_w]$, which the sweep-line `xor()` cancels out, preserving a seamless outer contour with no spurious shorelines.
    * **`Board.water()`**: Coordinate queries within the truncated region ($y \in [\text{pool.y}, o_y]$) evaluate `True` via `fluid.state.pool` before checking `_in_stream()`.
    * **`fields.py`**: Truncating the stream hitbox eliminates overlapping AABBs between the stream corridor and the pool, preventing double-intersection calculations.

---

##### Proposed Solution

Update `Actuator.propagate()` in `src/app/services/generators/game/actuator.py` to truncate `stream_length` at the outer pool boundary when a static obstacle is struck, and construct the stream hitbox from the truncated length:

```python
# src/app/services/generators/game/actuator.py

    def propagate(self, fluid: Asset, board: Board) -> Tuple[int, Optional[Pool], List[Hitbox]]:
        """
        Pass 1: Truncates fluid stream against map bounds and static obstacles (mass == 0),
        expands annular pooling, updates compound hitboxes, and resets dirty flag.
        """
        source_prop = fluid.state.source
        direction = source_prop.value if hasattr(source_prop, "value") else str(source_prop)        
        flow = fluid.state.flow
        fw = fluid.properties.dimensions.w
        fl = fluid.properties.dimensions.l
        fx = fluid.state.position.x
        fy = fluid.state.position.y

        fluid.frame.tile_w = fw
        fluid.frame.tile_l = fl

        obstacle_tuples = self._collect_obstacles(fluid, board, direction)
        max_dist = self._calculate_max_distance(fluid, board, direction)

        stream_length, struck_obstacle = geometry.raycast(
            fx,
            fy,
            fw,
            fl,
            direction,
            obstacle_tuples,
            max_dist
        )

        pool_bounds: Optional[Pool] = None
        pool_hitboxes: List[Hitbox] = []

        # 1. Expand pool and truncate stream corridor at pool margin (Fix B010)
        if isinstance(struck_obstacle, Asset) and flow > 0:
            pool_bounds, pool_hitboxes = self._partition_pool(struck_obstacle, fluid, flow)
            
            if direction == Directions.DOWN.value:
                stream_length = max(0, pool_bounds.y - fy)
            elif direction == Directions.UP.value:
                stream_length = max(0, fy - (pool_bounds.y + pool_bounds.l))
            elif direction == Directions.RIGHT.value:
                stream_length = max(0, pool_bounds.x - fx)
            elif direction == Directions.LEFT.value:
                stream_length = max(0, fx - (pool_bounds.x + pool_bounds.w))

        # 2. Build non-overlapping compound hitboxes
        hitboxes: List[Hitbox] = []
        stream_hb = self._build_stream_hitbox(direction, stream_length, fw, fl)
        if stream_hb:
            hitboxes.append(stream_hb)
        if pool_hitboxes:
            hitboxes.extend(pool_hitboxes)

        fluid.state.length = stream_length
        fluid.state.pool = pool_bounds
        fluid.state.hitboxes = hitboxes
        fluid.state.dirty = False

        return stream_length, pool_bounds, hitboxes

```