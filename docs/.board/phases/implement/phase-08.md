#### Implement: Phase 08 - Compositions

The implementation of Compositions requires treating them as macros or "prefabs." They exist strictly as a data-abstraction layer. Once the Orchestrator or Cradle unpacks a Composition, the Engine and Board should remain completely ignorant of its existence, managing the unpacked components as standard flat Assets.

Compositions can be instantiated both at boot (via state files) and at runtime (via the `build` Intention). The expansion logic must be decoupled from the `Orchestrator` and exposed as a shared utility.

**Architectural Assessment**

* **Macro Expansion vs. Engine Logic:** The `Board` operates on a flattened list of Assets. Compositions should never enter the `Board` object. They must be intercepted and expanded into their primitive `Asset` representations during the data-hydration phases (`Orchestrator.migrate()` and `Cradle.spawn_composition()`).
* **Binding Resolution:** The `bind(root.<attribute>)` syntax implies a late-binding evaluation step. During instantiation, the engine must parse the AST of the root Strut's deployment state, extract the referenced attribute, and inject it into the child's PseudoState.
* **Coordinate Superposition:** Component positions are relative to the root Strut. The expansion utility must recursively apply vector addition (`component.position = root.position + pseudo.position`) across all nested components and branches.

**Identified Code Deficiencies**

* **Missing Schema Definitions:** `ConfigurationSchema` (`app/models/config.py`) lacks a `compositions` field. Currently, `Loader.load_configurations()` will parse `config/compositions/main.yml`, but the Pydantic `TypeAdapter` will silently drop the data because the destination model does not define it.
* **Missing State Schemas:** `StateSchema` (`app/models/state.py`) has no definition for Compositions. If a user adds a `compositions:` key to a state YAML file, the loader will ignore it.
* **Increment Tracking:** The documentation specifies a unique naming schema (`<instance>-<strut>-<component>-<increment>`). Neither the `Orchestrator` nor the `Factory` currently maintain a monotonic counter or global registry to track this increment, guaranteeing namespace collisions on multiple deployments of the same Composition.
* **Missing Cradle Cost Logic:** `Cradle.spawn_strut` uses `CraftProperties.cost`. If a Composition is spawned at runtime via the `build` Intention, the Cradle lacks a mechanism to calculate the aggregate `cost` of the Composition (the sum of the root Strut, all branches, and all components).

##### Tasks

**1. Task: Schema Updates**

*Objective*: Expand Pydantic models to ingest Composition YAML data from both state and config directories.

- [ ] Subtack: Define `CompositionConfig` in `models/config.py`
- [ ] Subtask: Define `CompositionState` in `models/state.py`
- [ ] Subtask: Update root schemas to include these fields.

**2. Task: Hydration Engine**

*Objective*: Create a shared `CompositionExpander` utility to decouple expansion logic from the Orchestrator.

- [ ] Subtask: Implement recursive relative coordinate mapping.
- [ ] Subtask: Implement regex string parser for `bind(root.x)` syntax.
- [ ] Subtask: Implement global increment counter for unique naming.

**3. Task: Orchestrator Integration**

*Objective*: Intercept Compositions during bootstrapping and flatten them before Board initialization.

- [ ] Subtask: Update `Orchestrator.migrate()` to process `self.state.compositions`
- [ ] Subtask: Feed expanded PseudoStates into the standard `Asset` instantiation flow.

**4. Cradle Integration**

*Objective*: Enable runtime instantiation of Compositions for IndustryMechanics.

- [ ] Subtask: Add `spawn_composition()` to `Cradle`.
- [ ] Subtask: Implement aggregate `Cost` calculation for the entire Composition tree.