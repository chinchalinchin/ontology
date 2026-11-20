#### Refactor: Phase 01.04 - Board Optimization

##### Notes

1. **Temporal Coupling and Encapsulation Leaks in `Board`**

* **Nullable Late-Bound Dependencies Violating Type Annotations**: In `src/app/game/board/core.py` (lines 69–77), `plot: PlotState`, `device: Device`, and `cradle: Cradle` are annotated as non-optional, while `self.materializer` is unannotated. In `Board.__init__` (lines 90–95), all five are initialized to `None` and mutated later via setter methods (`set_device`, `set_cradle`, `set_plot`, `set_migrator`). Any mechanic or handler invoked before all setters run encounters `AttributeError` on `None`.
* **11 Private Cache Structures Exposed on `Board**`:  `src/app/game/board/core.py` exposes `_cached_categories`, `_cached_instances`, `_cached_layers`, `_cached_renderables`, `_cached_weights`, `_cached_tilemap`, `_cached_fluidmap`, `_cached_characters`, `_all_categories`, `_all_instances`, and `_shorelines` directly from `self._cache`. External callers inspecting these properties bypass `Board`'s query API and couple directly to `Cache` implementation details.

2. $O(N)$ Linear Scans for Unique Entity Lookups and Layer Dimensions in `Board`

* **`Board.asset(name, layer)` (`src/app/game/board/core.py`, lines 222–224)**:
```python
def asset(self, name: str, layer: Optional[str] = None) -> Optional[Asset]:
    search_list = self.renderables(layer) if layer else self._assets
    return next((a for a in search_list if a.name == name), None)
```

Although `asset.name` is globally unique across a deployed `Board` (`docs/01-assets.md`, *Hierarchy: Taxonomy*), `board.asset(name)` performs an $O(N)$ linear scan. Worse, when `layer` is specified, it searches `self.renderables(layer)`, which excludes `AssetCategories.TILES`—meaning `board.asset(tile_name, layer="main")` always returns `None`. Indexing `assets_by_name: Dict[str, Asset]` inside `Cache` reduces `board.asset(name)` to $O(1)$.

* **`Board.size(layer)` (`src/app/game/board/core.py`)**:

*Iterates over every asset on the layer in $O(N)$ on each invocation to compute `max_w` and `max_l`, rather than caching layer dimensions in `Cache` during `index_batch` / `evict_batch`.

3. **`dataclasses.asdict` Serialization on Cython Extension Types in `Board.serialize`**

*In `src/app/game/board/core.py` (line 408), `Board.serialize` converts runtime states to dictionaries via `asdict(asset.state)`. However, `SheetState`, `ObjectState`, `CraftState`, etc., store Cython `cdef class` extension types (`libs.core.models.Position`, `Velocity`, `Dimensions`, `Multiple`) in their fields (`src/app/models/state/assets/sheets.py`). Python's `dataclasses.asdict()` only unpacks standard Python `@dataclass` objects, lists, tuples, and dicts; for Cython `cdef class` instances, `asdict()` falls back to `copy.deepcopy(obj)`, leaving raw Cython extension instances in the output dict (or raising `TypeError` if `__reduce__`/`__deepcopy__` is not implemented on every `cdef class` in `libs.core.models`).

4. **Per-Call List and Tuple Allocations in `predicates.in_pool` and `predicates.in_stream`**

* `in_pool()` allocates a single-element list `[(pool.x, pool.y, pool.x + pool.w, pool.y + pool.l)]` on every call just to invoke `geometry.inside()` for a 4-integer comparison.
* `in_stream()` rebuilds `aabbs: List[Tuple[int, int, int, int]]` from `fluid.state.source` and `fluid.state.branches` on every `Board.fluid()` lookup (`60 Hz` per moving entity), even though `Actuator.propagate()` already compiles the active stream and pool geometry onto `fluid.state.hitboxes`.

