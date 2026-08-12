"""
# Ontology: Orchestration
"""
# Standard Libraries
import time
import logging
from typing import (
    Dict, 
    Tuple
)

# Application Libraries
from app.assets.base import Asset
from app.config.loader import Loader
from app.config.enums import (
    AssetCategories, 
    AssetInstances,
    Devices
)
from app.game.board import Board
from app.game.screen import Screen
from app.hooks.factory import Factory

# Cython Libraries
from libs.core.models import Dimensions
import libs.graphics.render as render
from libs.graphics.registry import Registry

logger = logging.getLogger(__name__)

class Orchestrator:
    """
    """
    # Configuration
    properties: Dict = {}
    recipes: Dict = {}
    state: Dict = {}
    devices: Dict = {}
    equipment: Dict = {}

    # Game
    registry: Registry
    board: Board
    screens: Dict[str, Screen]

    def __init__(self, state: str):
        logger.info(f"Initializing Orchestrator for target state: {state} ...")
        self.properties = Loader.load_properties()
        self.recipes = Loader.load_recipes()
        self.devices = Loader.load_devices()
        self.equipment = Loader.load_equipment()
        self.state = Loader.load_state(state)

    def instance_properties(self, category, instance, snapshot):
        """
        Returns Asset Properties based on their Taxonomy.
        """
        # Lookup properties using the 'id' before modifying the dictionary
        if category == AssetCategories.TILES:
            return self.properties[category][instance]

        if category == AssetCategories.SHEETS and instance != AssetInstances.PLAYERS:
            props = self.properties[category][instance]["personas"][snapshot["id"]].copy()
            props["actions"] = self.properties[category][instance]["actions"]
            return props

        if category == AssetCategories.SHEETS and instance == AssetInstances.PLAYERS:
            props = self.properties[category][AssetInstances.SPRITES]["personas"][snapshot["id"]].copy()
            props["actions"] = self.properties[category][AssetInstances.SPRITES]["actions"]
            return props

        return self.properties[category][instance][snapshot["id"]] 

    def migrate(self) -> Board:
        """
        # migrate

        Transfer the Pydantic DTOs to Python POPOs for the game engine and load them into the Board.
        """
        logger.info("Migrating validated states to engine Application Objects...")
        assets = []

        equipment = Factory.equipment(self.equipment)
        intentions = Factory.intentions(self.intentions)

        for category_key, instance_data in self.state.items():
            for instance_key, instance_list in instance_data.items():
                for instance in instance_list:

                    recipe = self.recipes[category_key][instance_key]
                    instance_props = self.instance_properties(category_key, instance_key, instance)

                    # Pop the taxonomy keys to strip them from the state snapshot
                    asset_id = instance.pop("id")
                    asset_name = instance.pop("name")

                    assets.append(Asset(
                        taxonomy   = Factory.taxonomy(category_key, instance_key, asset_id, asset_name),
                        properties = Factory.properties(category_key, instance_props),
                        state      = Factory.state(recipe["state"], instance),
                        frame      = Factory.frame(recipe["frame"]),
                        animation  = Factory.animation(recipe["animation"])
                    ))
                    
        logger.info(f"Successfully migrated {len(assets)} assets.")
        
        return Board(assets, equipment, intentions)
    
    def orchestrate(self, screensize: Dimensions, device: Devices) -> Tuple[Board, Registry, Dict[str, Screen]]:
        """
        # Ontology: Orchestrate

        Initialize and return game components.
        """
        logger.info("Initializing SDL...")
        render.init(screensize.w, screensize.l)

        logger.info("Initializing Board...")
        self.board = self.migrate()

        logger.info("Initializing Device...")
        device_mapping = self.devices.get("mappings", {}).get(device, {})
        device_instance = Factory.device(device, device_mapping)
        self.board.set_device(device_instance)

        logger.info("Initializing Registry..")
        self.registry = Registry(self.properties, self.recipes)
        
        logger.info("Initializing Screens...")
        self.screens = {
            layer: Screen(
                screensize, 
                self.board.size(layer)[0],
                self.board.categories(AssetCategories.TILES, layer),
                self.registry
            )
            for layer in self.board.layers()
        } 
        
        return self.board, self.registry, self.screens