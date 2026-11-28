"""
@domain.model
@domain.automata
@app.config
@modality.intention

# Ontology: Source - app.models.configurations.automata.goals

Models for typing the configuration attributes of automaton goals.
"""
# Standard Libraries
from typing import List
from dataclasses import dataclass

# Application Libraries
from app.models.adapters import Enumerated
from app.models.configurations import Configuration
from app.static.semantics import (
    Reflexes,
    Responses,
)

# ---------------------------------------------------------

@dataclass(slots=True, frozen=True)
class GoalConfiguration(Configuration):
    """
    """
    reflexes: List[Enumerated[Reflexes]]
    responses: List[Enumerated[Responses]]
    conditions: List[str]