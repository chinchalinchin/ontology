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

##### Goal: Autonomous Sprite Conversations

1. **Tick 1 (Ideation):** `CognitionMechanics._ideate` method, prior to the generation of Goals via Motivations in `CognitionMechanics._motivate`, sees `psyche.dialogue` is populated and intercepts. It sets `sprite.state.goal = Goal(name="Bob", category=Goals.SUBJECT)`. It pushes the previous goal to `memory.goals`.
2. **Tick 2-N (Navigation):** ISL routes the Sprite into `find`. `MotionMechanics` moves it toward Bob.
3. **Tick N+1 (Arrival):** The Sprite is within radius. ISL evaluates `find` $\to$ `speak`.
4. **Tick N+2 (Action):** `SocialMechanics` processes the `speak` intention. It passes the rumor to Bob, spawns the `LOQUACITY` expression with a TTL of 120 ticks, but *keeps* `dialogue` populated so the Sprite stays anchored.
5. **Tick N+122 (Decay):** `SocialMechanics` decrements TTL to 0. It sets `sprite.psyche.dialogue = None`.
6. **Tick N+123 (Resolution & Amnesia Prevention):**
* `CognitionMechanics._resolve_goal` runs. It sees `category == Target`. It checks `if not sprite.psyche.dialogue:`. The condition is met. It sets `sprite.state.goal = None`.
* `CognitionMechanics` immediately pops `memory.goals`, restoring the overarching goal.
* `TransitionMechanics` evaluates ISL. Because the goal is updated, the Sprite natively transits to `return`, `wander`, or `idle`.

##### Tasks

**1. Task: Establish the "Phantom State" Expression Architecture**

*Objective*: Upgrade the rendering pipeline to support nested offsets and implement data-driven Expression tracking.

* [ ] Subtask: Update `app.assets.base.Frame.keys()` signature to `def keys(self, id: str, state: AssetState) -> List[Tuple[str, int, int]]:`.
* [ ] Subtask: Update all base Frame implementations (`SingleFrame`, `IterableFrame`, `StateFrame`, `TraversalFrame`, `MeterFrame`, `IndexFrame`) to yield `(key, 0, 0)`.
* [ ] Subtask: Update `Screen._prerender` (Tiles), `Screen.draw` (World), `Screen.interface` (Widgets), and `Screen.stamp` (Text) to unpack the 3-tuple `(frame_key, ox, oy)` before querying the Registry.
* [ ] Subtask: Create `AttachmentState` dataclass (key, offset, dimensions) and add it to `app.models.state.sprites.Psyche` as `expression: Optional[AttachmentState]`.
* [ ] Subtask: Implement `Cradle.spawn_expression(...) -> AttachmentState`, calculating top-right anchoring based on target dimensions.
* [ ] Subtask: Update `SpriteFrame.keys` to check `state.psyche.expression` and append its pre-calculated tuple.

**2. Task: Resolve Memory Goal Architecture**

*Objective*: Align the data models and `CognitionMechanics` to support nested, interruptible goals. Fix "Goal Amnesia" by giving CognitionMechanics precise contexts for goal resolution.

* [ ] Subtask: Update `Goals` Enum: Replace `SPRITE` with `TARGET` (for combat) and `SUBJECT` (for social). 
* [ ] Subtask: Update `app.models.state.sprites.Memory` to type `goals` as `List[Goal] = field(default_factory=list)`.
* [ ] Subtask: Refactor `CognitionMechanics._resolve`. Map `Goals.TARGET` to the existing death check. Map `Goals.SUBJECT` to check `if not sprite.psyche.dialogue`.
* [ ] Subtask: Refactor `CognitionMechanics._resolve_goal` to use `.pop()` to retrieve the most recent goal from `memory.goals` when `sprite.state.goal` resolves to `None`.
* [ ] Subtask: Implement "Provenance" in `CognitionMechanics._acquire`: If `sprite.psyche.dialogue` exists, scan `board.characters()` for a valid target within vision radius, assign `Goals.SUBJECT`, and push the current goal to `memory.goals`.
* [ ] Subtask: Update `app.models.state.sprites.Memory` to type `goals` as `List[Goal] = field(default_factory=list)`.
* [ ] Subtask: Update `CognitionMechanics._resolve` to use `.pop()` to retrieve the most recent goal when `sprite.state.goal` resolves to `None`.

**3. Task: Implement `SocialMechanics`**

*Objective*: Create a dedicated mechanic for processing communicative Intention data transfers while preventing 1-frame glitches.

* [ ] Subtask: Create `SocialMechanics` inheriting from `Mechanic`. Register in `mechanics/main.yaml` under the `world` pipeline.
* [ ] Subtask: Implement logic to filter Sprites with `SPEAK`, `BARTER`, and `THREATEN` Intentions.
* [ ] Subtask: Implement NPC-to-NPC logic: transfer `psyche.dialogue` to target's `memory.rumors`, set source `psyche.expression = Cradle.spawn_expression(...)`.
* [ ] Subtask: Implement tick-decay on `psyche.expression.ttl`. Set `psyche.dialogue = None` *only* when `ttl <= 0` to ensure the conversation renders before the ISL forces an Intention transition.
* [ ] Subtask: Implement Player-to-NPC logic: push `MenuEvent('dialogue', ...)` to the `bus` to pause the world and render the UI.

- *Logical Flaw:* `SocialMechanics.update()` executes every game tick. If a Sprite is in the `speak` Intention, the mechanic will continuously spawn new `AttachmentState` objects, reset the TTL to 120, and pass duplicate rumors to the target 60 times a second until the Intention forcefully changes.
    - *Correction:* `SocialMechanics` must use `sprite.psyche.expression` as a state lock. It should only execute the data transfer and spawn the Expression `if not sprite.psyche.expression`. On subsequent ticks, it simply decrements the TTL.

**4. Task: Refine Animation States for Stationary Intentions**

*Objective*: Fix stationary Intentions and update the matrix to utilize Semantic Goals.

* [ ] Subtask: Update `AnimationMap.action` to return `Actions.CAST` (serving as a physical gesture) for communicative Intentions, preventing the "Stationary Moonwalking" glitch.
* [ ] Subtask: Update `TransitionMechanics` to only evaluate `mutators.triggers.animated = True` if the Sprite has active velocity or an explicitly animated action, rather than a blanket catch-all.

**5. Flesh Out Motivations**

* [!] Subtask: Flesh out `PROFIT` in `CognitionMechanics._acquire_target` by querying `board._cached_objects` for unlooted `CHESTS` and mapping them to `Goals.ASSET`.
    * NOTE: Future refactor. Focus on `speak` now.
* [!] Subtask: Flesh out `SURVIVAL` in `CognitionMechanics` by mapping to `Goals.POSITION` (safe zones) or `Goals.LOOT` (health items).
    * NOTE: Future refactor. Focus on `speak` now.
* [!] Subtask: Implement `PROFIT`: scan `board.renderables()` for Assets classified as `CHESTS` or mineable resources; assign `Goals.ASSET` or `Goals.LOOT`.
    * NOTE: Future refactor. Focus on `speak` now.
* [!] Subtask: Implement `SURVIVAL`: calculate paths to healing items or safe zones.
    * NOTE: Future refactor. Focus on `speak` now.
* [!] Subtask: Implement `REVENGE`: identify and target Sprites that recently triggered the `struck` mutator.
    * NOTE: Future refactor. Focus on `speak` now.
    
**6. Task: Resolve Architectural Discrepancies & Bugs**

* [ ] Subtask: Introduce `_cached_objects: Dict[str, Asset]` to `app.game.board` alongside `_cached_characters` to provide $O(1)$ lookups for `Goals.ASSET` tracking in `CognitionMechanics`.
* [~] Subtask: Refactor `CognitionMechanics`, `TransitionMechanics`, and `AnimationMap` to replace `getattr(state, 'field', None)` anti-patterns with direct namespace access, relying on Pydantic's guaranteed data schemas.
* [ ] Subtask: Update `TransitionMechanics` to only evaluate `mutators.triggers.animated = True` if the Sprite has active velocity or an explicitly animated action.
* [ ] Subtask: Update `intentions/main.yaml` to route `speak` -> `return` matching the `00-speak.md` specification.
* [ ] Subtask: Update `intentions/main.yaml` to use `.get()` on relationship dictionaries (`sprite.memory.relationships.get(sprite.goal.name) in [...]`) to prevent runtime KeyErrors.
* [ ] Subtask: Update `/src/data/config/intentions/main.yaml` ISL conditions to safely evaluate `sprite.memory.goals` as a list rather than a scalar attribute.
* [ ] Refactor `/src/data/config/intentions/main.yaml`: Replace array attribute queries like `sprite.memory.goal.category == ...` with the new `functions.check_memory(sprite.memory.goals, ...)` helper.