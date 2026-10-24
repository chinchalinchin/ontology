
"""
@app.config
@app.input

# Ontology: Source - app.models.config.mappings

Device Mapping Configuration Models.
"""
# Standard Libraries
from typing import Dict
from dataclasses import (
    dataclass, 
    field
)

# Application Libraries
from app.static.semantics import (
    Intentions,
    PlayerGoals,
    Menus,
    Interactions,
    Traversal
)
from app.models.config.core import Configuration

# ---------------------------------------------------------

@dataclass(slots=True, frozen=True)
class WorldMapping:
    menus: Dict[Menus, int] = field(default_factory=dict)
    intentions: Dict[Intentions, int] = field(default_factory=dict)
    goals: Dict[PlayerGoals, int] = field(default_factory=dict)

@dataclass(slots=True, frozen=True)
class MenuMapping:
    traversal: Dict[Traversal, int] = field(default_factory=dict)
    interactions: Dict[Interactions, int] = field(default_factory=dict)

@dataclass(slots=True, frozen=True)
class DeviceMapping:
    world: WorldMapping
    menu: MenuMapping

# ---------------------------------------------------------

@dataclass(slots=True, frozen=True)
class MappingConfiguration(Configuration):
    keyboard: DeviceMapping
    controller: DeviceMapping = None