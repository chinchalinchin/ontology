#### Refactor: Phase 05.03 - Menu Controllers

**Overview** 

TODO

##### Bugs

**Bug 1. Pass-by-Reference Optimization Failure (HUD Deadlock)**

`Provider._unpack_widget` locates the reference but extracts immutable primitive values (`reading = resolved.current`). Furthermore, `MeterState` was never updated to implement the `@property` wrappers. Health and magic bars will render their initial values but never update.

**Bug 2. Hardcoded Icon Pagination**

In `Provider._unpack_widget`, the `pagesize` attribute is hardcoded to `1`. While this functions correctly for text (since `_paginate` calculates and returns a list of fitted strings), it breaks Icon widgets. A Page widget designed to display a grid of inventory Icons will only render a single Icon per page.

##### Tasks

**Task 1. Delegate Equipment Handling to Controller**

*Objective*: Ensure controller specific logic is migrated into the new Menu-Widget paradigm.

* [!] Remove `MenuMechanics.equip()`. 
* [!] Create `InventoryController` in `app.game.menus.controllers.inventory` to handle equipment logic via `SelectionEvent` bindings.

