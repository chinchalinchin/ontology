- Cartographer and Actuator are static. They shouldn't actually be injected anywhere.



An inspection of `Orchestrator`, `Builder`, `Factory`, `Migrator`, `Decomposer`, `Cradle`, `Board`, and `MaterialIndex` reveals six structural inconsistencies in the current dependency tree.

#### Inconsistency 1: Triplicated `Asset` Construction (`Migrator` vs. `Decomposer` vs. `Cradle`)

Right now, `Asset` instantiation (`Taxonomy`, `Properties`, `Recipe` lookup, `Frame`, `Animation`, `Hitbox`, and `substrate` resolution) is manually implemented in **three separate services** across **8 methods**:

1. **`Migrator._build_generator()`**: Looks up `recipes`, aliases `players -> sprites`, looks up `properties`, calls `Factory.taxonomy/frame/animation/hitbox`, resolves `materials.substrate()`, and calls `Asset(...)`.
2. **`Decomposer._create_asset()` & `Decomposer._spawn_unit()**`: Repeats the exact same `recipes` lookup, `players -> sprites` alias, `properties` lookup, `Factory` calls, and `materials.substrate()` resolution.
3. **`Cradle.spawn_*()`** (`spawn_projectile`, `spawn_collectable`, `spawn_hazard`, `spawn_passive`, `spawn_strut`, `spawn_shoreline`): Repeats `Factory.frame/animation/hitbox/taxonomy`, `materials.substrate()`, and `Asset(...)` six times.

**Consequence**: Whenever `Asset.__init__` changes—such as adding `HitboxSchema` in Phase 07.02, `substrate` in Phase 07.04, or `Mutators` in Phase 08.04 (`@TODO(08-04)`)—you have to modify 8+ separate instantiation sites across three services.

* **Fix**: Centralize `Asset` assembly in `Factory.asset(category, instance, state, properties, recipes, materials)` (or make `Cradle` the single low-level `Asset` spawner injected into both `Decomposer` and `Migrator`). `Migrator` should only orchestrate time-sliced state loading, not know how to resolve `Factory` recipes or `PLAYERS -> SPRITES` property aliases.

#### Inconsistency 2: Split-Brain Injection vs. Hidden `Singleton` Locator on `MaterialIndex`

`MaterialIndex` is currently treated as **both** an injected dependency and a global `Singleton`:

* In `Builder`, `MaterialIndex` is compiled in `build_relations()` and explicitly injected into `Decomposer`, `Migrator`, `Cradle`, and `Mechanics`.
* However, in `MaterialFrame.index()`, `ObjectFrame.index()`, `BinaryFrame.index()`, and `MaterialHitbox.get()`/`elevations()`, `MaterialIndex` is **not** injected—those methods call `MaterialIndex()` directly as a global singleton!
* **Hidden Temporal Coupling Bug**: `Builder.build_registry()` initializes `Registry`, which immediately calls `Frame.index()` on all Craft and Object properties. Because `MaterialFrame.index()` relies on the global `MaterialIndex()` singleton having been populated as a side-effect of `Builder.build_relations()`, calling `build_registry()` before `build_relations()` (e.g., in a unit test or CLI utility) silently indexes **zero frames** for every Craft and Object without raising an error.
* Furthermore, `Builder.build_board()` and `Builder.build_pipeline()` check `if not self.relations: self.build_relations()`, whereas `Builder.build_registry()` does not, even though `Registry` implicitly depends on `Relations.MATERIALS`.

#### Inconsistency 3: Hidden Fallback Constructors Masking Wiring Errors

In `Migrator.__init__()`:

```python
self.actuator = actuator or Actuator()
self.materials = materials or MaterialIndex.from_configuration(
    self.configurations.materials
)
self.decomposer = decomposer or Decomposer(
    compositions=self.configurations.compositions,
    properties=self.properties,
    recipes=self.configurations.recipes
)

```

And in `Decomposer.__init__()`:

```python
self.materials = materials or MaterialIndex()

```

Because `Builder` is responsible for constructing and injecting the dependency graph, services should **not** secretly instantiate their own fallback copies of `Decomposer`, `Actuator`, or `MaterialIndex`. If a caller omits a required dependency, failing fast at `__init__` (by making `actuator`, `decomposer`, and `materials` required positional parameters) prevents silent split-state bugs where two services hold different instances.

#### Inconsistency 4: Dead I/O and Dead Branches in `Builder` & `Orchestrator`

1. **Double Disk Load of State YAML**:
* `Orchestrator.orchestrate(state_key)` calls `self.builder.load_data(state_key)`.
* When `state_key` is provided, `Builder.load_data()` calls `self.context.state = Loader.load_state(state_key)`.
* **Nothing in `Builder` ever reads `self.context.state**`. Instead, `Orchestrator` pushes `StateEvent(id=state_key)` onto `engine.bus`, which triggers `Migrator._build_generator()`, which calls `Loader.load_state(self.target)` a **second time**.
* `Builder.load_data()` should take zero arguments and only load `properties` and `configurations`.


2. **Dead `else` Branch in `Builder.build_pipeline()**`:
* Because `build_board()` always initializes `Board([])` and defers hydration to `Migrator`, `self.board.layers()` is always empty during `build_pipeline()`. The `else` branch in `build_pipeline()` (lines 274–285) is unreachable during orchestration.


3. **Inconsistent `Board` Attachment**:
* `Board` declares `device: Device` and `cradle: Cradle` with explicit setters (`set_device`, `set_cradle`), but does not declare `migrator: Migrator` in `Board.__init__` or its class annotations—`Builder.build_board()` monkey-patches `self.board.migrator = Migrator(...)` onto the instance.


4. **Indirect `Registry` Retrieval in `Orchestrator` and `Engine.stop()**`:
* `Orchestrator` retrieves `registry` via `next(iter(engine.screens.values())).registry` instead of `self.builder.registry`.
* `Engine.stop()` reaches through `self.screens.values()` and `self.provider.binder.registry` to call `registry.clear()` twice. Injecting `registry: Registry` directly into `Engine` makes teardown explicit and O(1).



#### Inconsistency 5: `SpawnableGroup` & `EquipmentGroup` Indirection

`Builder` manually slices `self.context.properties` into `EquipmentGroup` (for `Board`) and `SpawnableGroup` (for `Cradle`). Meanwhile, `Decomposer` and `Migrator` receive the full `PropertiesSchema`.

* As the game adds more dynamically spawned entities (e.g., `Resources` in Phase 10.03 reproduction, `Obstacles` in Phase 11 geology, `Doors`/`Bridges`/`Stairs` in crafting), `SpawnableGroup` becomes a maintenance bottleneck that duplicates `PropertiesSchema`.

#### Inconsistency 6: Stale Delegations on `Cradle`

At the bottom of `Cradle`:

* `Cradle.spawn_bridge()` calls `self.decomposer.bridge(bridge_state)`, which was replaced by `self.decomposer.multiply(bridge_state, AssetCategories.CRAFTS.value, AssetInstances.BRIDGES.value)`.
* `Cradle.cost()` calls `self.decomposer.cost(id)`, which was removed when cost calculation moved to `Materializer`.

---

### Recommended Dependency Graph Simplification

The dependency hierarchy naturally stratifies into **5 strict layers** with zero circularity and a single point of `Asset` creation:

| Layer | Components | Injected Dependencies |
| --- | --- | --- |
| **0. Static Data** | `PropertiesSchema`, `ConfigurationSchema` | Loaded once by `Loader` in `Builder.load_data()`. |
| **1. Compiled Domain Indices & Executors** | `MaterialIndex`, `ShorelineIndex`, `Executors` (`Intention`, `Plot`, `Actuator`, `Lifespans`) | Compiled purely from Layer 0 (`PropertiesSchema`, `ConfigurationSchema`). |
| **2. Core Asset Spawner & Registry** | `Registry`, `Cradle` (or `Factory.asset`) | Depends on Layer 0 (`PropertiesSchema`, `RecipeConfiguration`) + Layer 1 (`MaterialIndex`). **Single place in the entire codebase that calls `Asset(...)`.** |
| **3. Higher-Order Generators** | `Decomposer`, `Migrator`, `Cartographer`, `Materializer` | `Decomposer` receives `(compositions, cradle, materials)` and delegates unit creation to `cradle`. `Migrator` receives `(board, decomposer, cradle, actuator)`. |
| **4. Runtime Containers & Pipeline** | `Board`, `Screen`, `Provider`, `Mechanics`, `Engine` | Assembled from Layers 1–3. |