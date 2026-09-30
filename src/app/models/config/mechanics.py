"""
# Ontology: app.models.config.mechanics

Models for typing the configuration attributes of Mechanics.
"""
# Standard Libraries
from typing import (
    List, 
)
from dataclasses import (
    dataclass, 
    field
)

# Application Libraries
from app.models.config.core import Configuration

# ---------------------------------------------------------------------------------------
# --------------------------------------------------------------- MECHANICS CONFIGURATION
# ---------------------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class MechanicsInstance:
    key: str
    executors: List[str] = field(default_factory = list)
    relations: List[str] = field(default_factory=list)

@dataclass(slots=True, frozen=True)
class MechanicsConfiguration(Configuration):
    core: List[MechanicsInstance] = field(default_factory=list)
    world: List[MechanicsInstance] = field(default_factory=list)
