#### Refactor: Phase 06.03 - Combat

**Overview**

Induct `AttackHitbox` and `Equipment` into the unified Entity-Component-System (`HitboxSchema`) architecture established in Phase 07.04, resolve the structural tension between a Sprite's physical collision footprint (`StaticHitbox`) and its active weapon reach (`AttackHitbox`), enforce discrete elevation partitioning in `CombatMechanics`, stabilize ranged combat projectile spawning, and migrate `test_combat.py` to the live `world-testbed` fixture framework.

##### Specification

In the Asset Hierarchy, `Sprites` (and `Players`) are stateful `Sheet` Assets deployed onto the `Board`, whereas `Equipment` (`weapons`, `tools`, `armor`, `shields`, `utilities`) are stateless `Sheet` Assets stored in `Board.equipment` (`EquipmentGroup`) and projected onto a wielding Sprite's state.

1. **Dual Footprint Separation (Hurtbox vs. Attackbox)**:
* **Body Footprint (`Hurtbox`)**: Owned by the deployed `Sprite` or `Player` (`Asset`). Resolved via `StaticHitbox` from `sprite.properties.hitboxes` (`List[Hitbox]`). Governs physical obstacle collision (`CollisionMechanics`), RRT pathfinding anchors (`NavigationMechanics`), environmental interactions (`InteractionMechanics`), fluid immersion (`MotionMechanics`), and incoming damage reception (`CombatMechanics`).
* **Action Footprint (`Attackbox`)**: Owned by stateless `Equipment` (`weapons` and `tools`). Resolved via `AttackHitbox` from `equipment_properties.hitboxes` (`Dict[str, List[Hitbox]]`) projected against the wielding entity's `SheetState` (`state.animation` and `state.elevation`).


2. **Property Schema Unification (`SheetProperties`)**:
* Align `SheetProperties` with `ObjectProperties`, `CraftProperties`, and `ResourceProperties` by consolidating `attackboxes` into a single polymorphic `hitboxes` field:

$$\text{SheetProperties.hitboxes} : \text{Optional}\Big[\text{Union}\big[\text{Dict}[\text{str}, \text{List}[\text{Hitbox}]],\; \text{List}[\text{Hitbox}]\big]\Big]$$


* Deployed character sheets (`sprites`, `players`, `pixies`) configure `hitboxes` as `List[Hitbox]` (interpreted by `StaticHitbox`).
* Stateless equipment sheets (`weapons`, `tools`) configure `hitboxes` as `Dict[str, List[Hitbox]]` keyed by `<action>-<direction>-<frame>` (interpreted by `AttackHitbox`).


3. **Stateless Projection Contract (`AttackHitbox` & `CombatMap`)**:
* Just as `StateFrame.keys(eq_key, sprite.state)` projects a Sprite's `AnimationState` onto stateless Equipment textures inside `SpriteFrame`, `AttackHitbox.get(weapon_props, sprite.state, elevation)` projects a Sprite's `AnimationState` and `elevation` onto stateless Equipment hitbox maps.
* `CombatMap.attackboxes(state, equipment, elevation)` serves as the resolution bridge: it extracts the active weapon (or tool) `SheetProperties` from `EquipmentGroup` and delegates geometric lookup to `AttackHitbox().get(weapon_props, state, elevation)`.



##### Architectural Analysis I

1. **Why `AttackHitbox` Cannot Replace `StaticHitbox` on `Sprite` Instances**:
Every deployed `Asset` possesses a single `hitbox: HitboxSchema` slot. Replacing `StaticHitbox` with `AttackHitbox` on `sheets.sprites` or `sheets.players` would cause `sprite.hitboxes` to evaluate to `[]` on all non-attack frames—breaking solid-body collision resolution, door/chest interaction padding, fluid immersion checks, and target hurtbox detection—while causing weapon swing footprints on active attack frames to transfer physical impulse against walls and shift RRT sensory anchors. Keeping `StaticHitbox` on the `Sprite` and binding `AttackHitbox` to `Equipment` preserves strict separation between the body hurtbox and the weapon attackbox.
2. **Defect in Existing `AttackHitbox.get()` Implementation (`src/app/assets/hitboxes/sheets.py`)**:
The current implementation of `AttackHitbox.get()` delegates key generation to `frame.keys(state.id, state)`:
```python
keys = frame.keys(state.id, state)
frame_key = keys[0][0]
return properties.attackboxes.get(frame_key, [])

```


This contains two incompatibilities:
* **Prefix Mismatch**: `StateFrame.keys(id, state)` prepends the Asset `id` to produce a Registry texture key (`f"{id}-{action}-{direction}-{frame}"`, e.g., `"player-slash-right-3"`), whereas weapon hitbox maps in `/src/assets/sheets/equipment/weapons/*.yaml` are keyed by canonical animation state (`f"{action}-{direction}-{frame}"`, e.g., `"slash-right-3"`).
* **Coupling to `Frame**`: No other `HitboxSchema` (`LayeredHitbox`, `MaterialHitbox`, `StageHitbox`) calls `Frame.keys()`; each indexes `properties.hitboxes` directly from `state` attributes (`state.layer`, `state.blueprint`, `state.stage`). Constructing `frame_key` directly from `state.animation` (`f"{state.animation.action}-{state.animation.direction}-{state.animation.frame}"`) inside `AttackHitbox.get()` decouples `HitboxSchema` from `Frame` and matches the YAML schema.


3. **Elevation Leakage and Unarmed/Ranged Crash in `CombatMechanics` (`src/app/game/logic/mechanics/spatial/combat.py`)**:
* **Elevation Leakage**: `CombatMechanics.update()` currently hashes all melee attackers and targets on a `layer` into `self.grid` without checking `elevation`. An attacker at `elevation = 0` will damage a target at `elevation = 1` if their 2D `(x, y)` coordinates overlap. Evaluating collisions per elevation tier (`elevation = attacker.elevation`) and resolving target hurtboxes via `target.hitbox.get(target.properties, target.state, elevation)` enforces 3D topological isolation.
* **Ranged / Unarmed Crash**: When an unarmed entity enters `Intentions.ATTACK.value`, `AnimationMap.action()` resolves its action to `Actions.CAST.value`. In `CombatMechanics.update()`, `Actions.CAST.value` and `Actions.SHOOT.value` enter the ranged combat branch, which accesses `attacker.state.mutators.triggers.executed` (an attribute that does not exist on `MutatorTriggers`) and passes `"TODO"` strings to `board.cradle.spawn_projectile()`.


4. **Blackbox Mocking in `test_combat.py` (`tests/unit/app/game/logic/mechanics/spatial/test_combat.py`)**:
`test_combat.py` currently relies on ad-hoc helper functions (`_create_player_attacker`, `_create_sprite_target`, `_create_reactable_target`, `_create_equipment`), `MagicMock` bus/payload objects, and monkeypatched `mock_board.instances` lambdas. All required assets (`player` with `shortsword`, `jasilynn`, `archaxes`, and `spinning-dummy`) are already hydrated in `world-testbed`.

##### User Review I

{# Reserved Block for User #}

##### Goals

###### Goal: Unify `SheetProperties.hitboxes` and Refactor `AttackHitbox`

Consolidate `SheetProperties.attackboxes` into `SheetProperties.hitboxes` so that all Asset Categories use a single `hitboxes` property field interpreted by their respective `HitboxSchema`. Update `AttackHitbox` to resolve `<action>-<direction>-<frame>` directly from `state.animation` without requiring a `Frame` instance:

```python
# src/app/models/properties/assets.py
@dataclass(slots=True)
class SheetProperties(AssetProperties):
    stack: List[str] = field(default_factory=list)
    mass: int = 1
    actions: Union[
        str,
        Dict[Enumerated[Actions], Action]
    ] = field(default_factory=dict)
    hitboxes: Optional[Union[
        Dict[str, List[Hitbox]],
        List[Hitbox]
    ]] = field(default_factory=list)

```

```python
# src/app/assets/hitboxes/sheets.py
class AttackHitbox(HitboxSchema):
    """
    Resolves directional and frame-keyed action hitboxes from SheetProperties.
    """
    def elevations(self, properties: SheetProperties, state: SheetState) -> List[int]:
        return [max(0, state.elevation if state.elevation is not None else 0)]

    def get(
        self,
        properties: SheetProperties,
        state: SheetState,
        elevation: int,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        if not properties or not isinstance(properties.hitboxes, dict):
            return []
        target_e = max(0, state.elevation if state.elevation is not None else 0)
        if max(0, elevation) != target_e:
            return []
        frame_key = settings.SEPARATOR.join([
            state.animation.action,
            state.animation.direction,
            str(state.animation.frame),
        ])
        return properties.hitboxes.get(frame_key, [])

```

###### Goal: Delegate `CombatMap.attackboxes` to `AttackHitbox`

Update `CombatMap` to act as the stateless equipment selector that resolves the active weapon's `SheetProperties` from `EquipmentGroup` and delegates hitbox extraction to `AttackHitbox`:

```python
# src/app/game/logic/modules/maps/combat.py
class CombatMap:
    @staticmethod
    def attackboxes(
        state: SheetState,
        equipment: EquipmentGroup,
        elevation: Optional[int] = None
    ) -> List[Hitbox]:
        weapon_key = state.inventory.equipment.weapon
        weapon_props = equipment.weapons.get(weapon_key) if weapon_key else None
        if not weapon_props:
            return []
        resolved_elevation = (
            elevation if elevation is not None
            else (state.elevation if state.elevation is not None else 0)
        )
        return AttackHitbox().get(weapon_props, state, resolved_elevation)

```

###### Goal: Enforce Elevation Partitioning in `CombatMechanics`

Partition melee combat resolution by discrete elevation plane so that weapon attackboxes only intersect targets whose `HitboxSchema` emits hitboxes at the attacker's elevation:

```python
# src/app/game/logic/mechanics/spatial/combat.py
for i, (attacker, active_hitboxes) in enumerate(melee_attackers):
    attacker_map[i] = attacker
    primitives.append(attacker.primitive(i, hitboxes=active_hitboxes))

target_offset = len(melee_attackers)
for j, target in enumerate(targets):
    idx = target_offset + j
    target_map[idx] = target
    primitives.append(target.primitive(idx))

self.grid.clear()
colliding_indices = physics.collisions(primitives, self.grid)

for id_a, id_b in colliding_indices:
    ...
    if attacker.elevation != target.elevation:
        continue

```

###### Goal: Induct `test_combat.py` into the Live Fixture Framework

Remove all `_create_*` helper functions, `MagicMock` instances, and monkeypatched `mock_board` lambdas from `tests/unit/app/game/logic/mechanics/spatial/test_combat.py`. Execute all combat tests against `mock_mechanic(Mechanics.COMBAT.value)`, `mock_board`, `mock_bus`, and `mock_payload`.

##### Tasks

**1. Task: Unify `SheetProperties` Hitbox Schema and YAML Assets**

*Objective*: Consolidate `attackboxes` into `hitboxes` on `SheetProperties` and update all Sheet property YAML definitions.

* [] Subtask: Update `SheetProperties` in `src/app/models/properties/assets.py` so `hitboxes` accepts `Optional[Union[Dict[str, List[Hitbox]], List[Hitbox]]]` and remove the legacy `attackboxes` field.
* [] Subtask: Replace `attackboxes` with `hitboxes` in `src/assets/sheets/equipment/weapons/slash.yaml`, `src/assets/sheets/equipment/weapons/thrust.yaml`, `src/assets/sheets/equipment/weapons/shoot.yaml`, `src/assets/sheets/equipment/tools/slash.yaml`, and `src/assets/sheets/equipment/tools/thrust.yaml`.
* [] Subtask: Remove redundant `attackboxes: null` keys from `src/assets/sheets/sprites/main.yaml` and `src/assets/sheets/pixies/main.yaml`.
* [] Subtask: Register `AttackHitbox` in `src/data/config/recipes/main.yaml` for `sheets.weapons` and `sheets.tools`.

##### Tasks

**2. Task: Refactor `AttackHitbox` and Wire `CombatMap**`

*Objective*: Fix `AttackHitbox.get()` to resolve canonical `<action>-<direction>-<frame>` keys from `state.animation` and route `CombatMap.attackboxes()` through `AttackHitbox`.

* [] Subtask: Update `AttackHitbox.get()` in `src/app/assets/hitboxes/sheets.py` to guard against `None` or non-dict `properties.hitboxes`, validate elevation parity, and build `frame_key` from `state.animation.action`, `state.animation.direction`, and `str(state.animation.frame)`.
* [] Subtask: Update `CombatMap.attackboxes()` in `src/app/game/logic/modules/maps/combat.py` to delegate hitbox resolution to `AttackHitbox().get(weapon_props, state, resolved_elevation)`.
* [] Subtask: Add unit tests for `AttackHitbox.elevations()` and `AttackHitbox.get()` (covering matching frame, unmatched frame, elevation mismatch, and `None` hitboxes) and update `tests/unit/app/game/logic/modules/maps/test_combat_maps.py`.

##### Tasks

**3. Task: Harden `CombatMechanics` Elevation & Ranged Execution**

*Objective*: Prevent cross-elevation melee hits and guard ranged combat execution in `CombatMechanics.update()`.

* [] Subtask: Normalize `asset.state.intention == Intentions.ATTACK.value` comparison in `src/app/game/logic/mechanics/spatial/combat.py` and remove the inner-loop `hb.to_dict()` logging call.
* [] Subtask: Enforce elevation parity (`attacker.elevation == target.elevation`) during narrow-phase combat pair resolution in `CombatMechanics.update()`.
* [] Subtask: Add `executed: bool = False` to `MutatorTriggers` (or guard the ranged projectile stub in `CombatMechanics.update()`) so unarmed `Actions.CAST` and bow `Actions.SHOOT` animations do not raise `AttributeError` at frame 0.

##### Tasks

**4. Task: Refactor `test_combat.py` to Use `world-testbed` Fixtures**

*Objective*: Replace all ad-hoc asset builders and `MagicMock` overrides in `tests/unit/app/game/logic/mechanics/spatial/test_combat.py` with live `mock_board` and `mock_mechanic` fixtures.

* [] Subtask: Remove `_create_player_attacker`, `_create_sprite_target`, `_create_reactable_target`, and `_create_equipment` from `tests/unit/app/game/logic/mechanics/spatial/test_combat.py`.
* [] Subtask: Refactor `test_combat_mechanics_melee_resolution`, `test_combat_mechanics_lethal_blow`, `test_combat_mechanics_reactable_trigger`, `test_combat_mechanics_inactive_attackbox_filtered`, and `test_combat_mechanics_unarmed_bypasses_melee` to query `mock_board.player()`, `mock_board.instances(AssetInstances.SPRITES.value, "0")`, and `mock_board.instances(AssetInstances.REACTABLES.value, "0")`.
* [] Subtask: Add `test_combat_mechanics_elevation_isolation` to verify that an attacker at `elevation = 0` cannot damage a overlapping target at `elevation = 1`.