"""
@domain.model
@app.config
@category.widgets

# Ontology: Source - app.models.config.menus

Models for typing the configuration attributes of Menus.
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
