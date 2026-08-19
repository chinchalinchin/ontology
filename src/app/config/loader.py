"""
# Ontology: app.config.loader

Package for loading in configuration files.
"""
# Standard Libraries
from typing import Any
import logging

# External Libraries
import yaml
from pydantic import TypeAdapter

# Application Libraries
import app.config.settings as settings
from app.models.state import StateSchema
from app.models.properties import PropertiesSchema
from app.models.config import ConfigurationSchema


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
                    target[key] = value
            else:
                target[key] = value
        return target


    def load_state(state: str) -> dict:
        """
        ### load_state

        Load validated state data from `/src/data/state/<state>/*.yaml`
        """
        target_dir = (settings.STATE_DIR / state).expanduser()
        merged_data: dict[str, Any] = {}
        
        logger.info(f"Loading YAML state configurations from {target_dir} ...")
        for file_path in target_dir.glob("*.yaml"):
            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    merged_data = Loader.merge(merged_data, data)

        logger.debug("Validating loaded state natively via Pydantic TypeAdapter.")
        return TypeAdapter(StateSchema).validate_python(merged_data)


    def load_properties() -> dict:
        """
        ### load_properties

        Load validated property schemas from `/src/assets/**/main.yaml`
        """
        merged_data: dict[str, Any] = {}
        logger.info("Loading YAML property schemas...")
        
        for file_path in settings.ASSET_DIR.rglob(settings.APP_EXT):
            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    merged_data = Loader.merge(merged_data, data)
                    
        return TypeAdapter(PropertiesSchema).validate_python(merged_data)


    def load_configurations() -> dict:
        """
        ### load_configurations

        Load validated configurations from `/src/data/config/**/main.yaml`.
        """
        merged_data: dict[str, Any] = {}
        logger.info("Loading YAML configurations...")
        
        for file_path in settings.CONFIG_DIR.rglob(settings.APP_EXT):
            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    merged_data = Loader.merge(merged_data, data)
                    
        return TypeAdapter(ConfigurationSchema).validate_python(merged_data)