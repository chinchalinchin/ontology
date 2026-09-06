#### Refactor: Phase 05.03 - ScrollController, Library & Plots

**Overview** 

The core functionality of Widgets and Menus has been implemented and tested. The View, Main and Load Menu are functional. Widgets react to live game state updates. The goal of this refactor is to enhance Menu interaction in the game loop, through implementing Controller interfaces and instantiating Events through interactions to initiate the Menu.

**Goals**

The eventual goal (in the next [phase](../refactor/phase-05-04.md)) is to layout and implement the Inventory controller, but the larger Menu framework needs to be put to the test first. Before the complexity of the Inventory is tackled, a simpler case of the ScrollController will be undertaken. This will involve implementing the [Sign Object](../../../01-assets.md#signs) to trigger an ingame Text Menu.

This, in turn, will require implementation of the [Library](../../../08-plots.md#library), to parse and hold the dialogue to be rendered. As yet another consequence, this will require further elaboration of the plotting mechanism used bythe game.

The font and text rendering is, as of yet, purely theoretical and untested. Many things could go wrong along the way. The current goal is to determine what must be done in order to get Signs up and running, alongside the Library and MenuEvent('text').

**Specification**

ScrollController will be polymorphic to handle Dialogue Menus with Character Portraits (initiated by the `speak` Intention in conjunction with Sprite `state.psyche.dialogue`) and simpler Text Menus (initiated by the `interact` Intention with Signs). It may also to be used to handle submenus in the Main Menu, when the Main Menu is fully implemented, although this is not a certainty at this point.

**Current Schemas in /src/data/config/menus/**

*NOTE*: This wil be updated during the implementation of this phase. See below.

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

**Working Schemas (Not Yet Implemented)**

```yaml
# ------ LIBRARY SCHEMA
library:
  castle-dawn-locked:
    jasiylnn:
      busy: Out of my way!
      greeting: Who are you?
      mock: Begone, simpleton!
      threaten: One wrong move and I will call my guards.
    castle-dawn-sign:
      spring: Spring has Sprung
      summer: Summer must Simmer
      autumn: Autumn has Fallen
      winter: Winter must Enter 
  castle-dawn-unlocked:
    jasiylnn:
      busy: Away with you! I am engaged in endeavors!
      greeting: Good morrow, neighbor!
      mock: Thou art a brutish knave!
      threaten: Your head shall soon be on a spike!
    castle-dawn-sign:
      spring: Welcome to Castle Dawn
      summer: Travelling Troupe in Town Square
      autumn: Harvest Festival Soon
      winter: Road Blocked
  castle-dawn-hostile:
    jasiylnn:
      busy: Go away!
      greeting: Bow before your betters.
      mock: Your presence is troublesome.
      threaten: My guards will cut you down!
    castle-dawn-sign:
      spring: BE GONE
      summer: NO TRAVELLERS WANTED 
      autumn: NO TRESPASSERS
      winter: ALL INTRUDERS WILL BE EXECUTED
```

```yaml
# ---- PLOT SCHEMA
plots:
  castle-dawn-locked:
    - next: castle-dawn-unlocked
      conditions:
        - sprites[constants.RequiredAssets.PLAYER.value].state.inventory.loot.get('writ-of-dawn') >= 1
    - next: town-unlocked
      conditions:
        - sprites.get('castle-dawn-guard')
        - sprites['castle-dawn-guard'].mutators.triggers.dead
    - next: castle-dawn-unlocked
      conditions:
        - sprites.get('evil-empress-jasilynn')
        - sprites['evil-empress-jasilynn'].state.memory.relationships['player'] != constants.Relationships.FRIEND
  castle-dawn-unlocked:
    - next: castle-dawn-hostile
      conditions:
        - sprites.get('evil-empress-jasilynn')
        - sprites['evil-empress-jasiylnn'].state.memory.relationships['player'] == constants.Relationships.FOE
  castle-dawn-hostile:
    - next: castle-dawn-unlocked
      conditions:
        - sprites.get('evil-empress-jasilynn')
        - sprites['evil-empress-jasiylnn'].state.memory.relationships['player'] != constants.Relationships.FOE
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

##### Goal: Update Widget Binding

Instead of hardcoding specific resolution paths in the UI, the `Provider` will act as a compiler for `Bindings`. When the `Provider` unpacks a Widget, it reads a `bind` dictionary from the YAML schema and returns a native Python `Callable` that the Widget's `State` object (e.g., `DisplayState.content_function`) evaluates continuously.

**Working Schema**

```yaml
# 1. LibraryBinding
bind:
  type: library
  schema: context.<asset>.<field>

# 2. MeterBinding
bind:
  schema: meter
  target: context.<asset>.<field>

# 3. IconBinding
bind:
  schema: icon
  target: context.<asset>.<field>

# 4. SelectBinding
bind:
  schema: select
  selection: scrolldown | scrollup
  selector: <asset-id>
```

Each binding *expects* the bound Asset field to conform to the binding schema; otherwise the binding will not function properly. In other words, 

- `if schema == library: typeof(context.<asset>.<field>) == LibraryBinding`
- `if schema == meter: typeof(context.<asset>.<field>) == MeterBinding`
- `if schema == icon: typeof(context.<asset>.<field>) == IconBinding`

`schema == select` are handled specially, since they are bindings to Widget actions in the menu itself, i.e. they do not receive external updates.

**Binder**

When `Engine._drain()` calls `Provider.unpack(...)`, it passes the `Board` and the resolved `MenuEvent.context.binding` payload (Binding model). The `Provider` utilizes the `Binder` factory methods, e.g.:

```python
def bind_library(self, binding: LibraryBinding) -> Callable:
   
    def content_function():
        return self.library.fetch(**binding)

    return content_function
```


##### Bug B005: DisplayState Pagination Performance Loop

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In the proposed implementation of `Provider._unpack_page()`, the `content_function` evaluates `self._paginate(raw, font, w, l)`. Because `DisplayState.current()`, `DisplayState.more()`, and `DisplayState._pagecount` all access the `self.content` property, the `content_function` lambda is executed multiple times per interaction.

`_paginate()` splits strings and calls the C-level SDL text measurement function (`TTF_SizeUTF8`) in a loop to calculate word wrapping. Executing this geometric calculation repeatedly every time the player scrolls or the UI refreshes will lock the main thread and severely degrade the frame rate.

**Steps to Replicate** 

1. Interact with a Sign Object to open a Text Menu.
2. The `ScrollController` triggers `MenuEvent('text')`.
3. Press `SELECT` to scroll down. `ScrollController` calls `page.state.scrolldown()`.
4. `scrolldown()` calls `self.more()`, which accesses `self.content`, executing `TTF_SizeUTF8` over the entire text block.
5. The bus emits `UpdateEvent` with `page.state.current()`, which accesses `self.content` again, executing `TTF_SizeUTF8` over the entire text block a second time.

**Proposed Remediation**

Introduce lazy-evaluation caching into `DisplayState` or the `Binder` lambda. 

When `content_function()` is executed, it should check a local `_cached_pages` variable. If the text has already been paginated, it should return the cached list. Because the game world pauses while a Menu is open, the Plot state cannot change, meaning the retrieved Library dialogue is guaranteed to remain perfectly static for the lifespan of the active Menu.

##### Tasks

**Task #0: Sign Object**

* [x] Create a Sign Object to trigger ingame Text menus.
  * [x] Add state model.
  * [x] Add property model.
  * [x] Configure assets and state files.

**Task #1: Data Models & Configurations**

* [x] Create `PlotConfiguration` in `app.models.config`.
* [x] Create `PlotState` in `app.models.state` (`current: str`, `path: List[str]`).
* [x] Add `plots` to `ConfigurationSchema` and `plot` to `StateSchema`.
* [x] Add `PLOT = 'plot'` to `app.config.enums.Shortcuts`.
* [x] In `Migrator._build_generator()`, extract the plot state immediately after loading: `self.board.plot = getattr(self.state, Shortcuts.PLOT.value, None)`.
* [x] Update the reflection loop's skip condition to bypass metadata fields: `if category_key in (Shortcuts.COMPOSITIONS.value, Shortcuts.PLOT.value): continue`

**Task #2: ISL Compiler Abstraction**

* [x] Refactor `Executor.evaluate()` to accept a generic `locals: dict` instead of strictly `SpriteState`.
* [x] Update `TransitionMechanics` to pass `{'sprite': sprite.state, 'sprites': board.characters()}` into the updated `Executor`.
* [x] Ensure `CompilerTranslator` and `LambdaTranslator` dynamically map the `locals` dictionary to the ISL runtime without breaking backwards compatibility.

**Task #3: Widget Binding System & Provider Refactor**

* [x] Create `app.game.menus.bindings` to define the `Binding` interface and concrete implementations (`LibraryBinding`, `MeterBinding`, `IconBinding`, `SelectBinding`).
    * `__init__(self, target: str, context: dict, **kwargs)`: Resolve the string target into `(parent, attr)` references immediately.
    * `get_callables(self, **kwargs) -> tuple[Callable, ...]`: Return the closures used by Widget states.
* [x] Implement lazy-evaluation cache specifically inside `LibraryBinding.get_callables(w, l)` to prevent `TTF_SizeUTF8` from re-calculating page wraps on every frame (Remediates B005).
* [x] Create `app.services.generators.binder.Binder` factory class.
    * Implement `binding(self, bind_cfg: dict, context: dict) -> Binding` to dispatch construction based on `bind_cfg.schema`.
* [x] Refactor `Provider` to utilize the `Binder`.
    * `_unpack_widget` calls `binder.binding(cfg.bind, context)`.
    * `_unpack_<widget>` methods are updated to accept `(cfg: MenuWidget, binding_component: Binding)`.
    * Remove all string-path parsing and data-smuggling from the `Provider`.

*Crucial:* The `library` binding must cache its paginated output on the first execution. It cannot recalculate pagination on every evaluation. Incorporate a lazy-evaluation cache into the `library` binding lambda to prevent the `_paginate` method from executing the SDL `TTF_SizeUTF8` calculations multiple times per frame. See B005 Report.

**Task #4: Library Service Integration**

* [x] Create `app.services.generators.library.Library` to parse `src/data/config/library/main.yaml`.
* [x] Implement `Library.fetch(plot, persona, lexicon) -> List[str]`.
* [x] Inject `Library` into `Provider` during the `Orchestrator` bootstrapping sequence.

**Task #5: Mechanics Routing (The Triggers)**

* [x] Create `PlotMechanics(Mechanic)`. Evaluate `board.configurations.plots[board.plot.current]` against the `PlotExecutor` and progress the plot key if conditions are met.
* [x] Add `plot` to the `world` mechanics sequence in `/src/data/config/mechanics/main.yaml`.
* [x] Update `InteractionMechanics.update()`: On sign interaction, emit `MenuEvent(id='text', context={'plot': board.plot, 'persona': target.persona, 'lexicon': target.lexicon)`.

**Task #6: ScrollController Implementation**

* [x] Implement `ScrollController(MenuController)`.
* [x] In `select()`, execute `target.state.scrollup()` or `scrolldown()` based on the `SelectBinding`.
* [x] Emit `UpdateEvent(widget=target)` to the bus to flag the screen for a partial render stamp.






### Documentation Divergences

The following discrepancies between the design documentation and the implemented code were discovered and should be updated to prevent configuration errors.

#### 1. Menu Widget Binding Schema

* **Page:** `06-widgets.md` or Phase 05.03 Task Board
* **Heading:** Working Schemas (Not Yet Implemented) / Text Menu Schema
* **Divergence:** The `text` menu documentation proposes `bind: { state: context.content }`. This breaks the implementation in two ways:
1. The `MenuBinding` dataclass utilizes `slots=True` and only accepts `schema`, `target`, `selection`, and `selector`. A `state` key will raise configuration validation errors.
2. `InteractionMechanics` passes `plot`, `persona`, and `lexicon` inside the `MenuEvent` context—it does not pass `content`. Using `TextBinding` will fail to resolve the string.


* **Recommended Update:** Update the `text` menu schema documentation to properly utilize `LibraryBinding`:

```yaml
children: 
  - instance: pages
    id: text
    name: text-display
    bind:
      schema: library
      target: context

```

#### 2. Plot ISL Condition Syntax

* **Page:** `08-plots.md`
* **Heading:** Plot Mechanics / Transition Matrix
* **Divergence:** The example ISL conditions for `PlotMechanics` contain runtime errors based on how the environment is injected.
1. It references `sprites['...'].state.memory...`. The `sprites` local dictionary (provided by `board.characters()`) caches `AssetState` objects directly. Attempting to access `.state` on a `SpriteState` will trigger an `AttributeError`.
2. It references `player.state.inventory...` directly as a local variable. `player` is not injected into `PlotMechanics` locals (only `sprites` and `board` are).


* **Recommended Update:** Revise the documentation to reflect proper syntax using `.get()` and bypassing `.state`:

```yaml
plots:
  castle-dawn-locked:
    - next: castle-dawn-unlocked
      conditions:
        - sprites.get('player').inventory.loot.get('writ-of-dawn') >= 1
    - next: town-unlocked
      conditions:
        - sprites.get('castle-dawn-guard')
        - sprites.get('castle-dawn-guard').mutators.triggers.dead

```