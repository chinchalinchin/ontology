#### Implement: Phase III - Finetuning

Current keyboard mappings are given by,

```yaml
mappings:
  keyboard:
    intentions:
      interact: 44  # SDL_SCANCODE_SPACE
      sprint: 225   # SDL_SCANCODE_LSHIFT
      speak:
      build: 
      mine: 
      attack:
    goals:
      up: 26    # SDL_SCANCODE_W
      down: 22  # SDL_SCANCODE_S
      left: 4   # SDL_SCANCODE_A
      right: 7  # SDL_SCANCODE_D
```

**Goals:**

- Ensure animations are smooth, i.e. FPS and UPS is well-balanced.
- Ensure player only animates when input is provided or player is otherwise locked into a state (i.e. swinging a sword in `slash`). Same applies to non-player Sprites.
- Ensure keyboard mappings translate to state changes.

**Current Problems:**

- Player sprite animates as soon as engine boots. The intended function `mutators.triggers.animated` does not exist in the data schema.

**1. Task: Resolve Critical Initialization Exceptions**

*Objective*: Fix schema and enum misalignments preventing engine loop execution.
- [x] Subtask: Add `POSITION` to the `GoalCategories` Enum in `app/config/enums.py`.
- [!] Subtask: Update `Board.player()` to use `.get()` with safe list checking to prevent `KeyError` exceptions when evaluating the `PLAYERS` instance array. (CLOSED: There is currently no reason for the board to exist without a player.)
- [ ] Subtask: Update `AnimationMap.action()` to explicitly handle the `IDLE` intention, returning a locked `WALK` action but preparing the state for frame 0.

**2. Task: Reconcile Mutator Schemas & Implement Animation Triggers**

*Objective*: Allow Sprites to halt animation cycles based on behavioral state.
- [ ] Subtask: Modify `app.models.state.Mutators` to include `triggers: Dict[str, bool]` as dictated by the documentation.
- [ ] Subtask: Update `PlayerMechanics` to set `player.state.mutators.triggers['animated'] = has_movement`. Ensure this evaluation ignores movement if the player is locked in a non-interruptible action (e.g., `attack`).
- [ ] Subtask: Update `StateAnimation.animate()` in `app/assets/animations.py` to check `state.mutators.triggers.get('animated', True)`. If False, force `state.animation.frame = 0` and bypass the increment calculation.

**3. Task: Resolve Cartesian Motion Mechanics**

*Objective*: Standardize velocity calculations to prevent diagonal speed exploitation.

- [ ] Subtask: Refactor `MotionMechanics.update()` to calculate the Euclidean distance to the goal. Normalize the $dx, dy$ components into a unit vector, then multiply by `speed` before applying the positional translation.

**4. Task: Implement Rendering Constraint (Frame Limiter)**

*Objective*: Stop the engine from busy-waiting and rendering visually redundant frames.

- [x] Subtask: Introduce a `TARGET_FPS` configuration into `app.config.settings` (e.g., 60 or 144).
- [ ] Subtask: Update app.game.engine.Engine.start() to track a render_accumulator or sleep delta. If the time elapsed since the last draw() call is less than 1.0 / target_fps, invoke time.sleep() or an equivalent SDL yield to release the CPU thread back to the operating system.