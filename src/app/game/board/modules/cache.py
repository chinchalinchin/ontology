"""
@domain.system
@app.module
@app.board

# Ontology: Source - app.game.board.modules.caches

Acceleration structures and caching container for the Board.
"""
# Standard Libraries
import logging
from typing import (
    List,
    Dict,
    Set,
    Tuple,
    Any,
    Optional
)

# Application Libraries
import app.static.settings as settings
import app.game.logic.predicates as predicates
from app.assets.base import Asset
from app.models.state.core import AssetState
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Directions
)

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Position
)

logger = logging.getLogger(__name__)

# -------------------------------------------

class Cache:
    """
    Encapsulates all categorical, instance, spatial grid, and layer-scoped caches.
    """
    cached_categories: Dict[str, Dict[str, List[Asset]]]
    cached_instances: Dict[str, Dict[str, List[Asset]]]
    cached_layers: Dict[str, List[Asset]]
    cached_renderables: Dict[str, List[Asset]]
    cached_weights: Dict[str, List[Asset]]
    cached_tilemap: Dict[str, Dict[str, Dict[Tuple[int, int], Asset]]]
    cached_fluidmap: Dict[str, Dict[Tuple[int, int], List[Asset]]]
    cached_characters: Dict[str, Any]
    cached_states: Dict[str, Dict[str, AssetState]]
    cached_sizes: Dict[str, Dimensions]
    assets_by_name: Dict[str, Asset]
    shorelines: Dict[str, List[Asset]]
    all_categories: Dict[str, List[Asset]]
    all_instances: Dict[str, List[Asset]]


    def __init__(self) -> None:
        """Initializes all categorical, instance, spatial grid, and layer-scoped stores."""
        self.clear()


    @staticmethod
    def _asset_extent(asset: Asset) -> Tuple[int, int]:
        """
        Computes the far-corner (max_x, max_y) world extent contributed by an asset.
        """
        position = asset.state.position
        if position is None:
            return (0, 0)

        if asset.category == AssetCategories.TILES:
            multiple = asset.state.multiple
            if multiple is None:
                return (0, 0)
            ext_w = int(position.x) + (multiple.nx * asset.properties.dimensions.w)
            ext_l = int(position.y) + (multiple.ny * asset.properties.dimensions.l)
            return (ext_w, ext_l)

        if asset.dimensions:
            ext_w = int(position.x) + asset.dimensions.w
            ext_l = int(position.y) + asset.dimensions.l
            return (ext_w, ext_l)

        return (0, 0)


    def init_layer(self, layer: str) -> None:
        """
        Initializes cache buckets for a specific layer.
        """
        if layer is None:
            return

        self.cached_categories.setdefault(layer, {})
        self.cached_instances.setdefault(layer, {})
        self.cached_layers.setdefault(layer, [])
        self.cached_renderables.setdefault(layer, [])
        self.cached_weights.setdefault(layer, [])
        self.cached_tilemap.setdefault(layer, {
            AssetInstances.ENVIRON: {},
            AssetInstances.CANOPY: {}
        })
        self.cached_fluidmap.setdefault(layer, {})
        self.cached_states.setdefault(layer, {})
        self.cached_sizes.setdefault(layer, Dimensions(w=0, l=0))
        self.shorelines.setdefault(layer, [])


    def map_fluid(self, layer: str, fluid: Asset) -> None:
        """
        Indexes parent corridors, annular pools, and all active branch corridors
        into the O(1) broad-phase fluid spatial hash grid.
        """
        if layer not in self.cached_fluidmap:
            self.cached_fluidmap[layer] = {}

        fx = fluid.state.position.x
        fy = fluid.state.position.y
        fw = fluid.properties.dimensions.w
        fl = fluid.properties.dimensions.l
        length = fluid.state.length
        direction = fluid.state.source

        def _index_box(x1: int, y1: int, x2: int, y2: int) -> None:
            if x2 > x1 and y2 > y1:
                start_cx = int(x1) // settings.TILE_HASH_SIZE
                end_cx = (int(x2) - 1) // settings.TILE_HASH_SIZE + 1
                start_cy = int(y1) // settings.TILE_HASH_SIZE
                end_cy = (int(y2) - 1) // settings.TILE_HASH_SIZE + 1
                for cx in range(start_cx, end_cx):
                    for cy in range(start_cy, end_cy):
                        bucket = self.cached_fluidmap[layer].setdefault((cx, cy), [])
                        if fluid not in bucket:
                            bucket.append(fluid)

        # 1. Parent directional stream corridor
        if length > 0:
            if direction == Directions.DOWN:
                _index_box(fx, fy, fx + fw, fy + length)
            elif direction == Directions.UP:
                _index_box(fx, fy - length, fx + fw, fy)
            elif direction == Directions.RIGHT:
                _index_box(fx, fy, fx + length, fy + fl)
            elif direction == Directions.LEFT:
                _index_box(fx - length, fy, fx, fy + fl)

        # 2. Annular pool
        pool = fluid.state.pool
        if pool and pool.w > 0 and pool.l > 0:
            _index_box(pool.x, pool.y, pool.x + pool.w, pool.y + pool.l)

        # 3. Child branch corridors
        branches = fluid.state.branches
        if branches:
            for branch in branches:
                if branch.length <= 0:
                    continue
                bx = branch.position.x
                by = branch.position.y
                b_dir = branch.source

                if b_dir == Directions.DOWN:
                    _index_box(bx, by, bx + fw, by + branch.length)
                elif b_dir == Directions.UP:
                    _index_box(bx, by - branch.length, bx + fw, by)
                elif b_dir == Directions.RIGHT:
                    _index_box(bx, by, bx + branch.length, by + fl)
                elif b_dir == Directions.LEFT:
                    _index_box(bx - branch.length, by, bx, by + fl)


    def rebuild_fluid(self, layer: str) -> None:
        """
        Rebuilds the O(1) spatial fluid grid cache for the specified layer.
        """
        if layer not in self.cached_fluidmap:
            self.cached_fluidmap[layer] = {}
        else:
            self.cached_fluidmap[layer].clear()

        fluids = self.get_instances(AssetInstances.FLUIDS, layer)
        for fluid in fluids:
            self.map_fluid(layer, fluid)


    def index_batch(self, assets: List[Asset]) -> None:
        """
        Indexes a batch of assets across all multi-tier dictionaries and spatial grids.
        """
        affected_fluid_layers: Set[str] = set()
        batch_extents: Dict[str, List[int]] = {}

        for asset in assets:
            layer = asset.state.layer
            cat = asset.category
            inst = asset.instance

            # Always register in global catalogues regardless of layer deployment
            self.all_categories.setdefault(cat, []).append(asset)
            self.all_instances.setdefault(inst, []).append(asset)

            if asset.name:
                self.assets_by_name[asset.name] = asset

            if cat == AssetCategories.SHEETS and inst in (
                AssetInstances.SPRITES,
                AssetInstances.PLAYERS
            ):
                if asset.name:
                    self.cached_characters[asset.name] = asset.state

            # Layerless assets (e.g., stateless Equipment wrappers) skip layer-scoped caches
            if layer is None:
                continue

            if layer not in self.cached_categories:
                self.init_layer(layer)

            self.cached_categories[layer].setdefault(cat, []).append(asset)
            self.cached_instances[layer].setdefault(inst, []).append(asset)
            self.cached_layers[layer].append(asset)

            if asset.name:
                self.cached_states[layer][asset.name] = asset.state

            if cat != AssetCategories.TILES:
                self.cached_renderables[layer].append(asset)

            if predicates.is_weight(asset):
                self.cached_weights[layer].append(asset)

            if inst == AssetInstances.SHORELINES:
                self.shorelines[layer].append(asset)

            if inst == AssetInstances.FLUIDS:
                affected_fluid_layers.add(layer)

            # Update cached layer dimensions monotonically when the layer is not dirty
            if layer in self.cached_sizes:
                ext_w, ext_l = self._asset_extent(asset)
                bounds = batch_extents.get(layer)
                if bounds is None:
                    cur = self.cached_sizes[layer]
                    bounds = [cur.w, cur.l]
                    batch_extents[layer] = bounds
                if ext_w > bounds[0]:
                    bounds[0] = ext_w
                if ext_l > bounds[1]:
                    bounds[1] = ext_l

            if cat == AssetCategories.TILES:
                w = asset.properties.dimensions.w
                l = asset.properties.dimensions.l

                start_x = int(asset.state.position.x)
                start_y = int(asset.state.position.y)
                end_x = start_x + (asset.state.multiple.nx * w)
                end_y = start_y + (asset.state.multiple.ny * l)

                for cx in range(
                    start_x // settings.TILE_HASH_SIZE,
                    (end_x - 1) // settings.TILE_HASH_SIZE + 1
                ):
                    for cy in range(
                        start_y // settings.TILE_HASH_SIZE,
                        (end_y - 1) // settings.TILE_HASH_SIZE + 1
                    ):
                        if inst not in self.cached_tilemap[layer]:
                            self.cached_tilemap[layer][inst] = {}
                        self.cached_tilemap[layer][inst][(cx, cy)] = asset

        # Commit updated layer dimensions once per modified layer
        for layer, (max_w, max_l) in batch_extents.items():
            cur = self.cached_sizes[layer]
            if max_w > cur.w or max_l > cur.l:
                self.cached_sizes[layer] = Dimensions(w=max_w, l=max_l)

        for layer in affected_fluid_layers:
            self.rebuild_fluid(layer)


    def evict_batch(self, removals: List[Asset]) -> None:
        """
        Evicts a batch of assets across all dictionaries, resolving B012 by avoiding method collision.
        """
        if not removals:
            return

        removal_set = set(removals)
        removal_names = {
            a.name for a in removals 
            if a.name
        }
        affected_layers = {
            a.state.layer for a in removals 
            if a.state and a.state.layer
        }
        affected_categories = {
            a.category for a in removals 
            if a.category
        }
        affected_instances = {
            a.instance for a in removals 
            if a.instance
        }

        # 1. Layer-scoped cache filters
        for layer in affected_layers:
            if layer in self.cached_categories:
                for cat in affected_categories:
                    if cat in self.cached_categories[layer]:
                        self.cached_categories[layer][cat] = [
                            a for a in self.cached_categories[layer][cat]
                            if a not in removal_set
                        ]

            if layer in self.cached_instances:
                for inst in affected_instances:
                    if inst in self.cached_instances[layer]:
                        self.cached_instances[layer][inst] = [
                            a for a in self.cached_instances[layer][inst]
                            if a not in removal_set
                        ]

            if layer in self.cached_layers:
                self.cached_layers[layer] = [
                    a for a in self.cached_layers[layer]
                    if a not in removal_set
                ]

            if layer in self.cached_renderables:
                self.cached_renderables[layer] = [
                    a for a in self.cached_renderables[layer]
                    if a not in removal_set
                ]

            if layer in self.cached_weights:
                self.cached_weights[layer] = [
                    a for a in self.cached_weights[layer]
                    if a not in removal_set
                ]

            if layer in self.shorelines:
                self.shorelines[layer] = [
                    a for a in self.shorelines[layer]
                    if a not in removal_set
                ]

            # Invalidate cached layer size so extents recompute lazily after eviction
            self.cached_sizes.pop(layer, None)

        # 2. Global catalogue filters
        for cat in affected_categories:
            if cat in self.all_categories:
                self.all_categories[cat] = [
                    a for a in self.all_categories[cat]
                    if a not in removal_set
                ]

        for inst in affected_instances:
            if inst in self.all_instances:
                self.all_instances[inst] = [
                    a for a in self.all_instances[inst]
                    if a not in removal_set
                ]

        for asset in removals:
            if asset.name and self.assets_by_name.get(asset.name) is asset:
                del self.assets_by_name[asset.name]

            # Identity-safe eviction preserves reciprocal Door projections on other layers
            layer = asset.state.layer
            if (
                layer is not None
                and asset.name
                and layer in self.cached_states
                and self.cached_states[layer].get(asset.name) is asset.state
            ):
                del self.cached_states[layer][asset.name]

        # 3. Character cache evictions
        for name in removal_names:
            if name in self.cached_characters:
                del self.cached_characters[name]

        # 4. Invalidate fluid cache if fluids removed
        if AssetInstances.FLUIDS in affected_instances:
            for layer in affected_layers:
                self.rebuild_fluid(layer)


    def relayer(self, asset: Asset, new_layer: Optional[str]) -> None:
        """
        Atomically shifts an asset's cache indexing across layers.
        """
        old_layer = asset.state.layer
        if old_layer == new_layer:
            return

        logger.debug(f"Relayering asset '{asset.taxonomy.name}' from layer '{old_layer}' -> '{new_layer}'.")

        cat = asset.category
        inst = asset.instance

        if old_layer is not None:
            if old_layer in self.cached_categories and cat in self.cached_categories[old_layer]:
                if asset in self.cached_categories[old_layer][cat]:
                    self.cached_categories[old_layer][cat].remove(asset)

            if old_layer in self.cached_instances and inst in self.cached_instances[old_layer]:
                if asset in self.cached_instances[old_layer][inst]:
                    self.cached_instances[old_layer][inst].remove(asset)

            if old_layer in self.cached_layers and asset in self.cached_layers[old_layer]:
                self.cached_layers[old_layer].remove(asset)

            if old_layer in self.cached_renderables and asset in self.cached_renderables[old_layer]:
                self.cached_renderables[old_layer].remove(asset)

            if old_layer in self.cached_weights and asset in self.cached_weights[old_layer]:
                self.cached_weights[old_layer].remove(asset)

            if old_layer in self.shorelines and asset in self.shorelines[old_layer]:
                self.shorelines[old_layer].remove(asset)

            if (
                old_layer in self.cached_states
                and asset.name
                and self.cached_states[old_layer].get(asset.name) is asset.state
            ):
                del self.cached_states[old_layer][asset.name]

            self.cached_sizes.pop(old_layer, None)

        asset.state.layer = new_layer

        # Detaching an asset from all layers requires no target layer registration
        if new_layer is None:
            if inst == AssetInstances.FLUIDS and old_layer is not None:
                self.rebuild_fluid(old_layer)
            return

        if new_layer not in self.cached_categories:
            self.init_layer(new_layer)

        self.cached_categories[new_layer].setdefault(cat, []).append(asset)
        self.cached_instances[new_layer].setdefault(inst, []).append(asset)
        self.cached_layers[new_layer].append(asset)

        if asset.name:
            self.cached_states[new_layer][asset.name] = asset.state

        if cat != AssetCategories.TILES:
            self.cached_renderables[new_layer].append(asset)

        if predicates.is_weight(asset):
            self.cached_weights[new_layer].append(asset)

        if inst == AssetInstances.SHORELINES:
            self.shorelines[new_layer].append(asset)

        if new_layer in self.cached_sizes:
            ext_w, ext_l = self._asset_extent(asset)
            cur = self.cached_sizes[new_layer]
            if ext_w > cur.w or ext_l > cur.l:
                self.cached_sizes[new_layer] = Dimensions(
                    w=max(cur.w, ext_w),
                    l=max(cur.l, ext_l)
                )

        if inst == AssetInstances.FLUIDS:
            if old_layer is not None:
                self.rebuild_fluid(old_layer)
            self.rebuild_fluid(new_layer)


    def clear(self) -> None:
        """
        Clears all indices and resets layer stores.
        """
        self.cached_categories = {}
        self.cached_instances = {}
        self.cached_layers = {}
        self.cached_renderables = {}
        self.cached_weights = {}
        self.cached_tilemap = {}
        self.cached_fluidmap = {}
        self.cached_characters = {}
        self.cached_states = {}
        self.cached_sizes = {}
        self.assets_by_name = {}
        self.shorelines = {}
        self.all_categories = {}
        self.all_instances = {}

    # ------------------------------------------------ GETTERS

    def get_asset(self, name: str, layer: Optional[str] = None) -> Optional[Asset]:
        """
        Retrieves an asset in O(1) by unique deployment name, optionally
        verifying membership on the specified layer.
        """
        asset = self.assets_by_name.get(name)
        if asset is None:
            return None
        if layer is not None and asset.state.layer != layer:
            return None
        return asset

    def get_size(self, layer: str) -> Dimensions:
        """
        Returns cached layer dimensions in O(1), lazily recomputing after
        evictions or relayer invalidations.
        """
        cached = self.cached_sizes.get(layer)
        if cached is not None:
            return cached

        layer_assets = self.cached_layers.get(layer)
        if layer_assets is None:
            return Dimensions(w=0, l=0)

        max_w = 0
        max_l = 0
        for asset in layer_assets:
            ext_w, ext_l = self._asset_extent(asset)
            if ext_w > max_w:
                max_w = ext_w
            if ext_l > max_l:
                max_l = ext_l

        size = Dimensions(w=max_w, l=max_l)
        self.cached_sizes[layer] = size
        return size

    def get_categories(self, category: str, layer: Optional[str] = None) -> List[Asset]:
        if layer is not None:
            return self.cached_categories.get(layer, {}).get(category, [])
        return self.all_categories.get(category, [])

    def get_instances(self, instance: str, layer: Optional[str] = None) -> List[Asset]:
        if layer is not None:
            return self.cached_instances.get(layer, {}).get(instance, [])
        return self.all_instances.get(instance, [])

    def get_layers(self) -> List[str]:
        return list(self.cached_categories.keys())

    def get_layer_assets(self, layer: str) -> List[Asset]:
        return self.cached_layers.get(layer, [])

    def get_renderables(self, layer: Optional[str] = None) -> List[Asset]:
        if layer is not None:
            return self.cached_renderables.get(layer, [])
        all_renderables: List[Asset] = []
        for layer_list in self.cached_renderables.values():
            all_renderables.extend(layer_list)
        return all_renderables

    def get_weights(self, layer: Optional[str] = None) -> List[Asset]:
        if layer is not None:
            return self.cached_weights.get(layer, [])
        all_weights: List[Asset] = []
        for layer_list in self.cached_weights.values():
            all_weights.extend(layer_list)
        return all_weights

    def get_obstacles(self, layer: str) -> List[Asset]:
        obstacles: List[Asset] = []
        layer_inst = self.cached_instances.get(layer, {})
        for inst_key in (
            AssetInstances.CRATES,
            AssetInstances.GATES,
            AssetInstances.STRUTS,
            AssetInstances.SIGNS,
            AssetInstances.CHESTS
        ):
            obstacles.extend(layer_inst.get(inst_key, []))
        return obstacles

    def get_shorelines(self, layer: Optional[str] = None) -> List[Asset]:
        if layer is not None:
            return self.shorelines.get(layer, [])
        all_shores: List[Asset] = []
        for l_shores in self.shorelines.values():
            all_shores.extend(l_shores)
        return all_shores

    def get_tile(
        self,
        layer: str,
        position: Position,
        instance: str = AssetInstances.ENVIRON
    ) -> Optional[Asset]:
        cx = int(position.x) // settings.TILE_HASH_SIZE
        cy = int(position.y) // settings.TILE_HASH_SIZE
        return self.cached_tilemap.get(layer, {}).get(instance, {}).get((cx, cy))

    def get_character(self, name: str) -> Optional[Any]:
        return self.cached_characters.get(name)

    def get_characters(self) -> Dict[str, Any]:
        return self.cached_characters

    def get_states(self, layer: str) -> Dict[str, AssetState]:
        """Returns the O(1) layer-scoped mapping of asset names to AssetStates."""
        return self.cached_states.get(layer, {})

    def get_fluid_bucket(self, layer: str, cx: int, cy: int) -> Optional[List[Asset]]:
        return self.cached_fluidmap.get(layer, {}).get((cx, cy))