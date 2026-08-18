#### Refactor: Phase 04.01 - Mechanics

- **CURRENT FOCUS**: Newtownian mechanics and inelastic collisions. Layout step-by-step what needs implemented and in which layer (Cython vs. Python) to create a collision system that obeys the laws of inelastic collisions (e.g. conservation of momentum and surface friction). Consider where the coefficient of friction should live. Tile Properties? Would require a refactor of data structures, but would allow customization of Tile interactions. It also requires Assets with weight have velocity. Determine what exactly needs added and where for momentum-based collisions.

##### Tasks

**1. Task: Implement Door Traversal & Sprite Chest Interaction**

*Objective*: Allow entities to traverse independent Layer coordinate planes when intersecting Door hitboxes.

* [ ] **Subtask**: Assign `mass: -1` (Sensor) to Door properties schema.
* [ ] **Subtask**: Implement Door mechanics in `InteractionMechanics`. Query intersections between Sprites and Doors conditional on `sprite.state.intention == 'interact'`.
* [ ] **Subtask**: Check if the mutating Sprite's center point intersects the Door. If true, execute `board.relayer(asset, door.state.outlayer)`.
* [ ] **Subtask**: Update the Sprite's `position` to match `door.state.out`.
* [ ] **Subtask**: Implement Sprite interaction mechanics in `InteractionMechanics`. Query intersections between Sprites and Chests conditional on `sprite.state.intention == 'interact'`.
* [ ] **Subtask**: Check if the mutating Sprite's center point intersects the Chest. If true, remove `chest.state.contents` and append to `sprite.state.inventory.loot`.

**2. Task: Implement Player Interaction**

*Objective*: Separate autonomous in-game object interactions from Player-driven UI Menu events.

* [x] **Subtask**: Introduce UI-specific Intentions to the configuration schemas.
* [ ] **Subtask**: Create conditional-stub for instantiating MenuEvents in the `InteractionMechanics`

**3. Task: Implement the Runtime Factory (`Cradle`)**

*Objective*: Centralize runtime Asset hydration to support dynamic spawning triggered by Mechanics.

* [~] **Subtask**: Create a `Cradle` class initialized with references to `RecipeConfiguration` and `Spawnable. Attach `Cradle` to `Board`.
* [~] **Subtask**: Create a Group model for Spawnable Assets (projectiles, temporary effects, struts). Ensure this Group is hydrated with spawnable Asset properties in the Factory and passed into the Cradle by the Orchestrator.
* [~] **Subtask**: Expose `spawn_projectile(id, position, direction, speed)`, `spawn_temporary(id, position)`, and `spawn_strut(id, position, owner)` methods on the `Cradle` that assemble the components and append them to the `Board` asset lists.

**4. Task: Update `CombatMechanics` (Spatial Regression & Cradle Spawning)**

*Objective*: Eradicate the $O(N^2)$ nested loop and utilize the `Cradle` for ranged combat.

* [ ] **Subtask**: Refactor `CombatMechanics` to inherit `SpatialMechanic`. 
* [ ] **Subtask**: Remove the nested for target in targets: loop in CombatMechanics.update().
* [ ] **Subtask**: Feed attackers and targets into self.query_collisions(attackers + targets). Iterate over the returned candidate pairs to apply Geometry.intersects with the attacker's active weapon hitboxes.
* [ ] **Subtask**: Implement ranged attack logic: If the attacker's animation matches the critical shoot or cast frame, call board.cradle.spawn_projectile() with the initial vector.
* [ ] **Subtask**: Implement ranged attack logic: If the attacker's animation matches the critical `shoot` or `cast` frame, call `board.cradle.spawn_projectile()` with the initial vector after the Equipment animation check.

**5. Task: Update `MotionMechanics` & `CollisionMechanics` (Newtonian Integration)**

*Objective*: Apply mass-based physics, momentum conservation, and true AABB sliding.

* [ ] **Subtask**: Add `mass: int` property to `AssetProperties` ($m > 0$ for Dynamic, $m = 0$ for Static, $m = -1$ for Sensor).
* [ ] **Subtask**: Implement `Board.weights(layer)` to return a cached list of Assets where `mass >= 0`.
* [ ] **Subtask**: Modify `MotionMechanics` to integrate `velocity = speed * delta_time` and apply linear surface friction.
* [ ] **Subtask**: Modify `CollisionMechanics` to query `Board.weights(layer)` and resolve spatial overlap using inelastic momentum transfer formulae.

**6. Task: Implement Board Boundaries & Environmental Collisions**

*Objective*: Calculate rigid board boundaries dynamically and allow projectiles to impact solid matter.

* [!] **Subtask**: In `Board.__init__`, implement the Orthogonal Boundary Algorithm: scan the Tile coordinate set and instantiate $m=0$ Hitboxes on any adjacent empty grid space.
* [!] **Subtask**: Update `ProjectileMechanics` to query collisions against `Board.weights(layer)`. On impact with $m \ge 0$ objects, call `board.cradle.spawn_effect(dust)` and flag the projectile for garbage collection.