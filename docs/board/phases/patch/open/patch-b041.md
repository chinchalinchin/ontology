
##### Bug B041: `Cache.get_obstacles()` Diverges from `predicates.is_obstacle()`, Omits `OBSTACLES` and `TREES`, and Fails on `layer=None`

**STATUS**: OPEN
**SEVERITY**: HIGH

**Description**

1. `Cache.get_obstacles(layer)` (`src/app/game/board/modules/cache.py`, lines 404–414) hardcodes five instance keys (`CRATES`, `GATES`, `STRUTS`, `SIGNS`, `CHESTS`), omitting `AssetInstances.OBSTACLES` and `AssetInstances.TREES` even though `predicates.is_obstacle()` (`src/app/game/logic/predicates.py`, lines 46–59) explicitly classifies both as navigational obstacles. Consequently, `NavigationMechanics` and obstacle-aware callers querying `board.obstacles(layer)` ignore rocks/outcroppings and trees.
2. `Cache.get_obstacles()` rebuilds and allocates a new `List[Asset]` on every invocation and includes passable `AssetInstances.STRUTS` (e.g., `floors`, `flats`, `paths`, `corridors`).
3. `Board.obstacles(layer=None)` (`src/app/game/board/core.py`, line 248) unconditionally returns `[]` when `layer is None`, contradicting its `Optional[str]` signature and all sibling query methods (`weights`, `categories`, `instances`).

**Steps to Replicate**

1. Construct a `Board` with an `AssetInstances.OBSTACLES` asset and an `AssetInstances.TREES` asset on layer `"main"`.
2. Call `board.obstacles("main")`: neither asset is returned.
3. Call `board.obstacles()` (with `layer=None`): returns `[]` even when crates/gates/struts exist on `"main"`.

**Proposed Remeditation**

Maintain a layer-keyed `cached_obstacles: Dict[str, List[Asset]]` inside `Cache` populated during `index_batch`, `evict_batch`, `relayer`, and `clear` using `predicates.is_obstacle(asset)` (further filtering passable `MaterialHitbox` struts via `MaterialIndex().is_obstacle(asset.state.blueprint)`), and support `layer=None` aggregation in `Cache.get_obstacles(layer=None)`.