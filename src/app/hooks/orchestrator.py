"""
# Ontology: Orchestration
"""
# Standard Libraries
from typing import List, Any, Union
from pathlib import Path
import os

# External Libraries
import yaml

# Application Libraries
import app.config.settings as settings
from app.assets.base import Asset
from app.game.board import Board
from app.hooks.factory import Factory
from app.config.enums import StateRecipe
from app.config.validators import (
    PyRecipeConfiguration,
    PyStateConfiguration
)

# Cython Libraries
import libs.render as render
from libs.registry import Registry

class Orchestrator:
    asset_recipes: PyRecipeConfiguration
    valid_sate: PyStateConfiguration
    registry: Registry

    def __init__(self, board_key: str):
        render.init()
        self.asset_recipes = PyRecipeConfiguration()
        self.registry = Registry()
        self._load(board_key)

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

    def _load(board_key: str):
        board_path = settings.DATA_DIR / board_key  
        target_dir = board_path.expanduser()
        merged_data: dict[str, Any] = {}

        for file_path in target_dir.glob("*.yaml"):
            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                
                if isinstance(data, dict):
                    merged_data = Orchestrator.merge(merged_data, data)

        return PyStateConfiguration.model_validate(merged_data)

    def _migrate( ) -> List[Any]:
        """
        # migrate

        Transfer the Pydantic DTOs to Python POPOs for the game engine.
        """
        pass

    def orchestrate(self, board_key: str = "world-00"):
        """
        # Ontology: Orchestrate
        """


        # 6. Rely on the Factory to translate Enums into live POPOs
        assets.append(
            Asset(
                properties = Factory.properties(category, prop_dict),
                state      = Factory.state(recipe.state, state_dict),
                frame      = Factory.frame(recipe.frame),
                animation  = Factory.animation(recipe.animation)
            )
        )

        self.board = Board(assets), registry
        return self.board