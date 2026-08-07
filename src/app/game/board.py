"""
# Ontology: Board

Package for game Board. The Board holds and mutates the state of the game for the engine loop.
"""

# Standard Libraries 
from typing import List, Dict

# Application Libraries
from app.assets.base import Asset
from app.game.mechanics import (
    Mechanic, AnimationMechanics, CollisionMechanics, 
    ProjectileMechanics, SwitchMechanics, IntentionMechanics
)
from app.player import Player

class Board:
    """
    """
    player: Player
    mechanics: List[Mechanic]
    assets: List[Asset]
    
    _cached_categories: Dict[str, Dict[str, List[Asset]]]
    _cached_instances: Dict[str, Dict[str, List[Asset]]]
    _all_categories: Dict[str, List[Asset]]
    _all_instances: Dict[str, List[Asset]]

    def __init__(self, 
        assets: List[Asset]
    ):
        self.assets = assets
        self.mechanics = [ 
            AnimationMechanics(),
            IntentionMechanics(),
            CollisionMechanics(),
            ProjectileMechanics(),
            SwitchMechanics(),
        ]
        
        self._cached_categories = {}
        self._cached_instances = {}
        self._all_categories = {}
        self._all_instances = {}

        for asset in self.assets:
            layer = asset.state.layer
            cat = asset.state.category
            inst = asset.state.instance

            # Initialize layer dictionaries if not present
            if layer not in self._cached_categories:
                self._cached_categories[layer] = {}
                self._cached_instances[layer] = {}
            
            # Cache by layer and category
            if cat not in self._cached_categories[layer]:
                self._cached_categories[layer][cat] = []
            self._cached_categories[layer][cat].append(asset)
            
            # Cache by layer and instance
            if inst not in self._cached_instances[layer]:
                self._cached_instances[layer][inst] = []
            self._cached_instances[layer][inst].append(asset)

            # Cache globally by category
            if cat not in self._all_categories:
                self._all_categories[cat] = []
            self._all_categories[cat].append(asset)

            # Cache globally by instance
            if inst not in self._all_instances:
                self._all_instances[inst] = []
            self._all_instances[inst].append(asset)

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
            
        cat = asset.state.category
        inst = asset.state.instance

        # 1. Remove from old cached lists
        if old_layer in self._cached_categories and cat in self._cached_categories[old_layer]:
            if asset in self._cached_categories[old_layer][cat]:
                self._cached_categories[old_layer][cat].remove(asset)
                
        if old_layer in self._cached_instances and inst in self._cached_instances[old_layer]:
            if asset in self._cached_instances[old_layer][inst]:
                self._cached_instances[old_layer][inst].remove(asset)

        # 2. Update state
        asset.state.layer = new_layer

        # 3. Append to new cached lists
        if new_layer not in self._cached_categories:
            self._cached_categories[new_layer] = {}
            self._cached_instances[new_layer] = {}
            
        if cat not in self._cached_categories[new_layer]:
            self._cached_categories[new_layer][cat] = []
        self._cached_categories[new_layer][cat].append(asset)
        
        if inst not in self._cached_instances[new_layer]:
            self._cached_instances[new_layer][inst] = []
        self._cached_instances[new_layer][inst].append(asset)

    def menu(self) -> None:
        """
        """
        # TODO: implement
        pass 

    def play(self, delta: float) -> None:
        """
        """
        # ------------------------- MECHANIC HANDLING
        for this in self.mechanics:
            this.update(self, delta)

        # ------------------------- PLAYER HANDLING
        self.player
        # TODO: player logic
        # -------------------------