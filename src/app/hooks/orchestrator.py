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
from app.config.enums import AssetCategories, Devices
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
    PyCraftPropertyConfiguration
)

# Cython Libraries
from libs.core import Dimensions
import libs.render as render
from libs.registry import Registry

logger = logging.getLogger(__name__)

class Orchestrator:
    """
    """

    properties: Dict
    recipes: PyRecipeConfiguration
    state: PyStateConfiguration
    registry: Registry
    board: Board
    screens: Dict[str, Screen]

    def __init__(self, state: str):
        logger.info(f"Initializing Orchestrator for target state: {state}")
        self.recipes = PyRecipeConfiguration()
        self.properties = { }
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
        self.state = PyStateConfiguration.model_validate(merged_data)

    def migrate(self) -> List[Asset]:
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

        for category_key, instance_data in self.state.model_dump(exclude_none=True).items():
            for instance_key, instance_list in instance_data.items():
                for instance in instance_list:

                    recipe = getattr(getattr(self.recipes.assets, category_key), instance_key)
                    
                    # Lookup properties using the 'id' before modifying the dictionary
                    if category_key == AssetCategories.TILES:
                        instance_props = self.properties[category_key][instance_key]
                    elif category_key == AssetCategories.SHEETS:
                        instance_props = self.properties[category_key][instance_key]["personas"][instance["id"]] 
                    else:
                        instance_props = self.properties[category_key][instance_key][instance["id"]] 

                    # Pop the taxonomy keys to strip them from the state snapshot
                    asset_id = instance.pop("id")
                    asset_name = instance.pop("name")

                    assets.append(
                        Asset(
                            taxonomy   = Factory.taxonomy(category_key, instance_key, asset_id, asset_name),
                            properties = Factory.properties(category_key, instance_props),
                            state      = Factory.state(recipe.state, instance),
                            frame      = Factory.frame(recipe.frame),
                            animation  = Factory.animation(recipe.animation)
                        )
                    )
                    
        logger.info(f"Successfully migrated {len(assets)} assets.")
        return assets
    
    def orchestrate(self, 
        screensize: Dimensions,
        device: Device
    ) -> Tuple[Board, Registry, Dict[str, Screen]]:
        """
        # Ontology: Orchestrate

        Initialize and return game components.
        """
        logger.info("Bootstrapping internal SDL environment and initializing Registry.")
        render.init(screensize.w, screensize.l)

        assets = self.migrate()
        player = Player(device)

        self.board = Board(assets, player)
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

    def start(self, screensize) -> None:
        self.orchestrate(screensize, device=Devices.KEYBOARD) # Assuming keyboard as default for actual gameplay
        
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

                # Determine camera target (Defaults to player, but could be a cutscene target)
                target_pos = self.board.player.state.position
                target_dim = self.board.player.dimensions

                self.screens[self.board.player.layer].draw(
                    self.board.assets(self.board.player.layer), 
                    target_pos,
                    target_dim,
                    self.registry
                )

            while self.board.paused: 
                self.board.menu()