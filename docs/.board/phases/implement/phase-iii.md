
#### Implement: Phase III - Widgets

Goals: Widget Creation, Menu Configuration and Instantiation, Menu Traversal

**1. Data Models & Application Hooks**

* [ ] **Define Widget Properties**: Implement `WidgetProperties`, `MenuProperties`, and derived classes (e.g., `ButtonProperties`) in `app.models.properties`.
* [ ] **Define Widget State**: Implement `WidgetState` (managing `status: Enum`), `MenuState` (managing `focus`), and `ScreenPosition` in `app.models.state`.
* [ ] **Extend Factory Hydration**: Update `Factory.PROPERTY_MAP`, `Factory.STATE_MAP`, and `_hydrate` to parse the new schemas.
* [ ] **Configure Loaders**: Update `Loader` and `Orchestrator` to ingest `assets/widgets/main.yaml` and `data/menus/main.yaml`.

**2. Frame & Animation Implementation**

* [ ] **Widget Frames**: Implement `WidgetFrame` in `app.assets.frames`. The key schema must map to the Widget's status (e.g., `{id}-{state.status}`).
* [ ] **Widget Animations**: Implement `WidgetAnimation` in `app.assets.animations` to handle status transitions (e.g., `enabled` -> `selected` -> `active`).

**3. Event Bus & Game Loop Interruption**

* [ ] **Implement Event Queue**: Add an `Event` data class and an event queue to `Board` (or create a dedicated `Bus` class).
* [ ] **Trigger Events via Intentions**: Update `SpeechMechanics` and `CommerceMechanics` to push Events (e.g., `DialogueEvent`, `TradeEvent`) to the queue when specific Intentions are resolved.
* [ ] **Handle Interruptions**: Modify `Board` to process the event queue at the end of a tick. If an Event exists, set `self.paused = True`, instantiate the requested Menu, and load it into a temporary active UI state.

**4. Layout Engine & Instantiation**

* [ ] **Menu Constructor**: Create logic to build Menus based on the `layout` enum (`dock`, `stack`).
* [ ] **Coordinate Translation**: Implement a layout algorithm that converts `ScreenPosition` percentages into absolute `Position` coordinates using `screensize`.
* [ ] **State Injection**: Pass required arguments (e.g., `sprite.state.inventory`, `psyche.communication`) into the Menu constructor to hydrate dynamic Widget labels and icons.

**5. Mechanics & Input Handling**

* [ ] **Device Context Switching**: Update `Device` mappings to support a `MENU` context, translating raw SDL inputs into UI commands (Next, Previous, Select, Cancel).
* [ ] **Implement MenuMechanics**: Create `MenuMechanics.update()`. This system must query the `Device` for UI commands and mutate the `MenuState.focus` and `WidgetState.status`.
* [ ] **Execute in Loop**: Update `Board.menu()` to execute `MenuMechanics` while paused. Resolve menu closures by setting `board.paused = False` and purging the active Menu state.

**6. HUD / Screen Rendering**

* [ ] **Absolute Rendering Pass**: Add a `draw_menu()` method to `Screen` (or update `draw()`) that skips the `camera` clamping logic. Widget primitives must be flattened directly using their absolute `Position` and stamped onto the composite buffer without world-space culling.