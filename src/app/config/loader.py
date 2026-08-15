"""
# Ontology: app.config.loader

Package for loading in configuration files.
"""
# Standard Libraries
from typing import Any
import logging

# External Libraries
import yaml

# Application Libraries
import app.config.settings as settings
from app.config.validators import (
    PyRecipeConfiguration,
    PyMappingConfiguration,
    PyIntentionConfiguration,
    PyActionsConfiguration,
    PyStateSchema,
    PySheetPropertySchema,
    PyObjectPropertySchema,
    PyCursorPropertySchema,
    PyEffectPropertySchema,
    PyTilePropertySchema,
    PyCraftPropertySchema,
)

logger = logging.getLogger(__name__)

class Loader:
    """
    ## Loader

    """

    @staticmethod
    def merge(
        target: dict[str, Any], 
        source: dict[str, Any]
    ) -> dict[str, Any]:
        """
        ### merge

        Recursively merge source dictionary into target dictionary.
        """
        for key, value in source.items():
            if key in target:
                if isinstance(target[key], dict) and isinstance(value, dict):
                    Loader.merge(target[key], value)
                elif isinstance(target[key], list) and isinstance(value, list):
                    target[key].extend(value)
                else:
                    # If types clash or aren't combinable, source overwrites
                    target[key] = value
            else:
                target[key] = value
        return target

    def load_state(state: str) -> dict:
        """
        ### load_state

        Load validated state data from `/src/data/state/<state>/*.yaml`
        """
        board_path = settings.STATE_DIR / state  
        target_dir = board_path.expanduser()
        merged_data: dict[str, Any] = {}
        
        logger.info(f"Loading YAML state configurations from {target_dir} ...")

        for file_path in target_dir.glob("*.yaml"):
            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    merged_data = Loader.merge(merged_data, data)

        logger.debug(f"Validating loaded state via Pydantic model.")
        return PyStateSchema.model_validate(merged_data).model_dump(exclude_none=True)

    def load_properties() -> dict:
        """
        ### load_properties

        Load validated property schemas from `/src/assets/**/main.yaml`
        """
        return {
            **PyTilePropertySchema().model_dump(),
            **PyObjectPropertySchema().model_dump(),
            **PyEffectPropertySchema().model_dump(),
            **PyCursorPropertySchema().model_dump(),
            **PyCraftPropertySchema().model_dump(),
            **PySheetPropertySchema().model_dump()
        }

    def load_configurations() -> dict:
        """
        ### load_configurations

        Load validated configurations from `/src/data/config/**/main.yaml`.
        """
        return {
            **PyRecipeConfiguration().model_dump(),
            **PyMappingConfiguration().model_dump(),
            **PyIntentionConfiguration().model_dump(),
            **PyActionsConfiguration().model_dump()
        }