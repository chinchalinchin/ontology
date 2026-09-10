#### Refactor: Phase 04.03 - Motion Modules

In the [Phase 04.01](./phase-04-01.md) & [Phase 04.02](./phase-04-02.md) refactors, velocity-based motion and momentum transfer collisions were implemented for Players and Sprites alike. After experimenting with the setup, it is decided the momentum-based controls (i.e. conservation of momentum making it hard to come to a complete without zeroing out) need adjusted. Momentum-based motion will be a great addition for Sprites and Objects, but cannot stay for Players.

**Goals** 

- Separate the motion calculation in `app.game.logic.mechanics.core` into modules in `app.game.logic.mechanics.core.motion`:
    - **KinematicMotion**: This is used for the Player. When player presses right, the Sprite immediately changes *velocity* to right, snapping to the inputted direction without getting sent into circular motion. Velocity is used to control Player position updates through Symplectic Euler updates, but it will no longer change as a vector. It will only change by an amount equal to impulse in one direction at a time, with the other direction nulled out (unless Player is pressing a combination, e.g. up arrow + left arrow). 
    - **MotiveMotion**: This is used for Sprites. Velocity vectors are calculated by using the direction of (Goal - Position) unit vectors and impulse. However, they have Friction applied to them to stop them from going into "orbit" due to conservation of momentum.
    - **FrictiveMotion**: This is used for Crates. Velocity vectors do not have impulse changes applied. Friction is used to decrement velocity until coming to stop. 

To adhere to the Single Responsibility Principle, `MotionMechanics` should not be a monolithic loop. However, defining `Kinematic`, `Motive`, and `Frictive` as entirely separate `Mechanic` classes injected into the `MechanicsConfiguration` introduces unnecessary overhead, as the `Board` would be queried repeatedly for the same mutable Assets.

Instead, `MotionMechanics` should act as a delegator that iterates over the mutable Assets once, routing them to isolated strategy modules based on their mass/motive classification.

Here is how the pipeline should treat the Player:

* **Property Level:** The Player retains a normal, dynamic mass (e.g., $m = 10$).
* **Phase 1 - Spatial Resolution (Unchanged):**
    * **Player vs. Wall ($m=0$):** `inv_total` is $> 0$. The Wall absorbs 0% of the overlap shift, and the Player absorbs 100%. The Player correctly halts at the wall boundary.
    * **Player vs. Crate ($m=5$):** Both absorb the spatial shift proportional to their inverse mass. The Player effectively pushes the Crate out of the way.
* **Phase 2 - Momentum Transfer (The Fix):** Bypass the 1D elastic collision calculation *only* for the Player.

Instead of changing the Player's mass, update the momentum transfer logic in `spatial/collision.py` to something like this:

```python
# 2. Momentum Transfer
has_v1 = hasattr(asset_a.state, 'velocity') and asset_a.state.velocity is not None
has_v2 = hasattr(asset_b.state, 'velocity') and asset_b.state.velocity is not None

is_a_player = asset_a.taxonomy.instance == AssetInstances.PLAYERS
is_b_player = asset_b.taxonomy.instance == AssetInstances.PLAYERS

# ... mass checks ...

else:
    # Both dynamic, calculate 1D elastic collisions independently for X and Y
    v1f_x = (v1x * (m1 - m2) + 2 * m2 * v2x) / (m1 + m2)
    v1f_y = (v1y * (m1 - m2) + 2 * m2 * v2y) / (m1 + m2)
    
    v2f_x = (v2x * (m2 - m1) + 2 * m1 * v1x) / (m1 + m2)
    v2f_y = (v2y * (m2 - m1) + 2 * m1 * v1y) / (m1 + m2)

    # Apply momentum UNLESS the asset is a Player
    if has_v1 and not is_a_player:
        asset_a.state.velocity.vx = v1f_x
        asset_a.state.velocity.vy = v1f_y
    if has_v2 and not is_b_player:
        asset_b.state.velocity.vx = v2f_x
        asset_b.state.velocity.vy = v2f_y

```

By decoupling the spatial shift (to keep player from breaking the map) from the momentum rebound (to keep player from bouncing), the engine simulates kinematic, sliding movement against walls without breaking inverse mass calculations.

##### Tasks

**1. Task: Submodule Architecture**

*Objective*: Decouple monolithic motion logic into discrete procedural modules.

* [x] Subtask: Create `app.game.logic.mechanics.core.motion` package.
* [x] Subtask: Implement `kinematic.py` to handle Symplectic Euler integration and sub-pixel accumulation (`rx`, `ry`) for all assets.
* [x] Subtask: Implement `motive.py` to handle directional impulses, device polling resolution for Players, and pathfinding vector calculations for Sprites.
* [x] Subtask: Implement `frictive.py` to handle spatial Tile queries and linear velocity decay for Crates/Inert objects.
* [x] Subtask: Refactor `MotionMechanics.update()` to map assets to their respective motion strategies in a single pass.

**2. Task: Correct Physics Integrations**

*Objective*: Resolve mathematical flaws in movement and collision code.

* [x] Subtask: Update `motive.py` pathfinding to evaluate distance to `goal.position` and clamp velocity to prevent target oscillation.
* [!] Subtask: Update `CollisionMechanics._resolve` to determine the collision normal based on the shallowest penetration axis.
* [!] Subtask: Apply the 1D elastic collision formula *only* to the determined normal axis.

**3. Task: Implement Kinematic Player Motion**

*Objective*: Create a dedicated motion module for snappy, instant-response player controls.

* [x] Subtask: Implement `kinematic.py`.
* [x] Subtask: Add Axis-Snapping logic. When calculating player velocity from the `Mapping` poll, explicitly nullify the orthogonal axis. If input is strictly horizontal, set $v_y = 0$. If input is strictly vertical, set $v_x = 0$.
* [x] Subtask: Bypass `impulse` for the Player. Map input directions directly to the maximum `speed` magnitude.
* [x] Subtask: Retain diagonal support. If both axes are polled simultaneously, normalize the vector and multiply by `speed` to prevent faster diagonal movement.

**4. Task: Kinematic Collision Bypass**

*Objective*: Allow the player to slide along walls without bouncing, while still pushing dynamic objects.

* [x] Subtask: In `CollisionMechanics._resolve`, separate the Spatial Resolution phase from the Momentum Transfer phase.
* [x] Subtask: Update Spatial Resolution. The player should still be pushed out of static walls (to prevent boundary breaking) and should still push dynamic crates based on mass ratios.
* [x] Subtask: Update Momentum Transfer. Add a conditional check: `if asset.taxonomy.instance == AssetInstances.PLAYERS`, bypass the elastic rebound formula entirely. The player's velocity must remain untouched by physical impacts.

**5. Task: Cython Physics Migration**

*Objective*: Offload all heavy floating-point integrations and overlap resolutions to `libs.core.math.Physics`.

* [x] Subtask: Define `cdef void resolve_collision(...)` in `libs.core.math.pxd`. It should accept typed arguments: `Position p1`, `Dimensions d1`, `Velocity v1`, `float m1`, `bint is_kinematic1` (and the same for asset 2).
* [x] Subtask: Port the spatial resolution and momentum transfer logic from `CollisionMechanics._resolve` into `resolve_collision`. Use C-native `abs()` and float division.
* [x] Subtask: Define `cpdef void integrate_kinematics(list assets, float delta)` in `Physics`.
* [x] Subtask: In `integrate_kinematics`, loop through the provided objects, extract their `Position` and `Velocity` extension types, and perform the `rx/ry` accumulation and threshold shifting natively.

**6. Task: Python Mechanics Refactor**

*Objective*: Strip raw math from the Python game loop, turning Mechanics into lightweight dispatchers.

* [x] Subtask: Refactor `CollisionMechanics._resolve` to evaluate the game logic (e.g., determining `m1`, `m2`, `is_a_player`), and pass those variables into `Physics.resolve_collision()`.
* [x] Subtask: Refactor the final integration step of `MotionMechanics` (or the new `kinematic.py` submodule) to strip the `rx/ry` accumulation math and instead call `Physics.integrate_kinematics()`.

