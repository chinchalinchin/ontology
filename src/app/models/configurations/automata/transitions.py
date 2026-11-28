"""
@domain.model
@domain.automata
@app.config
@modality.intention
@modality.lifespan

# Ontology: Source - app.models.configurations.automata.transitions

Models for typing the configuration attributes of automaton transition.
"""
# Standard Libraries
from typing import List
from dataclasses import (
    dataclass, 
    field
)

# Application Libraries
from app.models.configurations import Configuration


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
