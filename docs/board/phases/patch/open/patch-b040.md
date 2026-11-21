
##### Bug B040: `Cache.evict_batch` Leaves Stale Tile References in `cached_tilemap`

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/game/board/modules/cache.py`, `Cache.index_batch` populates the spatial hash `self.cached_tilemap[layer][inst][(cx, cy)] = asset` for every `AssetCategories.TILES` asset. However, `Cache.evict_batch` (lines 222–300) never removes evicted tile entries from `self.cached_tilemap`. After `board.remove(tiles)` is called, `board.tile(layer, position)` continues returning references to deleted tile assets (preserving stale terrain lookups and friction values).

**Steps to Replicate**

1. Add an `AssetInstances.ENVIRON` tile at `Position(0, 0)` on layer `'0'` via `board.add([tile])`.
2. Remove the tile via `board.remove([tile])`.
3. Query `board.tile('0', Position(0, 0))` and observe that the removed `tile` is still returned instead of `None`.

**Proposed Remeditation**

In `Cache.evict_batch`, when `AssetCategories.TILES` is present in `affected_categories`, iterate over evicted tiles (or rebuild affected layer tilemaps from remaining `cached_categories[layer][AssetCategories.TILES]`) to remove matching entries from `self.cached_tilemap`.


##### Bug B040-B (Duplicate Report): `Cache.evict_batch()` and `Cache.relayer()` Leave Stale Tile References in `cached_tilemap`

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

`Cache.index_batch()` (`src/app/game/board/modules/cache.py`, lines 212–233) indexes `AssetCategories.TILES` cells into `self.cached_tilemap[layer][inst][(cx, cy)] = asset`, but neither `Cache.evict_batch()` nor `Cache.relayer()` removes or updates entries in `self.cached_tilemap`. Removing or relayering a Tile leaves dangling asset references in `cached_tilemap`, causing `board.tile(layer, pos)` to return removed tiles (corrupting friction lookups in `MotionMechanics` and shoreline probes in `Cartographer`) and retaining references that prevent garbage collection.

**Steps to Replicate**

1. Add an `AssetInstances.ENVIRON` tile at `Position(0, 0)` on layer `"main"` to a `Board`.
2. Call `board.remove([tile])` (or `board.relayer(tile, "other")`).
3. Call `board.tile("main", Position(0, 0))`: the removed/relayered tile is still returned instead of `None`.

**Proposed Remeditation**

Add a `rebuild_tilemap(layer: str)` helper (or cell-level eviction/re-indexing) on `Cache` and invoke it in `evict_batch()` whenever `AssetCategories.TILES in affected_categories`, and in `relayer()` whenever `asset.category == AssetCategories.TILES` (updating both `old_layer` and `new_layer`).
