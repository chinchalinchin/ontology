#### Refactor: Phase 04.01 - Mechanics

- **CURRENT FOCUS (Tile Refactoring)**: If friction is added to Tiles, then Tiles need to be separated by `id` in the property schema, where each has a unique taxonomy, e.g. `<category>.<instance>.<id>`. Analyze the impacts this will have on the application Registry, Orchestrator, Factory and other core components. Document anything that needs changed in Tasks.

##### Tasks

**0. Task: Mechanics Prepartion**

*Objective*: Abstract Mechanics instantiation using configuration.

* [ ] **Subtack**: Add MechanicsConfiguration to `app.models.config`. Update corresonding DTO Pydantic validators. 
* [ ] **Subtack**: Enumerate Mechanics in `app.config.enums`.
* [ ] **Subtack**: Use configuration in Orchestrator to hydrate the Mechanics.

**1. Task: Implement Door Traversal & Sprite Chest Interaction**

*Objective*: Allow entities to traverse independent Layer coordinate planes when intersecting Door hitboxes.

* [x] **Subtask**: Assign `mass: -1` (Sensor) to Door properties schema.
* [ ] **Subtask**: Implement Door mechanics in `InteractionMechanics`. Query intersections between Sprites and Doors conditional on `sprite.state.intention == 'interact'`.
* [ ] **Subtask**: Check if the mutating Sprite's center point intersects the Door. If true, execute `board.relayer(asset, door.state.outlayer)`.
* [ ] **Subtask**: Update the Sprite's `position` to match `door.state.out`.
* [ ] **Subtask**: Implement Sprite interaction mechanics in `InteractionMechanics`. Query intersections between Sprites and Chests conditional on `sprite.state.intention == 'interact'`.
* [ ] **Subtask**: Check if the mutating Sprite's center point intersects the Chest. If true, remove `chest.state.contents` and append to `sprite.state.inventory.loot`.

---

**2. Task: Implement Player Interaction**

*Objective*: Separate autonomous in-game object interactions from Player-driven UI Menu events.

* [x] **Subtask**: Introduce UI-specific Intentions to the configuration schemas.
* [ ] **Subtask**: Create conditional-stub for instantiating MenuEvents in the `InteractionMechanics`

---

**3. Task: Implement the Runtime Factory (`Cradle`)**

*Objective*: Centralize runtime Asset hydration to support dynamic spawning triggered by Mechanics.

* [~] **Subtask**: Create a `Cradle` class initialized with references to `RecipeConfiguration` and `Spawnable. Attach `Cradle` to `Board`.
* [~] **Subtask**: Create a Group model for Spawnable Assets (projectiles, temporary effects, struts). Ensure this Group is hydrated with spawnable Asset properties in the Factory and passed into the Cradle by the Orchestrator.
* [~] **Subtask**: Expose `spawn_projectile(id, position, direction, speed)`, `spawn_temporary(id, position)`, and `spawn_strut(id, position, owner)` methods on the `Cradle` that assemble the components and append them to the `Board` asset lists.

---

**4. Task: Update `CombatMechanics` (Spatial Regression & Cradle Spawning)**

*Objective*: Eradicate the $O(N^2)$ nested loop and utilize the `Cradle` for ranged combat.

* [x] **Subtask**: Refactor `CombatMechanics` to inherit `SpatialMechanic`. 
* [ ] **Subtask**: Remove the nested for target in targets: loop in `CombatMechanics.update()`.
* [ ] **Subtask**: Feed attackers and targets into `self.query_collisions(attackers + targets)`. Iterate over the returned candidate pairs to apply `Geometry.intersects` with the attacker's active weapon hitboxes.
* [ ] **Subtask**: Implement ranged attack logic: If the attacker's animation matches the critical `shoot` or `cast` frame, call `board.cradle.spawn_projectile()` with the initial vector after the Equipment animation check.

---

**5. Task: Update Data Structures for Newtonian Physics**

*Objective*: Support continuous integration without integer truncation failure. Introduce Vectors and Steering properties to the schemas.

* [ ] **Subtask**: Update `libs.core.models.Position` to track `cdef public double rx, ry` for sub-pixel accumulation.
* [ ] **Subtask**: Create `Velocity(vx: double, vy: double)` in `libs.core.models.pxd`.
* [ ] **Subtask**: Add `velocity: Velocity` to `SpriteState`, `MotorState`, and `PositionalState` schemas.
* [ ] **Subtask**: Add `impulse: int` to `Character` properties (the rate of acceleration for self-propelled Sprites).
* [ ] **Subtask**: Add `friction: float` to `TileProperties`.
    * [ ] Refactor Tile property parsing. Currently all Tile `ids` are listed under a field, instead of the `<category>.<instance>.<id>` nesting data structure applied to the other assets. Separating Tiles by friction will require modifying the Tile Property schema to fit the normal Asset data shape.
    * [ ] Update documentation and asset schemas.
* [ ] **Subtask**: Implement `Board.tile(layer, position) -> Asset` using grid-index math ($O(1)$) to return the Tile at a specific coordinate.
* [x] **Subtask**: Add `mass: int` property to collidable Asset Properties ($m > 0$ for Dynamic, $m = 0$ for Static, $m = -1$ for Sensor).
* [~] **Subtask**: Implement `Board.weights(layer)` to return a cached list of Assets where `mass >= 0`.

---

**6. Task: Overhaul `MotionMechanics` (Time, Velocity & Friction)**

*Objective*: Apply velocity, friction, and sub-pixel accumulation.

* [ ] **Subtask**: Remove kinematic integer snapping. Map Intention and Goal directly to a target velocity vector.
* [ ] **Subtask**: **Sprites & Players:** Calculate the desired direction based on Intention/Goal. Apply `impulse` to `velocity` in that direction. Cap the magnitude of `velocity` at `character.speed`.
* [ ] **Subtask**: **Crates & Inert Objects:** Query `Board.tile()` using the asset's center point. Multiply `velocity` by $(1 - \text{friction} \cdot \text{delta})$.
* [ ] **Subtask**: **Integration:** Apply `velocity * delta` to `rx/ry`. When the accumulators exceed $1.0$ or $-1.0$, cast to `int`, shift the physical `Position`, and decrement the accumulator.

---

**7. Task: Overhaul `CollisionMechanics` (Inverse Mass Resolution)**

*Objective*: Stop static environments from being displaced by dynamic bodies.

* [ ] **Subtask**: Modify `CollisionMechanics` to query `Board.weights(layer)` and resolve spatial overlap using inelastic momentum transfer formulae.
* [ ] **Subtask**: Update `CollisionMechanics._resolve()` to calculate the inverse mass of both objects. If $m=0$, $m_{inv} = 0$.
* [ ] **Subtask**: **Positional Correction:** Modify `_resolve()` to calculate the inverse mass of both objects ($1/m$, where $m=0 \to 0$). Distribute the `overlap_x` and `overlap_y` shifts proportionally to their inverse mass ratio, ensuring static walls do not move.
* [ ] **Subtask**: **Elastic Velocity:** Apply 1D elastic collision formulae to the `Velocity` vectors post-separation: $v_{1f} = \frac{v_1(m_1 - m_2) + 2m_2v_2}{m_1 + m_2}$. (Treat $m=0$ as infinite mass mathematically so objects bounce cleanly off walls).

---

**x. Task: Implement Board Boundaries & Environmental Collisions**

*Objective*: Calculate rigid board boundaries dynamically and allow projectiles to impact solid matter.

* [!] **Subtask**: In `Board.__init__`, implement the Orthogonal Boundary Algorithm: scan the Tile coordinate set and instantiate $m=0$ Hitboxes on any adjacent empty grid space.

---
