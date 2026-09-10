#### Refactor: Phase 05.05 - Expression Animations

**Loquacity**

This Expressions is currently "functional", in the sense it is getting appended when Sprite transitions into `speak`. However, the Expression TTL stops counting down when the Sprite transitions in `IDLE`, which it does instantly in the case of Player-to-Sprite dialogue, in order to allow the Player to press the `interact` key.

*Proposal*: The Expression TTL logic should probably be in the Sprite animation. Right now Expression decay is specific to LOQUACITY and is located inside of the SocialMechanics, but it will need to be generalized for different types of Expressions, bringing us to...

**Confusion**

During the Dialogue Intention loop, if the Sprite gets to its Goal without locating the Sprite, it should have the `Expressions.CONFUSION.value` expressiong appended to it, similar to the how the `Expression.LOQUACITY.value` is appended when it enters `speak`.

**Overview**

Expressions currently suffer from orphaned TTLs when a Sprite's Intention changes abruptly (e.g., interacting with the Player and snapping to `IDLE`). This phase introduces a `SpriteAnimation` component to encapsulate the Expression decay logic, decoupling visual decay from the Intention state machine. It also implements dynamic emotional reactions (like Confusion) when pathfinding goals fail.

##### Goal: Implement SpriteAnimation

Create a dedicated `SpriteAnimation` component that extends `StateAnimation`. This component will naturally decrement `psyche.expression.ttl` and nullify the expression when it expires, allowing the visual to fade independently of the Sprite's AI state.

##### Goal: Clean SocialMechanics

Remove all decay logic from `SocialMechanics`. Its only responsibility regarding Expressions should be spawning `LOQUACITY` when entering `SPEAK` (if an expression doesn't already exist), and handling the actual transfer of `dialogue` to `rumors` for NPC-to-NPC interactions.

##### Goal: Implement Confusion Reaction

When a Sprite arrives at a target's last known location (`goal.position`) but lacks vision of the target, the tracking goal is invalidated. This psychological failure state should dynamically trigger a `CONFUSION` expression via the `Cradle`.

##### Tasks

**1. Task: Create SpriteAnimation Component**

*Objective*: Encapsulate Expression TTL decay into a Sprite-specific animation strategy.

* [x] Subtask: In `app.assets.animations.core`, create `SpriteAnimation(StateAnimation)`.
* [x] Subtask: Override `animate()` to call `state = super().animate(state, properties)`.
* [x] Subtask: Within `animate()`, check if `state.psyche.expression` exists. If so, decrement its `ttl`. If `ttl <= 0`, set `state.psyche.expression = None`.
* [x] Subtask: Update the configuration Recipes so `AssetInstances.SPRITES` and `AssetInstances.PLAYERS` utilize `SpriteAnimation` instead of `StateAnimation`.

**2. Task: Clean SocialMechanics**

*Objective*: Remove the orphaned TTL decay loop.

* [x] Subtask: In `SocialMechanics.update`, remove the `else:` block containing `sprite.state.psyche.expression.ttl -= 1` and its associated nullification logic.

**3. Task: Implement Confusion Expression**

*Objective*: Inject the `CONFUSION` expression when a tracking goal fails.

* [x] Subtask: In `CognitionMechanics._resolve`, locate the fallback condition for `TARGET` and `SUBJECT` goals where the Sprite is nearby but lacks vision (`elif self.nearby(...) and not sprite.state.mutators.triggers.vision:`).
* [x] Subtask: Before setting `sprite.state.goal = None`, utilize `board.cradle.spawn_expression(ExpressionsPalette.BUBBLES.value, Expressions.CONFUSION.value, sprite)` to attach the confusion expression.
