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

**1. Task: Implement Door Traversal & Sprite Chest Interaction**

*Objective*: Allow entities to traverse independent Layer coordinate planes when intersecting Door hitboxes.

* [ ] **Subtask**: Assign `mass: -1` (Sensor) to Door properties schema.
* [ ] **Subtask**: Implement Door mechanics in `InteractionMechanics`. Query intersections between Sprites and Doors conditional on `sprite.state.intention == 'interact'`.
* [ ] **Subtask**: Check if the mutating Sprite's center point intersects the Door. If true, execute `board.relayer(asset, door.state.outlayer)`.
* [ ] **Subtask**: Update the Sprite's `position` to match `door.state.out`.
* [ ] **Subtask**: Implement Sprite interaction mechanics in `InteractionMechanics`. Query intersections between Sprites and Chests conditional on `sprite.state.intention == 'interact'`.
* [ ] **Subtask**: Check if the mutating Sprite's center point intersects the Chest. If true, remove `chest.state.contents` and append to `sprite.state.inventory.loot`.

**2. Task: Implement the Runtime Factory (`Cradle`)**

*Objective*: Centralize runtime Asset hydration to support dynamic spawning triggered by Mechanics.

* [~] **Subtask**: Create a `Cradle` class initialized with references to `RecipeConfiguration`. Attach `Cradle` to `Board`.
* [~] **Subtask**: Expose `spawn_projectile(id, properties, position, direction, speed)`, `spawn_temporary(id, properties, position)`, and `spawn_strut(id, properties, position, owner)` methods on the `Cradle` that assemble the components and append them to the `Board` asset lists.

**3. Task: Implement World Interaction (`InteractionMechanics` & `MenuMechanics`)**

*Objective*: Separate autonomous in-game object interactions from Player-driven UI Menu events.

* [ ] **Subtask**: Introduce UI-specific Intentions (e.g., `MENU_INVENTORY`, `MENU_TRADE`, `MENU_PAUSE`) to the configuration schemas.
* [ ] **Subtask**: Create `InteractionMechanics(SpatialMechanic)`. For Sprites with `intention == INTERACT` overlapping Chests, autonomously exchange inventory data and toggle `chest.state.switch`.
* [ ] **Subtask**: Update `MenuMechanics` to poll strictly for the Player's UI Intentions. When triggered, append the appropriate `MenuEvent` to the `Board.bus` and halt the simulation (`board.paused = True`).

**4. Task: Update `CombatMechanics` (Spatial Regression & Cradle Spawning)**

*Objective*: Eradicate the $O(N^2)$ nested loop and utilize the `Cradle` for ranged combat.

* [ ] **Subtask**: Refactor `CombatMechanics` to inherit `SpatialMechanic`. Query overlaps for melee attackers using active weapon hitboxes.
* [ ] **Subtask**: Implement ranged attack logic: If the attacker's animation matches the critical `shoot` or `cast` frame, call `board.cradle.spawn_projectile()` with the initial vector.

**5. Task: Update `MotionMechanics` & `CollisionMechanics` (Newtonian Integration)**

*Objective*: Apply mass-based physics, momentum conservation, and true AABB sliding.

* [ ] **Subtask**: Add `mass: int` property to `AssetProperties` ($m > 0$ for Dynamic, $m = 0$ for Static, $m = -1$ for Sensor).
* [ ] **Subtask**: Implement `Board.weights(layer)` to return a cached list of Assets where `mass >= 0`.
* [ ] **Subtask**: Modify `MotionMechanics` to integrate `velocity = speed * delta_time` and apply linear surface friction.
* [ ] **Subtask**: Modify `CollisionMechanics` to query `Board.weights(layer)` and resolve spatial overlap using inelastic momentum transfer formulae.

**6. Task: Implement Board Boundaries & Environmental Collisions**

*Objective*: Calculate rigid board boundaries dynamically and allow projectiles to impact solid matter.

* [ ] **Subtask**: Define an `Environ` Asset property.
* [ ] **Subtask**: In `Board.__init__`, implement the Orthogonal Boundary Algorithm: scan the Tile coordinate set and instantiate $m=0$ `Environ` Hitboxes on any adjacent empty grid space.
* [ ] **Subtask**: Update `ProjectileMechanics` to query collisions against `Board.weights(layer)`. On impact with $m \ge 0$ objects, call `board.cradle.spawn_effect(dust)` and flag the projectile for garbage collection.