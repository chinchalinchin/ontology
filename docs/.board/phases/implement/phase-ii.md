#### Implement: Phase II - Player

Here are the architectural adjustments and the detailed task board for Phase II, aligning the Player and input devices with the engine's data-driven, ECS-like philosophy.

### Architectural & Design Adjustments

**Data-Driven Player Initialization**

* [ ] **Configuration:** Create `src/data/state/<board>/player.yaml` to define the Player's initial state (Layer, Position, Character stats). Map the category to `sheets` and instance to `sprites`.
* [ ] **Factory Migration:** Remove the hardcoded `__init__` in `src/app/input/player.py`. Route the Player's instantiation through `Orchestrator.migrate()` using the standard `Factory` methods.
* **Board Integration:** Modify `Board.__init__` to ensure the Player is appended to `self._assets` so it successfully enters the `_cached_categories` and `_cached_instances` dictionaries.

**Input Device Configuration & Mapping**

* [ ] **Schemas:** Define a `PyInputConfiguration` Pydantic model and corresponding YAML schema (`src/app/config/input.yaml`) to map physical hardware keys (e.g., SDL scancodes) to `Actions`, `Directions`, and `Extensions`.
* [ ] **Device Polling:** Implement `Keyboard.poll()` and `Controller.poll()`. These methods must query the hardware state (via Cython/SDL) and return a lightweight input bitmask or data structure, *not* a full `PlayerState` object.

**Implement PlayerMechanic**

* [ ] **Creation:** Add `PlayerMechanic` to `src/app/game/mechanics.py` and register it in the `Board`'s mechanics list.
* [ ] **Logic:** The mechanic will query the `Device` for the current input vector. It will translate this vector into state mutations applied directly to the Player's `state.animation.action`, `state.animation.direction`, and `state.position` attributes.
* [ ] **Decoupling:** Remove the `# TODO: player logic` block from the `Board.play()` method loop.

**Unified Rendering Integration**

* [ ] **Refactor `Screen.draw`:** Update the signature to `draw(self, assets: List[Asset], registry: Registry)`. Remove the explicit `player` argument.
* **Z-Ordering Preparation:** Ensure the Player is rendered as part of the `active_assets` list iteration. Prepare the rendering pipeline to eventually support sorting `active_assets` by `asset.state.position.y` prior to dispatching the C-level `render()` function.

**[ ] Task 5: Physics & Collision Connectivity**

* **Verification:** Ensure that once the Player is cached as `AssetCategories.SHEETS`, `CollisionMechanics` and `SwitchMechanics` correctly calculate overlaps with the Player's hitboxes. No new logic should be required in the mechanics classes if Task 1 is executed correctly.