#### Refactor: Phase 07.01 Speak Intention

**Goal**: Implement the `speak` Intention. Flesh out Sprite Goal Acquisition. Expand Sprite Finite Automata.

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

##### Tasks

**1. Task: Resolve Memory Goal Architecture**

*Objective*: Align the data models and `CognitionMechanics` to support nested, interruptible goals.

* [ ] Subtask: Update `app.models.state.sprites.Memory` to type `goals` as `List[Goal] = field(default_factory=list)`.
* [ ] Subtask: Update `CognitionMechanics._resolve_goal` to use `.pop()` to retrieve the most recent goal when `sprite.state.goal` resolves to `None`.
* [ ] Subtask: Update `/src/data/config/intentions/main.yaml` ISL conditions to safely check `sprite.memory.goals` instead of a scalar attribute.

**2. Task: Implement `SocialMechanics`**

*Objective*: Create a dedicated mechanic for processing communicative Intention data transfers.

* [ ] Subtask: Create `SocialMechanics` inheriting from `Mechanic` (not `SpatialMechanic`).
* [ ] Subtask: Implement logic to filter Sprites with `SPEAK`, `BARTER`, and `THREATEN` Intentions.
* [ ] Subtask: Implement radial proximity checks using `is_near` against the Sprite's Goal position.
* [ ] Subtask: Implement NPC-to-NPC logic: transfer `psyche.dialogue` to target's `memory.rumors`, set source `psyche.expression = 'LOQUACITY'`, and set source `psyche.dialogue = None`.
* [ ] Subtask: Implement Player-to-NPC logic: construct and push `MenuEvent('dialogue', ...)` to the `bus` to pause the world and render the UI.
* [ ] Subtask: Register `speech` in `/src/data/config/mechanics/main.yaml` under the `world` pipeline.

**3. Task: Flesh out Goal Acquisition (`CognitionMechanics`)**

*Objective*: Implement the target acquisition strategies defined by the `Motivations` enum.

* [ ] Subtask: Implement `PROFIT`: scan `board.renderables()` for Assets classified as `CHESTS` or mineable resources; assign `Goals.ASSET` or `Goals.LOOT`.
* [ ] Subtask: Implement `SURVIVAL`: calculate paths to healing items or safe zones.
* [ ] Subtask: Implement `REVENGE`: identify and target Sprites that recently triggered the `struck` mutator.

**4. Task: Refine Animation States for Stationary Intentions**

*Objective*: Prevent Sprites from animating a walk cycle while engaged in stationary interactions.

* [ ] Subtask: Modify `TransitionMechanics` so `mutators.triggers.animated` evaluates to `False` if the Intention is `SPEAK`, `BARTER`, or `INTERACT` *and* `velocity == 0`.
* [ ] Subtask: Ensure `psyche.expression` cleanly appends the `LOQUACITY` cursor frame to the rendering stack in `SpriteFrame.keys()`.







### Bug Report & Logical Inconsistencies

Prior to task execution, several logical flaws and discrepancies between the documentation and the codebase must be addressed:

* **Bug 1: The Memory Goal Stack Discrepancy:** The specification dictates that `memory.goals` acts as a stack ("pop the top goal"). However, in `app.models.state.sprites`, `Memory.goals` is typed as a scalar `Optional[Goal] = None`. Furthermore, `CognitionMechanics` executes a scalar assignment (`sprite.state.goal = sprite.state.memory.goals`), overwriting rather than popping. If a Sprite is interrupted multiple times, it will lose its original directives.
* **Bug 2: Animation Moonwalking:** `AnimationMap.action()` defaults to `Actions.WALK`. In `TransitionMechanics`, the `triggers.animated` flag is forcefully set to `True` if `intention not in (IDLE, WANDER)`. This means a Sprite engaged in a stationary `speak` or `barter` Intention will continuously play its walking animation in place.








#### Refactor: Phase 07.01 Speak Intention & Goal Acquisition

### IV. Documentation & Schema Adjustments

To ensure the ISL execution environment remains robust, the following updates should be made to the configuration:

1. **Strict Existential ISL Checks:** Update `intentions/main.yaml` to ensure all nested dictionary accesses are preceded by an existential check.
```yaml
barter:
  - next: threaten
    conditions:
      - sprite.memory.goals
      - sprite.memory.prices
      - sprite.inventory.wallet < sprite.memory.prices.get(sprite.memory.goals[-1].name, 9999)

```


2. **Clarify Device Context Mapping:** The documentation notes that `InteractionMechanics` pushes a MenuEvent for Player-to-Chest interactions. With `SpeechMechanics` handling Player-to-Sign/NPC interactions, the documentation for `InteractionMechanics` should be explicitly narrowed to state that it *only* handles physical Asset interactions (Doors, Crates, Chests), leaving all linguistic and commercial interactions to `SpeechMechanics`.


















##### Tasks

**1. Task: Refactor `Frame` Interface for Sub-Component Rendering**

*Objective*: Allow `SpriteFrame` to dynamically position Expression overlays without VRAM padding or `Cradle` instantiation.
- [ ] Subtask: Update `app.assets.base.Frame.keys()` signature to `def keys(self, asset: 'Asset') -> List[Tuple[str, int, int]]:`.
- [ ] Subtask: Update `SingleFrame`, `IterableFrame`, and `StateFrame` to yield `(key, 0, 0)`.
- [ ] Subtask: Update `SpriteFrame.keys` to conditionally append `(f"bubbles-{state.psyche.expression}", asset.dimensions.w - 16, -16)`.
- [ ] Subtask: Update `Screen.draw` and `Screen._prerender` to unpack `ox, oy` and add them to `dx, dy`.

**2. Task: Implement `SpeechMechanics`**

*Objective*: Isolate linguistic data transfers from physical mechanics.
- [ ] Subtask: Create `SpeechMechanics` inheriting from `Mechanic`.
- [ ] Subtask: Implement logic targeting Sprites with `SPEAK`, `BARTER`, and `THREATEN` Intentions using `functions.is_near()` against `sprite.state.goal.position`.
- [ ] Subtask: Implement NPC data transfer: move `psyche.dialogue` to target's `memory.rumors`.
- [ ] Subtask: Clear source `psyche.dialogue` post-transfer to unblock the ISL matrix transition.
- [ ] Subtask: Emit `MenuEvent` payloads to the Engine `bus` for Player-to-NPC dialogue.
- [ ] Subtask: Register `speech` in `/src/data/config/mechanics/main.yaml`.

**3. Task: Resolve Architectural Discrepancies & Bugs**
*Objective*: Patch Memory models, O(N) lookup hazards, and animation glitches.
- [ ] Subtask: Update `app.models.state.sprites.Memory` to define `goals` as `List[Goal] = field(default_factory=list)`. Update `CognitionMechanics` to utilize `.pop()`.
- [ ] Subtask: Introduce `_cached_objects: Dict[str, Asset]` to `app.game.board` to provide $O(1)$ lookups for `Goals.ASSET` tracking in `CognitionMechanics`.
- [ ] Subtask: Update `AnimationMap.action` to return `Actions.CAST` (acting as a physical gesture) for communicative Intentions to prevent the "Stationary Moonwalking" glitch.

**4. Task: Expand Cognition Target Acquisition**
*Objective*: Flesh out `CognitionMechanics._acquire_target` logic mapping to `Motivations`.
- [ ] Subtask: Implement `PROFIT`: map to `Goals.ASSET` by querying `board` for unlooted `CHESTS`.
- [ ] Subtask: Implement `SURVIVAL`: map to `Goals.POSITION` or `Goals.LOOT` for safe zones or health items. 

```








This is exactly the right mental model. "Phantom states" perfectly describes it—they are fully integrated into the data-driven property and indexing pipelines (so the Registry knows how to load them into VRAM), but they bypass the ECS instantiation overhead, existing merely as calculated offsets within a host Asset's state.

Here is the finalized Phase 07.01 document for your backlog. It synthesizes all our architectural decisions, squashes the identified bugs, and provides a clear, step-by-step roadmap for implementation.

---

# Refactor: Phase 07.01 Speak Intention & Goal Acquisition

**Goal**: Implement the `speak` Intention. Unify the Expression pipeline using "Phantom State" data overlays. Isolate linguistic interactions into a dedicated Mechanic. Resolve Goal Acquisition logic and memory bugs.

## Architectural Discussion

### 1. The "Phantom State" Expression Pipeline

Expressions (Cursors) are no longer instantiated as physical `Asset` objects on the `Board`. Because they are purely visual decorators, they operate as "Phantom States."

* **Indexing**: A new `MappedFrame` implementation allows the `Registry` to index string-based frame arrays (like the `bubbles` configuration) into VRAM during initialization.
* **Generation**: When an expression is triggered, the `Cradle` calculates the optimal spatial offsets using the target's dimensional properties and returns a pure data structure (`ExpressionData`).
* **Rendering**: The `Frame.keys()` interface is upgraded to yield a `List[Tuple[str, int, int]]` (key, offset_x, offset_y). `SpriteFrame` reads the `ExpressionData` embedded in the Sprite's `Psyche` state and dynamically appends the tuple. The Cython `Screen` unpacks these offsets and applies them natively to the destination coordinates, achieving zero-allocation overlay rendering without VRAM padding or complex state-syncing loops.

### 2. Separation of Intentional Concerns

The Engine rigorously separates "deciding," "moving," and "interacting." `InteractionMechanics` is strictly reserved for physical AABB bounding-box overlaps (Doors, Crates). Communicative Intentions (`speak`, `barter`, `threaten`) operate on radial proximity (`is_near`) and induce data transfers rather than physical changes. `SpeechMechanics` is introduced as a dedicated `world` pipeline to execute these transfers, emit UI payloads, and reset the `psyche.dialogue` field so the ISL transition matrix can seamlessly exit the Sprite to an `idle` state.

---

## Tasks

### 1. Task: Establish the "Phantom State" Expression Architecture

*Objective*: Upgrade the rendering pipeline to support nested offsets and implement data-driven Expression tracking.

* [ ] **Subtask**: Update `app.assets.base.Frame.keys()` signature to `def keys(self, id: str, state: AssetState) -> List[Tuple[str, int, int]]:`.
* [ ] **Subtask**: Update `SingleFrame`, `IterableFrame`, and `StateFrame` to yield `(key, 0, 0)`.
* [ ] **Subtask**: Create `MappedFrame(Frame)` to index properties with string-based `frames` lists (e.g., `bubbles`).
* [ ] **Subtask**: Update `Screen._prerender` and `Screen.draw` to unpack `frame_key, ox, oy` and apply the offsets directly to `dx, dy`.
* [ ] **Subtask**: Create `ExpressionData` dataclass (key, offset, dimensions) and add it to `app.models.state.sprites.Psyche` as `expression: Optional[ExpressionData]`.
* [ ] **Subtask**: Implement `Cradle.calculate_expression(self, id: str, key: str, target: Asset) -> ExpressionData`, executing the geometric math (e.g., top-right anchoring) purely through properties.
* [ ] **Subtask**: Update `SpriteFrame.keys` to check `state.psyche.expression` and append its pre-calculated tuple.

### 2. Task: Implement `SpeechMechanics`

*Objective*: Isolate linguistic data transfers and UI events from physical mechanics.

* [ ] **Subtask**: Create `SpeechMechanics` inheriting from `Mechanic`.
* [ ] **Subtask**: Filter Sprites with `SPEAK`, `BARTER`, and `THREATEN` Intentions. Verify target proximity using `functions.is_near()` against `sprite.state.goal.position`.
* [ ] **Subtask**: Implement NPC-to-NPC logic: transfer `sprite.state.psyche.dialogue` to the target Sprite's `memory.rumors`.
* [ ] **Subtask**: Implement Player-to-NPC logic: construct and append a `MenuEvent` to the Engine `bus` to pause the world and render the dialogue/barter UI.
* [ ] **Subtask**: Clear the source `sprite.state.psyche.dialogue` post-transfer to naturally unblock the ISL matrix (transitioning back to `idle`).
* [ ] **Subtask**: Register `speech` in `/src/data/config/mechanics/main.yaml` under the `world` pipeline.

### 3. Task: Resolve Architectural Discrepancies & Code Smells

*Objective*: Patch Memory models, O(N) lookup hazards, and strip defensive `getattr()` checks.

* [ ] **Subtask**: Update `app.models.state.sprites.Memory` to define `goals` as `List[Goal] = field(default_factory=list)`. Update `CognitionMechanics` to utilize `.pop()` to restore previous directives.
* [ ] **Subtask**: Introduce `_cached_objects: Dict[str, Asset]` to `app.game.board` alongside `_cached_characters` to provide $O(1)$ lookups for `Goals.ASSET` tracking in `CognitionMechanics`.
* [ ] **Subtask**: Refactor `CognitionMechanics`, `TransitionMechanics`, and `AnimationMap` to replace `getattr(state, 'field', None)` anti-patterns with direct namespace access, relying on Pydantic's guaranteed data schemas.

### 4. Task: Refine Animation Mapping & Goal Acquisition

*Objective*: Flesh out `Motivations` and prevent stationary Sprites from playing walking animations.

* [ ] **Subtask**: Update `AnimationMap.action` to return `Actions.CAST` (serving as a physical gesture) for communicative Intentions, preventing the "Stationary Moonwalking" glitch.
* [ ] **Subtask**: Update `TransitionMechanics` to only evaluate `mutators.triggers.animated = True` if the Sprite has active velocity or an explicitly animated action, rather than a blanket catch-all.
* [ ] **Subtask**: Flesh out `PROFIT` in `CognitionMechanics._acquire_target` by querying `board._cached_objects` for unlooted `CHESTS` and mapping them to `Goals.ASSET`.
* [ ] **Subtask**: Flesh out `SURVIVAL` in `CognitionMechanics` by mapping to `Goals.POSITION` (safe zones) or `Goals.LOOT` (health items).

---

Ready to dive into the code for one of these tasks, or is there another subsystem you want to groom before moving forward?