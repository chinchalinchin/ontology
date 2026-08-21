#### Refactor: Phase 04.02 - Consolidation

**Goals** 

- Eliminate the parallel Pydantic DTO pipeline.
- Fix critical bugs in spatial resolution and engine initialization.

##### Tasks

**1. Task: Pydantic Pipeline Consolidation**

*Objective*: Remove redundant DTOs and parse YAML directly into POPOs.

- [x] Subtask: Delete `app.config.validators`.
- [x] Subtask: Implement `__get_pydantic_core_schema__` or `BeforeValidator` annotations for Cython models (`Position`, `Dimensions`, `Hitbox`, `Velocity`).
- [x] Subtask: Update `Loader` to use `pydantic.TypeAdapter` on `app.models.*` classes.
- [x] Subtask: Remove `Factory._hydrate` and simplify `Orchestrator.migrate()`.

**2. Task: Spatial Mechanics Refactor**

*Objective*: Ensure top-down physics fidelity.

- [ ] Subtask: Refactor `CollisionMechanics._resolve` to calculate `overlap_x` and `overlap_y` using `Hitbox` coordinates rather than `Dimensions`.
- [ ] Subtask: Update `Geometry.intersects` to return the specific intersecting `Hitbox` pair, rather than a simple boolean, so the narrow-phase solver knows exactly which boundaries to push apart.

**3. Task: Engine & Orchestrator Patches**

*Objective*: Resolve fatal typos and logic drift.

- [x] Subtask: Fix `self.mechaniccs` typo in `Orchestrator.init()`.
- [x] Subtask: Refactor `Action` mapping in `Orchestrator.migrate()` to prevent mutating `self.properties`.
- [ ] Subtask: Add an `executed` boolean flag to `SpriteState.mutators.triggers` to prevent `CombatMechanics` from spawning multiple projectiles on `frame == 0`.

**4. Task: Event Bus Bootstrapping**

*Objective*: Prepare the engine for Phase 05: Widgets.

- [!] Subtask: Define `MenuEvent`, `SelectionEvent`, and `StateEvent` dataclasses in `app.models.state`.
- [!] Subtask: Add `bus: collections.deque` to `app.game.board.Board` to handle FIFO event queueing.
- [!] Subtask: Implement the `MenuMechanics` shell to drain and parse the `Board.bus` queue per tick.

**5. Task: Unit Test Coverage**

*Objective*: Lock in application functionality with unit-test coverage for core components.

- [ ] Subtask: Setup test fixtures for properties, state and configuration by reading in the data in the `src/assets/**/main.yaml` and `src/data/**/main.yaml` files. 
- [ ] Subtask: Write unit tests for the Factory.
- [ ] Subtask: Write unit tests for the Cradle. 
- [ ] Subtask: Write unit tests for the Orchestrator