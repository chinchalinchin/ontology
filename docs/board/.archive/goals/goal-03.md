#### Achieve: Goal 03 - ExchangeController & Loot Interactions

**Overview**

Implement `ExchangeController` and the dual-collection exchange menu to allow transactional inventory swapping between the player and container entities (Chests, Crates, and defeated NPC inventories). Leveraging the Phase 04.05 Gizmo macro pipeline, this controller will bind two independent `CollectionState` panes within a single modal, managing item transfers, capacity enforcement, and reciprocal UI refreshes.

##### Goal: Dual-Aperture Exchange Menu Layout

Declare the `exchange` menu configuration in `data/config/menus/main.yaml` pairing the player's pack grid with the target container's inventory grid, centered within a docking layout with transfer action buttons.

##### Goal: Transactional Exchange Logic

Implement `ExchangeController.select()` to process slot transfers: clicking an item in Pane A moves the item to the backing collection of Pane B if capacity permits, emitting reciprocal `UpdateEvent` signals to refresh both Gizmo aperture slices.

##### Tasks

**1. Task: Schematize Exchange Context & YAML Specification**

*Objective*: Define the runtime context payload and AST configuration for dual-collection inspection.

* [ ] Subtask: Implement `ExchangeContext(MenuContext)` in `app.game.menus.contexts` holding references to `source: Inventory` and `target: Inventory | ContainerState`.
* [ ] Subtask: Define `exchange` menu in `data/config/menus/main.yaml` declaring `player-exchange-grid` and `target-exchange-grid` gizmo nodes with distinct bindings.

**2. Task: Implement ExchangeController Service**

*Objective*: Build the controller managing bidirectional transfers and focus management across panes.

* [ ] Subtask: Implement `app.game.menus.controllers.exchange.ExchangeController` inheriting from `MenuController`.
* [ ] Subtask: Implement `select()` logic handling `selection: "slot"` to pop the item from the selected container and append it to the reciprocal container.
* [ ] Subtask: Emit `UpdateEvent` payloads targeting both Gizmo pane IDs to update frame indices without rebuilding ASTs.
* [ ] Subtask: Implement `Interactions.CANCEL` handling to serialize container state and close modal.

**3. Task: Connect Chest & Loot Interaction Pipeline**

*Objective*: Trigger the exchange menu from world interactions.

* [ ] Subtask: Update `InteractionMechanics` to emit `MenuEvent("exchange", ExchangeContext(...))` when a player interacts with an open `Chest` or loot drop.
* [ ] Subtask: Write unit tests verifying cross-container item transfer and focus retention.
