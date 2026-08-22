#### Refactor: Phase 04.02 - Consolidation

**Goals** 

- Eliminate the parallel Pydantic DTO pipeline.
- Fix critical bugs in spatial resolution and engine initialization.
- Ensure stability of core application components as development proceeds.

##### Tasks

**1. Task: Pydantic Pipeline Consolidation**

*Objective*: Remove redundant DTOs and parse YAML directly into POPOs.

- [x] Subtask: Delete `app.config.validators`.
- [x] Subtask: Implement `__get_pydantic_core_schema__` or `BeforeValidator` annotations for Cython models (`Position`, `Dimensions`, `Hitbox`, `Velocity`).
- [x] Subtask: Update `Loader` to use `pydantic.TypeAdapter` on `app.models.*` classes.
- [x] Subtask: Remove `Factory._hydrate` and simplify `Orchestrator.migrate()`.

**2. Task: Spatial Mechanics Refactor**

*Objective*: Ensure top-down physics fidelity.

- [x] Subtask: Refactor `CollisionMechanics._resolve` to calculate `overlap_x` and `overlap_y` using `Hitbox` coordinates rather than `Dimensions`.
- [x] Subtask: Update `Geometry.intersects` to return the specific intersecting `Hitbox` pair, rather than a simple boolean, so the narrow-phase solver knows exactly which boundaries to push apart.

**3. Task: Engine & Orchestrator Patches**

*Objective*: Resolve fatal typos and logic drift.

- [x] Subtask: Fix `self.mechaniccs` typo in `Orchestrator.init()`.
- [x] Subtask: Refactor `Action` mapping in `Orchestrator.migrate()` to prevent mutating `self.properties`.
- [x] Subtask: Add an `executed` boolean flag to `SpriteState.mutators.triggers` to prevent `CombatMechanics` from spawning multiple projectiles on `frame == 0`.

**4. Task: Unit Test Coverage**

*Objective*: Lock in application functionality with unit-test coverage for core components.

- [x] Subtask: Setup test fixtures for properties, state and configuration. 
- [x] Subtask: Write unit tests for the Factory.
- [x] Subtask: Write unit tests for the Cradle. 
- [x] Subtask: Write unit tests for the Orchestrator
- [x] Subtask: Write unit tests for the Board.
- [x] Subtask: Write unit tests for the Decomposer.
- [ ] Subtask: Write unit tests for the Registry. 
    - The primary goal is to get coverage on the `index()` Frame methods and ensure they are being calculated correctly for all possible Frame implementations.
    - Ensure the rest of the code has good coverage and SDL methods are mocked.
- [ ] Subtask: Write unit tests for the Screen.
    - The primary goal is to get coverage on the `keys()` Frame methods and ensure they are being calculated correctly for all possible Frame implementations.
    - Ensure the rest of the code has good coverage and SDL methods are mocked.