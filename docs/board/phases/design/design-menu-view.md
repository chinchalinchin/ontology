#### Design: Menu M000 - View

* **Purpose**: The View is the Heads-Up Display (HUD). 
* **Description**: Displays the Player's currently slotted inventory and stats.

##### Menu: Specification

Root Panes is transparent. Buttons and Meters should not have visible panes beneath them.

* top left corner: 
    * pane(stack: Meters): meter(health), meter(manager)
* bottom right corner:
    * pane(dock: Grip): slot(grip.left), slot(grip.right)
* bottom left corner:
    * pane(stack):
        * pane(dock: Gear): slot(equipment.armor), slot(equipment.shield)
        * pane(dock: Slottables): slot(equipment.utility), slot(equipment.tool), slot(equipment.weapon)