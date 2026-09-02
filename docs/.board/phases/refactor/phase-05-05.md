#### Refactor: Phase 05.05 - Main Menu & Saving

**Overview** 

The goal is to instantiate the Main Menu before the main loop kicks in and determine where in the initialization flow the Main Menu should be instaniated and shown. 

Currently the `init_subsystems()` in the Orchestrator requires,

```python
    if not headless:
        render.show()
```

This *MUST* be called before the Registry inits, or else nothing will render. This statement has been moved to various locations to confirm this behavior; it's current location is the *only* location that has produced animation and rendering. 

However, in doing this, a blank screen is produced during Registry initialization. Ideally, the Main Menu should be shown as quickly as possible, before the other systems even come online. 

**Schema**

```yaml
# --- DRAFT: MAIN MENU SCHEMA
menus:
  main:
    controller: display
    roots: 
      - id: neutral
        name: main-menu
        position:
          px: 0
          py: 0
        layout: stack
        alignment: center
        gap: 10
        children: 
          - instance: buttons
            id: label
            name: new-game
            bind: 
              selection: new
          - instance: buttons
            id: label
            name: load-game
            bind: 
              selection: load
          - instance: buttons
            id: label
            name: options-menu
            bind:
              selector: options
              selection: menu
          - instance: buttons
            id: label
            name: editor-menu
            bind:
              selector: editor
              selection: menu
```

##### Tasks

**1. Task: TODO**

*Objective*: TODO

- [] Subtask: TODO

**2. Task: TODO**

*Objective*: TODO

- [] Subtask: TODO