#### Refactor: Phase 05.02 - Simplification

**Overview** 

With the introduction of Widgets and Mechanics, the application architecture needs to be re-evaluated to see if any simplification can be introduced.

!!! "definition"
    Simplification = Simple, readable patterns

##### Tasks

**Task #1: Centralize Input Polling**

*Objective*: Prevent `_last_state` mutation bugs during the game loop.

- [x] Remove `board.device.poll()` from all individual `Mechanic` implementations. 
- [x] Update `Engine._play()` to call `poll()` once per tick and pass the `DevicePayload` alongside the `bus` to the Mechanics interface.

**Task #2: Decompose the Orchestrator**

*Objective*: Decompose the GOD object into its constitutent functions.

- [x] Create an `Context` dataclass to pass along the assembly line.
    * **Holds:** `properties`, `state`, `configurations`, `device_mapping`, and `screensize`.
- [x] Move `Decomposer`, `Provider`, and `Cradle` into the new `app.services.generators` package.
    - [x] Update their constructors to accept only the specific properties and recipes they need from the `Context`, rather than the whole schema.
- [x] Create an `Builder` class that breaks the `Orchestrator`'s monolithic `init()`, `migrate()`, and `inject()` methods into discrete, single-responsibility steps.
    - [x] `load_data(state_key)`: Wraps the `Loader` logic and populates the `EngineContext`.
    - [x] `init_subsystems(screensize, headless)`: Calls `render.init()` to boot the SDL/Cython backend.
    - [x] `build_registry()`: Unboxes Enums and instantiates the `Registry`, caching the fonts and textures.
    - [x] `build_board()`: Uses the `Decomposer` to unpack Compositions, applies the ECS property mappings, and instantiates the `Board`.
    - [x]  `build_services(device)`: Instantiates the `Cradle`, Device mapping, and assigns them to the `Board`.
    - [x] `build_pipeline()`: Instantiates the `Provider`, creates the `screens`, and resolves the `core` and `world` Mechanics lists.
    - [x] `get_engine()`: Injects all the built components into the final `Engine` object and returns it.
- [x] Implement the Director
    - [x] The Director takes the Builder as an argument and executes the steps in the exact sequence required.
    - [x] This removes all sequence-enforcement logic from the construction classes.