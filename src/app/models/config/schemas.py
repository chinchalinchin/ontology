"""
# Ontology: app.models.config

Models for typing the configuration attributes of Mechanics and other game components. See documentation for a more in-depth explanation of each field and its purpose. 
"""
# Standard Libraries
from typing import (
    Dict, 
    List, 
)
from dataclasses import dataclass, field

# Application Libraries
from app.config.enums import (
    Intentions
)
from app.models.config.core import (
    ActionConfiguration, 
    IntentionConfiguration,
    MechanicsConfiguration,
    PlotConfiguration,
    CompositionConfiguration,
    LibraryConfiguration
)
from app.models.config.mappings import MappingConfiguration
from app.models.config.menus import MenuConfiguration
from app.models.config.recipes import RecipeConfiguration

# ---------------------------------------------------------------------------------------
# --------------------------------------------------------------------------- ROOT SCHEMA

@dataclass(slots=True, frozen=True)
class ConfigurationSchema:
    actions: List[ActionConfiguration] = field(default_factory=list)
    compositions: Dict[str, CompositionConfiguration] = field(default_factory=dict)
    intentions: Dict[Intentions, List[IntentionConfiguration]] = field(default_factory=dict)
    library: Dict[str, Dict[str, Dict[str, str]]] = field(default_factory=dict)
    mappings: MappingConfiguration = field(default_factory=MappingConfiguration)
    mechanics: MechanicsConfiguration = field(default_factory=MechanicsConfiguration)
    plots: Dict[str, List[PlotConfiguration]] = field(default_factory=dict)
    recipes: RecipeConfiguration = field(default_factory=RecipeConfiguration)
    menus: Dict[str, MenuConfiguration] = field(default_factory=dict)
