"""
# Ontology: app.game.board

Module for game database class, Board.
"""
# Standard Libraries 
import logging
from typing import (
    List, 
    Dict, 
    Tuple,
    Any,
    Optional
)
from dataclasses import asdict

# Application Libraries
import app.config.settings as settings
from app.assets.base import Asset
from app.config.enums import (
    AssetCategories,
    AssetInstances,
    Directions,
    Lifecycles
)
from app.config.loader import Loader
from app.game.devices import Device
from app.game.menus.core import Menu
from app.services.generators.game.cradle import Cradle
from app.models.state.core import PlotState
from app.models.config import ConfigurationSchema
from app.models.groups import EquipmentGroup

# Cython Libraries
from libs.core.models import (
    Dimensions, 
    Position,
    Boundary
)

logger = logging.getLogger(__name__)

class Board:
    """
    ## Board

    Central database for the game Engine. Holds all Asset state and configuration,
    and provides queryable interfaces for Mechanics to retrieve pertinent game data.
    """
    # ------- Public Fields
    # Flags
    loaded: bool
    paused: bool
    # Game Data
    plot: PlotState
    perimeters: Dict[str, List[Boundary]]
    shorelines: Dict[str, List[Asset]]
    # Configurations
    configurations: ConfigurationSchema
    equipment: EquipmentGroup
    # Game Components
    device: Device
    cradle: Cradle
    menus: List[Menu]
    overlays: List[Menu]
    # ------- Private Fields
    # Assets
    _assets: List[Asset]
    # Caches
    _cached_categories: Dict[str, Dict[str, List[Asset]]]
    _cached_instances: Dict[str, Dict[str, List[Asset]]]
    _cached_layers: Dict[str, List[Asset]]
    _cached_renderables: Dict[str, List[Asset]]
    _cached_weights: Dict[str, List[Asset]]
    _cached_tilemap: Dict[str, Dict[Tuple[int, int], Asset]]
    _cached_characters: Dict[str, Any]
    # Catalogues
    _all_categories: Dict[str, List[Asset]]
    _all_instances: Dict[str, List[Asset]]

    def __init__(self, 
        assets: List[Asset], 
        configurations: ConfigurationSchema,
        equipment: EquipmentGroup
    ):
        logger.info(f"Initializing Board with {len(assets)} incoming assets.")
        self.loaded = False
        self.paused = False
        self.plot = None
        self.device = None
        self.cradle = None
        self.menus = []
        self.overlays = []
        self.configurations = configurations
        self.equipment = equipment
        self.perimeters = {}
        self.shorelines = {}
        self._assets = assets
        self._catalogue()
        self._cache()
        logger.info("Board completely hydrated and initialized.")

    # ---------------------------------------------------------
    # ----------------------------------------- PRIVATE METHODS

    def _catalogue(self):
        self._all_categories = {}
        self._all_instances = {}
        for asset in self._assets:
            cat = asset.category
            inst = asset.instance

            if cat not in self._all_categories:
                self._all_categories[cat] = []
            self._all_categories[cat].append(asset)

            if inst not in self._all_instances:
                self._all_instances[inst] = []
            self._all_instances[inst].append(asset)

    def _init_cache(self, layer: Optional[str] = None) -> None:
        if layer is None:
            self._cached_categories = {}
            self._cached_instances = {}
            self._cached_layers = {}
            self._cached_renderables = {}
            self._cached_weights = {}
            self._cached_tilemap = {}
            self._cached_characters = {}
            self.perimeters = {}
            self.shorelines = {}
            return

        self._cached_categories[layer] = {}
        self._cached_instances[layer] = {}
        self._cached_layers[layer] = []
        self._cached_renderables[layer] = []
        self._cached_weights[layer] = []
        self._cached_tilemap[layer] = {
            AssetInstances.BACK.value: {},
            AssetInstances.FORE.value: {}
        }
        self.perimeters[layer] = []
        self.shorelines[layer] = []
        return

    def _cache(self):
        logger.debug("Building initial board spatial caching dictionaries by layer/category/instance.")
        self._init_cache()

        for asset in self._assets:
            layer = asset.state.layer
            cat = asset.category
            inst = asset.instance

            if layer not in self._cached_categories:
                self._init_cache(layer)

            if cat not in self._cached_categories[layer]:
                self._cached_categories[layer][cat] = []
            self._cached_categories[layer][cat].append(asset)
            
            if inst not in self._cached_instances[layer]:
                self._cached_instances[layer][inst] = []
            self._cached_instances[layer][inst].append(asset)

            self._cached_layers[layer].append(asset)
            
            if cat != AssetCategories.TILES.value:
                self._cached_renderables[layer].append(asset)

            if hasattr(asset.properties, 'mass') and asset.properties.mass >= 0:
                self._cached_weights[layer].append(asset)
                
            if cat == AssetCategories.SHEETS.value and inst in (
                AssetInstances.SPRITES.value, 
                AssetInstances.PLAYERS.value
            ):
                if asset.name:
                    self._cached_characters[asset.name] = asset.state

            if inst == AssetInstances.SHORELINES.value:
                self.shorelines[layer].append(asset)

            if cat == AssetCategories.TILES.value:
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
                        if inst not in self._cached_tilemap[layer]:
                            self._cached_tilemap[layer][inst] = {}
                        self._cached_tilemap[layer][inst][(cx, cy)] = asset

    def _in_stream(self, position: Position, fluid: Asset) -> bool:
        """
        Evaluates whether Cartesian coordinate intersects the directional stream corridor
        of the specified fluid entity.
        """
        px = position.x
        py = position.y
        fx = fluid.state.position.x
        fy = fluid.state.position.y
        fw = fluid.properties.dimensions.w
        fl = fluid.properties.dimensions.l
        slen = fluid.state.length

        direction = fluid.state.source
        direction_val = direction.value if hasattr(direction, "value") else str(direction)

        if direction_val == Directions.DOWN.value:
            return fx <= px < fx + fw and fy <= py < fy + slen
        elif direction_val == Directions.UP.value:
            return fx <= px < fx + fw and fy - slen <= py < fy
        elif direction_val == Directions.RIGHT.value:
            return fx <= px < fx + slen and fy <= py < fy + fl
        elif direction_val == Directions.LEFT.value:
            return fx - slen <= px < fx and fy <= py < fy + fl

        return False

    # ---------------------------------------------------------
    # ------------------------------------------ PUBLIC METHODS

    # ---------------------------------------------- PREDICATES

    def water(
        self,
        layer: str,
        position: Position,
        exclude: Optional[str] = None
    ) -> bool:
        """
        Evaluates whether world coordinate (pos.x, pos.y) intersects any active
        fluid stream corridor or annular pool on the given layer.
        """
        fluids = self.instances(AssetInstances.FLUIDS.value, layer)
        for fluid in fluids:
            if exclude and fluid.name == exclude:
                continue
            # Evaluate pool bounds
            pool = fluid.state.pool
            if pool and pool.x <= position.x < pool.x + pool.w and pool.y <= position.y < pool.y + pool.l:
                return True
            # Evaluate directional stream corridor bounds
            if fluid.state.length > 0:
                if self._in_stream(position, fluid):
                    return True
        return False

    # ------------------------------------------------ SETTERS 

    def set_device(self, device: Device) -> None: self.device = device

    def set_cradle(self, cradle: Cradle) -> None: self.cradle = cradle

    def set_overlays(self, overlays: List[Menu]) -> None: self.overlays = overlays

    def set_plot(self, plot: str) -> None: self.plot = plot

    # ------------------------------------------------ GETTERS

    def player(self, slot = 0) -> Asset:
        players = self._all_instances.get(AssetInstances.PLAYERS.value, [])
        if not players:
            return None
        if slot < len(players):
            return players[slot]
        return players[0]

    def tile(self, 
        layer: str, 
        position: Position, 
        instance: str = AssetInstances.BACK.value
    ) -> Asset:
        cx = int(position.x) // settings.TILE_HASH_SIZE
        cy = int(position.y) // settings.TILE_HASH_SIZE
        return self._cached_tilemap.get(layer, {}).get(instance, {}).get((cx, cy))

    def character(self, name: str) -> Any:
        return self._cached_characters.get(name)

    def characters(self) -> Dict[str, Any]:
        return self._cached_characters

    def asset(self, name: str, layer: str = None) -> Asset:
        search_list = self.renderables(layer) if layer else self._assets
        return next((a for a in search_list if a.name == name), None)

    def assets(self, layer=None) -> List[Asset]:
        if layer is None:
            return self._assets
        return self._cached_layers.get(layer, [])

    def weights(self, layer=None) -> List[Asset]:
        if layer is None:
            return [ asset for asset in self._assets if asset.properties.mass >= 0 ]
        return self._cached_weights.get(layer, [])

    def obstacles(self, layer=None) -> List[Asset]:
        if layer is None:
            return []
        chests = self._cached_instances.get(layer, {}).get(AssetInstances.CHESTS.value, [])
        signs = self._cached_instances.get(layer, {}).get(AssetInstances.SIGNS.value, [])
        crates = self._cached_instances.get(layer, {}).get(AssetInstances.CRATES.value, [])
        gates = self._cached_instances.get(layer, {}).get(AssetInstances.GATES.value, [])
        struts = self._cached_instances.get(layer, {}).get(AssetInstances.STRUTS.value, [])
        return crates + gates + struts + signs + chests

    def layers(self) -> List[str]:
        return list(self._cached_categories.keys())

    def categories(self, category, layer = None) -> List[Asset]:
        if layer is not None:
            return self._cached_categories.get(layer, {}).get(category, [])
        return self._all_categories.get(category, [])

    def instances(self, instance, layer = None) -> List[Asset]:
        if layer is not None:
            return self._cached_instances.get(layer, {}).get(instance, [])
        return self._all_instances.get(instance, [])

    def renderables(self, layer=None) -> List[Asset]:
        if layer is None:
            return [ asset for asset in self._assets if asset.category != AssetCategories.TILES.value ]
        return self._cached_renderables.get(layer, [])

    def get_shorelines(self, layer: Optional[str] = None) -> List[Asset]:
        """
        Retrieves active procedural shoreline assets for a specific layer or across all layers.
        """
        if layer is not None:
            return self.shorelines.get(layer, [])
        all_shores: List[Asset] = []
        for l_shores in self.shorelines.values():
            all_shores.extend(l_shores)
        return all_shores

    def size(self, layer=None) -> List[Dimensions]:
        layers = [layer] if layer is not None else self.layers()
        layer_sizes = []

        for l in layers:
            layer_assets = self.assets(l)
            max_w = 0
            max_l = 0

            for asset in layer_assets:
                if asset.category == AssetCategories.TILES.value:
                    ext_w = int(asset.state.position.x) + (asset.state.multiple.nx * asset.properties.dimensions.w)
                    ext_l = int(asset.state.position.y) + (asset.state.multiple.ny * asset.properties.dimensions.l)
                elif asset.dimensions:
                    ext_w = int(asset.state.position.x) + asset.dimensions.w
                    ext_l = int(asset.state.position.y) + asset.dimensions.l
                else:
                    continue

                if ext_w > max_w:
                    max_w = ext_w
                if ext_l > max_l:
                    max_l = ext_l

            layer_sizes.append(Dimensions(w=max_w, l=max_l))

        return layer_sizes

    # ------------------------------------------------ MUTATORS

    def relayer(self, asset: Asset, new_layer: str) -> None:
        old_layer = asset.state.layer
        if old_layer == new_layer:
            return
            
        logger.debug(f"Relayering asset '{asset.taxonomy.name}' from layer '{old_layer}' -> '{new_layer}'.")
        
        cat = asset.category
        inst = asset.instance

        if old_layer in self._cached_categories and cat in self._cached_categories[old_layer]:
            if asset in self._cached_categories[old_layer][cat]:
                self._cached_categories[old_layer][cat].remove(asset)
                
        if old_layer in self._cached_instances and inst in self._cached_instances[old_layer]:
            if asset in self._cached_instances[old_layer][inst]:
                self._cached_instances[old_layer][inst].remove(asset)

        if old_layer in self._cached_layers:
            if asset in self._cached_layers[old_layer]:
                self._cached_layers[old_layer].remove(asset)

        if old_layer in self._cached_renderables:
            if asset in self._cached_renderables[old_layer]:
                self._cached_renderables[old_layer].remove(asset)

        if old_layer in self._cached_weights:
            if asset in self._cached_weights[old_layer]:
                self._cached_weights[old_layer].remove(asset)

        if old_layer in self.shorelines and asset in self.shorelines[old_layer]:
            self.shorelines[old_layer].remove(asset)

        asset.state.layer = new_layer

        if new_layer not in self._cached_categories:
            self._init_cache(new_layer)
            
        if cat not in self._cached_categories[new_layer]:
            self._cached_categories[new_layer][cat] = []
        self._cached_categories[new_layer][cat].append(asset)
        
        if inst not in self._cached_instances[new_layer]:
            self._cached_instances[new_layer][inst] = []
        self._cached_instances[new_layer][inst].append(asset)

        if new_layer not in self._cached_layers:
            self._cached_layers[new_layer] = []
        self._cached_layers[new_layer].append(asset)
        
        if new_layer not in self._cached_renderables:
            self._cached_renderables[new_layer] = []
        self._cached_renderables[new_layer].append(asset)

        if new_layer not in self._cached_weights:
            self._cached_weights[new_layer] = []
            
        if asset.properties.mass >= 0:
            self._cached_weights[new_layer].append(asset)

        if inst == AssetInstances.SHORELINES.value:
            if new_layer not in self.shorelines:
                self.shorelines[new_layer] = []
            self.shorelines[new_layer].append(asset)

    def add(self, additions: List[Asset]) -> None:
        for asset in additions:
            layer = asset.state.layer

            self._assets.append(asset)
            self._all_categories.setdefault(asset.category, []).append(asset)
            self._all_instances.setdefault(asset.instance, []).append(asset)
            
            if layer not in self._cached_categories:
                self._init_cache(layer)
                
            self._cached_categories[layer].setdefault(asset.category, []).append(asset)
            self._cached_instances[layer].setdefault(asset.instance, []).append(asset)
            self._cached_layers[layer].append(asset)

            logger.info(
                f"Appending Asset(id={asset.id}, "
                f"name={asset.name}, "
                f"category={asset.category}, "
                f"instance={asset.instance})"
            )

            if asset.category != AssetCategories.TILES.value:
                self._cached_renderables[layer].append(asset)
                if asset.category != AssetCategories.CURSORS and (
                    asset.properties.mass >= 0
                ):
                    self._cached_weights[layer].append(asset)
                
            if asset.instance in (
                AssetInstances.SPRITES.value, 
                AssetInstances.PLAYERS.value
            ):
                if asset.name:
                    self._cached_characters[asset.name] = asset.state

            if asset.instance == AssetInstances.SHORELINES.value:
                self.shorelines[layer].append(asset)

            if asset.category == AssetCategories.TILES.value:
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
                        if asset.instance not in self._cached_tilemap[layer]:
                            self._cached_tilemap[layer][asset.instance] = {}
                        self._cached_tilemap[layer][asset.instance][(cx, cy)] = asset

    def remove(self, removals: List[Asset]) -> None:
        for asset in removals:
            layer = asset.state.layer
            cat = asset.category
            inst = asset.instance

            if asset in self._assets:
                self._assets.remove(asset)

            if layer in self._cached_categories and cat in self._cached_categories[layer]:
                if asset in self._cached_categories[layer][cat]:
                    self._cached_categories[layer][cat].remove(asset)
            
            if layer in self._cached_instances and inst in self._cached_instances[layer]:
                if asset in self._cached_instances[layer][inst]:
                    self._cached_instances[layer][inst].remove(asset)

            if layer in self._cached_layers and asset in self._cached_layers[layer]:
                self._cached_layers[layer].remove(asset)

            if layer in self._cached_renderables and asset in self._cached_renderables[layer]:
                self._cached_renderables[layer].remove(asset)

            if layer in self._cached_weights and asset in self._cached_weights[layer]:
                self._cached_weights[layer].remove(asset)

            if cat in self._all_categories and asset in self._all_categories[cat]:
                self._all_categories[cat].remove(asset)
                
            if inst in self._all_instances and asset in self._all_instances[inst]:
                self._all_instances[inst].remove(asset)
                
            if inst in (
                AssetInstances.SPRITES.value, 
                AssetInstances.PLAYERS.value
            ):
                if asset.name and asset.name in self._cached_characters:
                    del self._cached_characters[asset.name]

            if layer in self.shorelines and asset in self.shorelines[layer]:
                self.shorelines[layer].remove(asset)

    def clear(self) -> None:
        self._assets.clear()
        self._init_cache()
        self.menus.clear()
        self.overlays.clear()
        self.shorelines.clear()

    # ------------------------------------------------ EXPORTERS

    def serialize(self, slot: str) -> None:
        dump: dict[str, dict[str, list[dict[str, Any]]]] = {}

        for asset in self._assets:
            if asset.category == AssetCategories.WIDGETS.value:
                continue

            if asset.category == AssetCategories.EFFECTS.value:
                lifecycle = getattr(asset.properties, "lifecycle", None)
                if lifecycle and lifecycle.type == Lifecycles.TEMPORARY.value and not lifecycle.persist:
                    continue

            if asset.category == AssetCategories.SHEETS.value and asset.instance not in (
                AssetInstances.SPRITES.value,
                AssetInstances.PLAYERS.value,
                AssetInstances.PIXIES.value,
            ):
                continue

            cat = str(asset.category)
            inst = str(asset.instance)

            if cat not in dump:
                dump[cat] = {}
            if inst not in dump[cat]:
                dump[cat][inst] = []

            dump[cat][inst].append(asdict(asset.state))

        Loader.save_state(slot, dump)