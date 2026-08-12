"""
# Ontology: Board

Package for game Board. The Board holds and mutates the state of the game for the engine loop.
"""

# Standard Libraries 
import logging
from typing import List, Dict

# Application Libraries
from app.assets.base import Asset
from app.config.enums import (
    AssetCategories,
    AssetInstances
)
from app.game.mechanics import (
    Mechanic, 
    AnimationMechanics, 
    CollisionMechanics, 
    ProjectileMechanics, 
    SwitchMechanics, 
    IntentionMechanics,
    RemoveMechanics
)
from app.input.player import Player

# Cython Libraries
from libs.core import Dimensions

logger = logging.getLogger(__name__)

class Board:
    """
    """
    mechanics: List[Mechanic]

    loaded: bool
    paused: bool

    _assets: List[Asset]
    _cached_categories: Dict[str, Dict[str, List[Asset]]]
    _cached_instances: Dict[str, Dict[str, List[Asset]]]
    _cached_layers: Dict[str, List[Asset]]
    _all_categories: Dict[str, List[Asset]]
    _all_instances: Dict[str, List[Asset]]

    def __init__(self, 
        assets: List[Asset], 
    ):
        logger.info(f"Initializing Board with {len(assets)} incoming assets.")
        
        self.loaded = False
        self.paused = False
        self.mechanics = [ 
            AnimationMechanics(),
            IntentionMechanics(),
            CollisionMechanics(),
            ProjectileMechanics(),
            SwitchMechanics(),
            RemoveMechanics()
        ]
        self._assets = assets
        self._cache()
        
        self.loaded = True
        logger.info("Board completely hydrated and initialized.")

    def _cache(self):
        """
        Cache Assets queries by layer to prevent excessive list generations.

        Anytime an Asset changes layer, the `relayer()` method must be called, to invalidate the Asset caches.
        """
        logger.debug("Building initial board spatial caching dictionaries by layer/category/instance.")
        self._cached_categories = {}
        self._cached_instances = {}
        self._cached_layers = {}
        self._all_categories = {}
        self._all_instances = {}

        for asset in self._assets:
            layer = asset.state.layer
            cat = asset.category
            inst = asset.instance

            # Initialize layer dictionaries if not present
            if layer not in self._cached_categories:
                self._cached_categories[layer] = {}
                self._cached_instances[layer] = {}
                self._cached_layers[layer] = []
            
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

            # Cache globally by category
            if cat not in self._all_categories:
                self._all_categories[cat] = []
            self._all_categories[cat].append(asset)

            # Cache globally by instance
            if inst not in self._all_instances:
                self._all_instances[inst] = []
            self._all_instances[inst].append(asset)

    def player(self, slot = 0) -> Asset:
        """
        Returns the player at the indicated slot. Defaults 0.
        """
        if slot < len(self._all_instances[AssetInstances.PLAYERS]):
            return self._all_instances[AssetInstances.PLAYERS][slot]
        return self._all_instances[AssetInstances.PLAYERS][0]

    def assets(self, layer=None) -> List[Asset]:
        """
        Returns a list of Assets. If `layer` is specified, list will be filtered by Layer.
        """
        if layer is None:
            return self._assets
        return self._cached_layers[layer]
    
    def layers(self) -> List[str]:
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
        
    def relayer(self, asset: Asset, new_layer: str) -> None:
        """
        Safely moves an asset between cached layer lists.
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

        # 2. Update state
        asset.state.layer = new_layer

        # 3. Append to new cached lists
        if new_layer not in self._cached_categories:
            self._cached_categories[new_layer] = {}
            self._cached_instances[new_layer] = {}
            self._cached_layers[new_layer] = []
            
        if cat not in self._cached_categories[new_layer]:
            self._cached_categories[new_layer][cat] = []
        self._cached_categories[new_layer][cat].append(asset)
        
        if inst not in self._cached_instances[new_layer]:
            self._cached_instances[new_layer][inst] = []
        self._cached_instances[new_layer][inst].append(asset)

        if new_layer not in self._cached_layers:
            self._cached_layers[new_layer] = []
        self._cached_layers[new_layer].append(asset)
        
    def menu(self) -> None:
        """
        """
        # TODO: implement
        pass 

    def play(self, delta: float) -> None:
        """
        """
        # NOTE: Intentionally omitting logging here to prevent I/O bottlenecks in the core game loop.
        
        # ------------------------- MECHANIC HANDLING
        for this in self.mechanics:
            this.update(self, delta)

        # ------------------------- PLAYER HANDLING
        self.player
        # TODO: player logic
        # -------------------------

    def size(self, layer=None) -> List[Dimensions]:
        """
        Calculates the size of Board by layer. 

        If no layer is specified, method will return a list of all layer sizes as a List.
        """

        layers = [ layer ] if layer is not None else self.layers()
        layer_sizes = []

        for layer in layers:
            tiles = self.categories(AssetCategories.TILES, layer)
            w = max([ tile.state.position.x + tile.state.multiple.nx * tile.properties.dimensions.w 
                    for tile in tiles ], default = 0)
            l = max([tile.state.position.y + tile.state.multiple.ny * tile.properties.dimensions.l
                    for tile in tiles], default = 0)
            layer_sizes.append(Dimensions(w=w, l=l))
        return layer_sizes