#### Refactor: Phase 04.05 - Gizmos

**Goal**: Similar to Compositions, there needs to be a way of unpacking reusable menu components into flat lists of Widgets for rendering. A pre-defined configuration of Widgets will be called a *Gizmo*.

**Use Case**: The InventoryController will require a configuration of Widgets (a Gizmo) for listing an arbitrary number of items from different fields of the Inventory (`pouch`, `pack`). 

**General Idea** New `app.services.generators` for generating Menu Gizmos.
    - Input: List of icon str.
    - Ouput: List of Widgets. 

**Edge Cases**

- If number of items exceeds the number of slots that can fit into a Gizmo pane. How to handle traversal and rendering in these cases?
    - Consideration: Implicitly needs to handle scrolling.

**Current Widget Properties**

```yaml
widgets:
  buttons:
    slot: 
      dimensions:
        w: 40
        l: 40
    icon:
      dimensions:
        w: 71
        l: 28
    label: 
      dimensions:
        w: 142
        l: 28
    arrow-down:
      dimensions:
        w: 24
        l: 24
    arrow-left:
      dimensions:
        w: 24
        l: 24
    arrow-right:
      dimensions:
        w: 24
        l: 24
    arrow-up:
      dimensions:
        w: 24
        l: 24
  icons:
    digits:
      dimensions:
        w: 12
        l: 14
      frames:
        - zero
        - one
        - two
        - three
        - four
        - five
        - six
        - seven
        - eight
        - nine
    weapons:
      dimensions:
        w: 32
        l: 32
      frames:
        - shortsword
        - dagger
        - knife
        - spear
    shields:
      dimensions:
        w: 32
        l: 32
      frames:
        - buckler
    portraits:
      dimensions: 
        w: 50
        l: 63
      frames:
        - female-persona-1
        - female-persona-2
        - female-persona-3
        - female-persona-4
        - female-persona-5
        - female-persona-6
        - empress-jasilynn
        - female-persona-8
        - female-persona-9
        - female-persona-10
        - female-persona-11
        - female-persona-12
        - female-persona-13
        - male-persona-1
        - male-persona-2
        - male-persona-3
        - male-persona-4
        - male-persona-5
        - male-persona-6
        - male-persona-7
        - male-persona-8
        - male-persona-9
        - male-persona-10
        - male-persona-11
  meters:
    health:
      dimensions:
        w: 72
        l: 20
    magic:
      dimensions:
        w: 72
        l: 20
  pages:
    dialogue:
      dimensions:
        w: 640
        l: 96
    header:
      dimensions:
        w: 426
        l: 163 
    scroll:
      dimensions:
        w: 330
        l: 54
    notification:
      dimensions:
        w: 192
        l: 64
    parchment:
      dimensions:
        w: 465
        l: 273
    portrait:
      dimensions:
        w: 96
        l: 95
  panes:
    dark:
      dimensions:
        w: 318
        l: 180
    dark-small:
      dimensions:
        w: 318
        l: 78
    neutral:
      dimensions:
        w: 318
        l: 180
    neutral-small:
      dimensions:
        w: 318
        l: 78
    light:
      dimensions:
        w: 318 
        l: 180
    light-small:
      dimensions:
        w: 318
        l: 78
    transparent-slot:
      dimensions:
        w: 40
        l: 40
    transparent-block:
      dimensions:
        w: 80
        l: 80
```

**Current Text Menu**

Example of a Menu configuration,

```yaml
menus:
  text:
    controller: scroll
    roots: 
      - id: neutral
        name: text-menu
        position:
          # 480 x 480
          px: 0.175
          py: 0.60
        layout: dock
        alignment: center
        gap: 15
        children: 
          - instance: pages
            id: notification
            name: text-display
            bind:
              schema: library
              target: 
                plot: context.plot.current
                persona: context.object.persona
                lexicon: context.object.lexicon
          - id: transparent-slot
            name: text-scroll-buttons
            layout: stack
            alignment: center
            gap: 5
            children:
              - instance: buttons
                id: arrow-up
                name: text-scroll-up
                bind: 
                  schema: select
                  target:
                    selection: scrollup
                    selector: text-display
              - instance: buttons
                id: arrow-down
                name: text-scroll-down
                bind: 
                  schema: select
                  target:
                    selection: scrolldown
                    selector: text-display
```

**Notes**

- Need a Menu concept of "Pseudo-state" to prepopulate the Gizmo widget bindings.