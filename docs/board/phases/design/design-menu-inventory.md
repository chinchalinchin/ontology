#### Design: Menu M000 - Inventory

* **Purpose**: The Inventory is a collection of Menus for updating the Player's Slotted Inventory. 
* **Description**: Displays the Player's currently slotted inventory and stats.

##### Menu: Specification

!!! note "Scope"
    Eventually, Tabs will be introduced into the Menu system and the Menus described will be aggregated into different Tabs of the unified Inventory Menu. For the time being, each Menu will be mapped to a different input and displayed separately through different `MenuEvent` dispatches, using a Tab-less Menu for each one.

**Menu: Equipment**

* `dock(header)`: `pane(content="Equipment")`
* `dock(gear)`: `button(slot[k]) for k, v in slots.equipment.items() if k in Gear` (`armor`, `shield`)
* `dock(equipment)`: `button(slot[k]) + gizmo(inventory[m(k)]) for k in slots.equipment.keys() if k not in Gear`
    * `slots.equipment.weapon` $\to$ `inventory.sheathe`
    * `slots.equipment.tool` $\to$ `inventory.belt`
    * `slots.equipment.utility` $\to$ `inventory.bag`

Each non-Gear row of `Equipment` is traversible. Selecting a slottable equipment piece from a row updates the corresponding slot at the beginning of the row, mutating `SheetState.slots.equipment` in place and updating the bound icon closure.

**Menu: Crafts**

* `dock(header)`: `pane(content="Crafts")`
* `stack`:
    * `dock(subheader)`: `pane(content="Resources")`
    * `dock(materials)`: `gizmo(inventory.pack)`
    * `dock(crops)`: `gizmo(inventory.sack)`
* `stack`:
    * `docker(subheader)`: `pane(content="Placeholder for Known Craft Formulae")`

**Menu: Pouch**

* `Row(header)`: `pane(content="Pouch")`
* `Row(grip)`: `button(slots.grip.right) + button(slots.grip.left)`
* `Row(items)`: `gizmo(inventory.pouch)`
