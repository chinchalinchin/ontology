"""
@domain.system
@app.config

# Ontology: Source - app.static.loader
"""
# Standard Libraries
from typing import (
    Any,
    Optional
)
import logging

# External Libraries
import yaml
from pydantic import TypeAdapter

# Application Libraries
import app.static.settings as settings
from app.static.macros.compositions import CompositionCompiler
from app.models.state import StateSchema
from app.models.properties import PropertiesSchema
from app.models.config import ConfigurationSchema

logger = logging.getLogger(__name__)

class Loader:
    @staticmethod
    def merge(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
        """
        Recursively merges incoming YAML dictionaries so multi-file top-level
        keys (e.g., 'menus.load' and 'menus.main') do not overwrite each other.
        """
        for key, val in incoming.items():
            if (
                key in base
                and isinstance(base[key], dict)
                and isinstance(val, dict)
            ):
                Loader.merge(base[key], val)
            else:
                base[key] = val
        return base

    @staticmethod
    def load_state(state: str) -> StateSchema:
        target_dir = (settings.STATE_DIR / state).expanduser()
        merged_data: dict[str, Any] = {}
        
        logger.info(f"Loading YAML state configurations from {target_dir} ...")
        for file_path in target_dir.rglob("*.yaml"):
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
    def load_configurations(properties: Optional[PropertiesSchema] = None) -> ConfigurationSchema:
        target_dir = settings.CONFIG_DIR.expanduser()
        merged_data: dict[str, Any] = {}
        logger.info("Loading YAML configurations...")

        for file_path in target_dir.rglob("*.yaml"):
            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    merged_data = Loader.merge(merged_data, data)

        if properties is not None:
            merged_data = CompositionCompiler.compile(merged_data, properties)

        return TypeAdapter(ConfigurationSchema).validate_python(merged_data)
    
    @staticmethod
    def save_state(slot: str, state_data: dict[str, Any]) -> None:
        """
        Validates and serializes runtime state to disk matching StateSchema.
        """
        adapter = TypeAdapter(StateSchema)
        
        # 1. Validate structure against StateSchema and coerce to pure primitives
        validated_schema = adapter.validate_python(state_data)
        primitive_dump = adapter.dump_python(validated_schema, mode="json", exclude_none=True)

        # 2. Write clean YAML via safe_dump
        out_dir = settings.SAVE_DIR.expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{slot}.yaml"

        logger.info(f"Serializing board state to {out_path} ...")
        with out_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(primitive_dump, f, default_flow_style=False, sort_keys=False)