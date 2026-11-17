#### Refactor: Phase 07.06 - Crafting

**Overview**

Building upon the Material aspect of Assets, design and introduce a Crafting system managed through a new Craft Menu.

##### Specification

**(Blueprints, Materials)**

* materials: 
    * organics: cottons, thatches, wood
    * ceramics: clay
    * geologics: limestone, feldspar, granite, marble
    * metallics: copper, iron, gold
    * chromatics: neutral, blue, red, yellow, green
* blueprints: 
    * buildings: floors, walls, flats, roofs, paths, halls
    * corridors: solids, stripes, designs
    * columns: crowns, shafts, bases 
    * decor: decor
    * enclosures: north, east, south, west
    * inclines: up, left, right
    * orientations: horizontal, vertical

**Definition: Primitives**

Primitive Crafts can be constructed by the User without a Composition container.

* Stairs
* Bridges
* Decor Struts

**Definition: Armatures**

To hide the complexity of the Strut (Blueprint, Material) space from the User, a subdirectory of Compositions (`/src/data/config/compositions/armatures/**/*.yaml`) will be maintained, known as *Armatures*. In a sense, Armatures integrate a Strut over its Blueprint partition. 

These are "*User Facing Crafts*". Users do not directly instantiate Struts. They instantiate Armatures of Struts (e.g. parameterized Compositions). In the `src/data/config/compositions/armatures/buildings/home/main.yaml` example, the branch Struts depend on the `material` of the root Struts, which is dependent on the parameter passed into the Composition. In this way, the parameter of Material is a degree of freedom determined by User selection.

Each Armature will be keyed according to the following schema:

* `armature/<icon-filter>/<strut>`
    * `<icon-filter>`: The Icon to which the Armature activates when filtering. (See **Feature: Craft Filters**)
    * `<strut>`: The Primitive Strut which the Armature integrates over its Blueprint Partition.

* `icon-filters`: `building`, `road`, `tower`, `carpentry`, `railing`

**Initialization**: 

* The MaterialIndex Relation and Materializer Service are used to construct a Cost Ledger for all indexed Primitive Crafts and configured Armatures.
    * Each separate instance of a Primitive Craft will need to be unpacked across the dimension of (Blueprints, Materials). For example, a `steps` Stair unpacks into `steps-up-limestone`, `steps-left-limestone`, `steps-right-limestone`, `steps-up-feldspar`, `steps-left-feldspar`, `steps-right-feldspar`, ... 

**Menu: Pack**

* `dock(header)`: `pane(content="Pack")`
* `stack`:
    * `dock(subheader)`: `pane(content="Resources")`
    * `dock(materials)`: `gizmo(context.inventory.pack)`
    * `dock(crops)`: `gizmo(context.inventory.sack)`
* `stack`:
    * `dock(subheader)`: `pane(content="Crafts")`
    * `dock(filters)`: `gizmo(context.filters)` 
    * `dock(crafts)`: `gizmo(context.crafts)`

`dock(filters)` needs to be able to bind to an Enum, i.e. the static list of Frames in the `crafts` Icon, *and* a dynamically generated list of Crafts. These fields can be stored in the Menu context.

**Minimum Viable Product: Craft Workflow**

1. Player opens Craft Menu.
2. Menu populates the Craft Formulae Pane with Slots hydrated from *all* entries in the Cost Ledger and initializes each one with the `disabled` Status. 
3. Controller takes Player Inventory and compares it to the Cost Ledger. Any entry in the Cost Ledger that is satisfied by the Player Inventory is set to `enabled` Status.
4. Player selects a constructable Craft.
5. Craft Menu closes.
6. A Craft is instantiated *level* with the Player (where *level* is defined as their ground baseline's being equal) and directly *adjacent* (where *adjacent* is defined as touching with no pixel overlap).
 
**Feature: Craft Filters**

The `crafts` Icon Widget can be utilized to represent user-facing Crafts (Primitives & Armatures). The Craft Menu should have a traversible dock of `crafts` Icons. When one of the `crafts` is selected, the Cost Ledger hides any entries that do not match the filter.

##### Architectural Analysis I

1. **Unified Cost Ledger (`LedgerService` / `CraftEntry`)**: Rather than splitting UI flows between Primitives and Armatures, both are unpacked at boot into a flat, queryable Cost Ledger indexed by `(filter_icon, asset_id, blueprint, material, host)`. Each `CraftEntry` precomputes its unit `List[Cost]` via `Materializer` and its multiplied footprint `Dimensions` via `MaterialIndex`.
2. **Decomposer Late-Binding Extension**: `Decomposer.unpack()` currently omits `material` and `blueprint` from `root_context`. Exposing `deployed_state.material` in `root_context` enables `bind(root.material)` on Armature branch and component struts to resolve cleanly during deployment.
3. **Pack Menu & Traversal**: Extending `menus/inventory/pack/main.yaml` with a filter strip Gizmo (`icons.crafts`), a filtered formulae grid Gizmo, and a reactive cost/detail readout pane preserves the existing declarative `Binder` and `Fabricator` pipeline. To let players inspect recipes they cannot yet afford, `MenuMechanics` (or `CollectionState`) must distinguish between *vacant* slots (non-traversable) and *unaffordable* slots (traversable with visual disabled/dimmed state, or inspected via focus).
4. **Spatial Placement Solver**: Spawning a Craft from `CraftController.select()` requires a deterministic placement check that aligns ground baselines ($y_{\text{craft}} + \text{span}.l + \text{anchor} = y_{\text{player}} + \text{dim}_{\text{player}}.l$), offsets horizontally/vertically clear of the player's hitbox along `player.state.animation.direction`, and validates against `board.obstacles()`, `board.weights()`, and `board.perimeters` before consuming `inventory.pack` resources.

##### User Review I

In order to parameterize Compositions, the PseudoState needs alteration. Since Compositions use the StateSchema for their configuration schema, they get validated against the State Models. This means when the Composition leaves a parameter empty, the PseudoState will fail to validate.

##### Goals

###### Goal: Unified Craft Ledger & Cost Indexing

Construct a `CraftLedger` (or extend `Materializer`) during bootstrap that enumerates all Primitive Crafts (`stairs`, `bridges`, `decor` struts) across their `(BlueprintPartition, MaterialSpace)` cross-products and all configured Armatures (`armature/<filter>/<strut>`) across their root strut's `MaterialSpace` (resolving `host` materials for `chromatics`), storing precomputed `List[Cost]` and `Dimensions` spans.

###### Goal: Armature Late-Binding & Configuration

Support parameterized `material` injection in `Decomposer.unpack()` and establish initial Armature YAML definitions under `/src/data/config/compositions/armatures/` keyed to `icons.crafts` filter frames.

###### Goal: Pack Menu Craft UI & `CraftController`

Wire `menus.pack` (`PackContext` / `InventoryContext`) to `CraftController`, adding the `crafts` filter dock, filtered formulae grid, live ingredient cost display, inventory sufficiency validation, and adjacent level placement via `board.cradle`.

##### Tasks

**1. Task: Semantics & Armature Composition Support**

*Objective*: Align icon filter semantics and enable runtime `material` binding on Armature root struts.

- [x] Subtask: Update `Decomposer.unpack()` in `src/app/services/generators/game/decomposer.py` to inject `deployed_state.material` and `deployed_state.blueprint` into `root_context` for `bind(root.material)` resolution.
- [ ] Subtask: Author baseline Armature configurations in `/src/data/config/compositions/armatures/` (e.g., `armature/house/home`).

**2. Task: Craft Cost Ledger Compilation**

*Objective*: Index all constructable Primitives and Armatures with their precomputed `Materializer` resource costs and spans.

- [ ] Subtask: Define `CraftEntry` model (`key`, `filter`, `category`, `instance`, `id`, `blueprint`, `material`, `host`, `costs: List[Cost]`, `span: Dimensions`, `is_armature: bool`).
- [ ] Subtask: Implement ledger compilation in `Materializer` (or `CraftLedger`) during `Orchestrator` bootstrap, unpacking Primitives across `(blueprints, materials)` and Armatures across root `materials` (including `chromatics` host pairing).
- [ ] Subtask: Attach the compiled ledger to `Board` (or `Materializer`) for $O(1)$ lookup by filter category and craft key.

**3. Task: Pack Menu Layout & Bindings**

*Objective*: Complete the `CRAFT FORMULAE` column in `src/data/config/menus/inventory/pack/main.yaml` with filter traversal, formula slots, and recipe cost readout.

- [ ] Subtask: Extend `PackContext(InventoryContext)` with `ledger`, `active_filter`, `filtered_crafts`, and `selected_cost` fields.
- [ ] Subtask: Update `src/data/config/menus/inventory/pack/main.yaml` to include the `crafts` filter strip Gizmo (`dock`), the filtered craft slots Gizmo (`grid`), and a bound `TextBinding` / `IconBinding` cost readout pane.
- [ ] Subtask: Ensure `CollectionState` and `MenuMechanics` allow focusing unaffordable craft slots to inspect costs while preventing `select()` execution when inventory resources are insufficient.

**4. Task: `CraftController` Workflow & Spatial Placement**

*Objective*: Implement craft filtering, affordability checks, resource deduction, and adjacent level instantiation.

- [ ] Subtask: Implement `CraftController.open()` and `update()` to filter the Cost Ledger by `active_filter`, evaluate `inventory.pack` quantities against `CraftEntry.costs`, and update slot statuses and cost readouts.
- [ ] Subtask: Implement placement coordinate calculation in `CraftController` (or a placement helper) ensuring ground-baseline equality ($y_{g,\text{craft}} = y_{g,\text{player}}$) and zero-overlap directional adjacency along `player.state.animation.direction`, validated against `board.obstacles()`, `board.weights()`, and `board.perimeters`.
- [ ] Subtask: Implement `CraftController.select()` to switch filters when a filter button is activated, or—when an affordable craft is selected—deduct required materials from `inventory.pack`, instantiate the Primitive or Armature via `board.cradle` with `owner = player.name`, and emit `TerminalEvent()`.