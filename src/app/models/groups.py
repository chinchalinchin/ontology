"""
# Ontology: app.models.groups

"""
# Standard Libraries
from typing import Dict, List
from dataclasses import dataclass, field

# Application Libraries
from app.config.enums import (
    Intentions
)
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
    shields: Dict[str, SheetProperties] = field(default_factory=dict)

@dataclass(slots=True)
class ConfigurationGroup:
    """
    """
    recipes: RecipeConfiguration
    mappings: MappingConfiguration
    intentions: Dict[Intentions, List[IntentionConfiguration]]
    actions: List[ActionConfiguration]