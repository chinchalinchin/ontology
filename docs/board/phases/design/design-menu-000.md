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

##### Menu: Model

```yaml
# ---------------------------------------------------------------------
# -------------------------------------------------------- MENU: THEMES
# ---------------------------------------------------------------------
themes:
  colors:
    pane: &pane dark-solid
  alignments:
    bottom: &bottom
      horizontal: center
      vertical: end
    center: &center
      horizontal: center
      vertical: center
    start: &start
      horizontal: start
      vertical: center
    end: &end
      horizontal: end
      vertical: center
  dimensions:
    root: &root
      pw: 0.50
      pl: 0.175
    child: &child
      pw: 0.16
      pl: 0.10
    slot: &slot
      pw: 0.08
      pl: 0.08
# ---------------------------------------------------------------------
# ---------------------------------------------------------- MENU: VIEW
# ---------------------------------------------------------------------
menus:
  view:
    controller: display
    roots:
      - instance: panes
        id: *pane
        name: view-menu
        parameters:
          dimensions: *root
          justification: *bottom
          alignment: *center
          layout: dock
          gap: 5
          margins: 5
          children:
            # ----------------------------------------------------------
            # --------------------------------------------- VIEW: METERS
            # ----------------------------------------------------------
            - instance: panes
              id: transparent
              name: view-pane-meters
              parameters:
                dimensions: *child
                layout: stack
                alignment: *start
                gap: 5
                children:
                  # ------------------------------------- METER: HEALTH
                  - instance: meters
                    id: health
                    name: health-meter
                    bind:
                      schema: meter
                      target:
                        meter: context.sprite.meters.health
                  # --------------------------------------------------
                  # ------------------------------------- METER: MAGIC
                  - instance: meters
                    id: magic
                    name: magic-meter
                    bind:
                      schema: meter
                      target:
                        meter: context.sprite.meters.magic
                  # --------------------------------------------------
            # ----------------------------------------------------------
            # ---------------------------------------------- VIEW: SLOTS
            # ----------------------------------------------------------
            - instance: panes
              id: transparent
              name: view-pane-slots
              parameters:
                dimensions: *child
                layout: dock
                alignment: *start
                margins: 2
                gap: 5
                children:
                  # -------------------------------------- SLOT: WEAPON
                  - instance: panes
                    id: transparent
                    name: pane-slot-weapon
                    parameters:
                      dimensions: *slot
                      layout: overlay
                      alignment: *center
                      gap: 0
                      children:
                        - instance: buttons
                          id: slot
                          name: weapon-slot
                          parameters:
                            status: disabled
                        - instance: icons
                          id: weapons
                          name: weapon-icon
                          bind:
                            schema: icon
                            target:
                              icon: context.sprite.slots.equipment.weapon
                  # --------------------------------------------------
                  # ------------------------------------- SLOT: SHIELD
                  - instance: panes
                    id: transparent
                    name: pane-slot-shield
                    parameters:
                      dimensions: *slot
                      layout: overlay
                      alignment: *center
                      gap: 0
                      children:
                        - instance: buttons
                          id: slot
                          name: shield-slot
                          parameters:
                            status: disabled
                        - instance: icons
                          id: shields
                          name: shield-icon
                          bind:
                            schema: icon
                            target:
                              icon: context.sprite.slots.equipment.shield
                  # --------------------------------------------------
```