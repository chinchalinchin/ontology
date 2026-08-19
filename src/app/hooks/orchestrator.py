"""
# Ontology: app.hooks.orchestrator

Package for managing dependency injection. 
"""
# Standard Libraries
import logging
import dataclasses
from typing import (
    Dict,
    List, 
    Tuple
)

# Application Libraries
from app.assets.base import Asset
from app.config.loader import Loader
from app.config.enums import (
    AssetCategories, 
    AssetInstances,
    Devices,
    Groups,
    Mechanics,
    Equipment
)
from app.game.board import Board
from app.game.engine import Engine
from app.game.screen import Screen
from app.hooks.factory import Factory
from app.models.groups import (
    SpawnableGroup,
    EquipmentGroup
)
from app.models.state import StateSchema
from app.models.properties import PropertiesSchema
from app.models.config import ConfigurationSchema

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
    properties: PropertiesSchema
    state: StateSchema
    configurations: ConfigurationSchema
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
        if category == AssetCategories.SHEETS and instance == AssetInstances.PLAYERS:
            return self.properties[category][AssetInstances.SPRITES][id]

        return self.properties[category][instance][id] 


    def migrate(self) -> Board:
        """
        # migrate

        Transfer the Pydantic DTOs to Python POPOs for the game engine and load them into the Board.
        """
        logger.info("Migrating validated data to engine models...")

        # 1. Migrate Assets without State (Equipment)
        raw_equipment = {}
        for equip_key in Equipment:
            equip_dict = getattr(self.properties.sheets, equip_key, {})
            resolved_equip = {}
            for e_id, e_props in equip_dict.items():
                if isinstance(e_props.actions, str):
                    action_data = next((
                        a.data 
                        for a in self.configurations.actions 
                        if a.id == e_props.actions
                    ), {})
                    resolved_equip[e_id] = dataclasses.replace(e_props, actions=action_data)
                else:
                    resolved_equip[e_id] = e_props
            raw_equipment[equip_key] = resolved_equip
        
        equipment = EquipmentGroup(**raw_equipment)

        # 2. Migrate Assets with State        
        assets = []
        
        for cat_field in dataclasses.fields(self.state):
            category_key = cat_field.name
            category_data = getattr(self.state, category_key)
            if not category_data: continue
            
            for inst_field in dataclasses.fields(category_data):
                instance_key = inst_field.name
                instance_list = getattr(category_data, instance_key)
                if not instance_list: continue
                
                for state_obj in instance_list:
                    asset_id = state_obj.id
                    asset_name = state_obj.name
                    
                    cat_recipes = getattr(self.configurations.recipes, category_key, None)
                    recipe = getattr(cat_recipes, instance_key, None) if cat_recipes else None
                    
                    cat_props = getattr(self.properties, category_key, None)
                    inst_props = getattr(cat_props, instance_key, {}) if cat_props else {}
                    props = inst_props.get(asset_id)
                    
                    if category_key == AssetCategories.SHEETS and props \
                        and isinstance(props.actions, str):
                        action_data = next((
                            a.data 
                            for a in self.configurations.actions 
                            if a.id == props.actions
                        ), {})
                        props = dataclasses.replace(props, actions=action_data)
                        
                    assets.append(Asset(
                        taxonomy   = Factory.taxonomy(asset_id, asset_name, category_key, instance_key),
                        properties = props,
                        state      = state_obj,
                        frame      = Factory.frame(recipe.frame) if recipe and recipe.frame else Factory.frame(None),
                        animation  = Factory.animation(recipe.animation) if recipe and recipe.animation else Factory.animation(None)
                    ))
                    
        logger.info(f"Successfully migrated {len(assets)} assets.")

        self.board = Board(assets, self.configurations, equipment)
        return self.board


    def inject(self, device: Devices) -> Board:
        """
        Inject the board with ancillary game components.
        """
        # 1. Instantiate Device and inject into Board
        device_mapping = getattr(self.configurations.mappings, device.value, None)
        if not device_mapping:
            from app.models.config import Mapping
            device_mapping = Mapping()
            
        device_instance = Factory.device(device.value, device_mapping)
        self.board.set_device(device_instance)

        # 2. Assemble SpawnableGroup directly from POPOs, bypassing missing Factory functions
        spawnable_groups = SpawnableGroup(
            projectiles=self.properties.cursors.projectiles,
            expressions=self.properties.cursors.expressions,
            temporary=self.properties.effects.temporary,
            struts=self.properties.crafts.struts
        )
        cradle = Factory.cradle(spawnable_groups, self.configurations.recipes)
        self.board.set_cradle(cradle)

        return self.board
        
    def init(self, 
        screensize: Dimensions, 
        device: Devices, 
        headless: bool=True
    ) -> Tuple[Board, Registry, Dict[str, Screen], List[Mechanics]]:
        """
        # Ontology: Orchestrate
        Initialize and return game components.
        """
        logger.info("Initializing SDL...")
        render.init(screensize.w, screensize.l, headless)

        logger.info("Initializing Board...")
        self.migrate()
        self.inject(device)

        # NOTE: Map the window to the OS to validate the OpenGL context
        #   strictly prior to allocating VRAM target textures.
        if not headless:
            render.show()

        logger.info("Initializing Registry..")
        # Registry is Cython and expects dictionaries. dataclasses.asdict safely extracts them.
        self.registry = Registry(
            dataclasses.asdict(self.properties), 
            dataclasses.asdict(self.configurations.recipes)
        )

        logger.info("Initializing Screens...")
        self.screens = {
            layer: Screen(
                screensize, 
                self.board.size(layer)[0] if self.board.size(layer) else Dimensions(0, 0),
                self.board.categories(AssetCategories.TILES, layer),
                self.registry
            )
            for layer in self.board.layers()
        } 

        logger.info("Initializing Mechanics...")
        order = getattr(self.configurations.mechanics, 'order', None)
        if not order:
            order = [
                Mechanics.PLAYER,
                Mechanics.MOTION,
                Mechanics.ANIMATION,
                Mechanics.REMOVE
            ]
            
        self.mechanics = [Factory.mechanics(m) for m in order]
        
        return self.board, self.registry, self.screens, self.mechanics

    def ignite(self, screensize: Dimensions, device: Devices) -> Engine:
        """
        Entry point to fire up the dependency-injected execution sequence.
        """
        self.init(screensize, device, headless=False)
        self.engine = Engine(self.board, self.screens, self.mechanics)
        return self.engine