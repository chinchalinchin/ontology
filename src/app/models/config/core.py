"""
# Ontology: app.models.config.core

Models for typing the core configuration attributes of game components.
"""
# Standard Libraries
from typing import (
    Dict, 
    List, 
)
from dataclasses import (
    dataclass, 
    field
)

# Application Libraries
from app.models.properties import Action

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------ CONFIGURATION MODELS
# ---------------------------------------------------------------------------------------

class Configuration:
    pass

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------ ACTION CONFIGURATION

@dataclass(slots=True, frozen=True)
class ActionConfiguration(Configuration):
    id: str
    data: Dict[str, Action]
    
# ---------------------------------------------------------------------------------------
# --------------------------------------------------------------- INTENTION CONFIGURATION

@dataclass(slots=True, frozen=True)
class IntentionConfiguration(Configuration):
    """
    """
    next: str
    conditions: List[str] = field(default_factory=list)

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------- PLOT CONFIGURATION

@dataclass(slots=True, frozen=True)
class PlotConfiguration(Configuration):
    """
    """
    next: str
    conditions: List[str] = field(default_factory=list)

# ---------------------------------------------------------------------------------------
# ----------------------------------------------------------------- LIBRARY CONFIGURATION

@dataclass(slots=True, frozen=True)
class LibraryConfiguration:
    """
    """
    pass