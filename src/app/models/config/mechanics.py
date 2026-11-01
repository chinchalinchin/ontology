"""
@app.core
@app.config
@app.mechanics

# Ontology: Source - app.models.config.mechanics

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
from app.models.adapters import Enumerated
from app.static.semantics import (
    Executors,
    Relations
)
# ---------------------------------------------------------

@dataclass(slots=True, frozen=True)
class MechanicsInstance:
    key: str
    executors: List[Enumerated[Executors]] = field(default_factory = list)
    relations: List[Enumerated[Relations]] = field(default_factory=list)

@dataclass(slots=True, frozen=True)
class MechanicsConfiguration(Configuration):
    core: List[MechanicsInstance] = field(default_factory=list)
    world: List[MechanicsInstance] = field(default_factory=list)
