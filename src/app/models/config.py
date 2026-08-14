"""
# Ontology: app.models.configuration

Models for typing the configuration attributes of Mechanics and other game components. See documentation for a more in-depth explanation of each field and its purpose. 
"""
# Standard Libraries
from typing import Dict, List, Callable
from dataclasses import dataclass, field

# Application Libraries
from app.config.enums import Directions, Actions


# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------ CONFIGURATION MODELS
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# --------------------------------------------------------------- EQUIPMENT CONFIGURATION

@dataclass(slots=True)
class EquipmentAnimationConfiguration:
    action: Actions
    direction: Directions

@dataclass(slots=True)
class EquipmentConfig:
    animation: EquipmentAnimationConfiguration
    sheets: List[str]

@dataclass(slots=True)
class EquipmentConfiguration:
    armor: Dict[str, EquipmentConfig]
    tools: Dict[str, EquipmentConfig]
    utilities: Dict[str, EquipmentConfig]
    weapons: Dict[str, EquipmentConfig]

# ---------------------------------------------------------------------------------------
# ---------------------------------------------------------------- INTENTION CONFIGURTION

@dataclass(slots=True)
class Transition:
    """
    """
    next: str
    conditions: List[Callable] = field(default_factory=list)

@dataclass(slots=True)
class IntentionConfiguration:
    """
    """
    intentions: Dict[str, List[Transition]] = field(default_factory=dict)