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
    PyStateConfiguration,
    PySheetPropertyConfiguration,
    PyObjectPropertyConfiguration,
    PyCursorPropertyConfiguration,
    PyEffectPropertyConfiguration,
    PyTilePropertyConfiguration,
    PyCraftPropertyConfiguration,
    PyEquipmentPropertyConfiguration,
    PyIntentionPropertyConfiguration,
    PyDeviceMappingConfiguration
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
        return PyStateConfiguration.model_validate(merged_data).model_dump(exclude_none=True)

    def load_properties() -> dict:
        """
        ### load_properties

        Load validated property configuration from `/src/assets/**/main.yaml`
        """
        return {
            **PyTilePropertyConfiguration().model_dump(),
            **PyObjectPropertyConfiguration().model_dump(),
            **PyEffectPropertyConfiguration().model_dump(),
            **PyCursorPropertyConfiguration().model_dump(),
            **PyCraftPropertyConfiguration().model_dump(),
            **PySheetPropertyConfiguration().model_dump()
        }

    def load_recipes() -> dict:
        """
        ### load_recipes

        Load validated Asset recipe configuration from `/src/assets/main.yaml`
        """
        return PyRecipeConfiguration().assets.model_dump()

    def load_devices() -> dict:
        """
        ### load_devices

        Load validated Device mapping configuration from `/src/data/mappings/main.yaml`
        """
        return PyDeviceMappingConfiguration().model_dump()

    def load_equipment() -> dict:
        """
        ### load_equipment

        Load validated Equipment configuration from `/src/data/equipment/main.yaml`
        """
        return PyEquipmentPropertyConfiguration().equipment.model_dump()

    def load_intentions() -> dict:
        """
        ### load_intentions

        Load validated Intention configuration from `/src/data/intentions/main/yaml`
        """
        return PyIntentionPropertyConfiguration().model_dump()