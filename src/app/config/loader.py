"""
# Ontology: app.config.loader
"""
from typing import Any
import logging
import yaml
from pydantic import TypeAdapter

import app.config.settings as settings
from app.models.state import StateSchema
from app.models.properties import PropertiesSchema
from app.models.config import ConfigurationSchema

logger = logging.getLogger(__name__)

class Loader:
    @staticmethod
    def merge(target: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
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

    @staticmethod
    def load_state(state: str) -> StateSchema:
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

    @staticmethod
    def load_properties() -> PropertiesSchema:
        target_dir = settings.ASSET_DIR.expanduser()
        merged_data: dict[str, Any] = {}
        logger.info("Loading YAML property schemas...")
        
        for file_path in target_dir.rglob("*.yaml"):
            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    merged_data = Loader.merge(merged_data, data)
                    
        return TypeAdapter(PropertiesSchema).validate_python(merged_data)

    @staticmethod
    def load_configurations() -> ConfigurationSchema:
        target_dir = settings.CONFIG_DIR.expanduser()
        merged_data: dict[str, Any] = {}
        logger.info("Loading YAML configurations...")
        
        for file_path in target_dir.rglob("*.yaml"):
            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    merged_data = Loader.merge(merged_data, data)
                    
        return TypeAdapter(ConfigurationSchema).validate_python(merged_data)