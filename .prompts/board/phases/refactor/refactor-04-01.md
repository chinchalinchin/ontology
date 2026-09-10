#### Refactor: Phase 04.01 - Mechanics

##### Tasks

**0. Task: Mechanics Prepartion**

*Objective*: Abstract Mechanics instantiation using configuration.

* [x] **Subtack**: Add MechanicsConfiguration to `app.models.config`. Update corresonding DTO Pydantic validators. 
* [x] **Subtack**: Enumerate Mechanics in `app.config.enums`.
* [x] **Subtack**: Use configuration in Orchestrator to hydrate the Mechanics and inject into Board in order they are specified.

**1. Task: Implement Door Traversal & Sprite Chest Interaction**

*Objective*: Allow entities to traverse independent Layer coordinate planes when intersecting Door hitboxes.

* [x] **Subtask**: Assign `mass: -1` (Sensor) to Door properties schema.
* [x] **Subtask**: Implement Door mechanics in `InteractionMechanics`. Query intersections between Sprites and Doors conditional on `sprite.state.intention == 'interact'`.
* [x] **Subtask**: Check if the mutating Sprite's center point intersects the Door. If true, execute `board.relayer(asset, door.state.outlayer)`.
* [x] **Subtask**: Update the Sprite's `position` to match `door.state.out`.
* [x] **Subtask**: Implement Sprite interaction mechanics in `InteractionMechanics`. Query intersections between Sprites and Chests conditional on `sprite.state.intention == 'interact'`.
* [x] **Subtask**: Check if the mutating Sprite's center point intersects the Chest. If true, remove `chest.state.contents` and append to `sprite.state.inventory.loot`.

---

**2. Task: Implement Player Interaction**

*Objective*: Separate autonomous in-game object interactions from Player-driven UI Menu events.

* [x] **Subtask**: Introduce UI-specific Intentions to the configuration schemas.
* [x] **Subtask**: Create conditional-stub for instantiating MenuEvents in the `InteractionMechanics`

---

**3. Task: Implement the Runtime Factory (Cradle)**

*Objective*: Centralize runtime Asset hydration to support dynamic spawning triggered by Mechanics.

* [x] **Subtask**: Create a Cradle class initialized with references to `RecipeConfiguration` and `Spawnable`. Attach Cradle to Board.
* [x] **Subtask**: Create a Group model for Spawnable Assets (projectiles, temporary effects, struts). Ensure this Group is hydrated with spawnable Asset properties in the Factory and passed into the Cradle by the Orchestrator.
* [x] **Subtask**: Expose `spawn_projectile(id, position, direction, speed)`, `spawn_temporary(id, position)`, and `spawn_strut(id, position, owner)` methods on the Cradle that assemble the components and append them for the Board.

---

**4. Task: Update `CombatMechanics` (Spatial Regression & Cradle Spawning)**

*Objective*: Eradicate the $O(N^2)$ nested loop and utilize the `Cradle` for ranged combat.

* [x] **Subtask**: Refactor `CombatMechanics` to inherit `SpatialMechanic`. 
* [x] **Subtask**: Remove the nested for target in targets: loop in `CombatMechanics.update()`.
* [x] **Subtask**: Feed attackers and targets into `self.query_collisions(attackers + targets)`. Iterate over the returned candidate pairs to apply `Geometry.intersects` with the attacker's active weapon hitboxes.
* [x] **Subtask**: Implement ranged attack logic: If the attacker's animation matches the critical `shoot` or `cast` frame, call `board.cradle.spawn_projectile()` with the initial vector after the Equipment animation check.

---

**5. Task: Update Data Structures for Newtonian Physics**

*Objective*: Support continuous integration without integer truncation failure. Introduce Vectors and Steering properties to the schemas.

* [x] **Subtask**: Update `libs.core.models.Position` to track `cdef public double rx, ry` for sub-pixel accumulation.
* [x] **Subtask**: Create `Velocity(vx: double, vy: double)` in `libs.core.models.pxd`.
* [x] **Subtask**: Add `velocity: Velocity` to `SpriteState`, `MotorState`, and `PositionalState` schemas.
* [x] **Subtask**: Add `impulse: int` to `Character` properties (the rate of acceleration for self-propelled Sprites).
* [x] **Subtask**: Add `friction: float` to `TileProperties`.
* [x] **Subtask**: Implement `Board.tile(layer, position) -> Asset` using grid-index math ($O(1)$) to return the Tile at a specific coordinate.
* [x] **Subtask**: Add `mass: int` property to collidable Asset Properties ($m > 0$ for Dynamic, $m = 0$ for Static, $m = -1$ for Sensor).
* [x] **Subtask**: Create `Velocity(vx: double, vy: double)` in `libs.core.models.pxd`.
* [x] **Subtask**: Add `velocity: Velocity` to `SpriteState`, `MotorState`, and `PositionalState` schemas.
* [x] **Subtask**: Add `impulse: int` to `Character` properties.
* [x] **Subtask**: **Tile Refactor - Schema**: Update `/src/assets/tiles/main.yaml` to nest IDs under instances, mapping each to `dimensions` and `friction`.
* [x] **Subtask**: **Tile Refactor - Models**: Update `app.models.properties.TileProperties`. Remove `ids: List[str]`, add `friction: float`.
* [x] **Subtask**: **Tile Refactor - Orchestrator**: Remove the `if category == AssetCategories.TILES:` bypass in `Orchestrator.instance_properties()`.
* [x] **Subtask**: **Tile Refactor - Registry**: Remove the `elif "ids" in inst_props:` block in `Registry._extract()`.
* [x] **Subtask**: **Tile Refactor - Cache**: Implement a spatial `TileMap` dictionary in `Board._cache()`. Expose `Board.tile(layer, position) -> Asset` for $O(1)$ friction lookups.
* [x] **Subtask**: Implement `Board.weights(layer)` to return a cached list of Assets where `mass >= 0`.

---

**6. Task: Overhaul `MotionMechanics` (Symplectic Euler Integration)**

*Objective*: Apply impulses to modify velocity, then use the resulting velocity to translate position.

* [x] **Subtask**: **Velocity Update (Player):** Check `device.poll()`. If directional input is present, calculate impulse vector, apply to `velocity`, and clamp magnitude to `character.speed`. If no input is present, hardcode `velocity = (0,0)`.
* [x] **Subtask**: **Velocity Update (Sprites):** Calculate the unit vector pointing from `current_position` to `goal_position`. Multiply by `impulse` and $\Delta t$. Add to `velocity`. Clamp magnitude to `character.speed`.
* [x] **Subtask**: **Velocity Update (Frictive):** Query `Board.tile()` at asset's center. Calculate $\Delta v = \text{friction} \cdot \Delta t$. Apply $\Delta v$ in the direction opposite to the current `velocity`. If $\Delta v > \vert{}\text{velocity}\vert{}$, set `velocity = (0,0)`.
* [x] **Subtask**: **Position Update (All Mutable Assets):** Exclude Projectiles from the above steps. For all assets, apply $v \cdot \Delta t$ to the sub-pixel accumulators `rx/ry`. When `rx/ry` exceed $1.0$ 

---

**7. Task: Overhaul `CollisionMechanics` (Mass Resolution & Momentum)**

*Objective*: Isolate overlap resolution from physical momentum transfer.

* [x] **Subtask**: Query `Board.weights(layer)` to evaluate overlaps.
* [x] **Subtask**: **Spatial Resolution:** Calculate the inverse mass for both colliding assets ($1/m$). Treat $m=0$ as an inverse mass of $0$. Distribute the `overlap_x` and `overlap_y` displacement proportionally to their inverse mass ratio, immediately shifting the `Position` coordinates.
* [x] **Subtask**: **Momentum Transfer:** Following separation, calculate the new 1D elastic velocities for the `x` and `y` axes independently using the formula: 
$$v_{1f} = \frac{v_1(m_1 - m_2) + 2m_2v_2}{m_1 + m_2}$$
* [x] Update the `velocity` vectors for both bodies.

---

**!. Task: Implement Board Boundaries & Environmental Collisions**

*Objective*: Calculate rigid board boundaries dynamically and allow projectiles to impact solid matter.

* [!] **Subtask**: In `Board.__init__`, implement the Orthogonal Boundary Algorithm: scan the Tile coordinate set and instantiate $m=0$ Hitboxes on any adjacent empty grid space.

---


