"""
@domain.model
@app.core

# Ontology: Source - app.models.core

Models for typing the core Application Models.
"""
from dataclasses import dataclass

# Application Libraries
from app.static.semantics import Alignments
from app.models.adapters import Enumerated

# ---------------------------------------------------------

@dataclass(slots=True, frozen=True)
class AxisAlignment:
    horizontal: Enumerated[Alignments] = Alignments.CENTER.value
    vertical: Enumerated[Alignments] = Alignments.CENTER.value
