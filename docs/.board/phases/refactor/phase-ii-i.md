#### Refactor: Phase II - Frames

The basis of the Intention system has been laid. Both Sprite and Player Assets have been writed to transmit their Animations through (Intention, Goals). Before moving onto expanding the Intention mechanics, it is time to refactor what we have already. 

**Goals**

- The application has started to accumulate bloat. The Orchestrator class has a lot of responsibility that would be better broken up into components.
- Mechanics are currently being enumerated and instantiated in the Board class. Discuss the possibility of a `@mechanic` annotation for registering Mechanics in an application dispatch dictionary. Discuss other possibilities. Determine what would be the most Pythonic and architecturally sound way of reducing the verbosity of the application.
- Equipment frames needs incorporated into the rendering pipeline. The `all` Action and Direction value for Equipment Animations needs handled.

**Design Improvements**

- *Extract the Game Loop*: The `while` loop and delta-time calculations in `Orchestrator.start()` must be extracted into a dedicated `Engine` class. This class takes a `Board`, a `Screen` map, and a list of `Mechanic` instances, executing them sequentially.
- *Demote the Boar*d: `Board.play()` should be removed. The Board must become a pure state container and querying interface. The Engine will iterate over the injected Mechanics, passing the Board to each.
- *Isolate Configuration I/O*: `Orchestrator.load()` and `Orchestrator.merge()` handle raw file I/O and dictionary manipulation. This logic belongs in a `Loader` utility, leaving the `Orchestrator` to strictly handle dependency injection and component wiring.

##### Tasks

**Task 1: Extract Configuration Loader**

*Objective*: Remove file parsing and dictionary merging from the Orchestrator.

- [x] Create a `Loader` utility class.
- [x] Move `Orchestrator.merge()` and `Orchestrator.load()` into `Loader`.
- [x] Ensure `Loader` returns the fully merged and Pydantic-validated dictionaries.
- [x] Update `Orchestrator.__init__` to instantiate and call `Loader`.

**Task 2: Implement Mechanics Pipeline**

*Objective*: Decouple Mechanics from the Board instantiation.

- [x] Define the execution order of mechanics in a YAML configuration file.
- [ ] Update `Factory` to instantiate the list of `Mechanic` objects based on the YAML configuration.
- [x] Remove `self._mechanics` instantiation and the play() method from Board.

**Task 3: Extract Game Loop into Engine Class**

*Objective*: Remove runtime execution responsibilities from the Orchestrator.

- [x] Create an `Engine` class responsible for clock cycles, delta-time accumulation, and frame dispatching.
- [x] Move `Orchestrator.time()` and `Orchestrator.start()` into the Engine.
- [x] The `Engine` constructor should accept: the `Board`, the `Screens` dictionary, and the instantiated `Mechanics` list.
- [x] The `Engine` loop will replace `Board.play()` by explicitly iterating over its injected mechanics: `[m.update(board, delta) for m in self.mechanics]`.

**Task 4: Streamline Orchestrator**

*Objective*: Reduce Orchestrator to a pure dependency injection container.

- [~] Initialize `Mechanics` in `Orchestrator.ignite()`
- [~] Initialize `Engine` in `Orchestrator.ignite()`
- [x] Verify the `Orchestrator` no longer contains runtime logic or file-system traversal.

**Task 5: Upgrade the Frame Interface**

*Objective*: Evolve the Frame component interface to support multi-layered texture rendering for a single Asset.

* [ ] Refactor the `Frame.key()` abstract method to `Frame.keys()`, updating the return type from `str` to `List[str]`.
* [ ] Update `SingleFrame`, `IterableFrame`, and `StateFrame` implementations to wrap their resolved string in a list.
* [ ] Update `Registry.data()` to anticipate iterative querying if necessary, or ensure `Screen.draw()` handles the list iteration.

**Task 6: Implement SpriteFrame for Layered Equipment**

*Objective*: Create a specialized `Frame` component for Sprites that yields a strict Z-indexed list of frame keys based on the Sprite's inventory, delegating existence checks to the Registry.

* [ ] Create a `SpriteFrame` class inheriting from `StateFrame`.
* [ ] Override `keys(id, state)` to initialize a list, starting with the base Persona frame key: `{persona}-{state.action}-{state.direction}-{state.frame}`.
* [ ] Iterate over the active equipment keys in `state.inventory.equipment` in strict Z-index order (e.g., Base -> Armor -> Utility -> Tool -> Weapon).
* [ ] For each active equipment piece, blindly format and append the equipment frame key: `{equipment_key}-{state.action}-{state.direction}-{state.frame}`.

**Task 7: Update Rendering Pipeline in Screen.draw()**

*Objective*: Modify the Python-side culling and primitive extraction loop to handle multiple textures per Asset.

* [ ] In `Screen.draw()`, update the loop to iterate over the `List[str]` returned by `asset.frame.keys(asset.id, asset.state)`.
* [ ] For each key in the returned list, query `registry.data(key)`.
* [ ] If the texture exists, flatten it into the primitive tuple and append it to `active_assets`.
* [ ] Ensure `active_assets.sort(key=lambda x: x[6] + x[8])` remains untouched, relying on Python's stable sort to preserve the Z-index order yielded by `SpriteFrame`.

### Documentation Updates

!!! note
    To be completed by user.

The documentation currently reflects the older conceptual model and needs alignment with the grounded architecture.

**1. `01-assets.md # Asset Architecture**`

* **Update:** Explicitly state that the `Frame` component returns a `List[str]` rather than a single `str`. Clarify that an `Asset` can be a single logical entity composed of multiple superimposed rendered textures.

**2. `02-sprites.md # Equipment**`

* **Update:** Remove the section discussing `all` vs specific Action/Direction filters applied at runtime.
* **Add:** Document the "Registry Miss" pattern. Explain that equipment rendering is dictated by `SheetProperties.actions` configured in the asset directory. If an equipment does not possess an action, its omission from the rendering pipeline is handled implicitly by the `Registry` returning `None`.

**3. `06-architecture.md # Mechanics**`

* **Add:** Elaborate on the `AnimationMap`. Detail how `TransitionMechanics` and `PlayerMechanics` use `AnimationMap.action(state, equipment)` to enforce logical constraints (e.g., preventing a `attack` intention from translating into a `thrust` action if the Sprite lacks the required tool/weapon).