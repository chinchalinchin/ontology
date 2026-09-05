#### Refactor: Phase 05.03 - ScrollController, Library & Plots

**Overview** 

The core functionality of Widgets and Menus has been implemented and tested. The View, Main and Load Menu are functional. Widgets react to live game state updates. The goal of this refactor is to enhance Menu interaction in the game loop, through implementing Controller interfaces and instantiating Events through interactions to initiate the Menu.

**Goals**

The eventual goal (in the next [phase](../refactor/phase-05-04.md)) is to layout and implement the Inventory controller, but the larger Menu framework needs to be put to the test first. Before the complexity of the Inventory is tackled, a simpler case of the ScrollController will be undertaken. This will involve implementing the [Sign Object](../../../01-assets.md#signs) to trigger an ingame Text Menu.

This, in turn, will require implementation of the [Library](../../../08-plots.md#library), to parse and hold the dialogue to be rendered. As yet another consequence, this will require further elaboration of the plotting mechanism used bythe game.

The font and text rendering is, as of yet, purely theoretical and untested. Many things could go wrong along the way. The current goal is to determine what must be done in order to get Signs up and running, alongside the Library and MenuEvent('text').

**Specification**

ScrollController will be polymorphic to handle Dialogue Menus with Character Portraits (initiated by the `speak` Intention in conjunction with Sprite `state.psyche.dialogue`) and simpler Text Menus (initiated by the `interact` Intention with Signs). It may also to be used to handle submenus in the Main Menu, when the Main Menu is fully implemented, although this is not a certainty at this point.

**Working Schemas**

```yaml
menus:
  # ---- TEXT MENU SCHEMA
  text:
    controller: scroll
    roots: 
      - id: neutral
        name: text-menu
        position:
          px: 0.1
          py: 0.55
        layout: dock
        alignment: start
        gap: 10
        children: 
          - instance: pages
            id: text
            name: text-display
            bind:
              state: context.content # WORKING IDEA
          - instance: buttons
            id: arrow-up
            name: text-scroll-up
            bind: 
              selection: scrollup
              selector: text-display
          - instance: buttons
            id: arrow-down
            name: text-scroll-down
            bind: 
              selection: scrolldown
              selector: text-display
  # ---- DIALOGUE MENU SCHEMA
  dialogue:
    controller: scroll
    roots: 
      - id: neutral
        name: dialogue-menu
        position:
          px: 0.1
          py: 0.55
        layout: dock
        alignment: start
        gap: 10
        children:
          - id: transparent-slot 
            name: portrait-slot-container
            layout: overlay
            alignment: center
            gap: 0
            children:
              - instance: buttons
                id: slot
                name: portrait-slot
                status: disabled
              - instance: icons
                id: portraits 
                name: character-portrait-icon
                bind:
                  state: context.sprite.state.character.portrait
          - instance: pages
            id: dialogue
            name: character-speech
            bind:
              state: context.sprite.state.psyche.dialogue
          - instance: buttons
            id: arrow-up
            name: character-speech-scroll-up
            bind: 
              selection: scrollup
              selector: character-speech
          - instance: buttons
            id: arrow-down
            name: character-speech-scroll-down
            bind: 
              selection: scrolldown
              selector: character-speech
```

```yaml
# ------ LIBRARY SCHEMA
library:
  plot-a:
    sprite-a:
      busy: Away with you! I am engaged in endeavors!
      greeting: Good morrow, neighbor!
      insult: Thou art a brutish knave!
    town-sign:
      spring: Welcome to Town
      summer: WANTED Player 
      autumn: Harvest Festival Coming
      winter: Road Blocked
  plot-b:
    sprite-a:
      busy: Go away!
      greeting: What mistery...
      insult:  You're a right simpleton!
    town-sign:
      spring: BE GONE
      summer: NO TRAVELLERS WANTED 
      autumn: NO TRESPASSERS
      winter: ALL INTRUDERS WILL BE EXECUTED
```

```yaml
# ---- PLOT SCHEMA
plots:
  town-locked:
    - next: town-unlocked
      conditions:
        - sprites['player'].state.inventory.loot['town-key'] >= 1
    - next: town-unlocked
      conditions:
        - sprites['town-guard'].mutators.triggers.dead
    - next: town-unlocked
      conditions:
        - sprites['mayor'].state.memory.relationships['player'] != Relationships.FRIEND
  town-unlocked:
    - next: town-hostile
      conditions:
        - sprites['mayor'].state.memory.relationships['player'] == Relationships.FOE
  town-hostile:
    - next: town-unlocked
      conditions:
        - sprites['mayor'].state.memory.relationships['player'] != Relationships.FOE
```

##### Goal: Plot State & Mechanics

Because the Plot is a property of the World, its current state belongs on the `Board`. When the engine bootstraps, it needs to know where the world currently stands so the `Library` can route dialogue correctly.

**Location:** `/src/data/state/<board-key>/plot.yaml`

```yaml
plot:
  current: town-unlocked
  path:
    - woke-up
    - found-sword

```

Where `current` is the current state of the plot and `path` is a list of time-ordered plot states the plot has progressed through during the entire history of gameplay. The first entry is the earliest.

To progress the plot, introduce `PlotMechanics` into the `world` mechanics pipeline.

Just as `TransitionMechanics` iterates over Sprites to check if their Intention conditions are met, `PlotMechanics` checks if the *Board's* current plot conditions are met.

**Logical Flow of `PlotMechanics.update()`:**

1. Retrieve the current plot key: `current_plot = board.plot.current`.
2. Look up its rules: `rules = board.configurations.plots.get(current_plot)`.
3. Evaluate the ISL `conditions` against the current `board` and `sprites` dictionaries (using the same lambda compilation strategy you use for Intentions).
4. If the conditions evaluate to `True`, update the state: `board.plot.current = rules.next`.

*Benefit:* Because this executes in the `world` mechanics array, it naturally pauses when a `MenuEvent` fires. The plot cannot advance while the player is reading dialogue or trading, which prevents edge-case bugs where a background event triggers a plot shift while the UI is open.

##### Goal: Library

When `InteractionMechanics` processes a Player reading a Sign, it executes:
`content = Library.fetch(board.plot.current, target.state.persona, target.state.lexicon)`
and emits the literal string to the Event Bus.

##### Tasks

**Task #0: Sign Object**

* [x] Create a Sign Object to trigger ingame Text menus.
  * [x] Add state model.
  * [x] Add property model.
  * [x] Configure assets and state files.

**Task #1: Data Models & Configurations**

* [ ] Create `PlotConfiguration` in `app.models.config` (mirroring `IntentionConfiguration`).
* [ ] Create `PlotState` in `app.models.state` (fields: `current: str`, `previous: List[str]`).
* [ ] Add `plots` to `ConfigurationSchema` and `plot` to `StateSchema`.
* [ ] Update `Board.__init__` to accept and expose `board.plot`.

**Task #2: Library Service**

* [ ] Create `app.services.library.Library` to parse `src/data/config/library/main.yaml`.
* [ ] Implement a static or singleton fetch method: `Library.fetch(plot_key, persona, lexicon) -> str`.
* [ ] Inject `Library` into `Board`.

**Task #2: InteractionMechanics Injection**

* [ ] Update `InteractionMechanics.update()`: When a Player interacts with a `Sign`, query the `Library` using `board.plot`, `sign.state.persona`, and `sign.state.lexicon`.
* [ ] Emit `MenuEvent(id='text', context={'content': fetched_text})` to the bus.

**Task #3: Plot Mechanics**

* [ ] Create `PlotMechanics(Mechanic)` in `app.game.logic.mechanics.intentional`.
* [ ] Implement `update()` to evaluate `board.configurations.plots[board.plot.current].conditions` using the existing ISL parser.
* [ ] Add `Mechanics.PLOT` to the `Mechanics` Enum and `Factory.MECHANICS_MAP`.
* [ ] Add `plot` to the `world` mechanics sequence in `/src/data/config/mechanics/main.yaml`.

**Task #4: ScrollController Implementation**

* [ ] Create `ScrollController(Controller)`.
* [ ] Implement `select(focus: str, menu: Menu, board: Board, bus: deque)`.
* [ ] In `select()`, retrieve `action = menu.widgets[focus].binding.selection` (e.g., `scrollup`).
* [ ] Retrieve target widget `target = menu.widgets[menu.widgets[focus].binding.selector]`.
* [ ] Call `target.state.scrolldown()` (or up) and emit `UpdateEvent(widget=target, content=target.state.current())` to the bus.

**Task #5: Interaction Routing**

* [ ] Update `InteractionMechanics` (for Signs/Objects) and `SpeechMechanics` (for Sprites).
* [ ] When triggering dialogue, query the `Library` using `board.plot.current`.
* [ ] Emit `MenuEvent` with the fully resolved text payload, keeping the UI generic and isolated.