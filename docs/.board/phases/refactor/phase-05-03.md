#### Refactor: Phase 05.03 - Menu Controllers

**Overview** 

TODO

##### Bugs

**Bug 1. Hardcoded Icon Pagination**

In `Provider._unpack_widget`, the `pagesize` attribute is hardcoded to `1`. While this functions correctly for text (since `_paginate` calculates and returns a list of fitted strings), it breaks Icon widgets. A Page widget designed to display a grid of inventory Icons will only render a single Icon per page.

##### Tasks

**Task 1. Delegate Equipment Handling to Controller**

*Objective*: Ensure controller specific logic is migrated into the new Menu-Widget paradigm.

* [ ] Remove the `equip()` method from `MenuMechanics`.
* [ ] Verify `MenuMechanics.update()` acts strictly as a traversal router and event delegator.

**Task #2: Inventory Controller**

* [ ] Create `InventoryController(MenuController)`.
* [ ] Implement `select()` to intercept `EQUIP` selections, resolving the target equipment key and modifying the `SpriteState.inventory`.
* [ ] Implement `update()` to monitor Sprite inventory arrays and emit `UpdateEvents` to redraw capacity meters or dynamically rebuild the layout if items are dropped.

**Task #3: Dialogue Controller**

* [ ] Create `DialogueController(MenuController)`.
* [ ] Implement `open()` to query the `Library` service using the `SpriteState.psyche.persona` and `plot` keys, injecting the resulting script into the context.
* [ ] Implement `select()` to hook the `SCROLLDOWN` / `SCROLLUP` bindings and route them to the active `Page` widget.

