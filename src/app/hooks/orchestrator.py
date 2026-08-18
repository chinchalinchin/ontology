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
    Groups,
    Mechanics
)
from app.game.board import Board
from app.game.engine import Engine
from app.game.screen import Screen
from app.hooks.factory import Factory
from app.models.groups import SpawnableGroup

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


    def instance_actions(self, category: str, instance: str, id: str) -> dict:
        action_set_key = self.properties[category][instance][id].get("actions")
        
        if isinstance(action_set_key, dict):
            return action_set_key
            
        try:
            return next(
                action["data"] for action 
                in self.configurations.get("actions", [])
                if action["id"] == action_set_key
            )
        except StopIteration:
            logger.warning(f"No actions exist for {action_set_key}")
            return {}


    def instance_properties(self, category: str, instance: str, id: str) -> dict:
        """
        Returns Asset Properties based on their Taxonomy.
        """
        if category == AssetCategories.TILES:
            return self.properties[category][instance]

        if category == AssetCategories.SHEETS and instance == AssetInstances.PLAYERS:
            return self.properties[category][AssetInstances.SPRITES][id]

        return self.properties[category][instance][id] 


    def migrate(self) -> Board:
        """
        # migrate

        Transfer the Pydantic DTOs to Python POPOs for the game engine and load them into the Board.
        """
        logger.info("Migrating validated data to engine models...")
        assets = []

        # 1. Migrate Configuration
        configurations = Factory.group(Groups.CONFIGURATIONS, self.configurations)

        # Pre-hydrate all Action strings in properties to unblock Factory and Registry processing.
        if AssetCategories.SHEETS in self.properties:
            for instance, instance_props in self.properties[AssetCategories.SHEETS].items():
                if not instance_props: continue
                for item_id, props in instance_props.items():
                    if isinstance(props.get("actions"), str):
                        props["actions"] = self.instance_actions(AssetCategories.SHEETS, instance, item_id)

        # 2. Migrate Assets without State
        raw_equipment = { }
        for equip_instance_key in Equipment:
            raw_equipment[equip_instance_key] = { }

            equip_dict = self.properties[AssetCategories.SHEETS].get(equip_instance_key, {})
            if not equip_dict:
                continue

            for equip_instance_id, equip_instance in equip_dict.items():
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
                    instance_props = self.instance_properties(category_key, instance_key, instance["id"])

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


    def inject(self, device: Devices):
        """
        Inject the board with ancillary game components.
        """
        # 1. Instantiate Device and inject into Board
        device_mapping = self.configurations.get("mappings", {}).get(device, {})
        device_instance = Factory.device(device, device_mapping)
        self.board.set_device(device_instance)

        # 2. Instantiate Cradle and inject into Board
        spawnable_props = {
            k: v
            for k,v in self.properties.items()
            if k in SpawnableGroup
        }
        spawnable_groups = Factory.groups(Groups.Spawnable, spawnable_props)
        cradle = Factory.cradle(spawnable_groups, self.configurations["recipes"])
        self.board.set_cradle(cradle)

        
    def init(self, screensize: Dimensions, device: Devices, headless: bool=True) -> Tuple[Board, Registry, Dict[str, Screen]]:
        """
        # Ontology: Orchestrate

        Initialize and return game components.
        """
        logger.info("Initializing SDL...")
        render.init(screensize.w, screensize.l, headless)

        logger.info("Initializing Board...")
        self.board = self.migrate()

        # TODO: replace with call to self.inject(device)
        logger.info("Initializing Device...")
        device_mapping = self.configurations.get("mappings", {}).get(device, {})
        device_instance = Factory.device(device, device_mapping)
        self.board.set_device(device_instance)

        # TODO
        # self.inject(device)

        # Map the window to the OS to validate the OpenGL context
        # strictly prior to allocating VRAM target textures.
        if not headless:
            render.show()

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
        Entry point to fire up the dependency-injected execution sequence.
        """
        # Explicitly initialize as a windowed application for gameplay
        self.init(screensize, device, headless=False)

        # TODO: iterate over Mechanics Configuration and instantiate in order
        self.mechanics = [
            Factory.mechanics(Mechanics.PLAYER),
            Factory.mechanics(Mechanics.TRANSITION),
            Factory.mechanics(Mechanics.MOTION),
            Factory.mechanics(Mechanics.COLLISION),
            Factory.mechanics(Mechanics.SWITCH),
            Factory.mechanics(Mechanics.PROJECTILE),
            Factory.mechanics(Mechanics.COMBAT),
            Factory.mechanics(Mechanics.COMMERCE),
            Factory.mechanics(Mechanics.SPEECH),
            Factory.mechanics(Mechanics.ANIMATION),
            Factory.mechanics(Mechanics.REMOVE)
        ]

        self.engine = Engine(self.board, self.screens, self.mechanics)

        return self.engine