#### Refactor: Phase 05.02 - Simplification

**Overview** 

With the introduction of Widgets and Mechanics, the application architecture needs to be re-evaluated to see if any simplification can be introduced.

!!! "definition"
    Simplification = Simple, readable patterns

##### Tasks

1. **Task: Centralize Input Polling**

*Objective*: Prevent `_last_state` mutation bugs during the game loop.

- [x] Remove `board.device.poll()` from all individual `Mechanic` implementations. 
- [x] Update `Engine._play()` to call `poll()` once per tick and pass the `DevicePayload` alongside the `bus` to the Mechanics interface.

###### Mega Task: Decompose the Orchestrator

Step 1: Define the Build Context

The Builder needs a place to hold intermediate data while it works, without muddying the final `Engine` class. Create an `EngineContext` dataclass to pass along the assembly line.

* **Holds:** `properties`, `state`, `configurations`, `device_mapping`, and `screensize`.
* **Purpose:** Decouples the raw YAML data from the logic that builds the actual game components.

Step 2: Extract the Generators

The `Decomposer`, `Provider`, and `Cradle` currently rely on the Orchestrator for their setup. Move these into the new `app.services.generators` package.

* Update their constructors to accept only the specific properties and recipes they need from the `EngineContext`, rather than the whole schema.

Step 3: Construct the Builder Interface

Create an `EngineBuilder` class that breaks the `Orchestrator`'s monolithic `init()`, `migrate()`, and `inject()` methods into discrete, single-responsibility steps.

1. `load_data(state_key)`: Wraps the `Loader` logic and populates the `EngineContext`.
2. `init_subsystems(screensize, headless)`: Calls `render.init()` to boot the SDL/Cython backend.
3. `build_registry()`: Unboxes Enums and instantiates the `Registry`, caching the fonts and textures.
4. `build_board()`: Uses the `Decomposer` to unpack Compositions, applies the ECS property mappings, and instantiates the `Board`.
5. `build_services(device)`: Instantiates the `Cradle`, Device mapping, and assigns them to the `Board`.
6. `build_pipeline()`: Instantiates the `Provider`, creates the `screens`, and resolves the `core` and `world` Mechanics lists.
7. `get_engine()`: Injects all the built components into the final `Engine` object and returns it.

Step 4: Implement the Director

Because the Engine's initialization is strictly order-dependent (e.g., you cannot build the Registry before initializing SDL, and you cannot build the Board before the Registry), create an `EngineDirector`.

* The Director takes the Builder as an argument and executes the steps in the exact sequence required.
* This removes all sequence-enforcement logic from the construction classes.

The Resulting Execution Flow

Instead of calling `Orchestrator(state).ignite()`, your main entry point becomes radically simplified:

```python
builder = OntologyBuilder()
director = EngineDirector(builder)

# The Director enforces the sequence, the Builder handles the logic
engine = director.construct(
    state_key="dev_board", 
    screensize=Dimensions(1920, 1080), 
    device=Devices.KEYBOARD
)

engine.start()
```