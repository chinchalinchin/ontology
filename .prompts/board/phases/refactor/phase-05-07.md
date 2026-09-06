#### Refactor: Phase 05.04 - InventoryController

**Overview** 

TODO

##### Tasks

**Task 1. Delegate Equipment Handling to Controller**

*Objective*: Ensure controller specific logic is migrated into the new Menu-Widget paradigm.

* [ ] Remove the `equip()` method from `MenuMechanics`.
* [ ] Verify `MenuMechanics.update()` acts strictly as a traversal router and event delegator.

**Task #2: Inventory Controller**

* [!] Create `InventoryController(MenuController)`.
* [!] Implement `select()` to intercept `EQUIP` selections, resolving the target equipment key and modifying the `SpriteState.inventory`.
* [!] Implement `update()` to monitor Sprite inventory arrays and emit `UpdateEvents` to redraw capacity meters or dynamically rebuild the layout if items are dropped.

