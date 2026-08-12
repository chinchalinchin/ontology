#### Implement: Phase II - Player

1. **Data-Driven Player Initialization**

* [~] **Configuration:** Create `src/data/state/<board>/player.yaml` to define the Player's initial state (Layer, Position, Character stats). Map the category to `sheets` and instance to `sprites`.
* [~] **Factory Migration:** Remove the hardcoded `__init__` in `src/app/input/player.py`. Route the Player's instantiation through `Orchestrator.migrate()` using the standard `Factory` methods.
* [~] **Board Integration:** Modify `Board.__init__` to ensure the Player is appended to `self._assets` so it successfully enters the `_cached_categories` and `_cached_instances` dictionaries.
* [x] Remove the Player wrapper class in `src/app/input/player.py`.
* [x] Update `Orchestrator.migrate()` to instantiate the Player as a standard Asset using the `PyPlayerState` model, i.e. add `sheets.players` to Asset Recipes (`/src/assets/main.yaml`) .

2. **Input Device Configuration & Mapping**

* [ ] **Schemas:** Define a `PyDeviceMappingConfiguration` Pydantic model and corresponding YAML schema (`src/app/data/player/mappings.yaml`) to map physical hardware keys (e.g., SDL scancodes) to `Intentions` and `Goals`.
* [ ] **Device Polling:** Implement `Keyboard.poll()` in Cython/Python to return a mapped dictionary of current active intents and vectors. This method must query the hardware state (via Cython/SDL) and return a lightweight input bitmask or data structure, *not* a full `PlayerState` object.
* [ ] Modify `Orchestrator.orchestrate()` to initialize the `Keyboard` device and pass it directly to the `Board` (and subsequently the `PlayerMechanic`), completely decoupling it from the `Player` Asset.

3. **Implement PlayerMechanic**

* [~] Add PlayerMechanic(device: Device) to src/app/game/mechanics.py.
* [ ] Implement the update() method to poll the device and apply the mapped Intention directly to the Player's state.intention.
* [ ] Implement pseudo-goal projection: translate the polled directional vectors into a temporary state.goal.position relative to the Player's current position.
* [ ] Pipe the updated state through AnimationMap.action and AnimationMap.direction to resolve the animation frame.

4. **Unified Rendering Integration**

* [x] **Refactor `Screen.draw`:** Update the signature to `draw(self, assets: List[Asset], registry: Registry)`. Remove the explicit `player` argument. The Player will be passed automatically within the assets list.
* [ ] Implement a lightweight Python sort on the active_assets list immediately after camera culling. Sort `key: asset.state.position.y + asset.dimensions.l`
* [ ] Ensure the sorted tuples are passed to the C-level render() function to guarantee correct painter's algorithm execution.

5. **Physics & Collision Connectivity**

* [ ] **Verification:** Ensure that once the Player is cached as `AssetCategories.SHEETS`, `CollisionMechanics` and `SwitchMechanics` correctly calculate overlaps with the Player's hitboxes. No new logic should be required in the mechanics classes if Task 1 is executed correctly.