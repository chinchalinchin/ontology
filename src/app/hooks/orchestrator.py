"""
# Ontology: app.hooks.orchestrator
"""
import logging
import dataclasses
from typing import Dict, List, Tuple

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
from app.hooks.decomposer import Decomposer
from app.models.groups import SpawnableGroup, ConfigurationGroup, EquipmentGroup
from app.models.state import StateSchema
from app.models.properties import PropertiesSchema
from app.models.config import ConfigurationSchema

from libs.core.models import Dimensions
import libs.graphics.render as render
from libs.graphics.registry import Registry

logger = logging.getLogger(__name__)

class Orchestrator:
    properties: PropertiesSchema
    state: StateSchema
    configurations: ConfigurationSchema
    
    decomposer: Decomposer
    registry: Registry
    board: Board
    screens: Dict[str, Screen]
    engine: Engine

    def __init__(self, state: str):
        logger.info(f"Initializing Orchestrator for target state: {state} ...")
        self.properties = Loader.load_properties()
        self.configurations = Loader.load_configurations()
        self.state = Loader.load_state(state)

        # Instantiate Decomposer ahead of standard Asset migrations
        self.decomposer = Decomposer(
            compositions=self.configurations.compositions,
            properties=self.properties,
            recipes=self.configurations.recipes
        )

    def migrate(self) -> Board:
        logger.info("Migrating validated data to engine models...")
        
        # 1. Migrate Configuration
        configurations = ConfigurationGroup(
            recipes=self.configurations.recipes,
            mappings=self.configurations.mappings,
            intentions=self.configurations.intentions,
            actions=self.configurations.actions
        )

        # 2. Globally pre-hydrate Actions in Properties.
        resolved_sheets = {}
        for sheet_field in dataclasses.fields(self.properties.sheets):
            sheet_type = sheet_field.name
            sheet_dict = getattr(self.properties.sheets, sheet_type, {})
            resolved_dict = {}
            for e_id, e_props in sheet_dict.items():
                if isinstance(e_props.actions, str):
                    action_data = next((a.data for a in configurations.actions if a.id == e_props.actions), {})
                    resolved_dict[e_id] = dataclasses.replace(e_props, actions=action_data)
                else:
                    resolved_dict[e_id] = e_props
            resolved_sheets[sheet_type] = resolved_dict
            
        self.properties.sheets = dataclasses.replace(self.properties.sheets, **resolved_sheets)

        # 3. Migrate Assets without State (Equipment)
        equipment = EquipmentGroup(
            armor=self.properties.sheets.armor,
            weapons=self.properties.sheets.weapons,
            tools=self.properties.sheets.tools,
            utilities=self.properties.sheets.utilities,
            shields=self.properties.sheets.shields
        )
      
        assets = []
        
        # 4. Intercept and Migrate Compositions
        if hasattr(self.state, 'compositions') and self.state.compositions:
            for comp_deployed_state in self.state.compositions:
                expanded_assets = self.decomposer.unpack(comp_deployed_state)
                assets.extend(expanded_assets)

        # 5. Migrate Assets With State        
        for cat_field in dataclasses.fields(self.state):
            category_key = cat_field.name
            if category_key == 'compositions': continue  # Pre-handled above
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
                    
                    # --- PLAYER PROPERTY MAPPING ---
                    # Players are state instances, but their physical properties map to the Sprites schema
                    prop_instance_key = instance_key
                    if category_key == AssetCategories.SHEETS and instance_key == AssetInstances.PLAYERS:
                        prop_instance_key = AssetInstances.SPRITES
                        
                    cat_props = getattr(self.properties, category_key, None)
                    inst_props = getattr(cat_props, prop_instance_key, {}) if cat_props else {}
                    props = inst_props.get(asset_id)
                    # ---------------------------------
                    
                    assets.append(Asset(
                        taxonomy   = Factory.taxonomy(asset_id, asset_name, category_key, instance_key),
                        properties = props,
                        state      = state_obj,
                        frame      = Factory.frame(recipe.frame) if recipe and recipe.frame else Factory.frame(None),
                        animation  = Factory.animation(recipe.animation) if recipe and recipe.animation else Factory.animation(None)
                    ))
                    
        logger.info(f"Successfully migrated {len(assets)} assets.")

        self.board = Board(assets, configurations, equipment)
        return self.board

    def inject(self, device: Devices) -> Board:
        """
        Inject the board with ancillary game components.
        """
        device_mapping = getattr(self.configurations.mappings, device, None)
        if not device_mapping:
            from app.models.config import Mapping
            device_mapping = Mapping()
            
        device_instance = Factory.device(device, device_mapping)
        self.board.set_device(device_instance)

        spawnable_groups = SpawnableGroup(
            projectiles=self.properties.cursors.projectiles,
            expressions=self.properties.cursors.expressions,
            temporary=self.properties.effects.temporary,
            struts=self.properties.crafts.struts
        )
        cradle = Factory.cradle(spawnable_groups, self.configurations.recipes, self.decomposer)
        self.board.set_cradle(cradle)

        return self.board

    def init(self, 
        screensize: Dimensions, 
        device: Devices, 
        headless: bool=True
    ) -> Tuple[Board, Registry, Dict[str, Screen], List]:
        """
        # Ontology: Orchestrate
        Initialize and return game components.
        """
        logger.info("Initializing SDL...")
        render.init(screensize.w, screensize.l, headless)

        logger.info("Initializing Board...")
        self.migrate()
        self.inject(device)

        if not headless:
            render.show()

        logger.info("Initializing Registry..")
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