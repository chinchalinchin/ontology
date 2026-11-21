### Backlog Entry (B039.1 — Board Temporal Coupling & Late-Bound Dependencies)

#### Refactor: Eliminate Late-Bound Service Setters and Temporal Coupling on `Board`

**Overview**

While the immediate annotation mismatches on `Board` (`plot`, `device`, `cradle`, `materializer`) have been corrected to `Optional[...]`, `Board.__init__` still initializes its core runtime collaborators (`device`, `cradle`, `migrator`, `materializer`, `plot`) to `None` and relies on external callers (`Orchestrator`, `Migrator`, event handlers, and test fixtures) invoking mutable setter methods in an undocumented order. Eliminating this temporal coupling spans multiple orchestration and service layers outside the immediate `Board` patch boundary and warrants a dedicated refactoring pass.

##### Specification

Separate **Boot-Time Collaborators** (always present once `Board` is constructed in Phase 1: `device`, `cradle`, `migrator`, and `materializer` if active) from **Hydrated World State** (loaded/reset in Phase 2: `plot`, `calendar`, `assets`, `perimeters`, `overlays`).

* **Constructor Injection**: `Device` and `Cradle` (which depend only on `configurations` / `spawnables`, not a live `Board` instance) must be injected directly into `Board.__init__`.
* **Circular Dependency Resolution**: If `Migrator` requires a `Board` reference (or vice versa), invert the dependency so `Engine` / `LoadController` / `StateEventHandler` owns `Migrator` (or passes `board` into `migrator.step(board)`), eliminating `Board.migrator` and `Board.set_migrator()` altogether.
* **Non-Optional `PlotState`**: Default `self.plot = PlotState()` (matching `self.calendar = CalendarState()`) and update `Board.serialize()` to emit `Shortcuts.PLOTS` only when `self.plot.current is not None or self.plot.previous`.

##### Goals

###### Goal: Construct `Board` in a Valid, Non-Null Boot State

Every `Board` returned by `Orchestrator` should hold non-optional, ready-to-use `device` and `cradle` collaborators so `Engine._play()` (`self.board.device.poll()`) and `Cartographer` / `CombatMechanics` (`board.cradle`) cannot fail with `AttributeError` on `None`.

###### Goal: Decouple `Migrator` Lifecycle from `Board`

`Board` is the in-memory world database, whereas `Migrator` is an orchestration service that hydrates `Board`. Moving `Migrator` ownership to `EventData` / `Engine` (or passing `board` to `Migrator` methods) breaks the `Board <-> Migrator` cycle and removes `set_migrator`.

##### Tasks

**1. Task: Audit `Board` Collaborator Wiring and Remove Dead Attributes**

*Objective*: Map every caller of `set_device`, `set_cradle`, `set_plot`, `set_migrator`, and `board.materializer` across `app.services.orchestration`, `app.game.menus`, and `tests/`.

* [ ] Subtask: Verify whether `board.materializer` is referenced anywhere in `src/` or `tests/`; schedule removal or strict typing.
* [ ] Subtask: Trace whether `Cradle` or `Device` holds a back-reference to `Board`, and break any accidental reverse coupling.

**2. Task: Refactor `Board.__init__` and `Orchestrator` for Constructor Injection**

*Objective*: Inject mandatory Phase 1 collaborators at construction and eliminate mutable setter methods.

* [ ] Subtask: Update `Board.__init__` to accept `device: Device` and `cradle: Cradle` directly, removing `set_device` and `set_cradle`.
* [ ] Subtask: Default `Board.plot` to `PlotState()` and guard `Board.serialize()` on non-empty plot state (`self.plot.current is not None or self.plot.previous`).
* [ ] Subtask: Move `Migrator` ownership out of `Board` into `EventData` / `LoadController` (or pass `board` per step), removing `Board.migrator` and `set_migrator`.
* [ ] Subtask: Update `Orchestrator`, `StateEventHandler`, `LoadController`, and `tests/unit/conftest.py` fixtures to construct `Board` with the new signature.


##### Bug B054: Phantom Rising-Edge Input Across Context Switches in `Keyboard.context`

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/game/devices.py` (`Keyboard.context`), switching between `DeviceContexts.WORLD` and `DeviceContexts.MENU` unconditionally initializes `self._last_state = {code: 0 for code in self._scancodes}`. When a physical key is mapped in both contexts (e.g., `ESC` mapped to `world.menus.pause` and `menu.interactions.cancel`, or `SPACE`/`E` mapped to `world.intentions.interact` and `menu.interactions.select`), and remains physically depressed across the context transition (a typical human key press lasts 5–9 ticks at 60 FPS), the very next `Keyboard.poll()` observes `current_dict[code] == 1` and `self._last_state[code] == 0`, emitting a spurious rising edge in the new context. This causes a newly opened menu to be immediately cancelled/selected or a world action to fire immediately upon closing a menu.

**Steps to Replicate** 

1. Map the same SDL scancode (e.g., `ESC`) to `world.menus.pause` and `menu.interactions.cancel`.
2. Press and hold `ESC` in `DeviceContexts.WORLD` for > 2 ticks: tick 1 emits `WorldPayload(menu='pause')`, opening the Pause menu.
3. On context switch via `device.context(DeviceContexts.MENU)`, `self._last_state[ESC]` is reset to `0` while `ESC` is still down.
4. On the next tick, `device.poll()` emits `MenuPayload(interaction='cancel')`, immediately dismissing the Pause menu on the same physical keypress.

**Proposed Remeditation**

Seed `self._last_state` in `Keyboard.context` from the live keyboard state returned by `sdl.poll(self._scancodes)` (`{code: 1 if state else 0 for code, state in zip(self._scancodes, sdl.poll(self._scancodes))}`) so keys already held across a context switch must be released and pressed again before emitting a rising edge.

##### Bug B055: `Screen.__init__` and `Screen.rebake` Negate `opaque=True` on Tileless `bg_canvas` via `render.construct`

**STATUS**: OPEN
**SEVERITY**: LOW

**Description**

In `src/app/game/screen.py` (`Screen.__init__`, lines 97–105, and `Screen.rebake`, lines 355–362), when a layer has no tiles (`len(tiles) == 0`), `is_opaque` is set to `True` and `self.bg_canvas` is allocated via `render.canvas(canvas_w, canvas_l, opaque=True)`, which clears the texture to opaque black `RGBA(0, 0, 0, 255)`. Immediately afterward, `render.construct(self.bg_canvas, back_tiles)` is invoked with its default `clear_target=True`, which calls `SDL_SetRenderDrawColor(_renderer, 0, 0, 0, 0)` and `SDL_RenderClear(_renderer)`, overwriting the opaque black canvas back to fully transparent `RGBA(0, 0, 0, 0)`.

**Steps to Replicate** 

1. Instantiate a `Screen` (or invoke `screen.rebake(...)`) with `tiles = []`.
2. Call `screen.export_background("empty_bg.png")`.
3. Inspect the exported image: all pixels have alpha `0` (transparent) instead of the intended opaque black `RGBA(0, 0, 0, 255)`.

**Proposed Remeditation**

Pass `clear_target=not is_opaque` to `render.construct(self.bg_canvas, back_tiles, clear_target=not is_opaque)` in both `Screen.__init__` and `Screen.rebake` (or invoke `render.construct` on `self.bg_canvas` only when `back_tiles` is non-empty, since `render.canvas` has already cleared the freshly allocated texture).