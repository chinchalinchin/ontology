"""
# Ontology: app.models.config.transitions

Models for typing the transition configuration attributes of game components.
"""
# Standard Libraries
from typing import (
    List, 
    Optional
)
from dataclasses import (
    dataclass, 
    field
)

# Application Libraries
from app.models.config import Configuration


# ---------------------------------------------------------

@dataclass(slots=True, frozen=True)
class IntentionConfiguration(Configuration):
    """
    """
    next: str
    conditions: List[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class PlotConfiguration(Configuration):
    """
    """
    next: str
    conditions: List[str] = field(default_factory=list)


@dataclass(slots=True)
class StageConfiguration(Configuration):
    next: str
    conditions: List[str] = field(default_factory=list)
    phase: Optional[str] = None