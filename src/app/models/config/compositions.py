"""
# Ontology: app.models.config.compositions

Models for typing the configuration attributes of Compositions.
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
from app.models.state import (
    PropertyState, 
    StateSchema
)
from app.models.config.core import Configuration

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------- COMPOSITION CONFIGURATION
# ---------------------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class CompositionPseudoState:
    strut: PropertyState
    components: StateSchema

@dataclass(slots=True, frozen=True)
class CompositionConfiguration(Configuration):
    root: CompositionPseudoState
    branches: Optional[List[CompositionPseudoState]] = field(default_factory=list)