"""
# Ontology: app.models.config.core

Models for typing the configuration attributes of Mechanics, Menus and other game components. See documentation for a more in-depth explanation of each field and its purpose. 
"""
# Standard Libraries
from typing import (
    Dict, 
    List, 
    Optional
)
from dataclasses import (
    dataclass, 
    field
)

# Application Libraries
from app.models.state import (
    PropertyState, 
    StateSchema
)
from app.models.properties import Action

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------ CONFIGURATION MODELS
# ---------------------------------------------------------------------------------------

class Configuration:
    pass

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------ ACTION CONFIGURATION

@dataclass(slots=True)
class ActionConfiguration(Configuration):
    id: str
    data: Dict[str, Action]
    
# ---------------------------------------------------------------------------------------
# --------------------------------------------------------------- INTENTION CONFIGURATION

@dataclass(slots=True)
class IntentionConfiguration(Configuration):
    """
    """
    next: str
    conditions: List[str] = field(default_factory=list)

# ---------------------------------------------------------------------------------------
# --------------------------------------------------------------- INTENTION CONFIGURATION

@dataclass(slots=True)
class MechanicsConfiguration(Configuration):
    core: List[str] = field(default_factory=list)
    world: List[str] = field(default_factory=list)

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------- COMPOSITION CONFIGURATION

@dataclass(slots=True)
class CompositionPseudoState:
    strut: PropertyState
    components: StateSchema

@dataclass(slots=True)
class CompositionConfiguration(Configuration):
    root: CompositionPseudoState
    branches: Optional[List[CompositionPseudoState]] = field(default_factory=list)