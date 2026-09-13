#### Refactor: Phase 08.03 - Trajectory Optimization

**Overview**

Phase 08.02 successfully bifurcated strategic deliberation (`CognitionMechanics`) from tactical kinematics (`NavigationMechanics`) and moved continuous RRT tree expansion across the Cython boundary. However, the resulting navigation subsystem exhibits three primary operational deficiencies:

1. **Stochastic Trajectory Jitter**: Raw RRT produces exploratory, non-optimal polygonal paths. Without post-processing, navigating sprites exhibit unnatural zig-zags and angular detours along completely unobstructed corridors.
2. **Global Obstacle Ingestion Overhead**: `NavigationMechanics.obstacles()` extracts every physics body and perimeter hull across the active board layer. Passing hundreds of irrelevant obstacles into `rrt()` forces the inner sampling loop to evaluate line-of-sight against geometry located hundreds of pixels outside the search bounds.
3. **Rigid-Body Agent Deadlocks**: Because dynamic entities are excluded from static RRT obstacle matrices to avoid path thrashing, multi-agent navigation in tight corridors falls entirely back onto `physics.collide`. Moving sprites grind against each other's collision hitboxes, relying on elastic impulse and sliding friction rather than actively steering around oncoming bodies.

Phase 08.03 resolves these bottlenecks by implementing Cythonized raycast string-pulling (greedy path pruning), search-space broad-phase obstacle filtering, and Reciprocal Velocity Obstacle (RVO) local steering dynamics.

##### Goal: Path Pruning via Raycast String-Pulling

Post-process the raw RRT waypoint chain inside `src/libs/core/math/paths.pyx` prior to Python `Position` instantiation using a zero-allocation greedy string-pulling pass.

Given an initial backtraced node index chain $P = [p_0, p_1, \dots, p_m]$ where $p_0 = \text{target}$ and $p_m = \text{start}$:

1. Reverse the index chain to obtain the forward route from start to target: $W = [w_0, w_1, \dots, w_m]$.
2. Initialize anchor index $i = 0$.
3. For $j = m$ down to $i + 2$:
    * Evaluate `_is_segment_clear(nodes[w_i].x, nodes[w_i].y, nodes[w_j].x, nodes[w_j].y, c_obstacles, num_obstacles)`.
    * If line-of-sight is unobstructed: prune intermediate waypoints $w_{i+1}, \dots, w_{j-1}$, advance anchor $i \leftarrow j$, and repeat.
4. Output the reduced vertex chain.

```c
// Greedy string-pulling in paths.pyx (nogil)
cdef int pruned_len = 0;
cdef int anchor_idx = 0;
cdef int scan_idx;
cdef bint clear;

pruned_buf[pruned_len++] = forward_buf[0];

while anchor_idx < forward_len - 1:
    scan_idx = forward_len - 1;
    clear = False;
    while scan_idx > anchor_idx + 1:
        if _is_segment_clear(nodes[forward_buf[anchor_idx]].x, nodes[forward_buf[anchor_idx]].y,
                             nodes[forward_buf[scan_idx]].x, nodes[forward_buf[scan_idx]].y,
                             c_obstacles, num_obstacles):
            clear = True;
            break;
        scan_idx -= 1;
    
    if clear:
        pruned_buf[pruned_len++] = forward_buf[scan_idx];
        anchor_idx = scan_idx;
    else:
        anchor_idx += 1;
        pruned_buf[pruned_len++] = forward_buf[anchor_idx];
```

##### Goal: Broad-Phase Obstacle Culling for Search Spaces

Eliminate extraneous Liang-Barsky clipping evaluations by culling obstacles outside the padded search-space bounding box $[x_{\min}, y_{\min}, x_{\max}, y_{\max}]$.

Prior to allocating system memory for `c_obstacles` in `paths.pyx`, execute a 1D interval overlap check:

$$
\text{Reject if } (x_{\text{obs}} + w_{\text{obs}} < x_{\min}) \lor (x_{\text{obs}} > x_{\max}) \lor (y_{\text{obs}} + l_{\text{obs}} < y_{\min}) \lor (y_{\text{obs}} > y_{\max})
$$

Only bounding boxes intersecting the active exploration window are packed into the contiguous C-buffer.

```python
# In NavigationMechanics._navigate() or paths.pyx:
cdef int culled_count = 0
for i in range(num_obstacles):
    obs = obstacles[i]
    if (obs[0] + obs[2] >= min_x and obs[0] <= max_x and
        obs[1] + obs[3] >= min_y and obs[1] <= max_y):
        c_obstacles[culled_count].x = float(obs[0])
        c_obstacles[culled_count].y = float(obs[1])
        c_obstacles[culled_count].w = float(obs[2])
        c_obstacles[culled_count].l = float(obs[3])
        culled_count += 1
```

##### Goal: Multi-Agent Reciprocal Local Steering (RVO)

Integrate Reciprocal Velocity Obstacle (RVO) mechanics into `motive.update()` and `libs.core.math.physics`.

Instead of accelerating directly toward `trajectory.target` via `physics.dynamics` and colliding with oncoming entities, an entity calculates a preferred velocity vector $\mathbf{v}_{\text{pref}}$, senses neighboring characters within an interaction radius $R_{\text{avoid}}$, and selects an optimal avoidance velocity $\mathbf{v}_{\text{opt}}$ outside the reciprocal velocity obstacle cones.

For agents $A$ and $B$ with radii $r_A, r_B$ and velocities $\mathbf{v}_A, \mathbf{v}_B$:

$$
VO_{A\vert{}B} = \left\{ \mathbf{v} \;\middle\vert{}\; \exists t > 0 : t \cdot \mathbf{v} \in \mathcal{D}\left(\mathbf{p}_B - \mathbf{p}_A, r_A + r_B\right) \right\}
$$

$$
RVO_{A\vert{}B} = \left\{ \mathbf{v} \;\middle\vert{}\; 2\mathbf{v} - \mathbf{v}_A \in VO_{A\vert{}B} \right\}
$$

`physics.rvo()` evaluates candidate velocity samples around $\mathbf{v}_{\text{pref}}$, selecting the vector closest to $\mathbf{v}_{\text{pref}}$ that falls outside $\bigcup_{B} RVO_{A\vert{}B}$.

```python
# In app/game/logic/modules/motion/motive.py:
pref_vel = physics.desired_velocity(
    sprite.state.position,
    target_pos,
    sprite.state.character.speed
)

avoid_vel = physics.avoid(
    sprite.primitive(),
    pref_vel,
    neighbors,
    delta
)

sprite.state.velocity.vx = avoid_vel.vx
sprite.state.velocity.vy = avoid_vel.vy
```

##### Tasks

**1. Task: Cython Path Pruning Engine**

*Objective*: Implement zero-allocation raycast shortcutting within `libs.core.math.paths`.

* [ ] Subtask: In `src/libs/core/math/paths.pyx`, allocate an auxiliary `pruned_buf` sized to `max_iter + 2`.
* [ ] Subtask: Implement the `_prune_path()` C helper executing greedy line-of-sight checks via `_is_segment_clear()`.
* [ ] Subtask: Ensure string-pulling runs entirely within the `with nogil:` block prior to Python `Position` allocation.
* [ ] Subtask: Verify collinear and redundant diagonal waypoints collapse into single straight-line vectors when unobstructed.

**2. Task: Search-Space Obstacle Partitioning**

*Objective*: Eliminate non-local geometry checks from the RRT exploration loop.

* [ ] Subtask: In `src/libs/core/math/paths.pyx`, compute search bounds $[x_{\min}, y_{\min}, x_{\max}, y_{\max}]$ prior to obstacle ingestion.
* [ ] Subtask: Filter input obstacles against search bounds, packing only intersecting AABBs into `c_obstacles`.
* [ ] Subtask: Update memory allocation size to match the culled obstacle count rather than the layer-wide total.
* [ ] Subtask: Add fallback padding adjustments when $x_{\min}, y_{\min}, x_{\max}, y_{\max}$ bounds clamp to map boundaries.

**3. Task: Reciprocal Velocity Obstacles (RVO) Integration**

*Objective*: Prevent multi-agent physical overlap grinding and corridor deadlocks.

* [ ] Subtask: Implement `cpdef Velocity avoid(...)` in `src/libs/core/math/physics.pyx` calculating reciprocal velocity obstacles.
* [ ] Subtask: In `src/app/game/logic/modules/motion/motive.py`, query `board.characters()` on the active layer within $2 \times \text{action.radius}$.
* [ ] Subtask: Pass neighbors and preferred velocities into `physics.avoid()`, assigning the resulting vector to `sprite.state.velocity`.
* [ ] Subtask: Ensure kinematic player entities retain absolute control while NPC sprites steer around them.

**4. Task: Verification and Behavioral Regression Suite**

!!! note
    Task completion contingent on user acceptance of previous tasks.

*Objective*: Verify path smoothness, planning performance, and agent passing behavior.

* [!] Subtask: Add unit tests in `tests/unit/test_libs_core_math.py` validating path pruning on known stepped obstacle configurations.
* [!] Subtask: Add benchmarks in `tests/algorithms/rrt.py` measuring iteration speedup from search-space obstacle culling.
* [!] Subtask: Create unit tests in `tests/unit/test_app_game_logic_modules_motion_motive.py` verifying two opposing NPCs in a corridor steer laterally to pass without triggering `physics.collide`.