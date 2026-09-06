#### Refactor: Phase 05.04 - ExchangeController & Loot

**Overview** 

TODO

##### Tasks

**Task #1: Chest Interaction Mechanics**

* [ ] TODO

**Task #2: Exchange Controller**

* [!] Create `ExchangeController(MenuController)`.
* [!] Implement `select()` to intercept `EQUIP` selections, resolving the target equipment key and modifying the `SpriteState.inventory`.
* [!] Implement `update()` to monitor Sprite inventory arrays and emit `UpdateEvents` to redraw capacity meters or dynamically rebuild the layout if items are dropped.

