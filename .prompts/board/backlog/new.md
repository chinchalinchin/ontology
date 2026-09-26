### Architectural Review

1. **The Item/Inventory Transaction Bottleneck**: Entities cannot autonomously generate or exchange value. `SpriteState.inventory` remains an ad-hoc dictionary mutated directly by `InteractionMechanics` for chests and `MenuMechanics` for equipment slots. For Sprites to exhibit autonomous intentionality (mining, bartering, building), items and loot must exist as first-class physical entities with unified container interfaces.
2. **The Production-Consumption Disconnect**: `Resources` (ore, crops), `Crafts` (struts), and `Effects` (collectables) represent the material cycle of the world. Currently, mining and crafting are stubbed. Without harvestable resources that convert to collectables, collectables that transfer to inventory, and inventory that funds strut construction, an autonomous society cannot emerge.
3. **Decoupling Simulation from Tooling**: Phase 05 (Editor) is currently marked in progress (`[~]`). While authoring tools are convenient, the core value proposition of the engine is the headless, deterministic tick of the world state. Development effort should prioritize closed-loop simulation mechanics over UI authoring workflows.

### Phase Roadmap Realignment

The current roadmap attempts to jump from spatial combat and navigation into **Phase 09: Commerce** and **Phase 10: Towns**. This transition skips the foundational data pipelines required to support trade and settlement.

| Proposed Phase | Focus | Architectural Prerequisite | Replaces / Consolidates |
| --- | --- | --- | --- |
| **Phase 08.04: Inventory & Transaction Engine** | Unified Container Interfaces, Atomic Exchanges, Equip Controllers | Phase 02.06 (Collectables), Phase 05/06 Menus | Goal 03 (ExchangeController) & Goal 05 (InventoryController) |
| **Phase 08.05: Resource & Material Transformation** | Resource nodes, `mine` intention, Cradle item drops, Crafting formulas | Phase 08.04 (Inventory), Cradle Effects | Stubbed Resources (`docs/01-assets.md`) |
| **Phase 09: Commerce & Barter Simulation** | Price consensus algorithms, valuation updates, `barter`/`attract` mechanics | Phase 08.04 (Transactions), Phase 08.05 (Scarcity) | Phase 09: Commerce |
| **Phase 10: Emergent Settlement (Towns)** | Strut construction via `build`, property claims, community clustering | Phase 07 (Compositions), Phase 09 (Markets) | Phase 10: Towns |

**The Immediate Next Step**: Execute **Phase 08.04 (Inventory & Transaction Engine)** by implementing `InventoryController` (Goal 05) and `ExchangeController` (Goal 03). Decouple item manipulation entirely from `InteractionMechanics` and `MenuMechanics`, establishing transactional safety before introducing market exchange logic.

### Bug Reports

##### Bug B010: Incomplete Cradle Effect Spawning Pipeline and SpawnableGroup Omissions

**STATUS**: OPEN
**SEVERITY**: High

**Description**

Phase 02.06 refactored the effects taxonomy into functional variants (`passive`, `hazards`, `collectables`, `reactables`). However, `Cradle` and its supporting groups were only partially updated:

1. `SpawnableGroup` in `app/models/groups.py` registers `collectables` and `hazards`, but omits `passive` and `reactables`.
2. `Cradle` in `app/services/generators/cradle.py` defines `spawn_collectable` and `spawn_hazard`, but lacks methods for `reactables` or `passive`, and never introduced the generalized `spawn_effect` method specified in Phase 02.06 Task 4.
3. `Spawnables` in `app/config/enums.py` still contains the deprecated `TEMPORARY = "temporary"` enum value.

**Steps to Replicate**

1. Attempt to dynamically spawn a `reactable` or `passive` effect at runtime via `board.cradle`.
2. Observe that `Cradle` has no corresponding factory method and `self.spawnables` lacks dictionary lookups for these instances.

**Proposed Remediation**

Remove `TEMPORARY` from `Spawnables` in `app/config/enums.py`. Update `SpawnableGroup` to index `reactables` and `passive` property mappings. Implement a unified `Cradle.spawn_effect(id, instance, layer, position, **kwargs)` method that dynamically instantiates the correct typed state model (`AnimatorState`, `HazardState`, `CollectableState`, or `ReactableState`).

---

##### Bug B011: Singular and Plural Inconsistency in AssetInstances Effect Taxonomy

**STATUS**: OPEN
**SEVERITY**: Low

**Description**

In `src/app/config/enums.py`, `AssetInstances` declares `PASSIVE = "passive"` in singular form, while declaring `HAZARDS = "hazards"`, `COLLECTABLES = "collectables"`, and `REACTABLES = "reactables"` in plural form. Throughout the rest of the engine, instance categories are consistently pluralized (`CHESTS`, `CRATES`, `DOORS`, `SPRITES`, `TILES`). This discrepancy causes indexing mismatches when loading YAML state files or querying cached board instances (`board.instances(AssetInstances.PASSIVE.value)` vs expected plural directory structures).

**Steps to Replicate**

1. Query `AssetInstances.PASSIVE.value` (`"passive"`).
2. Compare against `AssetInstances.HAZARDS.value` (`"hazards"`) and `EffectPropertyInstances` fields in `app/models/properties.py`.

**Proposed Remediation**

Standardize `AssetInstances.PASSIVE` to `"passives"` (or normalize all effect instance enums to singular across properties, loaders, and state schemas consistently), updating all configuration loaders and YAML references accordingly.