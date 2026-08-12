"""
# Ontology: Orchestration
"""
# Standard Libraries
import time
import logging
from typing import List, Any, Dict, Tuple

# External Libraries
import yaml

# Application Libraries
import app.config.settings as settings
from app.config.enums import (
    AssetCategories, 
    AssetInstances,
    Devices
)
from app.assets.base import Asset
from app.game.board import Board
from app.game.screen import Screen
from app.input.player import Player, Device
from app.hooks.factory import Factory
from app.config.validators import (
    PyRecipeConfiguration,
    PyStateConfiguration,
    PySheetPropertyConfiguration,
    PyObjectPropertyConfiguration,
    PyCursorPropertyConfiguration,
    PyEffectPropertyConfiguration,
    PyTilePropertyConfiguration,
    PyCraftPropertyConfiguration,
    PyEquipmentPropertyConfiguration,
    PyIntentionPropertyConfiguration
)

# Cython Libraries
from libs.core import Dimensions
import libs.render as render
from libs.registry import Registry

logger = logging.getLogger(__name__)

class Orchestrator:
    """
    """
    # Configuration
    equipment: Dict = { }
    intentions: Dict = { }
    properties: Dict = { }
    recipes: Dict = {}
    state: Dict = {}

    # Game
    registry: Registry
    board: Board
    screens: Dict[str, Screen]

    def __init__(self, state: str):
        logger.info(f"Initializing Orchestrator for target state: {state}")
        self.load(state)

    @staticmethod
    def merge(
        target: dict[str, Any], 
        source: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Recursively merge source dictionary into target dictionary.
        """
        for key, value in source.items():
            if key in target:
                if isinstance(target[key], dict) and isinstance(value, dict):
                    Orchestrator.merge(target[key], value)
                elif isinstance(target[key], list) and isinstance(value, list):
                    target[key].extend(value)
                else:
                    # If types clash or aren't combinable, source overwrites
                    target[key] = value
            else:
                target[key] = value
        return target

    @staticmethod
    def time() -> float:
        return time.perf_counter()

    def instance_properties(self, category, instance, snapshot):
        # Lookup properties using the 'id' before modifying the dictionary
        if category == AssetCategories.TILES:
            return self.properties[category][instance]

        if category == AssetCategories.SHEETS:
            return self.properties[category][instance]["personas"][snapshot["id"]] 

        return self.properties[category][instance][snapshot["id"]] 

    def load(self, state: str) -> None:
        board_path = settings.STATE_DIR / state  
        target_dir = board_path.expanduser()
        merged_data: dict[str, Any] = {}
        
        logger.info(f"Loading YAML state configurations from {target_dir}")

        for file_path in target_dir.glob("*.yaml"):
            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    merged_data = Orchestrator.merge(merged_data, data)

        logger.debug(f"Validating loaded schema via Pydantic model.")
        self.state = PyStateConfiguration.model_validate(merged_data).model_dump(exclude_none=True)

    def migrate(self, device: Device) -> List[Asset]:
        """
        # migrate

        Transfer the Pydantic DTOs to Python POPOs for the game engine.
        """
        logger.info("Migrating configuration states to engine Application Objects (POPOs)...")
        assets = []

        if not self.properties:
            self.properties = {
                **PyTilePropertyConfiguration().model_dump(),
                **PyObjectPropertyConfiguration().model_dump(),
                **PyEffectPropertyConfiguration().model_dump(),
                **PyCursorPropertyConfiguration().model_dump(),
                **PyCraftPropertyConfiguration().model_dump(),
                **PySheetPropertyConfiguration().model_dump()
            }

        if not self.recipes:
            self.recipes = PyRecipeConfiguration().assets.model_dump()

        if not self.equipment:
            validated_equipment = PyEquipmentPropertyConfiguration().model_dump()

        if not self.intention:
            validated_intention = PyIntentionPropertyConfiguration().model_dump()

        for category_key, instance_data in self.state.items():
            for instance_key, instance_list in instance_data.items():
                for instance in instance_list:

                    recipe = self.recipes[category_key][instance_key]
                    instance_props = self.instance_properties(category_key, instance_key, instance)

                    # Pop the taxonomy keys to strip them from the state snapshot
                    asset_id = instance.pop("id")
                    asset_name = instance.pop("name")

                    if instance_key == AssetInstances.PLAYER:
                        assets.append(Player(
                            device      = device,
                            taxonomy    = Factory.taxonomy(category_key, instance_key, asset_id, asset_name),
                            properties  = Factory.properties(category_key, instance_props),
                            state       = Factory.state(recipe.state, instance),
                            frame       = Factory.frame(recipe.frame),
                            animation   = Factory.animation(recipe.animation)
                        ))
                        continue
                    
                    assets.append(Asset(
                        taxonomy   = Factory.taxonomy(category_key, instance_key, asset_id, asset_name),
                        properties = Factory.properties(category_key, instance_props),
                        state      = Factory.state(recipe.state, instance),
                        frame      = Factory.frame(recipe.frame),
                        animation  = Factory.animation(recipe.animation)
                    ))
                    
        logger.info(f"Successfully migrated {len(assets)} assets.")
        return assets
    
    def orchestrate(self, 
        screensize: Dimensions,
        device: Devices
    ) -> Tuple[Board, Registry, Dict[str, Screen]]:
        """
        # Ontology: Orchestrate

        Initialize and return game components.
        """
        logger.info("Bootstrapping internal SDL environment and initializing Registry.")
        render.init(screensize.w, screensize.l)

        assets = self.migrate(device)
        self.board = Board(assets)
        self.registry = Registry(self.properties, self.recipes)
        
        logger.info("Initializing game screens across layers...")
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

    def start(self, 
        screensize: Dimensions, 
        device: Devices
    ) -> None:
        self.orchestrate(screensize, device)
        
        logger.info("Entering Main Game Loop...")
        delta = 1.0 / 60.0
        accumulator = 0.0
        last_time = self.time()

        while self.board.loaded:
            current_time = self.time()
            frame_time = current_time - last_time
            last_time = current_time
            accumulator += frame_time
            
            while not self.board.paused:
                while accumulator >= delta:
                    self.board.play(delta)
                    accumulator -= delta

                player = self.board.player()

                self.screens[player.layer].draw(
                    self.board.assets(player.layer), 
                    player.state.positions,
                    player.dimensions,
                    self.registry
                )

            while self.board.paused: 
                self.board.menu()