"""
# Ontology: Orchestration
"""
# Standard Libraries
from typing import List, Any, Dict, Tuple

# External Libraries
import yaml

# Application Libraries
import app.config.settings as settings
from app.config.enums import AssetCategories
from app.assets.base import Asset
from app.game.board import Board
from app.game.screen import Screen
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
import libs.render as render
from libs.registry import Registry

class Orchestrator:
    """
    """

    properties: Dict
    asset_recipes: PyRecipeConfiguration
    valid_state: PyStateConfiguration
    registry: Registry
    board: Board
    screens: List[Screen]

    def __init__(self, board_key: str):
        render.init()
        self.asset_recipes = PyRecipeConfiguration()
        self.properties = { }
        self.load(board_key)

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
                    # If types clash or aren't combinable, source overwrites or 
                    # you can choose to raise a ValueError here depending on strictness.
                    target[key] = value
            else:
                target[key] = value
        return target

    @staticmethod
    def time(self) -> Time:
        return "TODO: some time" 
    
    def load(self, board_key: str):
        board_path = settings.DATA_DIR / board_key  
        target_dir = board_path.expanduser()
        merged_data: dict[str, Any] = {}

        for file_path in target_dir.glob("*.yaml"):
            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                
                if isinstance(data, dict):
                    merged_data = Orchestrator.merge(merged_data, data)

        self.valid_state = PyStateConfiguration.model_validate(merged_data)

    def migrate(self) -> List[Asset]:
        """
        # migrate

        Transfer the Pydantic DTOs to Python POPOs for the game engine.
        """
        assets = []

        if not self.properties:
            self.properties = {
                "tiles": PyTilePropertyConfiguration(),
                "objects": PyObjectPropertyConfiguration(),
                "effects": PyEffectPropertyConfiguration(),
                "cursors": PyCursorPropertyConfiguration(),
                "crafts": PyCraftPropertyConfiguration(),
                "sheets": PySheetPropertyConfiguration(),
            }

        for category_key, instance_data in self.valid_state:
            for instance_key, instance_list in instance_data:
                for instance in instance_list:

                    recipe = self.asset_recipes.assets[category_key][instance_key]
                    instance_props = self.property_map[category_key][category_key][instance_key]

                    if category_key != AssetCategories.TILES:
                        properties = properties[instance.id]

                    assets.append(
                        Asset(
                            properties = Factory.properties(category_key, instance_props),
                            state      = Factory.state(recipe.state, instance),
                            frame      = Factory.frame(recipe.frame),
                            animation  = Factory.animation(recipe.animation)
                        )
                    )

        return assets
    
    def orchestrate(self) -> Tuple[Board, Registry]:
        """
        # Ontology: Orchestrate

        Initialize and return game component.
        """

        assets = self.migrate()
        self.board = Board(assets)
        self.registry = Registry(self.property_map)

        self.board.layers()

        self.screens = [
            Screen(
                "TODO: screensize", 
                "TODO: boardsize",
                self.board.tiles(layer),
                self.registry
            )
            for layer 
            in self.board.layers
        ]
        
        self.screen = Screen()

        return self.board, self.registry, self.screens

    def start(self):
        self.orchestrate()
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

                player = self.board.player
                assets = self.board.assets()
                self.screens[player.layer].draw(assets, player)

            while self.board.paused: 
                self.board.menu()