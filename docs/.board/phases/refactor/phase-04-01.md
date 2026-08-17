#### Refactor: Phase 04.01 - Mechanics

**Missing: Layer Traversal (DoorMechanics)**

The `Door` object schema and `DoorState` (`layer`, `outlayer`, `out` position) exist, but there is no system to process them. A mechanic is required to detect when a mutable entity intersects a Door's hitbox, execute `board.relayer()`, and update the entity's coordinate position to the `out` target.

**Missing: Instantiation (SpawnMechanics)**

`ProjectileMechanics` handles projectiles *after* they are deployed, and `RemoveMechanics` handles Temporary Effects *after* they expire. However, nothing bridges the gap between a Sprite's state and the creation of these entities. A mechanic must poll for specific `(Action, Frame)` tuples (e.g., frame 4 of the `shoot` action) and instantiate the corresponding Projectile or Effect into the `Board` asset list.

**Missing: World Interaction (InteractionMechanics)**

Chests and other non-physics mutable objects require a dedicated interaction handler. While the `SwitchMechanics` resolves autonomous triggers (plates/gates), an interaction mechanic must translate a Sprite's physical proximity and action state into flipping a Chest's binary `switch` and dropping/transferring its `content` into the world or inventory.

**Update: CombatMechanics (Spatial Regression)**

This mechanic was bypassed during the Phase 04 physics overhaul. It currently utilizes a brute-force $O(N^2)$ nested loop to check attacker hitboxes against all targets on a layer natively in Python. It must be refactored to inherit `SpatialMechanic` and utilize `self.query_collisions(attackers + targets)` to leverage the Cython grid.

**Update: MotionMechanics (Kinematic Sliding & Delta-Time)**

Currently, movement is strictly evaluated as pixels-per-tick, ignoring the `delta` argument entirely. Furthermore, it applies direct X/Y vector offsets towards a goal. When paired with the new `CollisionMechanics`, a Sprite moving diagonally into a wall will be completely halted on both axes rather than sliding along the unblocked axis. The vector calculation must be decoupled to evaluate X and Y movement independently against physical boundaries.

**Update: ProjectileMechanics (Environmental Collisions)**

The current implementation stub only queries `Projectiles` and `Sheets`. Projectiles will currently fly through `Crates`, `Gates`, and boundary `Tiles`. The collision query must be expanded to include all solid environmental hitboxes, triggering entity garbage-collection upon environmental impact.

##### Tasks

**1. Task: Implement Layer Traversal (`DoorMechanics`)**

*Objective*: Allow entities to traverse independent Layer coordinate planes when intersecting Door hitboxes.

* [ ] **Subtask**: Assign `mass: -1` to Door properties.
* [ ] **Subtask**: Create `DoorMechanics(SpatialMechanic)`. Query intersections between `PLAYERS`/`SPRITES` and `DOORS`.
* [ ] **Subtask**: Check if the mutating entity's center point intersects the Door. If true, execute `board.relayer(asset, door.state.outlayer)`.
* [ ] **Subtask**: Update the entity's `position` to match `door.state.out`.

**2. Task: Implement Instantiation (`SpawnMechanics`)**

*Objective*: Bridge the gap between a Sprite's Animation Action and the spawning of dynamic entities (Projectiles, Effects) onto the Board.

* [ ] **Subtask**: Introduce a `Factory` or `Spawner` reference into `Board` to allow mid-loop instantiation.
* [ ] **Subtask**: Create `SpawnMechanics`. Iterate over `SHEETS`. Filter for specific `(Action, Frame)` tuples (e.g., frame 4 of the `shoot` action).
* [ ] **Subtask**: Instantiate the corresponding `Projectile` or `Effect` Asset. Inject `Asset.state.initial` and `Asset.state.velocity` based on the Sprite's `position` and `direction`. Append to `Board`.

**3. Task: Implement World Interaction (`InteractionMechanics`)**

*Objective*: Translate Sprite Intentions into physical state changes for in-game Objects.

* [ ] **Subtask**: Create `InteractionMechanics(SpatialMechanic)`. Query overlaps between `SHEETS` (where `intention == INTERACT`) and `CHESTS` (or other interactables).
* [ ] **Subtask**: For `PLAYERS`: Pause the board, append a `MenuEvent(trade)` to the `Board.bus` (Ensure Event Bus is implemented in Engine loop).
* [ ] **Subtask**: For `SPRITES`: Calculate inventory transfer logic autonomously. Toggle `chest.state.switch`.

**4. Task: Update `CombatMechanics` (Spatial Regression)**

*Objective*: Eradicate the $O(N^2)$ nested loop in favor of the Cython spatial hash grid.

* [ ] **Subtask**: Refactor `CombatMechanics` to inherit `SpatialMechanic`.
* [ ] **Subtask**: Extract `attackers` (Sprites/Players where `intention == ATTACK`). Query `self.query_collisions(attackers + targets)`.
* [ ] **Subtask**: Map active weapon hitboxes dynamically during the collision check. Decrement `target.state.meters.health` and trigger `mutators.triggers.struck` for valid overlaps.

**5. Task: Update `MotionMechanics` & `CollisionMechanics` (Newtonian Integration)**

*Objective*: Apply mass-based physics, momentum conservation, and true AABB sliding.

* [ ] **Subtask**: Add `mass: int` property to `AssetProperties`. Define $m > 0$ (Dynamic), $m = 0$ (Static), $m = -1$ (Sensor).
* [ ] **Subtask**: Implement `Board.weights(layer)` to return a cached list of Assets where `mass >= 0`.
* [ ] **Subtask**: Modify `MotionMechanics` to apply `acceleration` to `velocity`, and `velocity * delta_time` to `position`. Implement a linear damping factor to simulate surface friction.
* [ ] **Subtask**: Modify `CollisionMechanics` to exclusively query `Board.weights(layer)`. Calculate overlap resolution and update post-collision velocities using inelastic momentum conservation formulae.

### 6. Task: Update `ProjectileMechanics` (Environmental Collisions)

*Objective*: Detect impacts against solid environmental barriers and board boundaries, triggering entity garbage-collection.

* [ ] **Subtask**: Append solid objects (Assets where `mass == 0`) and the calculated boundaries of the `Board` to the spatial query in `ProjectileMechanics`.
* [ ] **Subtask**: On impact, instantiate a `TemporaryEffect` (e.g., dust puff) at the impact coordinate, and flag the `Projectile` for removal by `RemoveMechanics`.