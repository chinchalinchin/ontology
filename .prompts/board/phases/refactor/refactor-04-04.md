#### Refactor: Phase 04.04 - MenuContext

**Overview**

Formalize the Menu instantiation workflow by replacing unstructured dictionary payloads with strictly-typed `MenuContext` data classes. This eliminates ambiguity in the Provider pipeline, ensures schema validation, and clearly separates the responsibilities between what data a Menu holds (the Context) and how a Widget accesses that data (the Binding).

1. **The Menu Context (The Payload):** A Menu takes a single, strongly-typed state object. For the HUD (`ViewMenu`), the payload is the `Player` asset. The `ViewContext` simply wraps this: `ViewContext(sprite=player)`.
2. **The Widget Binding (The Pointer):** Widgets in the configuration define a `target` path. The `health-meter` uses `context.sprite.state.meters.health`. The `magic-meter` uses `context.sprite.state.meters.magic`.
3. **The Resolution (The Engine):** The existing `Binding._resolve` method uses `functools.reduce` to traverse down the string path. It already handles a mix of dataclasses (`getattr`) and dictionaries (`dict.get`). It will navigate a typed `ViewContext` object just as easily as it navigated nested dictionaries, natively solving demarcation obstacles (health meters vs magic meters) without changing the underlying binding logic.

- The **Mechanic** just says: *"Here is the Plot state and here is the Sprite state."* (The Context)
- The **YAML Configuration** says: *"To build a Library query, grab X from Plot, and Y and Z from Sprite."* (The Binding Target)
- The **Binder** resolves these independent paths and creates the closure.

##### Goal: MenuContext Data Models

Create a dedicated package for Context definitions. Instead of the Engine passing arbitrary dictionaries via `MenuEvent`, it will pass explicit runtime models.

```python
# app/game/menus/contexts.py

class MenuContext:
    pass

@dataclass(slots=True)
class ViewContext(MenuContext):
    sprite: Asset

@dataclass(slots=True)
class TextContext(MenuContext):
    plot: str
    persona: str
    lexicon: str

@dataclass(slots=True)
class LoadContext(MenuContext):
    registry: Registry
    screens: Dict[str, Any]
    screensize: Dimensions

```

##### Goal: Schema & Model Upgrades

Upgrade the Configuration models to accept multipart target dictionaries.

##### Goal: LibraryBinding Refactor

Rewrite the `LibraryBinding` to resolve and cache three independent state pointers, allowing `content_function()` to fetch from multiple domain objects at runtime.

##### Goal: Generic Text Binding Separation

Formalize the difference between `library` (multipart dialogue queries) and `text` (literal string interpolation) schemas across the configurations and contexts.

##### Bug B006: Binding Pipeline Type Hinting Constraints

**STATUS**: OPEN
**SEVERITY**: LOW

**Description**

While `Binding._resolve` safely uses `getattr` and `dict.get` to traverse objects, the type hinting throughout `Provider`, `Binder`, and `Binding` strictly enforces `context: dict`. If a `dataclass` or standard object is passed into the pipeline (such as a `MenuContext`), static type checkers (Mypy) will flag cascading validation errors, even though the runtime execution will succeed.

**Proposed Remediation**

Update the type hints across `app.services.generators.provider`, `app.services.generators.binder`, and `app.game.menus.bindings` from `context: dict` to `context: MenuContext` (or `Any` as an interim measure) to align with the Phase 05.08 grooming task.

##### Tasks

**1. Task: Update Menu Models**

*Objective*: Allow `MenuBinding.target` to accept dictionary formulas.

* [x] Subtask: In `app.models.config.menus`, update `MenuBinding.target` type hint to `Union[str, Dict[str, str]]`. Remove `selector` and `selection` since they will be embedded in the `target` field.

**2. Task: Update Dialogue Context & YAML**

*Objective*: Structure the `DialogueContext` and update the YAML to map the multipart formula.

* [x] Subtask: In `app.game.menus.contexts`, define `DialogueContext` to accept both `plot: PlotState` and `sprite: SpriteState`.
* [x] Subtask: In `data/config/menus/dialogue.yaml`, update the `character-speech` widget binding target to use the dictionary formula.

**3. Task: Refactor LibraryBinding**

*Objective*: Override the base `Binding` initialization to resolve multiple pointers.

* [x] Subtask: In `app.game.menus.bindings.py`, update `LibraryBinding.__init__` to bypass the base `super().__init__` and independently call `self._resolve()` for the `plot`, `persona`, and `lexicon` keys in the target dictionary.
* [x] Subtask: Update `LibraryBinding.bind()`'s `content_function` closure to execute retrievals for all three resolved pointers before calling `self.library.fetch()`.

**4. Task: Formalize TextBinding**

*Objective*: Ensure generic notifications use `TextContext` and `TextBinding`.

* [x] Subtask: In `app.game.menus.contexts`, ensure `TextContext` is defined simply as `content: Union[str, List[str]]`.
* [X] Subtask: Verify `app.game.menus.bindings.TextBinding` correctly resolves a single string `target` (e.g., `context.content`).
* [X] Subtask: In `data/config/menus/text.yaml`, verify the `text-display` widget binding schema is explicitly set to `text` instead of `library`.