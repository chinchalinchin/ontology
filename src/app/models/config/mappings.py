
"""
@domain.model
@domain.user
@app.config
@app.devices

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
from app.models.adapters import Enumerated
from app.models.config.core import Configuration

# ---------------------------------------------------------

@dataclass(slots=True, frozen=True)
class WorldMapping:
    menus: Dict[Enumerated[Menus], int] = field(default_factory=dict)
    intentions: Dict[Enumerated[Intentions], int] = field(default_factory=dict)
    goals: Dict[Enumerated[PlayerGoals], int] = field(default_factory=dict)

@dataclass(slots=True, frozen=True)
class MenuMapping:
    traversal: Dict[Enumerated[Traversal], int] = field(default_factory=dict)
    interactions: Dict[Enumerated[Interactions], int] = field(default_factory=dict)

@dataclass(slots=True, frozen=True)
class DeviceMapping:
    world: WorldMapping
    menu: MenuMapping

# ---------------------------------------------------------

@dataclass(slots=True, frozen=True)
class MappingConfiguration(Configuration):
    keyboard: DeviceMapping
    controller: DeviceMapping = None