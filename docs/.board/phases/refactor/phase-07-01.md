#### Refactor: Phase 07.01 Speak Intention

**CURRENT FOCUS**: `speak` entrypoints and exitpoints. Consider the conditions for transition and the logical flow of the intention states themselves. Are there any missing entry or exit points? Do any conditions need added to the transition matrix (for `speak` and connected nodes; ignore other areas for now)?

**Goal**: Implement the `speak` Intention. Unify the Expression pipeline using "Phantom State" data overlays. Isolate linguistic interactions into a dedicated Mechanic. Resolve Goal Acquisition logic and memory bugs.

Expressions (Cursors) are not physical `Asset` objects on the `Board`. Because they are purely visual decorators, they operate as "Phantom States."

* **Indexing**: Expressions will utilize the existing IndexFrame (used by Widgets) for indexing in the Registry.
* **Generation**: When an expression is triggered, the `Cradle` calculates the optimal spatial offsets using the target's dimensional properties and returns a pure data structure (`AttachmentState`).
* **Rendering**: The `Frame.keys()` interface is upgraded to yield a `List[Tuple[str, int, int]]` (key, offset_x, offset_y). `SpriteFrame` reads the `AttachmentState` embedded in the Sprite's `Psyche` state and dynamically appends the tuple. The Cython `Screen` unpacks these offsets and applies them natively to the destination coordinates, achieving zero-allocation overlay rendering without VRAM padding or complex state-syncing loops.

##### Goal: Phantom States

**Step A: Update the Interface (`app.assets.base.py`)**

Modify the abstract method to return a tuple:

```python
class Frame(ABC):
    @abstractmethod
    def keys(self, state: AssetState) -> List[Tuple[str, int, int]]:
        """Returns a list of tuples: (frame_key, offset_x, offset_y)"""
        pass

```

**Step B: Implement Dynamic Offsets (`app.assets.frames.py`)**

Update all standard frames (`SingleFrame`, `StateFrame`, etc.) to return `[(key, 0, 0)]`.
Then, specialize the `SpriteFrame` to calculate the expression offset dynamically:

```python
class SpriteFrame(StateFrame):
    def keys(self, state: AssetState) -> List[Tuple[str, int, int]]:
        frame_keys = super().keys(asset) 
        
        # Start with the base Persona frame key
        frame_keys = super().keys(id, state)
        
        # Iterate over active equipment in strict Z-index order: Base -> Armor -> Utility -> Tool -> Weapon
        if state.inventory.equipment:
            eq = state.inventory.equipment
            for eq_key in (eq.armor, eq.utility, eq.tool, eq.weapon, eq.shield):
                if eq_key:
                    key_str = settings.SEPARATOR.join([
                        eq_key,
                        state.animation.action,
                        state.animation.direction,
                        str(state.animation.frame)
                    ])
                    frame_keys.append((key_str, 0, 0))

        # Expressions
        if state.psyche.expression:
            expr_key = f"bubbles-{state.psyche.expression}"
            
            # Dynamically anchor to the top-right of the specific Sprite instance
            ox = state.psyche.expressions.offset.x  
            oy = state.psyche.expressions.offset.y
            
            frame_keys.append((expr_key, ox, oy))

        # logging

        return frame_keys

```

**Step C: Inject Offsets in the Renderer (`app.game.screen.py`)**

Update the inner loops of `Screen._prerender` and `Screen.draw` to unpack the 3-tuple and apply the offset to the hardware destination coordinates:

```python
# Inside Screen.draw()
frame_keys = asset.frame.keys(asset)

for frame_key, ox, oy in frame_keys:
    tex_data = self.registry.image(frame_key)
    if not tex_data: continue
    
    tex, sx, sy, sw, sl = tex_data
    
    # Apply dynamic offset
    dx = asset.state.position.x + ox
    dy = asset.state.position.y + oy
    dw, dl = sw, sl
```

- *The Ripple Effect:* Upgrading `Frame.keys()` to return a `List[Tuple[str, int, int]]` alters a fundamental interface. `Screen.interface` (Widgets) and `Screen.stamp` (Text mapping) also rely on `Frame.keys()`. If they aren't updated to unpack `(key, ox, oy)`, the moment the engine attempts to render a Menu or HUD, it will throw a `ValueError` trying to pass a tuple to `Registry.image(key)`.

**Step D: Spawn Expression**

```python
def spawn_expression(self, expression_id: str, expression_key: str, target: Asset) -> AttachmentState:
    """
    expression_id: 'bubbles'
    expression_key: 'loquacity'
    """
    properties = self.spawnables.expressions.get(expression_id)
    
    # Calculate top-right anchor
    ox = target.dimensions.w - properties.dimensions.w
    oy = -properties.dimensions.l
    
    return AttachmentState(
        key=f"{expression_id}-{expression_key}", 
        offset=Position(x=ox, y=oy)
    )
```

##### Tasks


**1. Task: Establish the "Phantom State" Expression Architecture**

*Objective*: Upgrade the rendering pipeline to support nested offsets and implement data-driven Expression tracking.

* [ ] Subtask: Update `app.assets.base.Frame.keys()` signature to `def keys(self, id: str, state: AssetState) -> List[Tuple[str, int, int]]:`.
* [ ] Subtask: Update `SingleFrame`, `IterableFrame`, `StateFrame` and Widget frames to yield `(key, 0, 0)`.
* [ ] Subtask: Update `Screen._prerender` and `Screen.draw` to unpack `frame_key, ox, oy` and apply the offsets directly to `dx, dy`.
* [ ] Subtask: Create `AttachmentState` dataclass (key, offset, dimensions) and add it to `app.models.state.sprites.Psyche` as `expression: Optional[AttachmentState]`.
* [ ] Subtask: Implement `Cradle.calculate_expression(self, id: str, key: str, target: Asset) -> AttachmentState`, executing the geometric math (e.g., top-right anchoring) purely through properties.
* [ ] Subtask: Update `SpriteFrame.keys` to check `state.psyche.expression` and append its pre-calculated tuple.


**2. Task: Resolve Memory Goal Architecture**

*Objective*: Align the data models and `CognitionMechanics` to support nested, interruptible goals.

* [ ] Subtask: Update `app.models.state.sprites.Memory` to type `goals` as `List[Goal] = field(default_factory=list)`.
* [ ] Subtask: Update `CognitionMechanics._resolve_goal` to use `.pop()` to retrieve the most recent goal when `sprite.state.goal` resolves to `None`.
* [ ] Subtask: Update `/src/data/config/intentions/main.yaml` ISL conditions to safely check `sprite.memory.goals` instead of a scalar attribute.

**3. Task: Implement `SocialMechanics`**

*Objective*: Create a dedicated mechanic for processing communicative Intention data transfers.

* [ ] Subtask: Create `SocialMechanics` inheriting from `Mechanic`.
* [ ] Subtask: Implement logic to filter Sprites with `SPEAK`, `BARTER`, and `THREATEN` Intentions.
* [ ] Subtask: Implement radial proximity checks using `is_near` against the Sprite's Goal position.
* [ ] Subtask: Implement NPC-to-NPC logic: transfer `psyche.dialogue` to target's `memory.rumors`, set source `psyche.expression = 'LOQUACITY'`, and set source `psyche.dialogue = None`.
* [ ] Subtask: Implement Player-to-NPC logic: construct and push `MenuEvent('dialogue', ...)` to the `bus` to pause the world and render the UI.
* [ ] Subtask: Register `social` in `/src/data/config/mechanics/main.yaml` under the `world` pipeline.

**4. Task: Flesh out Goal Acquisition (`CognitionMechanics`)**

*Objective*: Implement the target acquisition strategies defined by the `Motivations` enum.

* [ ] Subtask: Implement `PROFIT`: scan `board.renderables()` for Assets classified as `CHESTS` or mineable resources; assign `Goals.ASSET` or `Goals.LOOT`.
* [ ] Subtask: Implement `SURVIVAL`: calculate paths to healing items or safe zones.
* [ ] Subtask: Implement `REVENGE`: identify and target Sprites that recently triggered the `struck` mutator.

**5. Task: Refine Animation States for Stationary Intentions**

*Objective*: Flesh out `Motivations` and prevent stationary Sprites from playing walking animations.

* [ ] Subtask: Update `AnimationMap.action` to return `Actions.CAST` (serving as a physical gesture) for communicative Intentions, preventing the "Stationary Moonwalking" glitch.
* [ ] Subtask: Update `TransitionMechanics` to only evaluate `mutators.triggers.animated = True` if the Sprite has active velocity or an explicitly animated action, rather than a blanket catch-all.
* [!] Subtask: Flesh out `PROFIT` in `CognitionMechanics._acquire_target` by querying `board._cached_objects` for unlooted `CHESTS` and mapping them to `Goals.ASSET`.
    * NOTE: Future refactor. Focus on `speak` now.
* [!] Subtask: Flesh out `SURVIVAL` in `CognitionMechanics` by mapping to `Goals.POSITION` (safe zones) or `Goals.LOOT` (health items).
    * NOTE: Future refactor. Focus on `speak` now.

**6. Task: Resolve Architectural Discrepancies & Bugs**

* [ ] Subtask: Introduce `_cached_objects: Dict[str, Asset]` to `app.game.board` alongside `_cached_characters` to provide $O(1)$ lookups for `Goals.ASSET` tracking in `CognitionMechanics`.
* [~] Subtask: Refactor `CognitionMechanics`, `TransitionMechanics`, and `AnimationMap` to replace `getattr(state, 'field', None)` anti-patterns with direct namespace access, relying on Pydantic's guaranteed data schemas.















---

### 1. Architectural Assessment & Design Review

**The "Phantom State" Pipeline (Expressions)**
Your decision to use `AttachmentState` embedded in `sprite.psyche.expression` is the right move for a data-driven ECS. It prevents the `Board` and `MotionMechanics` from being bogged down by thousands of ephemeral entities.

*The Ripple Effect:* Upgrading `Frame.keys()` to return a `List[Tuple[str, int, int]]` alters a fundamental interface. The current Task Board only mentions updating `Screen._prerender` and `Screen.draw`. But `Screen.interface` (Widgets) and `Screen.stamp` (Text mapping) also rely on `Frame.keys()`. If they aren't updated to unpack `(key, ox, oy)`, the moment the engine attempts to render a Menu or HUD, it will throw a `ValueError` trying to pass a tuple to `Registry.image(key)`.

**SocialMechanics & The "1-Frame Conversation" Problem**
There is a temporal gap in the `speak` Intention logic.

1. Tick 1: A Sprite enters the `speak` intention.
2. Tick 1: `SocialMechanics` fires, transfers `dialogue` to the target, sets `source.psyche.dialogue = None`, and sets the `LOQUACITY` expression.
3. Tick 2: `TransitionMechanics` fires. The ISL checks `not sprite.psyche.dialogue` (which is now `True`). The Sprite immediately transitions out of `speak` into `idle` (or `return`).

*Result:* The conversation and the `LOQUACITY` speech bubble exist for exactly one game tick (approx. 16ms at 60 FPS). The player will never actually see the dialogue occur. We need a temporal anchor. The `SocialMechanics` needs to either wait for an `AnimationState` to complete its cycle (e.g., the `CAST` action), or `AttachmentState` needs an explicit time-to-live (`ttl: int`) that ticks down before the dialogue is wiped.

**Goal Memory Type Constraints**
The specification intends for `memory.goals` to operate as a stack (using `.pop()`), allowing Sprites to interrupt long-term motivations for short-term survival or interactions. However, `app.models.state.sprites.Memory` currently types `goals` as `Optional[Goal] = None`. It must be refactored into a `List[Goal]` to support list operations, or the `CognitionMechanics` update will crash.

**Trusting Pydantic (The `getattr` Anti-Pattern)**
As you noted, `getattr(state, 'field', None)` litters the codebase (e.g., `AnimationMap.action`, `Screen.draw`, `Cradle`). Because Pydantic strictly validates the YAML configuration upon loading, these data models are guaranteed to exist with their default values. Direct namespace access (`state.inventory.equipment.weapon`) is not only safer but faster, saving valuable nanoseconds in the hot loops.

---

### 2. Bugs & Logical Flaws (Bug Report)

Before writing the code, the following flaws need to be accounted for in the backlog:

1. **ISL / Spec Contradiction:**
* *The Docs (`00-speak.md`):* States the Sprite transitions from `speak` $\to$ `return`.
* *The YAML (`main.yaml`):* States the Sprite transitions from `speak` $\to$ `follow` or `idle`.
* *Resolution:* The YAML must be reconciled with the design document.


2. **ISL KeyError:**
In `main.yaml`, the `find` $\to$ `speak` transition uses:
`- sprite.memory.relationships[sprite.goal.name] in [...]`
If the target Sprite isn't in the `relationships` dictionary, the Python AST will raise a `KeyError` and crash the execution thread. It must be rewritten as:
`- sprite.memory.relationships.get(sprite.goal.name) in [...]`
3. **Registry Caching Fallback:**
In `Screen.interface`, the engine currently expects `widget.frame.keys()` to return strings. If the interface is updated to tuples, `base_keys[0]` in `Screen.stamp` will extract a tuple, not a string, breaking the `registry.image()` lookup.

---

### 3. Task Board Grooming

I have reworked Phase 07.01 of the Task Board to respect the architecture, fix the timing issues, and handle the UI pipeline regressions.

```markdown
#### Refactor: Phase 07.01 Speak Intention

**CURRENT FOCUS**: `speak` entrypoints and exitpoints. Unify the Expression pipeline using "Phantom State" data overlays. Isolate linguistic interactions into a dedicated Mechanic. Resolve Goal Acquisition logic and memory bugs.

##### Tasks

**1. Task: Establish the "Phantom State" Expression Architecture**
*Objective*: Upgrade the rendering pipeline to support nested offsets without breaking Widgets and Tiles.
* [ ] Subtask: Update `app.assets.base.Frame.keys()` signature to `def keys(self, id: str, state: AssetState) -> List[Tuple[str, int, int]]:`.
* [ ] Subtask: Update all base Frame implementations (`SingleFrame`, `IterableFrame`, `StateFrame`, `TraversalFrame`, `MeterFrame`, `IndexFrame`) to yield `(key, 0, 0)`.
* [ ] Subtask: Update `Screen._prerender` (Tiles), `Screen.draw` (World), `Screen.interface` (Widgets), and `Screen.stamp` (Text) to unpack the 3-tuple `(frame_key, ox, oy)` before querying the Registry.
* [ ] Subtask: Create `AttachmentState` dataclass (`key: str`, `offset: Position`, `ttl: int = 120`) and add it to `Psyche` as `expression: Optional[AttachmentState] = None`.
* [ ] Subtask: Implement `Cradle.spawn_expression(...) -> AttachmentState`, calculating top-right anchoring based on target dimensions.
* [ ] Subtask: Update `SpriteFrame.keys` to check `state.psyche.expression` and append its pre-calculated tuple.

**2. Task: Resolve Memory Goal Architecture**
*Objective*: Align the data models and `CognitionMechanics` to support nested, interruptible goals.
* [ ] Subtask: Update `app.models.state.sprites.Memory` to type `goals` as `List[Goal] = field(default_factory=list)`.
* [ ] Subtask: Update `CognitionMechanics._resolve_goal` to use `.pop()` to retrieve the most recent goal when `sprite.state.goal` resolves to `None`.
* [ ] Subtask: Update `/src/data/config/intentions/main.yaml` ISL conditions to safely evaluate `sprite.memory.goals` as a list rather than a scalar attribute.

**3. Task: Implement `SocialMechanics` (With Temporal Anchors)**
*Objective*: Create a dedicated mechanic for processing communicative Intention data transfers while preventing 1-frame glitches.
* [ ] Subtask: Create `SocialMechanics` inheriting from `Mechanic`. Register in `mechanics/main.yaml` under the `world` pipeline.
* [ ] Subtask: Implement logic to filter Sprites with `SPEAK`, `BARTER`, and `THREATEN` Intentions.
* [ ] Subtask: Implement NPC-to-NPC logic: transfer `psyche.dialogue` to target's `memory.rumors`, set source `psyche.expression = Cradle.spawn_expression(...)`.
* [ ] Subtask: **[Fix]** Implement tick-decay on `psyche.expression.ttl`. Set `psyche.dialogue = None` *only* when `ttl <= 0` to ensure the conversation renders before the ISL forces an Intention transition.
* [ ] Subtask: Implement Player-to-NPC logic: push `MenuEvent('dialogue', ...)` to the `bus` to pause the world and render the UI.

**4. Task: Refine Animation States & ISL Matrix**
*Objective*: Fix stationary Intentions and apply defensive programming to the runtime ISL.
* [ ] Subtask: Update `AnimationMap.action` to map communicative Intentions to `Actions.CAST`, preventing stationary Sprite moonwalking.
* [ ] Subtask: Update `TransitionMechanics` to only evaluate `mutators.triggers.animated = True` if the Sprite has active velocity or an explicitly animated action.
* [ ] Subtask: **[Fix]** Update `intentions/main.yaml` to route `speak` -> `return` matching the `00-speak.md` specification.
* [ ] Subtask: **[Fix]** Update `intentions/main.yaml` to use `.get()` on relationship dictionaries (`sprite.memory.relationships.get(sprite.goal.name) in [...]`) to prevent runtime KeyErrors.

**5. Task: Eradicate Anti-Patterns**
*Objective*: Leverage Pydantic's strict validation to speed up the execution loops.
* [ ] Subtask: Refactor `CognitionMechanics`, `TransitionMechanics`, `AnimationMap`, and `Screen` to replace `getattr(state, 'field', None)` with direct namespace accesses.

```

### 4. Suggested Documentation Updates

To bring the documentation in line with the required architectural changes:

* **Update `00-speak.md` (Workflow Section):**
Explicitly define the temporal delay.
*Current:* "It immediately changes it state.psyche.expression to LOQUACITY... The Sprite stays in the speak Intention for the next game tick."
*Proposed Change:* "It immediately injects an `AttachmentState` into `state.psyche.expression` configured with a Time-To-Live (TTL). The `SocialMechanics` decrements this TTL every game tick. The `state.psyche.dialogue` variable is only nulled, triggering an exit from the `speak` intention, once the TTL reaches zero. This guarantees the expression is rendered long enough for the Player to observe the interaction."