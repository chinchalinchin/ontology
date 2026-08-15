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
    Equipment,
    Groups
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

    The Orchestrator and the Loader are the only pure Python classes in the application that interact with the game data as dictionaries. The Loader accesses the data in the host environment and validates it with Pydantic models. The Orchestrator pipes the Pydantic-validated dictionaries retrieved from the Loader data dump into the in-game Python objects.

    The Registry, a Cython interface, uses dictionary representations of the data for speed as well.
    """
    # Data
    properties: Dict = {}
    state: Dict = {}
    configurations: Dict = {}
    # Game
    registry: Registry
    board: Board
    screens: Dict[str, Screen]
    engine: Engine

    def __init__(self, state: str):
        logger.info(f"Initializing Orchestrator for target state: {state} ...")
        self.properties = Loader.load_properties()
        self.configurations = Loader.load_configurations()
        self.state = Loader.load_state(state)

    def instance_actions(self, category, instance, id) -> dict:
        action_set_key = self.properties[category][instance][id]["actions"]
        try:
            return next(
                action["data"] for action in self.configurations["actions"]
                if action["id"] == action_set_key
            )
        except StopIteration:
            logger.warning(f"No actions exist for {action_set_key}")

    def instance_properties(self, category, instance, snapshot):
        """
        Returns Asset Properties based on their Taxonomy.
        """
        # Lookup properties using the 'id' before modifying the dictionary
        if category == AssetCategories.TILES:
            return self.properties[category][instance]

        if category == AssetCategories.SHEETS and instance != AssetInstances.PLAYERS:
            props = self.properties[category][instance][snapshot["id"]].copy()
            props["actions"] = self.instance_actions(category, instance, snapshot["id"])
            return props

        if category == AssetCategories.SHEETS and instance == AssetInstances.PLAYERS:
            props = self.properties[category][AssetInstances.SPRITES][snapshot["id"]].copy()
            props["actions"] = self.instance_actions(category, AssetInstances.SPRITES, snapshot["id"])
            return props

        return self.properties[category][instance][snapshot["id"]] 

    def migrate(self) -> Board:
        """
        # migrate

        Transfer the Pydantic DTOs to Python POPOs for the game engine and load them into the Board.
        """
        logger.info("Migrating validated data to engine models...")
        assets = []

        # 1. Migrate Configuration
        configurations = Factory.group(Groups.CONFIGURATIONS, self.configurations)

        # 2. Migrate Assets without State
        raw_equipment = { }
        for equip_instance_key in Equipment:
            raw_equipment[equip_instance_key] = { }

            for equip_instance_id, equip_instance in \
                self.properties[AssetCategories.SHEETS][equip_instance_key].items():

                raw_equipment[equip_instance_key][equip_instance_id] = Factory.properties(
                    AssetCategories.SHEETS,
                    equip_instance
                )

        equipment = Factory.group(Groups.EQUIPMENT, raw_equipment)

        # 3. Migrate Assets with State        
        assets = []
        for category_key, category_data in self.state.items():
            for instance_key, instance_list in category_data.items():
                for instance in instance_list:

                    recipe = self.configurations["recipes"][category_key][instance_key]
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
        device_mapping = self.configurations.get("mappings", {}).get(device, {})
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
