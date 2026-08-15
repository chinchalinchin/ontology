"""
# Ontology: app.models.configuration

Models for typing the configuration attributes of Mechanics and other game components. See documentation for a more in-depth explanation of each field and its purpose. 
"""
# Standard Libraries
from typing import Dict, List, Callable
from dataclasses import dataclass, field

# Application Libraries
from app.models.properties import Action

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------ CONFIGURATION MODELS
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------- ACTION CONFIGURTION

@dataclass(slots=True)
class ActionConfiguration:
    """
    """
    id: str
    data: Dict[str, Action]
    
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