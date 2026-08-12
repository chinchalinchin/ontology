#### Phase III: Intentions

##### Intentional Scripting Language (ISL)

To maintain performance, the custom disposition DPL defined in `/src/assets/intents/main.yaml` must be compiled into executable Python `lambda` functions during the orchestration phase of the application bootstrap.

**Implementation Outline**

1. **Grammar Tokenization:**

Create a parsing utility within `Factory` or a dedicated `app.parser` module. The utility must map the custom string terms to their programmatic Python equivalents:

* `sprite` : `self_asset.state`
* `sprites[<name>]`: `board_sprites[<name>].state`
* `not`, `and`, `or`, `==`, `!=`: Native Python operators.


2. **AST Compilation:**

Translate the tokenized strings directly into Python syntax and compile them utilizing Python's built-in `eval()` or `compile()` functions at startup.

* Input String: `"not sprite.goal.target"`
* Compiled Lambda: `lambda self_asset, board_sprites: not getattr(self_asset.state.goal, 'target', None)`


3. **Data Model Refactoring:**

Update the `PyIntentionState` and runtime `Intention` models to accept a `Callable`.

```python
from typing import Callable, Dict

class Transition:
    next: str
    # Callable takes the current SpriteState and a dictionary of all active SpriteStates
    condition: Callable[['SpriteState', Dict[str, 'SpriteState']], bool]

```

4. **Mechanic Integration:**

Implement a `IntentionMechanic`. During the `Board.play()` loop, the mechanic iterates over active sprites, looks up their current `Disposition` in the matrix, and executes the compiled lambda:

```python
for transition in current_disposition.transitions:
    # Executes in C-optimized Python bytecode, no string parsing
    if transition.condition(sprite.state, board.sprites_dict):
        sprite.state.intention.disposition = transition.next
        break

```