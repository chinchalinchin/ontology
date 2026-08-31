# Bug B000: Attacking

**Status:** CLOSED
**Resolution:** PATCHED

When pressing the Space Bar to attack, the player briefly (*very* briefly, less than a fraction of a second) enters into the appropriate Action, but immediately returns to the Walk Action.

**Initial Analysis**

It appears as though there needs to be a check in PlayerMechanics to prevent the Player intention from being overwritten when the Player is in a "blocking" Action.

Blocking Actions are: `cast`, `slash`, `thrust`, `shoot`

- Initial Proposed Solution: Add an `busy` mutator to the Sprite state. Add a check on the Player `update()` method to prevent Intention overwriting during blocked states. When Player enters these actions, set `busy` to `True`. Need to be careful to flip it off when action is concluded.

**Summary of Changes:**

1. **Intention Persistence:** Modified `PlayerMechanics` to respect blocking intentions (e.g., `ATTACK`, `MINE`). Replaced the unconditional `IDLE` fallback with a frame-aware check that only releases the player once the action's animation sequence completes (`frame == 0`).
2. **Registry Mapping Alignment:** Corrected the dimension properties for `shortsword` and other affected equipment in `sheets/main.yaml`. Equipment dimensions must match the parent sprite (e.g., `64x64`) to align with the `lpc-slash` coordinate mapping.

**Lessons Learned:**

* **Intrinsic State over Redundant Flags:** Avoid adding boolean flags (like `busy`) when the state is already mathematically represented by existing structures (`animation.frame > 0` during a blocking intention).
* **Cython/SDL Silent Failures:** C-level renderers inherently fail silently when fed mathematically impossible bounds. If a mapped coordinate asks SDL to crop a 64x64 square starting at Y=480 on a 32x32 image, the GPU yields an empty texture rather than a traceback. Telemetry and Registry introspection tools are mandatory for debugging the Python-to-C boundary.








### Controlling Animation Speed

Currently, `StateAnimation.animate()` advances `state.animation.frame` by exactly `1` every single game tick. If your engine runs at 60 UPS (Updates Per Second), a 6-frame slash animation finishes in a blistering 0.1 seconds.

To slow down specific actions without dropping the global engine tick rate or affecting the `walk` cycle, you must decouple the *game tick* from the *animation frame* using a data-driven **Ticks-Per-Frame (TPF)** approach.

Here is the implementation path:

#### 1. Update the Data Models

Add a `tick` accumulator to the dynamic state, and a `delay` (or `tpf`) property to the static configuration.

**File:** `/src/app/models/state.py`

```python
@dataclass(slots=True)
class AnimationState:
    action: str = Actions.WALK.value
    direction: str = Directions.DOWN.value
    frame: int = 0
    tick: int = 0  # Accumulates engine ticks

```

**File:** `/src/app/models/properties.py`

```python
@dataclass(slots=True)
class Action:
    count: int
    directions: Dict[str, Direction]
    delay: int = 1  # Number of engine ticks required to advance 1 frame

```

#### 2. Update the Animation Logic

Modify the animation strategy to check the accumulator against the configured delay.

**File:** `/src/app/assets/animations.py`

```python
class StateAnimation(Animation):
    """
    Advances frame based on configured action delay.
    """
    def animate(self, state: AssetState, properties: AssetProperties) -> AssetState:
        if hasattr(state, 'mutators') and state.mutators and hasattr(state.mutators, 'triggers'):
            if not state.mutators.triggers.animated:
                state.animation.frame = 0
                state.animation.tick = 0
                return state

        action_props = properties.actions[state.animation.action]
        delay = getattr(action_props, 'delay', 1)

        state.animation.tick += 1

        # Only advance the frame if the tick accumulator reaches the delay threshold
        if state.animation.tick >= delay:
            state.animation.tick = 0
            state.animation.frame += 1

            if state.animation.frame >= action_props.count:
                state.animation.frame = 0

        return state

```

#### 3. Update the YAML Configuration

You can now define specific speeds for specific actions. At 60 UPS, a delay of `4` means the frame updates 15 times per second.

**File:** `/src/data/config/actions/main.yaml`

```yaml
actions:
  - id: lpc-slash
    data:
      slash:
        count: 6
        delay: 4  # Slows down the slash animation
        directions:
          up:
            row: 12
          # ...
  - id: lpc-shoot
    data:
      shoot:
        count: 13
        delay: 3  # Adjust independently of slash
        directions:
          # ...

```