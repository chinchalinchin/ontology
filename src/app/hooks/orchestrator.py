"""
# Ontology: Orchestration
"""
# Standard Libraries
import time
from typing import List, Any, Dict, Tuple

# External Libraries
import yaml

# Application Libraries
import app.config.settings as settings
from app.config.enums import AssetCategories
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
                    # If types clash or aren't combinable, source overwrites or 
                    # you can choose to raise a ValueError here depending on strictness.
                    target[key] = value
            else:
                target[key] = value
        return target

    @staticmethod
    def time() -> float:
        return time.perf_counter()
    
    def load(self, state: str) -> None:
        board_path = settings.DATA_DIR / state  
        target_dir = board_path.expanduser()
        merged_data: dict[str, Any] = {}

        for file_path in target_dir.glob("*.yaml"):
            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                
                if isinstance(data, dict):
                    merged_data = Orchestrator.merge(merged_data, data)

        self.state = PyStateConfiguration.model_validate(merged_data)

    def migrate(self) -> List[Asset]:
        """
        # migrate

        Transfer the Pydantic DTOs to Python POPOs for the game engine.
        """
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

        for category_key, instance_data in self.state.model_dump().items():
            for instance_key, instance_list in instance_data.items():
                for instance in instance_list:

                    recipe = getattr(getattr(self.recipes.assets, category_key), instance_key)

                    if category_key == AssetCategories.TILES:
                        instance_props = self.properties[category_key][instance_key]
                    elif category_key == AssetCategories.SHEETS:
                        instance_props = self.properties[category_key][instance_key]["personas"][instance["id"]] 
                    else:
                        instance_props = self.properties[category_key][instance_key][instance["id"]] 

                    assets.append(
                        Asset(
                            taxonomy   = Factory.taxonomy(category_key, instance_key, instance["id"], instance["name"]),
                            properties = Factory.properties(category_key, instance_props),
                            state      = Factory.state(recipe.state, instance),
                            frame      = Factory.frame(recipe.frame),
                            animation  = Factory.animation(recipe.animation)
                        )
                    )

        return assets
    
    def orchestrate(self, 
        screensize: Dimensions,
        device: Device
    ) -> Tuple[Board, Registry, Dict[str, Screen]]:
        """
        # Ontology: Orchestrate

        Initialize and return game components.
        """
        render.init(screensize.w, screensize.l)

        assets = self.migrate()
        player = Player(device)

        self.board = Board(assets, player)
        self.registry = Registry(self.properties)
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
        self.orchestrate(screensize)
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

                self.screens[self.board.player.layer].draw(
                    self.board.assets(self.board.player.layer), 
                    self.board.player, 
                    self.registry
                )

            while self.board.paused: 
                self.board.menu()