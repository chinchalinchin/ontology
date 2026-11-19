#### Refactor: Phase 03.04 - Projectiles

**Overview**

Codify `Projectiles` (`cursors.projectiles`) using the Registry Load-Time Rotation strategy (`ProjectileFrame`, `RotatedHitbox`, and `render.rotate`), allowing a single canonical projectile texture frame to be quantized into arbitrary angular increments ($\Delta\theta \in (0, 360]$) in VRAM without modifying the 60 Hz `Screen._assemble()` / `render.render()` pipeline. Configure equipment-level projectile bindings and release frames on `SheetProperties`, resolve ranged release triggers and charged launch speed through `CombatMap`, track button hold duration in `Device` and `PlayerMechanics`, and resolve impacts in `ProjectileMechanics`.

##### Specification

1. **Angular Partitioning (`CursorProperties` & `MotorState`)**:
    * Extend `CursorProperties` (`src/app/models/properties/assets.py`) with `rotation: int = 90` (degrees per discrete rotational step, where $360 \bmod \text{rotation} == 0$). Because `rotation` defines the static frame-space partitioning of the image file, it belongs on `CursorProperties`.
    * The discrete set of valid projectile angles is $\Theta = \{ k \cdot \text{rotation} \mid 0 \le k < 360 // \text{rotation} \}$.
    * Extend `MotorState` (`src/app/models/state/assets/cursors.py`) with `angle: int = 0` ($\text{angle} \in \Theta$), `speed: int = 200`, and `owner: Optional[str] = None`. Because launch speed, angle, and shooter identity vary per deployed projectile instance, they reside on `MotorState`.
2. **Load-Time Texture Strip Synthesis (`ProjectileFrame` & `Registry`)**:
    * Authored projectile `.png` files contain a single canonical frame of dimensions $(W, L)$ oriented at $\theta = 0^\circ$ ($+x$, `Directions.RIGHT`).
    * `ProjectileFrame.index(id, properties)` maps each discrete angle key `f"{id}-{angle}"` ($\text{angle} = k \cdot \text{properties.rotation}$) to crop coordinate $(k \cdot W, 0, W, L)$ for $0 \le k < 360 // \text{properties.rotation}$.
    * `Registry._get_or_load_texture()` checks whether `asset_key in self.properties.cursors.projectiles` and invokes `render.rotate(raw_tex, self.properties.cursors.projectiles[asset_key].rotation)`, which allocates a target `TexturePtr` of dimensions $(N \cdot W, L)$ where $N = 360 // \text{rotation}$ and stamps the base texture $N$ times clockwise via `SDL_RenderCopyEx`.
    * `ProjectileFrame.keys(id, state)` projects `state.angle` directly to `[(f"{id}-{state.angle}", 0, 0)]`.
3. **Rotated AABB Hitbox Projection (`RotatedHitbox`)**:
    * Given frame dimensions $(W, L)$ with center $(c_x, c_y) = (W / 2, L / 2)$, `RotatedHitbox.get(properties, state, elevation)` rotates each base `Hitbox` $(x_0, y_0, w_0, l_0)$ in `properties.hitboxes` (falling back to the full frame bounds $(0, 0, W, L)$ when `properties.hitboxes` is `None`) by $\Delta\theta = \text{state.angle}$ clockwise around $(c_x, c_y)$:

    $$
    h_{cx} = \left(x_0 + \frac{w_0}{2}\right) - c_x, \qquad h_{cy} = \left(y_0 + \frac{l_0}{2}\right) - c_y
    $$

    $$
    \begin{pmatrix} h'_{cx} \\ h'_{cy} \end{pmatrix} = \begin{pmatrix} \cos\Delta\theta & -\sin\Delta\theta \\ \sin\Delta\theta & \cos\Delta\theta \end{pmatrix} \begin{pmatrix} h_{cx} \\ h_{cy} \end{pmatrix}
    $$

    $$
    w'(\Delta\theta) = \max\Big(1,\; \operatorname{round}\big(w_0 |\cos\Delta\theta| + l_0 |\sin\Delta\theta|\big)\Big), \qquad l'(\Delta\theta) = \max\Big(1,\; \operatorname{round}\big(w_0 |\sin\Delta\theta| + l_0 |\cos\Delta\theta|\big)\Big)
    $$

    $$
    x'(\Delta\theta) = \operatorname{round}\left(c_x + h'_{cx} - \frac{w'(\Delta\theta)}{2}\right), \qquad y'(\Delta\theta) = \operatorname{round}\left(c_y + h'_{cy} - \frac{l'(\Delta\theta)}{2}\right)
    $$

4. **Button Hold Counter (`Keyboard` & `WorldPayload`) and Charge State (`MutatorParameters`)**:
    * `Keyboard` (`src/app/game/devices.py`) accumulates consecutive press ticks per scancode in `self._last_state`:

    $$
    c_t(\text{code}) = \begin{cases} c_{t-1}(\text{code}) + 1 & \text{if } \text{pressed}(\text{code}) = 1 \\ 0 & \text{if } \text{pressed}(\text{code}) = 0 \end{cases}
    $$

    * `WorldPayload` (`src/app/models/state/devices.py`) is extended with `hold: int = 0`, populated with $c_t(v)$ for the active held intention scancode $v$ while preserving rising-edge singularity (`c_t(v) == 1`) on `WorldPayload.intention`.
    * `MutatorParameters` (`src/app/models/state/core.py`) is extended with `charge: int = 0` to store the accumulated `attack` hold duration on `SheetState` / `SpriteState`.
5. **Weapon-to-Projectile Relation (`app.game.logic.relations`) & `CombatMap` Fork**:
    * Partition combat actions in `src/app/static/semantics.py` into `MeleeActions` (`slash`, `thrust`) and `ProjectileActions` (`shoot`, `cast`).
    * Codify the mapping between ranged Weapons (`sheets.weapons`) and Projectiles (`cursors.projectiles`) in configuration and compile it into a `Relation` index (`ProjectileIndex` / `CombatIndex` in `src/app/game/logic/relations/`) during `Builder.build_relations()`, injecting it into `CombatMechanics` via `src/data/config/mechanics/main.yaml`.
    * Ranged weapons in `src/assets/sheets/equipments/weapons/main.yaml` configure their release frame and directional spawn offset using standard `<action>-<direction>-<frame>` `hitboxes` resolved by `AttackHitbox`.
    * `CombatMechanics.update()` resolves `action = CombatMap.action(attacker.state, board.equipment)` and forks on action group:
        * `action in MeleeActions`: executes `self._melee(attacker, board)` using `CombatMap.attackboxes(attacker.state, board.equipment, attacker.elevation)`.
        * `action in ProjectileActions`: executes `self._project(attacker, board)` using `CombatMap.release(attacker.state, board.equipment, attacker.elevation)` to pull the active `AttackHitbox` as the spawn origin/direction on the release frame and `CombatMap.projectile(attacker.state, board.equipment, self.relation)` to resolve the projectile ID and charged speed $s(S, n)$:

    $$
    N_{\max} = \max(1,\; \text{state.animation.frame} \cdot \text{delay}), \qquad \tau(n) = \min\left(1.0,\; \frac{n}{N_{\max}}\right), \qquad s(S, n) = \operatorname{round}\Big(\alpha S \big(1 + \tau(n)\big)\Big)
    $$


##### Architectural Analysis I

1. **Ontology of Properties vs. State (`rotation` vs. `speed` and `angle`)**:
    * In the Asset Hierarchy, `Properties` encode static, immutable characteristics intrinsic to the Asset file and its atlas partitioning, whereas `State` exemplifies dynamic attributes particular to an Asset's deployment on the `Board`.
    * `rotation: int = 90` on `CursorProperties` defines the angular resolution $\Delta\theta$ of the synthesized texture strip in `Registry` and `ProjectileFrame.index()`. Because every projectile has a deterministic angular step (defaulting to $90^\circ$ for cardinal projectiles such as `arrow` and `bolt`, or $45^\circ$ for `cannonball`), `rotation` is a concrete `int = 90` field rather than `Optional[int] = None`.
    * Conversely, `speed: int = 200` and `angle: int = 0` are situational parameters of a specific launch event and belong on `MotorState` alongside `position`, `initial`, `velocity`, and `owner`.

2. **Eliminating Duck-Typing in `Registry` via Asset Hierarchy Lookup**:
    * `Registry` holds the validated `PropertySchema` hierarchy on `self.properties`. Rather than inspecting arbitrary property objects for the presence of an optional `rotation` attribute, `Registry._get_or_load_texture()` checks membership directly against the `(cursors, projectiles)` hierarchy node (`if self.properties.cursors and asset_key in self.properties.cursors.projectiles:`), matching the pattern established in `Registry._load_font()` (`if font_key not in self.properties.fonts:`).
    * When `asset_key in self.properties.cursors.projectiles`, `Registry` retrieves `rotation = self.properties.cursors.projectiles[asset_key].rotation`, synthesizes the rotated horizontal texture strip via `render.rotate(raw_tex, rotation)`, and destroys the intermediate unrotated `raw_tex` via `render.destroy(raw_tex)` so single-frame textures do not linger in VRAM.
    * `Registry._index()` requires no special-case logic: it already iterates the `(category, instance)` fields of `self.properties` and `self.recipes`, delegating `cursors.projectiles` crop generation to `ProjectileFrame.index(item_id, item_props)`.

```mermaid
flowchart LR
    subgraph Boot["Phase 1: Registry._index()"]
        A["properties.cursors.projectiles[id]"] --> B["ProjectileFrame.index(id, props)"]
        B --> C["_frames['{id}-{k * rotation}'] = (id, k * w, 0, w, l)"]
    end
    subgraph Hydration["Phase 2: Registry._get_or_load_texture(id)"]
        D["_load_texture(filepath)"] --> E{"id in properties.cursors.projectiles"}
        E -- Yes --> F["render.rotate(raw_tex, props.rotation)"]
        F --> G["render.destroy(raw_tex)"]
        G --> H["_textures[id] = strip_tex"]
        E -- No --> H
    end
```

3. **Screen-Space Angle Convention & Launch Quantization (`Cradle.spawn_projectile`)**:
    * In screen coordinates ($+x$ right, $+y$ down), both `SDL_RenderCopyEx` and the 2D rotation matrix $R(\Delta\theta)$ rotate clockwise:
        * $\theta = 0^\circ \leftrightarrow (+1, 0)$ (`Directions.RIGHT`)
        * $\theta = 90^\circ \leftrightarrow (0, +1)$ (`Directions.DOWN`)
        * $\theta = 180^\circ \leftrightarrow (-1, 0)$ (`Directions.LEFT`)
        * $\theta = 270^\circ \leftrightarrow (0, -1)$ (`Directions.UP`)
    * Given a continuous displacement vector $(\Delta x, \Delta y)$ toward a target coordinate (or a cardinal `Directions` unit vector when no target coordinate is present), the raw launch angle in $[0, 360)$ is:

    $$
    \theta_{\text{raw}} = \left(\operatorname{atan2}(\Delta y, \Delta x) \cdot \frac{180}{\pi}\right) \bmod 360
    $$

    * Quantizing onto the nearest discrete step $R = \text{properties.rotation}$ yields:

    $$
    \text{angle} = \left(\operatorname{round}\left(\frac{\theta_{\text{raw}}}{R}\right) \cdot R\right) \bmod 360, \qquad \vec{v} = \begin{pmatrix} \text{speed} \cdot \cos(\text{angle} \cdot \frac{\pi}{180}) \\ \text{speed} \cdot \sin(\text{angle} \cdot \frac{\pi}{180}) \end{pmatrix}
    $$

    * `Cradle.spawn_projectile()` allocates distinct `Position(position.x, position.y)` instances for `state.position` and `state.initial` so in-place sub-pixel integration in `physics.integrate()` does not mutate `state.initial` or the shooter's position.

4. **Ranged Combat Trigger & Impact Resolution (`CombatMechanics` & `ProjectileMechanics`)**:
    * **Release Frame Edge Trigger**: In `CombatMechanics.update()`, an attacker with `state.animation.action == Actions.SHOOT` spawns a projectile only on the release frame when `state.animation.tick == 1`, preventing duplicate spawns when action `delay > 1`.
    * **Motion Integration Ownership**: `MotionMechanics` integrates velocity for inert projectile assets via `physics.integrate()`. `ProjectileMechanics.update()` evaluates range/boundary expiration and elevation-partitioned intersections (`projectile.elevation == target.elevation`) against obstacles (`board.obstacles(layer, elevation)`) and targets (`SPRITES`, `PLAYERS`, `REACTABLES`), excluding `target.name == projectile.state.owner`.

##### User Review I

* Examine the Device implementation. Determine what would be necessary to add a counter to a button to determine how long it has been pressed.
* Examine the Sprite state definitions and create a formula for calculating the speed of a spawned projectile base on `sprite.state.character.strength` and the length of time the Sprite has held down the `attack` intention. Determine what state attributes would need added to accomodate this.
    * For the Player, the length of time will be determined through device polling.
    * For the Sprite, the length of time will be determined through CognitionMechanics. This is actually a really complex problem, so let's defer it until later. MVP is Player Projectile spawning based on length of time button was held and Player strength.

##### Architectural Analysis II

1. **Button Hold Duration Counter in `Device` (`Keyboard.poll`)**:
    * In `src/app/game/devices.py`, `Keyboard` already initializes `self._last_state = {code: 0 for code in self._scancodes}` when setting the device context and polls raw boolean key states `(0, 1)` via `sdl.poll(self._scancodes)`.
    * By upgrading `current_dict` from a binary flag to a consecutive-tick accumulator:

    ```python
    current_dict = {
        code: (self._last_state.get(code, 0) + 1) if state else 0
        for code, state in zip(self._scancodes, current_state)
    }
    ```

    every pressed scancode tracks its exact hold duration in ticks ($c_t \ge 1$) while unpressed scancodes reset to `0`:
    * **Backward-Compatible Edge Triggering**: Because `self._last_state.get(v)` is `0` (falsy) only when unpressed on the prior tick and $\ge 1$ (truthy) on every held tick, existing rising-edge checks (`current_dict.get(v) and not self._last_state.get(v)`) across `intentions`, `grips`, `menus`, `traversal`, and `interactions` remain invariant.
    * **Hold Counter Propagation**: Extending `WorldPayload` (`src/app/models/state/devices.py`) with `hold: int = 0` allows `Keyboard.poll()` to emit the consecutive tick count of the active intention button in configuration order (preserving the Intention singularity rule):

    ```python
    for k, v in self.mapping.world.intentions.items():
        if v is not None and current_dict.get(v):
            if not self._last_state.get(v):
                world_payload.intention = k
            world_payload.hold = current_dict[v]
            break
    ```

```mermaid
flowchart LR
    A["sdl.poll(_scancodes)"] --> B["c_t(v) = c_{t-1}(v) + 1 if pressed else 0"]
    B --> C{"c_{t-1}(v) == 0?"}
    C -- Yes --> D["world_payload.intention = k<br/>world_payload.hold = 1"]
    C -- No --> E["world_payload.intention = None<br/>world_payload.hold = c_t(v)"]
    D --> F["PlayerMechanics: charge = hold"]
    E --> F
    F --> G["CombatMechanics: speed(strength, charge)"]
```

2. **State Attributes for Hold Duration (`MutatorParameters.charge`)**:
    * Inspecting `SheetState` (`src/app/models/state/assets/sheets.py`) and `AssetState` (`src/app/models/state/core.py`), `MutatorParameters` is the canonical container for dynamic parameters modulating an entity's active Intention or physical state (already housing `hand: Optional[Enumerated[Hands]] = None` for `Intentions.USE` and `descension: Optional[float] = 0.0` for gravity freefall).
    * Adding `charge: int = 0` to `MutatorParameters` provides a unified state field across both `Player` (`SheetState`) and `Sprite` (`SpriteState`) without duplicating fields across models:
        * **Player Lifecycle (`PlayerMechanics`)**:
            1. When `player.state.intention != intention` on a new `Intentions.ATTACK` transition, initialize `player.state.mutators.parameters.charge = payload.world.hold`.
            2. On subsequent ticks while `player.state.intention == Intentions.ATTACK` and `payload.world.hold > 0`, update `player.state.mutators.parameters.charge = payload.world.hold`.
            3. If the Player releases the attack key early (`payload.world.hold == 0`) while locked in the blocking `SHOOT` animation (`is_locked == True`), `player.state.mutators.parameters.charge` retains the peak tick count $n$ held during that draw rather than being wiped to `0` before the release frame is reached.
            4. When `player.state.intention` returns to `Intentions.IDLE` (or upon projectile release in `CombatMechanics`), reset `player.state.mutators.parameters.charge = 0`.
        * **Sprite Lifecycle (Deferred to Future Phase)**: Because `MutatorParameters.charge` lives on `AssetState`, `CognitionMechanics` can later populate `sprite.state.mutators.parameters.charge` without any schema or `CombatMechanics` changes.

3. **Projectile Speed Formula ($s(S, n)$)**:
    * Let $S = \text{state.character.strength}$ (default `10`), $n = \text{state.mutators.parameters.charge} \in \mathbb{Z}_{\ge 0}$, and $N_{\max} = \max(1, F_{\text{release}} \cdot \text{delay})$ be the number of ticks from frame `0` to the release frame $F_{\text{release}}$ of `Actions.SHOOT`.
    * Define the normalized draw ratio $\tau(n) \in [0, 1]$ and scalar launch speed $s(S, n)$:

    $$
    \tau(n) = \min\left(1.0,\; \frac{n}{N_{\max}}\right), \qquad s(S, n) = \operatorname{round}\Big(\alpha S \big(1 + \tau(n)\big)\Big)
    $$

    * With base strength coefficient $\alpha = 10\text{ px}/(\text{s}\cdot\text{strength})$ (`settings.PROJECTILE_BASE_SPEED_FACTOR = 10`):
        * **Uncharged / Instant Tap ($n \to 0, S = 10$)**: $\tau(0) = 0 \implies s(10, 0) = 100\text{ px/s}$, guaranteeing a positive minimum launch velocity even for a 1-tick tap or an uncharged NPC Sprite (`charge == 0`).
        * **Half Draw ($\tau = 0.5, S = 10$)**: $s(10, N_{\max}/2) = 150\text{ px/s}$.
        * **Full Draw ($n \ge N_{\max}, S = 10$)**: $\tau(n) = 1.0 \implies s(10, N_{\max}) = 200\text{ px/s}$, matching the nominal `MotorState.speed = 200` baseline and saturating cleanly so prolonged button holds cannot cause unbounded velocity or hitbox tunneling.

##### User Review II

* The concept of "release frame" in the spec seems ill defined. If I am understanding correctly, the current spec proposes to release the projectile the first tick of the first frame.
* However, this will not work in terms of animation fluidity. The LPC animations require flexibility, as the "release frame" is highly variable. The projectile has to be released on a certain frame, and that frame will be dependent on the type of Equipment, e.g. a crossbow animation might release a bolt at frame 3, but a longbow animation might release an arrow at frame 7.
* For non-projectile Equipment, AttackHitboxes are used in conjunction with the CombatMap and AnimationMap to resolve which attackbox applies on which frame. It would seem a similar solution can be adopted for Projectiles, insofar that the release frame needs to be mapped from the Equipment that spawns the Projectile, not the Projectile itself, i.e. release frame is a property of Equipment, not Projectiles.
* It would seem possible to define the "release frame" on the a certain keyed Hitbox, e.g. `shoot-up-3`. However, this seems to introduce some undesirable polymorphism, as both projectile equipment and non-projectile equipment get injected with the same Hitbox implementation. So, it seems like the AttackHitbox interface would have to "bend" to accomodate the different behaviors. However, perhaps, the Combat logic could abstract the release frame lookup the same way the CombatMap abstracts the `attackboxes`.

##### Architectural Analysis III

1. **Why Action-Based Detection and `AttackHitbox` Overloading Fail for Ranged Equipment**:
    * Inspecting `src/assets/sheets/equipments/weapons/main.yaml` reveals why ranged combat cannot be triggered by checking `if attacker.state.animation.action == Actions.SHOOT:`:
        * `longbow` uses `actions: lpc-shoot` (`Actions.SHOOT`), whereas `crossbow` uses `actions: lpc-thrust` (`Actions.THRUST`)—the exact same action set used by the melee `spear`!
        * Consequently, `AnimationState.action` is not a bijective indicator of ranged vs. melee combat; the equipped weapon itself determines whether an attack is melee or ranged, which projectile asset (`arrow` vs. `bolt`) is emitted, and on which frame index $F_{\text{release}}$ emission occurs.
    * Furthermore, overloading `properties.hitboxes` (e.g. `shoot-up-7`) and `AttackHitbox` to encode projectile release frames introduces structural polymorphism into `HitboxSchema`:
        * All `sheets.weapons` share a single recipe (`hitbox: AttackHitbox`).
        * `AttackHitbox.get()` fulfills the `HitboxSchema` contract by returning spatial `List[Hitbox]` primitives for melee collision resolution in `CombatMechanics`. A ranged weapon does not strike targets via a weapon-attached AABB; it spawns an autonomous `Projectile` asset whose own `RotatedHitbox` traverses the board.
        * Even if `properties.hitboxes` encoded a release frame key, it still could not express *which* projectile ID (`arrow` vs. `bolt` vs. `cannonball`) the weapon spawns. Keeping `hitboxes: null` on ranged weapons allows `AttackHitbox.get()` to return `[]` without modification or polymorphism.

2. **Equipment-Driven Release Frame & Projectile Binding on `SheetProperties`**:
    * Just as `ResourceProperties` declares `loot: str = None` to bind a biological resource to the `Collectable` it spawns, `SheetProperties` (`src/app/models/properties/assets.py`) should declare two optional equipment properties:
        * `projectile: Optional[Enumerated[ProjectilePalette]] = None`: The projectile asset ID in `cursors.projectiles` spawned by this weapon (`arrow` for `longbow`, `bolt` for `crossbow`, `None` for melee weapons).
        * `release: Optional[int] = None`: The 0-based frame index $F_{\text{release}}$ within the weapon's active `Action` on which the projectile is released (e.g. `release: 9` for `longbow` under 13-frame `lpc-shoot`; `release: 5` for `crossbow` under 8-frame `lpc-thrust`).
    * In `src/assets/sheets/equipments/weapons/main.yaml`:

    ```yaml
    sheets:
      weapons:
        # --------------------------------------- ACTION: SHOOT
        longbow:
          dimensions: *lpc
          hitboxes: null
          actions: lpc-shoot
          stack: [ longbow ]
          projectile: arrow
          release: 9
        ...
        # --------------------------------------- ACTION: THRUST
        crossbow:
          dimensions: *lpc
          hitboxes: null
          actions: lpc-thrust
          stack: [ crossbow ]
          projectile: bolt
          release: 5
    ```

3. **Abstracting Release Frame & Speed Resolution via `CombatMap.projectile()`**:
    * Mirroring how `CombatMap.attackboxes(state, equipment, elevation)` resolves active melee hitboxes from the equipped weapon, `CombatMap` (`src/app/game/logic/modules/maps/combat.py`) should expose `CombatMap.projectile(state: SheetState, equipment: EquipmentGroup) -> Optional[Tuple[str, int]]`:
        1. Resolve `weapon = equipment.weapons.get(state.slots.equipment.weapon)`. If `not weapon` or `not weapon.properties.projectile` or `weapon.properties.release is None`, return `None`.
        2. Verify that `state.animation.action in weapon.properties.actions` and `state.animation.frame == weapon.properties.release`.
        3. Enforce single-tick edge emission within that frame (`state.animation.tick <= 1`) so actions with `delay > 1` only emit one projectile upon entering `release`.
        4. Derive the weapon's draw window $N_{\max}$ directly from the weapon's configured `release` frame and action `delay`:

        $$
        N_{\max} = \max\Big(1,\; \text{weapon.properties.release} \cdot \text{weapon.properties.actions}[\text{state.animation.action}].\text{delay}\Big)
        $$

        5. Compute the charged launch speed $s(S, n)$ from $S = \text{state.character.strength}$ and $n = \text{state.mutators.parameters.charge}$, returning `(weapon.properties.projectile, speed)`.

```mermaid
flowchart TD
    A["CombatMechanics.update()"] --> B["attacker in Intentions.ATTACK"]
    B --> C["CombatMap.projectile(attacker.state, board.equipment)"]
    C --> D{"weapon.properties.projectile<br/>& frame == weapon.properties.release<br/>& tick <= 1?"}
    D -- Yes --> E["Compute N_max = release * action.delay<br/>Compute speed(strength, charge)"]
    E --> F["board.cradle.spawn_projectile(projectile_id, ..., speed)"]
    F --> G["board.add([projectile])<br/>attacker.state.mutators.parameters.charge = 0"]
    D -- No --> H["CombatMap.attackboxes(attacker.state, board.equipment, attacker.elevation)"]
    H --> I{"attackboxes non-empty?"}
    I -- Yes --> J["melee_attackers.append((attacker, attackboxes))"]
    I -- No --> K["Skip frame"]
```

4. **Decoupling `CombatMechanics` from Hardcoded Actions**:
    * In `CombatMechanics.update()`, the hardcoded `if attacker.state.animation.action in (Actions.SHOOT, Actions.CAST): continue` guard is replaced by querying `CombatMap.projectile(attacker.state, board.equipment)` and `CombatMap.attackboxes(attacker.state, board.equipment, attacker.elevation)`.
    * Ranged weapons (`longbow` on `SHOOT`, `crossbow` on `THRUST`) have `hitboxes: null`, so on non-release frames both `CombatMap.projectile()` and `CombatMap.attackboxes()` return empty/`None`, and on the configured `release` frame `CombatMap.projectile()` returns `(projectile_id, speed)` for `board.cradle.spawn_projectile()`.

##### User Review III

Disagree with the direction of analysis and proposed solution. Introducing an Instance specific field onto a category level model (Properties) seems like a poor design decision. Let's back up and consider how CombatMechanics works.

Here is how the CombatMechanics flow should work (very generally):

```python:pseudocode

def _melee(self, attacker, board):
    attackboxes = CombatMap.attackboxes(
        attacker.state,
        board.equipment,
        attacker.elevation
    )
    # existing logic

def _project(self, attacker, board):
    release_frame = CombatMap.release(
        attacker.state,
        board.equipment,
        attacker.elevation
    )
    projectile = CombatMap.projectile(...)
    # do other stuff

def update(self, board, delta, bus, payload):
    # existing filter of intentions 
    # ...

    for attacker in attckers:
        # PHASE 1: Determine if Action is possible.
        action = CombatMap.action(attacker.state, board.equipment)
        attacker.state.animation.action

        # PHASE 2: Fork on type of Action
        if action in MeleeActions:
            self._melee(attacker, board)

        elif action in ProjectileActions:
            self._project(attacker, board)
```

* CombatMap.action: maps the current Equipment and Intent to an Action. Ensures Sprites cannot enter into Actions without the correct Equipment. 
* CombatMap.release: pulls the AttackHitbox. Instead of using it to calculate intersections and attack vectors, it uses the AttackHitbox to determine where and in what direction the Projectil should be spawned.
* CombatMap.projectile: projectile mapping.

**NOTE**: this should be taken as gospel. I am attempting to clarify the logical flow.

No extraneous properties necessary so far. To account for the relation of Projectile to Weapon, rather than encode this into Properties, which are models of Assets in isolation, the proposed mapping is actually a *Relation* between Asset types. Thus, it calls for an addition to the Relations module. `app.game.logic.relations` is currently utilized for mapping Shorelines to Fluids (ShorelineIndex), and mapping Crafts to Material Behaviors (MaterialIndex). For example,

Probably the relation between Projectiles and Weapons should be codified as *Configuration* and then compiled into a Relation. 

##### Architectural Analysis IV

1. **Preserving Category-Level `SheetProperties` Purity via `AttackHitbox` & `CombatMap.release`**:
    * `SheetProperties` is a Category-level model shared across all `sheets` instances (`sprites`, `pixies`, `armor`, `shields`, `tools`, `utilities`, `weapons`). Polluting `SheetProperties` with weapon-specific or projectile-specific attributes breaks the strict $\text{Category} \to \text{Properties}$ mapping.
    * Every weapon in `sheets.weapons` already receives `AttackHitbox` (`recipes.sheets.weapons`) and declares `hitboxes: Dict[str, List[Hitbox]]` keyed by `<action>-<direction>-<frame>`.
    * Instead of modifying `AttackHitbox` or `SheetProperties`, the distinction between melee strikes and ranged projectile releases is a difference in how `CombatMechanics` and `CombatMap` *interpret* the weapon's active `AttackHitbox` after forking on `action`:
        * For `action in MeleeActions` (`slash`, `thrust`), `CombatMap.attackboxes(attacker.state, board.equipment, attacker.elevation)` retrieves the active `Hitbox` list on the strike frames, and `CombatMechanics._melee(attacker, board)` evaluates narrow-phase intersections against targets.
        * For `action in ProjectileActions` (`shoot`, `cast`), ranged weapons in `src/assets/sheets/equipments/weapons/main.yaml` define a `Hitbox` entry under `hitboxes` only on their release frame for each direction (e.g., `shoot-up-9`, `shoot-left-9`, `shoot-down-9`, `shoot-right-9` for `longbow`).
        * `CombatMap.release(attacker.state, board.equipment, attacker.elevation)` queries `weapon.hitbox.get(weapon.properties, attacker.state, resolved_elevation)` on the entry tick of the current frame. When non-empty, that `Hitbox` identifies the current frame as the weapon's release frame and defines the exact world-space spawn coordinate `(attacker.state.position.x + hb.position.x, attacker.state.position.y + hb.position.y)` where the projectile emerges!
        * Moreover, because `state.animation.frame` on the tick `CombatMap.release` succeeds *is* the release frame index $F_{\text{release}}$, the draw window $N_{\max} = \max(1, \text{state.animation.frame} \cdot \text{delay})$ is known directly from `state.animation.frame` without any extra property fields.
2. **Two-Phase Action Validation & Forking in `CombatMechanics`**:
    * In `CombatMechanics.update()`, each attacking entity (`state.intention == Intentions.ATTACK`) undergoes a two-phase evaluation:
        * **Phase 1 (Action Validation via `CombatMap.action`)**: `action = CombatMap.action(attacker.state, board.equipment)` validates that the attacker has the requisite equipment slotted to perform a combat action and assigns `attacker.state.animation.action = action`, ensuring Sprites cannot execute combat actions without matching equipment.
        * **Phase 2 (Action Group Fork)**:
            * If `action in MeleeActions`: routes to `self._melee(attacker, board)`.
            * If `action in ProjectileActions`: routes to `self._project(attacker, board)`.

```mermaid
flowchart TD
    A["CombatMechanics.update()"] --> B["attacker in Intentions.ATTACK"]
    B --> C["Phase 1: action = CombatMap.action(attacker.state, board.equipment)<br/>attacker.state.animation.action = action"]
    C --> D{"Phase 2: Fork on Action Group"}
    D -- "action in MeleeActions" --> E["self._melee(attacker, board)"]
    E --> F["CombatMap.attackboxes(attacker.state, board.equipment, attacker.elevation)"]
    F --> G["Broad/Narrow Phase Melee Intersection & Damage"]
    D -- "action in ProjectileActions" --> H["self._project(attacker, board)"]
    H --> I["release_hb = CombatMap.release(attacker.state, board.equipment, attacker.elevation)"]
    I --> J{"release_hb is not None<br/>(on entry tick)?"}
    J -- Yes --> K["projectile_id, speed = CombatMap.projectile(attacker.state, board.equipment, self.relation)"]
    K --> L["board.cradle.spawn_projectile(projectile_id, spawn_pos, ..., speed)<br/>board.add([projectile])"]
    J -- No --> M["Continue Draw"]
```

3. **Codifying the Weapon-to-Projectile Association as a `Relation` (`app.game.logic.relations`)**:
    * Because Properties model an Asset in isolation, the mapping between a `Weapon` (`sheets.weapons`, e.g., `longbow`, `crossbow`) and the `Projectile` it emits (`cursors.projectiles`, e.g., `arrow`, `bolt`) is a cross-asset **Relation**.
    * Following the exact pattern of `MaterialIndex.from_configuration(self.context.configurations.materials)` in `Builder.build_relations()`:
        1. Declare the weapon-to-projectile mapping in configuration (e.g., `longbow: arrow`, `crossbow: bolt`).
        2. Compile a `Singleton` relational index in `src/app/game/logic/relations/` (e.g., `ProjectileIndex` / `CombatIndex` with `from_configuration()` and `resolve(weapon_id) -> Optional[str]`) and register it in `Builder.build_relations()`.
        3. Inject the relation into `CombatMechanics` via `relations` in `src/data/config/mechanics/main.yaml` (accessed via `self.relation` on `Mechanic`).
        4. `CombatMap.projectile(attacker.state, board.equipment, self.relation)` queries the relation to resolve the projectile Asset ID for `attacker.state.slots.equipment.weapon` and computes the charged launch speed $s(S, n)$.

##### User Review V

###### Concept of "Maps"

Something seems off. The concept of "Maps" (Combat and Animation) seems to be vague. Before moving onto implementation, I want to clarify the entire Sprite Intention -> Action workflow. CombatMap and AnimationMap seems to be at odds, and this seems to indicate the interface that is being used is incorrect ins some capacity.

What is currently defined:

1. TransitionMechanics applies the following mapping after evalatuing the Intention Transition matrix:

```python
sprite.state.animation.action = AnimationMap.action(
    sprite.state, 
    board.equipment
)

# 3. Resolve Direction
target_pos = sprite.state.trajectory.target or (
    sprite.state.goal.position if sprite.state.goal else None
)

if target_pos:
    sprite.state.animation.direction = AnimationMap.direction(
        sprite.state.position, 
        target_pos
    )
```

This maps the Sprite Intention to an (Action, Direction)

2. PlayerMechanics similarly maps Intention paylods from the device to Player (Action, Direction):

```python
player.state.animation.action = AnimationMap.action(
    player.state, 
    board.equipment
)

if player.state.goal and has_movement:
    player.state.animation.direction = AnimationMap.direction(
        player.state.position,
        player.state.goal.position
    )
```

3. CombatMechanics does the following (currently, with the planned extensions also to be taken into account):

```python
attackboxes = CombatMap.attackboxes(
    attacker.state,
    board.equipment,
    attacker.elevation
)
```

In summary: 

* AnimationMap.action: (Intention, Equipment) -> Action
* AnimationMap.direction: (Position, Goal) -> Direction 
* CombatMap.attackboxes: (Slots, Equipment) -> Hitbox

In each case, we have a domain comprised of a Cartesian product of categorical variables (except Position, which is continuous and quantitative) and a function that is mapping those domains to a range. (action, direction) are semantic enumerations. Hitbox is a datastructure of (relative position, dimension).

Moreover, the proposed CombatMap.action overlaps with AnimationMap.action. The core issue is: where and when does the Sprite intention "transform" into an Action and Direction?

If TransitionMechanics does not assign an Action, then the Sprite will not animate when AnimationMechanics executes. However, the Combat Actions are not mapped (in the proposal) until CombatMechanics executes. So, TransitionMechanics will assign the Action of Slash before CombatMechanics has had a chance to determine if that Action is permissibile.

Please analyze this problem and clarify the combat flow. Update the backlog accordingly.

###### Projectile-Weapon Mapping

After examining the proposals, while I am still of the opinion that codifying the mapping as an `app.game.logic.relations` Relation is the correct move, I am now not so certain the relation shouldn't be defined as a property. Geography is an example of an Asset that is implicitly relational, i.e. shorelines cannot be embedded into the Board without awareness of the Tiles and Fluids they border, hence these are Properties of Geography. Hence,

```python
"""
@domain.logic
@app.module
@category.geography
@workflows.generation
@workflow.fluids

# Ontology: Source - app.game.logic.relations.shorelines

Relational index mapping Environ Tiles, Fluid Effects and Seasons to Geography Shorelines.
"""
from __future__ import annotations

# Standard Libraries
from typing import (
    Dict,
    Tuple,
    Optional,
    Any,
    TYPE_CHECKING
)
import logging

# Application Library
from app.models.abstracts import Singleton

if TYPE_CHECKING:
    from app.models.properties import GeographyProperties

# ---------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------

class ShorelineIndex(Singleton):
    """
    Relational secondary index mapping (tile_id, fluid_id, [season]) to shoreline Asset ID.
    Supports multi-level fallback:
    1. (tile_id, fluid_id, season)
    2. (tile_id, fluid_id)
    3. (tile_id, None, season)
    4. (tile_id, None)
    """
    _map: Dict[Tuple[str, Optional[str], Optional[str]], str] = {}
    _fallback_map: Dict[Tuple[str, Optional[str]], str] = {}

    def __init__(self, relations: Optional[Dict[Any, str]] = None):
        self._map = {}
        self._fallback_map = {}
        if relations:
            for key, shoreline_id in relations.items():
                self.register(key, shoreline_id)

    @classmethod
    def from_properties(cls, shorelines: Dict[str, GeographyProperties]) -> ShorelineIndex:
        """
        Factory constructor compiling relational definitions from geography property schemas.
        """
        index = cls()
        for shoreline_id, props in shorelines.items():
            season = getattr(props, "season", None)
            if season:
                index.register((props.tile, props.fluid, season), shoreline_id)
            index.register((props.tile, props.fluid), shoreline_id)
        return index

    def register(self, key: Tuple, shoreline_id: str) -> None:
        """
        Registers a composite relation tuple to target shoreline asset ID.
        """
        if len(key) == 3:
            tile_id, fluid_id, season = key
            self._map[(tile_id, fluid_id, season)] = shoreline_id
        elif len(key) == 2:
            tile_id, fluid_id = key
            self._fallback_map[(tile_id, fluid_id)] = shoreline_id

    def resolve(
        self,
        tile_id: str,
        fluid_id: Optional[str] = None,
        season: Optional[str] = None
    ) -> Optional[str]:
        """
        Resolves the appropriate shoreline asset ID across compound keys with seasonal fallback.
        """
        # 1. Primary seasonal resolution: (tile, fluid, season)
        if season is not None:
            seasonal_key = (tile_id, fluid_id, season)
            if seasonal_key in self._map:
                return self._map[seasonal_key]

            # Seasonal fallback without fluid constraint
            if fluid_id is not None:
                dry_seasonal_key = (tile_id, None, season)
                if dry_seasonal_key in self._map:
                    return self._map[dry_seasonal_key]

        # 2. Base relational fallback: (tile, fluid)
        base_key = (tile_id, fluid_id)
        if base_key in self._fallback_map:
            return self._fallback_map[base_key]

        # 3. Base fallback without fluid constraint: (tile, None)
        if fluid_id is not None:
            dry_base_key = (tile_id, None)
            if dry_base_key in self._fallback_map:
                return self._fallback_map[dry_base_key]

        return None
```

Projectiles and Weapons are inherently relational. A `crossbow` cannot fire a Projectile without knowing what type of Projectile is to be spawned. It does seem like the proper solution is to have the ProjectileIndex expose a factory method `from_properties` in a similar way to the ShorelineIndex. Then it can get compiled from Properties, not configuration. 

The question is what is the "independent" variable and what is the "dependent" variable. In my head, I see Projectiles are "dependent" on the existence of the Weapon, so it seems like Projectiles should contain the relational indexing properties. 

##### Goals

###### Goal: Implement `render.rotate` in Cython SDL2 Bindings

Expose `SDL_Point`, `SDL_RendererFlip`, and `SDL_RenderCopyEx` in `src/libs/graphics/render.pyx` and implement `rotate(TexturePtr base_ptr, int rotation) -> TexturePtr` to pre-bake rotated projectile frames into a single horizontal `TexturePtr` strip during `Registry` texture loading when `asset_key in self.properties.cursors.projectiles`.

###### Goal: Implement `ProjectileFrame` and `RotatedHitbox`

Create `ProjectileFrame` (`src/app/assets/frames/cursors.py`) and `RotatedHitbox` (`src/app/assets/hitboxes/cursors.py`) and register them under `recipes.cursors.projectiles` in `src/data/config/recipes/main.yaml`.

###### Goal: Track Intention Hold Duration in `Device` and `PlayerMechanics`

Update `Keyboard.poll()` (`src/app/game/devices.py`) to accumulate consecutive press ticks per scancode in `self._last_state` and expose the active intention hold count on `WorldPayload.hold` (`src/app/models/state/devices.py`). Extend `MutatorParameters` (`src/app/models/state/core.py`) with `charge: int = 0` and update `PlayerMechanics.update()` to record the held tick count during `Intentions.ATTACK`.

###### Goal: Compile Weapon-to-Projectile `Relation` and Wire `CombatMap`, `Cradle`, `CombatMechanics`, and `ProjectileMechanics`

Codify the weapon-to-projectile relation in configuration, compile it into a `Relation` index in `app.game.logic.relations` during `Builder.build_relations()`, and inject it into `CombatMechanics`. Configure release-frame `hitboxes` on ranged weapons in `src/assets/sheets/equipments/weapons/main.yaml`. Implement `CombatMap.action`, `CombatMap.release`, and `CombatMap.projectile`, fork `CombatMechanics.update()` into `_melee()` and `_project()` across `MeleeActions` and `ProjectileActions`, and resolve projectile trajectories and impacts in `Cradle.spawn_projectile()` and `ProjectileMechanics.update()`.

##### Tasks

**1. Task: Add Cython `render.rotate` and Registry Load-Time Rotation**

*Objective*: Synthesize rotated texture strips in VRAM during `Registry` texture loading for assets registered under `properties.cursors.projectiles`.

* [] Subtask: Declare `SDL_Point`, `SDL_RendererFlip`, and `SDL_RenderCopyEx` in `src/libs/graphics/render.pyx` and implement `rotate(TexturePtr base_ptr, int rotation) -> TexturePtr`.
* [] Subtask: Update `CursorProperties` in `src/app/models/properties/assets.py` to include `rotation: int = 90` and update `MotorState` (`src/app/models/state/assets/cursors.py`) to include `angle: int = 0`, `speed: int = 200`, and `owner: Optional[str] = None`.
* [] Subtask: Update `Registry._get_or_load_texture()` in `src/libs/graphics/registry.pyx` to check `asset_key in self.properties.cursors.projectiles`, invoke `render.rotate(raw_tex, self.properties.cursors.projectiles[asset_key].rotation)`, and destroy the temporary unrotated texture.

**2. Task: Implement `ProjectileFrame` and `RotatedHitbox`**

*Objective*: Index rotated projectile frame crops and transform base AABB hitboxes by `state.angle`.

* [] Subtask: Fix the `ProjectilFrame` class name typo and implement `ProjectileFrame` in `src/app/assets/frames/cursors.py` to index `f"{id}-{k * properties.rotation}"` crops and resolve `[(f"{id}-{state.angle}", 0, 0)]` in `keys()`.
* [] Subtask: Implement `RotatedHitbox` in `src/app/assets/hitboxes/cursors.py` (and export in `src/app/assets/hitboxes/__init__.py`) to project base `properties.hitboxes` around the frame center by `state.angle` at the projectile's `elevation`.
* [x] Subtask: Register `ProjectileFrame` and `RotatedHitbox` under `cursors.projectiles` in `src/data/config/recipes/main.yaml`.

**3. Task: Implement Button Hold Counter in `Device` and Charge Tracking in `PlayerMechanics`**

*Objective*: Measure how many consecutive ticks an intention button is held and persist the charge count on `MutatorParameters`.

* [] Subtask: Add `hold: int = 0` to `WorldPayload` in `src/app/models/state/devices.py` and `charge: int = 0` to `MutatorParameters` in `src/app/models/state/core.py`.
* [] Subtask: Update `Keyboard.poll()` in `src/app/game/devices.py` to increment per-scancode hold counters in `self._last_state` while pressed, reset to `0` on release, and populate `world_payload.hold` for the active intention key.
* [] Subtask: Update `PlayerMechanics.update()` in `src/app/game/logic/mechanics/intentional/player.py` to accumulate `payload.world.hold` into `player.state.mutators.parameters.charge` during `Intentions.ATTACK` (preserving the held count if released before the animation completes) and reset `charge = 0` when returning to `Intentions.IDLE`.

**4. Task: Implement Weapon-to-Projectile `Relation`, `CombatMap` Methods, and Ranged `CombatMechanics` / `ProjectileMechanics` Flow**

*Objective*: Compile weapon-to-projectile relations from configuration, resolve release frames and spawn geometry via `AttackHitbox` and `CombatMap`, and fork `CombatMechanics` into `_melee` and `_project`.

* [] Subtask: Define `MeleeActions` and `ProjectileActions` in `src/app/static/semantics.py` and configure release-frame directional `hitboxes` on ranged weapons (`longbow`, `crossbow`) in `src/assets/sheets/equipments/weapons/main.yaml`.
* [] Subtask: Codify the weapon-to-projectile relation in configuration, implement the relational index in `src/app/game/logic/relations/`, register it in `Builder.build_relations()`, and inject it into `CombatMechanics` in `src/data/config/mechanics/main.yaml`.
* [] Subtask: Implement `CombatMap.action()`, `CombatMap.release()`, and `CombatMap.projectile()` in `src/app/game/logic/modules/maps/combat.py` to validate equipment actions, pull the release-frame `AttackHitbox` for projectile spawn position/direction, resolve the projectile ID from the relation index, and compute charged speed $s(S, n)$.
* [] Subtask: Update `Cradle.spawn_projectile()` to clone `Position` for `position` and `initial`, quantize launch vectors onto the nearest multiple of `properties.rotation`, compute `Velocity(vx, vy)` from `angle` and `speed`, and populate `MotorState` at the shooter's `elevation`.
* [] Subtask: Refactor `CombatMechanics.update()` to resolve `action = CombatMap.action(attacker.state, board.equipment)` and fork into `self._melee(attacker, board)` for `MeleeActions` and `self._project(attacker, board)` for `ProjectileActions`, and update `ProjectileMechanics.update()` to resolve elevation-partitioned target/obstacle impacts and boundary removal.
