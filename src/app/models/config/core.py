"""
# Ontology: app.models.config.core

Models for typing the core configuration attributes of game components.
"""
# Standard Libraries
from typing import (
    Dict
)
from dataclasses import (
    dataclass, 
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
# ----------------------------------------------------------------- LIBRARY CONFIGURATION

@dataclass(slots=True, frozen=True)
class LibraryConfiguration:
    """
    """
    pass