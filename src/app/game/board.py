"""
# Ontology: app.game.board

Package for game Board.
"""
# Standard Libraries 
import logging
from typing import (
    List, 
    Dict, 
    Tuple,
    Any
)
from dataclasses import asdict

# External Libraries
import yaml

# Application Libraries
from app.assets.base import Asset
from app.config.enums import (
    AssetCategories,
    AssetInstances
)
import app.config.settings as settings
from app.game.devices import Device
from app.game.menus.core import Menu
from app.services.generators.cradle import Cradle
from app.models.config import ConfigurationSchema
from app.models.groups import EquipmentGroup

# Cython Libraries
from libs.core.models import Dimensions, Position

logger = logging.getLogger(__name__)

class Board:
    """
    ## Board

    Central database for the game Engine. Holds all Asset state and configuration, and provides queryable interfaces for Mechanics to retrieve pertinent game data.
    """
    # ------- Public Fields
    # Flags
    loaded: bool
    paused: bool
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
    _cached_characters: Dict[str, Any] # Cross-layer lookup for O(1) ISL targeting
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
        self.menus = []
        self.overlays = []
        self.configurations = configurations
        self.equipment = equipment
        self._assets = assets
        self._catalogue()
        self._cache()
        # Ensure loaded remains False until fully hydrated by the Migrator
        logger.info("Board completely hydrated and initialized.")

    # ---------------------------------------------------------
    # ----------------------------------------- PRIVATE METHODS

    def _catalogue(self):
        """
        """
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


    def _init_cache(self, layer = None) -> None:
        if layer is None:
            self._cached_categories = {}
            self._cached_instances = {}
            self._cached_layers = {}
            self._cached_renderables = {}
            self._cached_weights = {}
            self._cached_tilemap = {}
            self._cached_characters = {}
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
        return


    def _cache(self):
        """
        Cache Assets queries by layer to prevent excessive list generations.
        """
        logger.debug("Building initial board spatial caching dictionaries by layer/category/instance.")
        self._init_cache()

        for asset in self._assets:
            layer = asset.state.layer
            cat = asset.category
            inst = asset.instance

            # Initialize layer dictionaries if not present
            if layer not in self._cached_categories:
                self._init_cache(layer)

            # Cache by layer and category
            if cat not in self._cached_categories[layer]:
                self._cached_categories[layer][cat] = []
            self._cached_categories[layer][cat].append(asset)
            
            # Cache by layer and instance
            if inst not in self._cached_instances[layer]:
                self._cached_instances[layer][inst] = []
            self._cached_instances[layer][inst].append(asset)

            # Cache by layer only
            self._cached_layers[layer].append(asset)
            
            # Cache exclusively dynamic assets for the inner draw loop
            if cat != AssetCategories.TILES.value:
                self._cached_renderables[layer].append(asset)

            # Cached Assets with Weight
            if hasattr(asset.properties, 'mass') and asset.properties.mass >= 0:
                self._cached_weights[layer].append(asset)
                
            # Cross-layer Character lookup for Intentional Scripting Language
            if cat == AssetCategories.SHEETS.value and inst in (
                AssetInstances.SPRITES.value, 
                AssetInstances.PLAYERS.value
            ):
                if asset.name:
                    self._cached_characters[asset.name] = asset.state

            # Cache TileMap for O(1) friction/environment lookups
            if cat == AssetCategories.TILES.value:
                w = asset.properties.dimensions.w
                l = asset.properties.dimensions.l
                
                start_x = int(asset.state.position.x)
                start_y = int(asset.state.position.y)
                end_x = start_x + (asset.state.multiple.nx * w)
                end_y = start_y + (asset.state.multiple.ny * l)

                # Hash the tile into every HASH_SIZE cell it intersects
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

    # ---------------------------------------------------------
    # ------------------------------------------ PUBLIC METHODS

    # ------------------------------------------------ SETTERS 

    def set_device(self, device: Device) -> None:
        """
        Sets the Device on the board for polling.
        """
        self.device = device


    def set_cradle(self, cradle: Cradle) -> None:
        """
        """
        self.cradle = cradle

    def set_overlays(self, overlays: List[Menu]) -> None:
        """
        """
        self.overlays = overlays

    # ------------------------------------------------ GETTERS

    def player(self, slot = 0) -> Asset:
        """
        Returns the player at the indicated slot safely even if the board is empty. Defaults to 0.
        """
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
        """
        Returns the Tile at the specified coordinate using O(1) grid-index lookup.
        """
        cx = int(position.x) // settings.TILE_HASH_SIZE
        cy = int(position.y) // settings.TILE_HASH_SIZE
        return self._cached_tilemap.get(layer, {}).get(instance, {}).get((cx, cy))

    def character(self, name: str) -> Any:
        """
        O(1) retrieval of Sprite or Player state by name.
        """
        return self._cached_characters.get(name)

    def characters(self) -> Dict[str, Any]:
        """
        Returns the cross-layer dictionary of all active Sprite and Player states.
        """
        return self._cached_characters

    def asset(self, name: str, layer: str = None) -> Asset:
        """
        Retrieves a general Asset by its unique name. 
        """
        search_list = self.renderables(layer) if layer else self._assets
        return next((a for a in search_list if a.name == name), None)
    
    def assets(self, layer=None) -> List[Asset]:
        """
        Returns a list of Assets. If `layer` is specified, list will be filtered by Layer.
        """
        if layer is None:
            return self._assets
        return self._cached_layers[layer]


    def weights(self, layer=None) -> List[Asset]:
        """
        Returns a list of Assets that have mass. If `layer` is specified, list will be filtered by Layer.
        """
        if layer is None:
            return [
                asset 
                for asset in self._assets 
                if hasattr(asset.properties, 'mass') and asset.properties.mass >= 0
            ]
        return self._cached_weights.get(layer, [])


    def layers(self) -> List[str]:
        """
        Returns a list of Layers.
        """
        return list(self._cached_categories.keys())


    def categories(self, category, layer = None) -> List[Asset]:
        """
        Returns a reference to the cached list of categorized Assets. O(1) fetch.
        """
        if layer is not None:
            return self._cached_categories.get(layer, {}).get(category, [])
        return self._all_categories.get(category, [])


    def instances(self, instance, layer = None) -> List[Asset]:
        """
        Returns a reference to the cached list of instanced Assets. O(1) fetch.
        """
        if layer is not None:
            return self._cached_instances.get(layer, {}).get(instance, [])
        return self._all_instances.get(instance, [])

        
    def renderables(self, layer=None) -> List[Asset]:
        """
        Returns a cached list of non-tile dynamic assets for rendering, saving frame iteration time.
        """
        if layer is None:
            return [
                asset 
                for asset in self._assets 
                if asset.category != AssetCategories.TILES.value
            ]
        return self._cached_renderables.get(layer, [])


    def size(self, layer=None) -> List[Dimensions]:
        """
        Calculates the size of Board by layer. If no layer is specified, method will return a list of all layer sizes as a List.
        """

        layers = [ layer ] if layer is not None else self.layers()
        layer_sizes = []

        for layer in layers:
            tiles = self.categories(AssetCategories.TILES.value, layer)
            w = max([ tile.state.position.x + tile.state.multiple.nx * tile.properties.dimensions.w 
                    for tile in tiles ], default = 0)
            l = max([tile.state.position.y + tile.state.multiple.ny * tile.properties.dimensions.l
                    for tile in tiles], default = 0)
            layer_sizes.append(Dimensions(w=w, l=l))
        return layer_sizes

    # ------------------------------------------------ MUTATORS

    def relayer(self, asset: Asset, new_layer: str) -> None:
        """
        Safely moves an asset between cached layer lists.

        !!! warning
            *Must* be called by DoorMechanics to ensure Assets and the Cache stay in sync.
        """
        old_layer = asset.state.layer
        if old_layer == new_layer:
            return
            
        logger.debug(f"Relayering asset '{asset.taxonomy.name}' from layer '{old_layer}' -> '{new_layer}'.")
        
        cat = asset.category
        inst = asset.instance

        # 1. Remove from old cached lists
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

        # 2. Update state
        asset.state.layer = new_layer

        # 3. Append to new cached lists
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
            
        if hasattr(asset.properties, 'mass') and asset.properties.mass >= 0:
            self._cached_weights[new_layer].append(asset)


    def add(self, additions: List[Asset]) -> None:
        """
        Add Assets to the Board
        """

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
            
            if asset.category != AssetCategories.TILES.value:
                self._cached_renderables[layer].append(asset)

            if hasattr(asset.properties, 'mass') and asset.properties.mass >= 0:
                self._cached_weights[layer].append(asset)
                
            if asset.category == AssetCategories.SHEETS.value and asset.instance in (AssetInstances.SPRITES.value, AssetInstances.PLAYERS.value):
                if asset.name:
                    self._cached_characters[asset.name] = asset.state


    def remove(self, removals: List[Asset]) -> None:
        """
        Removes Assets from the board.
        """
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
                
            if cat == AssetCategories.SHEETS.value and inst in (AssetInstances.SPRITES.value, AssetInstances.PLAYERS.value):
                if asset.name and asset.name in self._cached_characters:
                    del self._cached_characters[asset.name]

        def serialize(self, slot: str) -> None:
            """
            Dumps runtime Board state back to YAML for saves.
            """
            dump = {}
            for asset in self._assets:
                # Exclude highly transient or completely stateless system assets
                if asset.category in (
                    AssetCategories.WIDGETS.value, 
                    AssetCategories.TILES.value, 
                    AssetCategories.EFFECTS.value
                ):
                    continue
                    
                # Exclude stateless Equipment wrappers (they bind directly to Sprite Inventories)
                if asset.category == AssetCategories.SHEETS.value and asset.instance not in (
                    AssetInstances.SPRITES.value, 
                    AssetInstances.PLAYERS.value, 
                    AssetInstances.PIXIES.value
                ):
                    continue
                    
                cat = asset.category
                inst = asset.instance
                
                if cat not in dump:
                    dump[cat] = {}
                if inst not in dump[cat]:
                    dump[cat][inst] = []
                    
                dump[cat][inst].append(asdict(asset.state))

            # TODO: file access should be handled through app.config.loader
            out_dir = settings.SAVE_DIR
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{slot}.yaml"
            
            with open(out_path, 'w') as f:
                yaml.dump(dump, f, default_flow_style=False)