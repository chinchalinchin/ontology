"""
# Ontology: app.hooks.orchestrator

Package for managing dependency injection.
"""
# Standard Libraries
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
    Devices,
    EquipmentGroup,
    Configurations
)
from app.game.board import Board
from app.game.engine import Engine
from app.game.screen import Screen
from app.hooks.factory import Factory

# Cython Libraries
from libs.core.models import Dimensions
import libs.graphics.render as render
from libs.graphics.registry import Registry

logger = logging.getLogger(__name__)

class Orchestrator:
    """
    ## Orchestrator
    """
    # Data
    properties: Dict = {}
    state: Dict = {}
    configuration: Dict = {}
    # Game
    registry: Registry
    board: Board
    screens: Dict[str, Screen]
    engine: Engine

    def __init__(self, state: str):
        logger.info(f"Initializing Orchestrator for target state: {state} ...")
        self.properties = Loader.load_properties()
        self.configuration = Loader.load_configurations()
        self.state = Loader.load_state(state)

    def instance_properties(self, category, instance, snapshot):
        """
        Returns Asset Properties based on their Taxonomy.
        """
        # Lookup properties using the 'id' before modifying the dictionary
        if category == AssetCategories.TILES:
            return self.properties[category][instance]

        if category == AssetCategories.SHEETS and instance != AssetInstances.PLAYERS:
            props = self.properties[category][instance][snapshot["id"]].copy()
            action_set = self.properties[category][instance]["actions"]
            # TODO: Query ActionConfiguration
            props["actions"]
            return props

        if category == AssetCategories.SHEETS and instance == AssetInstances.PLAYERS:
            props = self.properties[category][AssetInstances.SPRITES][snapshot["id"]].copy()
            action_set = self.properties[category][AssetInstances.SPRITES]["actions"]
            # TODO: Query ActionConfiguration
            props["actions"]
            return props

        return self.properties[category][instance][snapshot["id"]] 

    def migrate(self) -> Board:
        """
        # migrate

        Transfer the Pydantic DTOs to Python POPOs for the game engine and load them into the Board.
        """
        logger.info("Migrating validated states and configurations to engine data structures...")
        assets = []
        configurations = { }
        equipment = { }

        # 1. Migrate Configurations
        for config_key, config_data in self.configuration.items():
            configurations[config_key] = Factory.configuration(config_key, config_data)

        # 2. Migrate Assets without State
        for equip_key in EquipmentGroup:
            equipment[equip_key] = Factory.properties(
                equip_key,
                self.properties[AssetCategories.SHEETS][equip_key]
            )
        # 3. Migrate Assets with State
        for category_key, category_data in self.state.items():
            for instance_key, instance_list in category_data.items():
                for instance in instance_list:

                    recipe = self.configuration["recipes"][category_key][instance_key]
                    instance_props = self.instance_properties(category_key, instance_key, instance)

                    # Pop the taxonomy keys to strip them from the state snapshot
                    asset_id = instance.pop("id")
                    asset_name = instance.pop("name")

                    assets.append(Asset(
                        taxonomy   = Factory.taxonomy(asset_id, asset_name, category_key, instance_key),
                        properties = Factory.properties(category_key, instance_props),
                        state      = Factory.state(recipe["state"], instance),
                        frame      = Factory.frame(recipe["frame"]),
                        animation  = Factory.animation(recipe["animation"])
                    ))
                    
        logger.info(f"Successfully migrated {len(assets)} assets.")
        
        return Board(assets, configurations, equipment)
    
    def init(self, screensize: Dimensions, device: Devices) -> Tuple[Board, Registry, Dict[str, Screen]]:
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
        self.registry = Registry(self.properties, self.configurations["recipes"])
        
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

    def ignite(self, screensize: Dimensions, device: Devices) -> Engine:
        """
        """
        self.orchestrate(screensize, device)
        self.mechanics = { "TODO": "INIT" }
        self.engine = Engine(self.board, self.screens, self.mechanics)

        return self.engine
