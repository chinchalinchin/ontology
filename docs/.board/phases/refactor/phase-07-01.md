#### Refactor: Phase 07.01 Speak Intention

**Goal**: Implement the `speak` Intention. Flesh out Sprite Goal Acquisition. Expand Sprite Finite Automata.

**Context**: Before the completion of Phase 07, it was assumed SpeechMechanics would be their own mechanics. However, with the implementation of CognitionMechanics and TransitionMechanics, it is no longer clear if SpeechMechanics is actually necessary as an independent Mechanic.

##### Tasks


**1. Task: Resolve Memory Goal Architecture**

*Objective*: Align the data models and `CognitionMechanics` to support nested, interruptible goals.

* [ ] Subtask: Update `app.models.state.sprites.Memory` to type `goals` as `List[Goal] = field(default_factory=list)`.
* [ ] Subtask: Update `CognitionMechanics._resolve_goal` to use `.pop()` to retrieve the most recent goal when `sprite.state.goal` resolves to `None`.
* [ ] Subtask: Update `/src/data/config/intentions/main.yaml` ISL conditions to safely check `sprite.memory.goals` instead of a scalar attribute.

**2. Task: Implement `SocialMechanics`**
*Objective*: Create a dedicated mechanic for processing communicative Intention data transfers.

* [ ] Subtask: Create `SpeechMechanics` inheriting from `Mechanic` (not `SpatialMechanic`).
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









This is a rigorous architectural review of the Ontology game engine, focusing on the Phase 07-01 objective: implementing the `speak` Intention, fleshing out Goal Acquisition, and resolving the necessity of `SpeechMechanics`.

### I. Architectural Assessment: The Necessity of `SpeechMechanics`

The Task Board raises a critical architectural question: *With the implementation of CognitionMechanics and TransitionMechanics, is SpeechMechanics actually necessary as an independent Mechanic?*

**Deduction:** Yes, `SpeechMechanics` (or a generalized `SocialMechanics`) is strictly necessary.

**Reasoning:**
The engine cleanly separates "deciding what to do" from "doing it."

1. `CognitionMechanics` (The Brain) handles target acquisition and sets the spatial `Goal`.
2. `TransitionMechanics` (The Instinct) evaluates the ISL matrix to map the state to an `Intention` (e.g., `speak`) and calculates the `Animation` vector.
3. `InteractionMechanics` (The Muscle) resolves physical state changes, but it relies on AABB Hitbox intersections via Cython's `Physics.collisions`.

Communicative Intentions (`speak`, `barter`, `threaten`) operate on *radii* (`is_near`), not strict Hitbox overlaps. Furthermore, they induce side effects that fall outside the purview of the ISL matrix: transferring `psyche.dialogue` to `memory.rumors`, averaging `memory.prices`, setting UI Cursor tags (`psyche.expression`), and emitting `MenuEvent` payloads for Player interactions. Attempting to shoehorn these data-transfer operations into `TransitionMechanics` would violate the separation of concerns.

`SpeechMechanics` must be implemented to iterate over Sprites in communicative Intentions, calculate radial distance to targets, and execute the data transfers. Once the transfer occurs, `SpeechMechanics` sets `sprite.psyche.dialogue = None`, which naturally triggers `TransitionMechanics` on the next tick to transition the Sprite into `idle` via the ISL condition `not sprite.psyche.dialogue`.

### II. Bug Report & Logical Inconsistencies

Prior to task execution, several logical flaws and discrepancies between the documentation and the codebase must be addressed:

* **Bug 1: The Memory Goal Stack Discrepancy:** The specification dictates that `memory.goals` acts as a stack ("pop the top goal"). However, in `app.models.state.sprites`, `Memory.goals` is typed as a scalar `Optional[Goal] = None`. Furthermore, `CognitionMechanics` executes a scalar assignment (`sprite.state.goal = sprite.state.memory.goals`), overwriting rather than popping. If a Sprite is interrupted multiple times, it will lose its original directives.
* **Bug 2: Animation Moonwalking:** `AnimationMap.action()` defaults to `Actions.WALK`. In `TransitionMechanics`, the `triggers.animated` flag is forcefully set to `True` if `intention not in (IDLE, WANDER)`. This means a Sprite engaged in a stationary `speak` or `barter` Intention will continuously play its walking animation in place.
* **Bug 3: ISL Runtime Vulnerability:** The ISL matrix parses properties directly. In the `barter` configuration, the condition `- sprite.inventory.wallet < sprite.memory.prices.get(sprite.memory.goal.name, 9999)` will raise an `AttributeError` if `memory.prices` is `None`. The dictionary must be existentially checked first.

### III. Task Board: Phase 07.01 Groomed

Below is the groomed task backlog required to complete Phase 07.01, aligning the codebase with the architectural design.

#### Refactor: Phase 07.01 Speak Intention & Goal Acquisition

**Goal:** Implement the `speak` Intention. Flesh out Sprite Goal Acquisition. Expand Sprite Finite Automata.

##### Tasks


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