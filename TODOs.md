### 2. Bughunting — New Bug Reports for User Review

The following **8 new bugs (`B082`–`B089`)** were detected while auditing the current implementation. Per task instructions, no fixes have been implemented; all are opened below for User Review.

##### Bug B082: `NavigationMechanics._target` Bypasses Epistemic Vision Freeze for Unseen Same-Layer Characters

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

`Perception.track` (`src/app/game/logic/modules/cognition/perception.py`) freezes `goal.position` at the target's last-known coordinates and sets `sprite.state.mutators.triggers.vision = False` whenever a same-layer `Goals.TARGET` or `Goals.SUBJECT` leaves `vision.radius`.

However, `NavigationMechanics._target` (`src/app/game/logic/mechanics/intentional/navigation.py`) unconditionally queries `board.asset(goal.name, sprite.state.layer)` for any Goal where `goal.category != Goals.POSITION` without checking `sprite.state.mutators.triggers.vision`:

```python
if goal.name and goal.category != Goals.POSITION:
    target_asset = board.asset(goal.name, sprite.state.layer) or \
                   board.asset(goal.name)
    if target_asset and target_asset.state.layer == sprite.state.layer:
        return self.anchor(target_asset)
```

Because `NavigationMechanics` steers directly toward the unseen character's live coordinates rather than the frozen `goal.position`:
1. Autonomous Sprites retain omniscient same-layer telepathy, tracking targets across the entire Layer outside `vision.radius`.
2. Unless the Sprite happens to cross its old `goal.position` en route to the live target, `is_near(sprite.goal.position, sprite.position, action.radius)` never evaluates to `True`, bypassing `target.lost` / `subject.lost` (`StoreResponse` and `ConfusionReflex`).

**Steps to Replicate** 

1. Deploy a Sprite at `(100, 100)` (`vision.radius = 150`, `intention = Intentions.HUNT`) with `goal = Goal(name="player", category=Goals.TARGET, layer=L, position=Position(200, 100))`.
2. Move `"player"` on Layer `L` to `(600, 400)` (outside `vision.radius`).
3. Run `CognitionMechanics.update()` followed by `NavigationMechanics.update()`.
4. Observe `sprite.state.mutators.triggers.vision == False` and `sprite.state.goal.position == Position(200, 100)`, yet `sprite.state.trajectory.target` points directly to `"player"`'s live position at `(600, 400)` instead of `(200, 100)`.

**Proposed Remeditation**

In `NavigationMechanics._target`, restrict live `board.asset(goal.name, ...)` anchor resolution for mobile Character goals (`Goals.TARGET`, `Goals.SUBJECT`) to ticks where `sprite.state.mutators.triggers.vision` is `True`. When `triggers.vision` is `False`, fall through to `goal.position` (offset by the Sprite's anchor displacement) so the Sprite navigates to the frozen last-known coordinate and cleanly resolves `lost` if the target is absent.

##### Bug B083: `Perception.track` Assigns Origin-Layer Door Coordinates (`state.position`) Instead of Destination-Layer Coordinates (`state.out`) on Observed Door Transit

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

Each Board Layer has an independent coordinate plane and dimensions. When a Door on `layer-1` at `state.position = (x1, y1)` leads to `state.outlayer = "layer-2"`, entities exiting the Door appear at `state.out = (x2, y2)` in `"layer-2"`'s coordinate plane.

In `Perception.track` (`src/app/game/logic/modules/cognition/perception.py`), when a Sprite witnesses its tracked `TARGET` or `SUBJECT` transit a visible Door, it updates `goal.layer` to `outlayer` while overwriting `goal.position` with the Door's **origin-layer** `state.position`:

```python
if observed_door is not None:
    goal.layer = observed_door.state.outlayer
    goal.position.x = observed_door.state.position.x
    goal.position.y = observed_door.state.position.y
```

`LayeredOutcome` then pushes this `goal` onto `memory.stack` and creates a separate `Goals.DOOR` Goal (which independently reads `target_door.state.position` for navigating on `layer-1`). Once the Sprite traverses the Door into `"layer-2"` at `(x2, y2)` and `Recall` pops the parent Goal from `memory.stack`, if the target is out of sight the Sprite pursues `(x1, y1)` inside `"layer-2"`—sending it to an unrelated coordinate or outside `"layer-2"`'s perimeters (causing immediate RRT stalls).

Additionally, because `Perception.track` does not record the observed transition in `memory.doors`, `DoorLocator` can route the Sprite into a different, closer unmapped Door on `layer-1` rather than the Door it just witnessed the target enter.

**Steps to Replicate** 

1. Place `Door_1` on `layer-1` (dimensions `1000x1000`) at `position = (800, 600)` with `outlayer = "layer-2"` (dimensions `320x240`) and `out = Position(50, 50)`.
2. Place a Sprite at `(750, 600)` on `layer-1` with `triggers.vision = True` tracking `"player"` at `(800, 600)`.
3. Move `"player"` through `Door_1` onto `layer-2` and out of sight (e.g., to `(280, 200)`).
4. Run `CognitionMechanics.update()` and inspect the parent Goal pushed onto `sprite.state.memory.stack`: `goal.layer == "layer-2"`, while `goal.position == Position(800, 600)`—far outside `layer-2`'s `320x240` boundaries.

**Proposed Remeditation**

In `Perception.track`, set `goal.position.x = observed_door.state.out.x` and `goal.position.y = observed_door.state.out.y` so the updated Goal coordinates belong to `observed_door.state.outlayer`, and record `state.memory.doors.setdefault(current_layer, {})[observed_door.name] = observed_door.state.outlayer` so `DoorLocator` routes directly through the witnessed Door.

##### Bug B084: Origin-vs.-Hitbox-Center Offset Causes `find -> interact` Deadlock Against Static Objects and Doors

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

`NavigationMechanics._target` (`src/app/game/logic/mechanics/intentional/navigation.py`) steers a Sprite's **hitbox center** (`anchor(sprite)`) toward a target Object or Door's **hitbox center** (`anchor(target)`). However, `find -> interact` (`src/data/configurations/automata/intentions/main.yaml`) and `InteractionMechanics._resolve_sprites` (`src/app/game/logic/mechanics/spatial/interaction.py`) evaluate `is_near(sprite.position, target.position, action.radius)` between **top-left canvas origins**.

In `src/assets/sheets/sprites/sprites.yaml`, Sprites (`jasilynn`, `archaxes`) have `64x64` frames with an inset hitbox at `(x=23, y=34, w=18, l=15)`—an anchor offset of `(+32, +41)` and hitbox bounds `[x+23, x+41) x [y+34, y+49)`. Between two identical `64x64` Sheets, these offsets cancel out; against a smaller `32x32` or `16x16` Object/Door whose hitbox starts at `(0, 0)`, the uncancelled offset causes permanent `find` deadlocks in two ways:

1. **Solid static Objects (`mass = 0`, e.g., `32x32` Chest/Sign at `(200, 200)` with hitbox `(0, 0, 32, 32)`) approached from North or West**:
   * Approaching from North, `CollisionMechanics` clamps `sprite.y + 49 <= 200` (`sprite.y <= 151`), enforcing a minimum origin distance of `dy >= 49 px`, exceeding both the default `action.radius = 30` and `jasilynn`'s `action.radius = 25`.
   * Approaching from West, `CollisionMechanics` clamps `sprite.x + 41 <= 200` (`sprite.x <= 159`), enforcing `dx >= 41 px > 30`.
   * The Sprite walks endlessly into the North/West face of the Object and can never satisfy `find -> interact`.
2. **Walkable Doors (`32x32` at `(200, 200)`, anchor `(216, 216)`) with `action.radius = 25` (or `16x16` Doors with `action.radius = 30`)**:
   * `NavigationMechanics` brings the Sprite's anchor `(sprite.x + 32, sprite.y + 41)` to exact overlap with the Door's anchor `(216, 216)`, stopping the Sprite at `sprite.position = (184, 175)`.
   * Origin distance is $\sqrt{(200 - 184)^2 + (200 - 175)^2} = \sqrt{881} \approx 29.68\text{ px} > 25\text{ px}$ (and $\sqrt{24^2 + 33^2} \approx 40.8\text{ px} > 30\text{ px}$ for a `16x16` Door).
   * The Sprite halts dead-center over the Door and never transitions `find -> interact`.

**Steps to Replicate** 

1. Place `jasilynn` (`dimensions = 64x64`, `hitbox = (23, 34, 18, 15)`, `action.radius = 25`) at `(184, 100)` with `intention = Intentions.FIND` and a `Goals.DOOR` Goal for a `32x32` Door (or `Goals.OBJECT` for a solid `32x32` Chest) at `(200, 200)` with hitbox `(0, 0, 32, 32)`.
2. Tick `NavigationMechanics`, `MotionMechanics`, `CollisionMechanics`, and `TransitionMechanics`.
3. Observe `jasilynn` stop at `(184, 175)` over the Door (`dist = 29.68 > 25`) or stop pressed against the Chest at `(184, 151)` (`dist = 51.5 > 30`) while `find -> interact` remains permanently `False`.

**Proposed Remeditation**

Align the proximity reference frame across `NavigationMechanics`, `intentions/main.yaml`, and `InteractionMechanics`: evaluate `action.radius` proximity between physical anchors (hitbox centers) or hitbox bounding boxes rather than raw top-left canvas origins, or compute anchor-compensated Goal arrival coordinates consistently across both transition and interaction checks.

##### Bug B085: Dead Sprites Continue Processing `TransitionMechanics`, `NavigationMechanics`, and `InteractionMechanics`

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

`CognitionMechanics.update` (`src/app/game/logic/mechanics/intentional/cognition.py`) skips dead Sprites (`if sprite.state.mutators.triggers.dead: continue`), leaving `sprite.state.goal` and `sprite.state.intention` intact while the death animation plays (`lpc-full` `die` runs 6 frames at `delay: 3` = 18 ticks before `RemoveMechanics` collects the entity).

However, three downstream Mechanics omit `triggers.dead` checks:
1. **`TransitionMechanics.update`** (`src/app/game/logic/mechanics/intentional/transition.py`): continues evaluating the Intention Transition Matrix on dead Sprites (e.g., transitioning `hunt -> attack` or `find -> interact`), and executes Step 3 (`Resolve Direction`), overwriting `sprite.state.animation.direction` to point toward `target_pos`. Because `src/data/configurations/assets/actions/main.yaml` defines `lpc-full`'s `die` row strictly for `directions: { up: { row: 20 } }`, rotating a dead Sprite's direction to `down`, `left`, or `right` causes `StateFrame.keys` (`src/app/assets/frames/sheets.py`) to emit unindexed Registry frame keys (`{id}-die-{down|left|right}-{frame}`).
2. **`NavigationMechanics.update` / `_navigate`** (`src/app/game/logic/mechanics/intentional/navigation.py`): continues running LOS/RRT planning and maintaining `sprite.state.trajectory.target` for dead Sprites in `NavigationIntentions`.
3. **`InteractionMechanics.update`** (`src/app/game/logic/mechanics/spatial/interaction.py`): builds `sprite_sources` and `player_sources` without excluding `triggers.dead`, allowing dying Sprites in `Intentions.INTERACT` (including ones transitioned post-mortem by `TransitionMechanics`) to teleport through Doors or trigger Chests, Signs, and Reactables.

**Steps to Replicate** 

1. Deploy a Sprite at `(100, 100)` with `intention = Intentions.FIND`, `goal = Goal(name="door-1", category=Goals.DOOR, layer=L, position=Position(100, 120))` (south of Sprite, within `action.radius`).
2. Set `sprite.state.mutators.triggers.dead = True` and `sprite.state.animation.action = Actions.DIE`, `direction = Directions.UP`.
3. Run `CognitionMechanics.update()`, `TransitionMechanics.update()`, `NavigationMechanics.update()`, and `InteractionMechanics.update()`.
4. Observe `TransitionMechanics` transition the dead Sprite `find -> interact` and overwrite `sprite.state.animation.direction` to `Directions.DOWN` (invalid for `lpc-full` `die` frame keys), followed by `InteractionMechanics` teleporting the dead Sprite through `door-1`.

**Proposed Remeditation**

Guard `triggers.dead` across all three Mechanics:
* In `TransitionMechanics.update`: skip ISL transition evaluation and direction updates when `sprite.state.mutators.triggers.dead` is `True` (keeping `action = Actions.DIE`, `direction = Directions.UP`, and `triggers.animated = True` so the death animation plays cleanly).
* In `NavigationMechanics._navigate`: if `sprite.state.mutators.triggers.dead`, call `self._clear(sprite)` and return immediately.
* In `InteractionMechanics.update`: exclude `asset.state.mutators.triggers.dead` from `sprite_sources` and `player_sources`.

##### Bug B086: Dead or Removed `Goals.SUBJECT` Characters Are Never Completed or Evicted (Corpse Conversations & Ghost Memory Leak)

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

Unlike `Goals.TARGET`, `Goals.SUBJECT` has no liveness or existence invalidation across the cognitive pipeline:
1. In `src/data/configurations/automata/goals/main.yaml`, `subject.complete` checks only `- not sprite.psyche.dialogue`.
2. In `Perception.track` (`src/app/game/logic/modules/cognition/perception.py`), `board.character(goal.name)` still finds a dead `SUBJECT` on the same Layer and sets `triggers.vision = True`. Because `find -> speak` and `follow -> speak` (`src/data/configurations/automata/intentions/main.yaml`) do not check `not sprites.get(sprite.goal.name).mutators.triggers.dead`, the Sprite walks up to the corpse and transitions into `speak`.
3. In `Perception.scan`, dead characters observed in `memory.goals` are only evicted when `mem_goal.category == Goals.TARGET`, leaving dead `Goals.SUBJECT` entries in `memory.goals`.
4. Once `RemoveMechanics` removes the dead `SUBJECT` from the Board, `board.character(goal.name)` returns `None`, `triggers.vision` becomes `False`, and upon reaching `goal.position` (or stalling), `subject.lost` executes `StoreResponse`—permanently leaking a dormant ghost `Goal` for a deleted character in `memory.goals`.

**Steps to Replicate** 

1. Give a Sprite `psyche.dialogue = "greeting"`, `memory.relationships["ally"] = Relationships.FRIEND`, and `goal = Goal(name="ally", category=Goals.SUBJECT, layer=L, position=Position(110, 100))`.
2. Set `ally.state.mutators.triggers.dead = True` and tick `CognitionMechanics` and `TransitionMechanics` — observe the Sprite retain `vision = True` and transition `find -> speak` to the dead character.
3. Remove `"ally"` from the Board and tick `CognitionMechanics` — observe `subject.lost` fire `StoreResponse` and permanently store `"ally"` into `sprite.state.memory.goals` instead of forgetting it.

**Proposed Remeditation**

* Update `subject.complete` in `src/data/configurations/automata/goals/main.yaml` to include `not sprites.get(sprite.goal.name) or sprites.get(sprite.goal.name).mutators.triggers.dead` (so missing/dead Subjects execute `forget` cleanly without clearing `psyche.dialogue`, enabling `SocialInstinct` to target another living ally).
* In `Perception.scan`, evict observed dead characters from `memory.goals` for both `Goals.TARGET` and `Goals.SUBJECT`.
* In `src/data/configurations/automata/intentions/main.yaml`, add `sprites.get(sprite.goal.name)` and `not sprites.get(sprite.goal.name).mutators.triggers.dead` to `find -> speak` and `follow -> speak`.

##### Bug B087: `DoorLocator` Ignores `Perception._stalled_doors`, Blocking Fallback to Alternate Doors After a Door Stall

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

To resolve **B081**, `CognitionMechanics._resolve` (`src/app/game/logic/mechanics/intentional/cognition.py`) records stalled doors in `Perception._stalled_doors` via `self.perception.mark_stalled_door(...)`, preventing `Perception._wake_cross_layer` from re-waking dormant cross-layer Goals on that same blocked door.

However, `DoorLocator.locate` (`src/app/game/logic/modules/cognition/goals/locators.py`) has no awareness of stalled doors and strictly selects either (1) the shortest mapped route in `memory.doors` or (2) the nearest unmapped Door within `vision.radius`. If a blocked Door `Door_A` is closer to the Sprite (or mapped in `memory.doors`) when a second reachable Door `Door_B` enters `vision.radius`, `Perception._wake_cross_layer` wakes the cross-layer Goal on sighting `Door_B`, `Recall` pops it, and Stage 4 `Sync` invokes `DoorLocator.locate()`, which re-selects the blocked `Door_A` instead of `Door_B`.

**Steps to Replicate** 

1. Place a Sprite at `(120, 100)` (`vision.radius = 150`) on `layer-1` with a cross-layer Goal `G` (`layer-2`), an impassably walled-off unmapped `Door_A` at `(100, 100)`, and a reachable unmapped `Door_B` at `(280, 100)` (initially outside `vision.radius`).
2. Allow `DoorLocator` to select `Door_A`, RRT to stall, and `door.lost` to unwind `G` and call `perception.mark_stalled_door(sprite.name, "layer-1", "Door_A")`.
3. Move the Sprite east to `(140, 100)` so `Door_B` enters `vision.radius` (distance `140`) while `Door_A` remains closer (distance `40`).
4. Observe `Perception._wake_cross_layer` wake `G`, `Recall` pop `G`, and `DoorLocator.locate()` select the blocked `Door_A` again instead of `Door_B`.

**Proposed Remeditation**

Pass per-sprite stalled-door exclusions into `DoorLocator` (e.g., via `ResolutionContext` or a shared layer-scoped blocked-door set cleared upon Layer transition or backoff expiry) and filter excluded Doors in both `DoorLocator._route` and the unmapped-door fallback so `DoorLocator` cleanly falls back to reachable alternate Doors (or returns `None` when all candidate Doors are stalled).

##### Bug B088: Same-Layer Dormant Static Goals (`OBJECT`, `RESOURCE`, `PROPERTY`) Stored on Stall Never Wake Without a Layer Change

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/data/configurations/automata/goals/main.yaml`, `object.lost`, `resource.lost`, and `property.lost` execute `responses: [ store ]` on `sprite.trajectory.stalled`, setting `goal.dormant = True` and storing the Goal in `sprite.state.memory.goals`.

However, `Perception.scan` (`src/app/game/logic/modules/cognition/perception.py`) iterates exclusively over `board.characters()` when waking same-layer dormant `memory.goals`, and `Perception._wake_cross_layer` skips all same-layer Goals unless `layer_changed` is `True`:

```python
if layer_changed and mem_goal.layer == current_layer:
    mem_goal.dormant = False
    continue

if not mem_goal.layer or mem_goal.layer == current_layer:
    continue
```

Consequently, if a Sprite temporarily stalls trying to reach a same-layer Chest, Resource, or Property (e.g., due to a closed Gate, movable Crate, or passing Sprite), the Goal is stored dormant and can never wake again—even after the obstruction clears and the Sprite stands directly beside it—unless the Sprite leaves the Layer through a Door and returns. Missing/harvested `OBJECT` and `RESOURCE` entries stored in `memory.goals` are also never evicted by `Perception.scan`.

**Steps to Replicate** 

1. Assign a Sprite a same-layer `Goals.OBJECT` (e.g., a Chest on `layer-1`) temporarily blocked by a closed Gate or obstacle.
2. Allow RRT to stall so `object.lost` executes `StoreResponse` (`goal.dormant = True` in `memory.goals`).
3. Open the Gate / remove the obstacle and position the Sprite within `vision.radius` of the Chest on `layer-1`.
4. Tick `CognitionMechanics.update()` indefinitely and observe `memory.goals[chest.name].dormant` remains `True` permanently and is never recalled.

**Proposed Remeditation**

Extend `Perception.scan` to inspect same-layer `memory.goals` with `category in (Goals.OBJECT, Goals.RESOURCE, Goals.PROPERTY)` against `board.states(current_layer)`: evict removed `OBJECT`/`RESOURCE` entries when observed absent within `vision.radius`, and wake stalled static Goals via a stall-guarded wake condition (e.g., backoff cooldown or re-entry into `vision.radius` after moving away, preventing **B081**-style per-tick stall–store–wake oscillation).

##### Bug B089: `NavigationMechanics._clear` Preserves Stale `trajectory.cooldown` Across Distinct Goals

**STATUS**: OPEN
**SEVERITY**: LOW

**Description**

When `NavigationMechanics._plan` (`src/app/game/logic/mechanics/intentional/navigation.py`) fails to find an RRT path, it sets `sprite.state.trajectory.stalled = True` and `sprite.state.trajectory.cooldown = settings.PATH_RETRY_INTERVAL`.

On the next tick, `CognitionMechanics` resolves the stalled Goal as `lost` (clearing `goal = None`), `TransitionMechanics` returns the Sprite to `Intentions.IDLE`, and `NavigationMechanics._navigate` calls `self._clear(sprite)`:

```python
def _clear(self, sprite: Asset) -> None:
    sprite.state.trajectory.target = None
    sprite.state.trajectory.vertices.clear()
    sprite.state.trajectory.stalled = False
```

Because `_clear` does not reset `sprite.state.trajectory.cooldown = 0`, the previous Goal's retry backoff leaks onto whatever **new** Goal the Sprite next acquires (including an urgent `SurvivalInstinct` `escape` Goal or a freshly popped `memory.stack` Goal). If line of sight to the new Goal is occluded, `_navigate` decrements the stale `cooldown` and leaves the Sprite frozen with `trajectory.target = None` for up to `PATH_RETRY_INTERVAL` ticks before planning.

**Steps to Replicate** 

1. Stall a Sprite's RRT on an unreachable `Goal_1` so `trajectory.stalled = True` and `trajectory.cooldown = settings.PATH_RETRY_INTERVAL`.
2. Let `Goal_1` resolve as `lost`, return to `IDLE`, and run `NavigationMechanics.update()` (`_clear` runs while `cooldown` stays non-zero).
3. Assign a brand-new, reachable `Goal_2` (e.g., an `escape` or `wander` Goal) behind a small obstacle (occluded direct LOS).
4. Tick `NavigationMechanics.update()` and observe `_navigate` return early without calling `_plan` until the stale `cooldown` from `Goal_1` counts down to `0`.

**Proposed Remeditation**

Reset `sprite.state.trajectory.cooldown = 0` inside `NavigationMechanics._clear(sprite)`. (`_clear` is never called along the active occluded-cooldown backoff branch—only when ceasing navigation, handling cross-layer goals, handling missing targets, or acquiring clear LOS.)