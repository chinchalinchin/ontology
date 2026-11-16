
#### Refactor: Phase 03.04 - Projectiles

**Overview**

Codify `Projectiles` (`cursors.projectiles`) using the Registry Load-Time Rotation strategy (`ProjectileFrame`, `RotatedHitbox`, and `render.rotate`), allowing a single canonical projectile texture frame to be quantized into arbitrary angular increments ($\Delta\theta \in (0, 360]$) in VRAM without modifying the 60 Hz `Screen._assemble()` / `render.render()` pipeline. Wire ranged combat spawning in `CombatMechanics` and trajectory/impact resolution in `ProjectileMechanics`.

##### Specification

1. **Angular Partitioning (`CursorProperties`)**:
* Extend `CursorProperties` (`src/app/models/properties/assets.py`) with `delta: int = 90` (degrees per discrete rotational step, where $360 \bmod \text{delta} == 0$) and `speed: int = 200`.
* The discrete set of valid projectile angles is $\Theta = \{ k \cdot \text{delta} \mid 0 \le k < 360 // \text{delta} \}$.


2. **Load-Time Texture Strip Synthesis (`ProjectileFrame` & `Registry`)**:
* Authored projectile `.png` files contain a single canonical frame of square dimensions $(S, S)$ oriented at $\theta = 0^\circ$ (or canonical `left`).
* `ProjectileFrame.index(id, properties)` maps each discrete angle key `f"{id}-{angle}"` ($\text{angle} = k \cdot \text{delta}$) to crop coordinate $(k \cdot S, 0, S, S)$.
* `Registry._get_or_load_texture()` detects `delta` on projectile properties and invokes `render.rotate(raw_tex, delta)`, which allocates a target `TexturePtr` of dimensions $(N \cdot S, S)$ where $N = 360 // \text{delta}$ and stamps the base texture $N$ times via `SDL_RenderCopyEx`.
* `ProjectileFrame.keys(id, state)` projects `state.angle` directly to `[(f"{id}-{state.angle}", 0, 0)]`.


3. **Rotated AABB Hitbox Projection (`RotatedHitbox`)**:
* `RotatedHitbox.get(properties, state, elevation)` rotates each base `Hitbox` in `properties.hitboxes` by $\Delta\theta = \text{state.angle}$ around the frame center $(S/2, S/2)$:



$$\begin{pmatrix} h'_{cx} \\ h'_{cy} \end{pmatrix} = \begin{pmatrix} \cos\Delta\theta & -\sin\Delta\theta \\ \sin\Delta\theta & \cos\Delta\theta \end{pmatrix} \begin{pmatrix} h_{cx} \\ h_{cy} \end{pmatrix}$$

$$w'(\Delta\theta) = \max\Big(1,\; \text{round}\big(w_0 |\cos\Delta\theta| + l_0 |\sin\Delta\theta|\big)\Big), \qquad l'(\Delta\theta) = \max\Big(1,\; \text{round}\big(w_0 |\sin\Delta\theta| + l_0 |\cos\Delta\theta|\big)\Big)$$

##### Goals

###### Goal: Implement `render.rotate` in Cython SDL2 Bindings

Expose `SDL_RenderCopyEx` in `src/libs/graphics/render.pyx` and implement `rotate(TexturePtr base_ptr, int delta) -> TexturePtr` to pre-bake rotated projectile frames into a single horizontal `TexturePtr` strip during Registry texture loading.

###### Goal: Implement `ProjectileFrame` and `RotatedHitbox`

Create `ProjectileFrame` (`src/app/assets/frames/cursors.py`) and `RotatedHitbox` (`src/app/assets/hitboxes/cursors.py`) and register them under `recipes.cursors.projectiles` in `src/data/config/recipes/main.yaml`.

###### Goal: Wire Ranged Spawning in `Cradle` and Impact Resolution in `ProjectileMechanics`

Update `Cradle.spawn_projectile()` to quantize launch angles to `properties.delta`, compute initial `Velocity(vx, vy)`, and instantiate the projectile `Asset` at the attacker's `elevation`. Update `ProjectileMechanics` to integrate trajectories, enforce elevation-isolated impact detection, apply damage, and garbage-collect expired projectiles.

##### Tasks

**1. Task: Add Cython `render.rotate` and Registry Load-Time Rotation**

*Objective*: Synthesize rotated texture strips in VRAM during `Registry` texture loading.

* [] Subtask: Declare `SDL_Point`, `SDL_RendererFlip`, and `SDL_RenderCopyEx` in `src/libs/graphics/render.pyx` and implement `rotate(TexturePtr base_ptr, int delta) -> TexturePtr`.
* [] Subtask: Update `CursorProperties` in `src/app/models/properties/assets.py` to include `delta: Optional[int] = None` and `speed: int = 200`, and update `MotorState` (`src/app/models/state/assets/cursors.py`) to include `angle: int = 0`.
* [] Subtask: Update `Registry._get_or_load_texture()` in `src/libs/graphics/registry.pyx` to invoke `render.rotate()` when loading a projectile texture with a configured `delta`.

**2. Task: Implement `ProjectileFrame` and `RotatedHitbox**`

*Objective*: Index rotated projectile frame crops and transform base AABB hitboxes by `state.angle`.

* [] Subtask: Implement `ProjectileFrame` in `src/app/assets/frames/cursors.py` to index `f"{id}-{k * delta}"` crops and resolve `[(f"{id}-{state.angle}", 0, 0)]` in `keys()`.
* [] Subtask: Implement `RotatedHitbox` in `src/app/assets/hitboxes/cursors.py` to project base `properties.hitboxes` around the frame center by `state.angle` at the projectile's `elevation`.
* [] Subtask: Register `ProjectileFrame` and `RotatedHitbox` under `cursors.projectiles` in `src/data/config/recipes/main.yaml`.

**3. Task: Implement `Cradle.spawn_projectile`, `CombatMechanics` Ranged Trigger, and `ProjectileMechanics**`

*Objective*: Complete the end-to-end lifecycle of ranged projectiles from release frame to target impact or boundary removal.

* [] Subtask: Update `Cradle.spawn_projectile()` to quantize direction/target vectors onto the nearest multiple of `properties.delta` and populate `MotorState`.
* [] Subtask: Wire ranged projectile spawning in `CombatMechanics.update()` on the release frame of `Actions.SHOOT`.
* [] Subtask: Update `ProjectileMechanics.update()` to evaluate elevation-partitioned intersections against targets and obstacles and queue impacted or out-of-bounds projectiles for removal.
