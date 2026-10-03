#### Achieve: Goal 10 - Board Modularization

The **Board** (`src/app/game/board.py`) serves as the central in-memory entity database and spatial querying system for the engine. It hydrates assets from world state, maintains spatial acceleration structures, and exposes query interfaces to both `core` and `world` mechanics.

The `Board` has accumulated multiple overlapping responsibilities, violating the Single Responsibility Principle (SRP):

1. **Entity Management & Cataloging**: Storing global asset references and lifecycle arrays.
2. **Multi-tier Caching & Spatial Partitioning**: Maintaining categorical, instance-based, weight, shoreline, tile spatial hash grids, and fluid broad-phase buckets.
3. **Geometric & Domain Predicates**: Executing narrow-phase spatial intersection tests for fluid streams, annular pools, and asset classification.
4. **Serialization & World Snapshotting**: Dumping state models for persistence.

```
+-----------------------------------------------------------------------------------+
|                                 app.game.board                                    |
+-----------------------------------------------------------------------------------+
|  Entity Database (Board)        |  Indices & Grids (BoardCaches)  |  Predicates   |
|  - Asset lifecycle              |  - Categorical index            |  - is_weight  |
|  - Query interfaces (getters)   |  - Instance index               |  - in_stream  |
|  - Engine hooks (cradle, etc.)  |  - Spatial tile hash (O(1))     |  - in_pool    |
|  - State serialization          |  - Spatial fluid buckets (O(1)) |  - in_fluid   |
|                                 |  - Mutation lifecycle           |  - is_obstacle|
+-----------------------------------------------------------------------------------+
```

**Overview**

Decompose `app.game.board.Board` by extracting stateless predicates into `app.game.board.predicates` and spatial/categorical acceleration structures into `app.game.board.caches`. Restructure the `app.game.board` package to resolve module namespace collisions and establish clean lifecycle boundaries for cache maintenance.

##### Goal: Package Restructure & Namespacing

Consolidate the existing `src/app/game/board.py` file into `src/app/game/board/core.py` and establish `src/app/game/board/__init__.py` to re-export `Board`. This eliminates the file/directory collision between `board.py` and `board/` while preserving backward compatibility across imports in `Engine`, `Screen`, `Builder`, and `Mechanic` implementations.

##### Goal: app.game.board.predicates

Extract stateless geometric and classification tests into module-level functions in `src/app/game/board/predicates.py`. Functions must strictly evaluate immutable `AssetProperties` and transient `Position` or `Hitbox` models without referencing `Board` instances:

* `is_weight(asset: Asset) -> bool`: Verifies mass ($m \ge 0$) while filtering out sensory categories via `AssetCategories` enums.
* `is_obstacle(asset: Asset) -> bool`: Identifies obstacle entities (`chests`, `crates`, `gates`, `struts`, `signs`) via `AssetInstances` enums.
* `in_stream(position: Position, fluid: Asset) -> bool`: AABB raycast penetration test for directional parent and branch corridors.
* `in_pool(position: Position, fluid: Asset) -> bool`: Point-in-polygon/box test for annular fluid pools.
* `in_fluid(position: Position, fluid: Asset) -> bool`: Composite evaluation combining `in_pool` and `in_stream`.

##### Goal: app.game.board.caches

Implement `BoardCaches` in `src/app/game/board/caches.py` to own all acceleration structures:

* Categorical mappings (`_cached_categories`, `_all_categories`).
* Instance mappings (`_cached_instances`, `_all_instances`).
* Layer spatial arrays (`_cached_layers`, `_cached_renderables`, `_cached_weights`).
* Spatial tile hash table (`_cached_tilemap`).
* Broad-phase spatial water grid (`_cached_watermap`).
* Character state cache (`_cached_characters`) and shoreline collection (`_shorelines`).
Expose discrete lifecycle interfaces (`init_layer`, `index_batch`, `evict_batch`, `relayer`, `rebuild_water`, `clear`).

##### Goal: Board Core Refactoring & Delegation

Refactor `Board` in `src/app/game/board/core.py` to delegate all cache operations directly to an internal `self._caches = BoardCaches()` instance. Streamline `add()`, `remove()`, `relayer()`, and `clear()` to call composite cache methods rather than mutating internal dictionaries manually.

##### Tasks

**1. Task: Establish `app.game.board` Package Structure**

*Objective*: Convert `board.py` and `board/` into a unified Python package without breaking external imports.

* [x] Subtask: Move `src/app/game/board.py` to `src/app/game/board/core.py`.
* [x] Subtask: Create `src/app/game/board/__init__.py` exposing `Board`.
* [x] Subtask: Verify import resolution in `src/app/services/orchestration/builder.py` and `src/app/game/engine.py`.

**2. Task: Implement `app.game.board.predicates**`

*Objective*: Implement pure predicate functions in `src/app/game/board/predicates.py`.

* [x] Subtask: Implement `is_weight(asset: Asset) -> bool` using `AssetCategories` enums.
* [x] Subtask: Implement `is_obstacle(asset: Asset) -> bool` using `AssetInstances` enums.
* [x] Subtask: Implement `in_stream(position: Position, fluid: Asset) -> bool` and `in_pool(position: Position, fluid: Asset) -> bool`.
* [x] Subtask: Implement composite `in_fluid(position: Position, fluid: Asset) -> bool`.
* [x] Subtask: Add unit tests validating predicates with mock assets across dry, submerged, and obstructed conditions.

**3. Task: Implement `BoardCaches` Container**

*Objective*: Implement `BoardCaches` in `src/app/game/board/caches.py` to encapsulate all categorical and spatial hashing structures.

* [x] Subtask: Define internal dictionary structures and correct `watermap` type annotation to `Dict[str, Dict[Tuple[int, int], List[Asset]]]`.
* [x] Subtask: Implement `init_layer(layer: str)` and `clear()` cache wiping routines.
* [x] Subtask: Implement `index(asset: Asset)` and `index_batch(assets: List[Asset])` handling tile partitioning and fluid mapping.
* [x] Subtask: Implement `evict(asset: Asset)` and `evict_batch(assets: List[Asset])` set-membership comprehensions.
* [x] Subtask: Implement `relayer(asset: Asset, old_layer: str, new_layer: str)`.
* [x] Subtask: Implement `rebuild_water(layer: str, fluids: List[Asset])` broad-phase spatial hash synchronization.

**4. Task: Integrate `BoardCaches` into `Board`**

*Objective*: Refactor `Board` methods to delegate to `BoardCaches` and remove inline dictionary modifications.

* [x] Subtask: Replace dictionary definitions on `Board` with `self._caches: BoardCaches`.
* [x] Subtask: Refactor `Board.add()` to delegate to `self._caches.index_batch()`.
* [x] Subtask: Refactor `Board.remove()` to delegate to `self._caches.evict_batch()`.
* [x] Subtask: Refactor `Board.relayer()` to delegate to `self._caches.relayer()`.
* [x] Subtask: Refactor `Board.fluid()` to query `self._caches.watermap` and call `predicates.in_fluid()`.
* [x] Subtask: Update `Board.clear()` to trigger `self._caches.clear()`.
* [!] Subtask: Execute full test suite to guarantee zero regression across mechanics.