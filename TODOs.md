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