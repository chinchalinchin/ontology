"""
# Ontology: app.models.groups

"""
# Standard Libraries
from typing import Dict
from dataclasses import dataclass

# Application Libraries
from app.models.properties import (
    AssetProperties,
    SheetProperties
)
from app.models.config import (
    RecipeConfiguration,
    MappingConfiguration,
    IntentionConfiguration,
    ActionConfiguration
)

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------------- GROUP MODELS
# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class EquipmentGroup(AssetProperties):
    """
    """
    armor: Dict[str, SheetProperties]
    tools: Dict[str, SheetProperties]
    utilities: Dict[str, SheetProperties]
    weapons: Dict[str, SheetProperties]

@dataclass(slots=True)
class ConfigurationGroup:
    """
    """
    recipes: RecipeConfiguration
    mappings: MappingConfiguration
    intentions: IntentionConfiguration
    actions: ActionConfiguration
