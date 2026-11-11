#### Achieve: Goal 05 - InventoryController

**Overview** 

TODO

##### Tasks

**Task 1. Delegate Equipment Handling to Controller**

*Objective*: Ensure controller specific logic is migrated into the new Menu-Widget paradigm.

* [x] Remove the `equip()` method from `MenuMechanics`.
* [x] Verify `MenuMechanics.update()` acts strictly as a traversal router and event delegator.

**Task #2: Inventory Controller**

* [x] Create `InventoryController(MenuController)`.
* [x] Implement `select()` to intercept `EQUIP` selections, resolving the target equipment key and modifying the `SpriteState.inventory`.
* [ ] Implement `update()` to monitor Sprite inventory arrays and emit `UpdateEvents` to redraw.

