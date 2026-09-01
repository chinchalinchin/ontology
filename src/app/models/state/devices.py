"""
# Ontology: app.models.state.devices

Python data models for typing Device polling payloads.
"""
# Standard Libraries
from typing import (
    List,
    Optional, 
)
from dataclasses import dataclass, field


@dataclass(slots=True)
class WorldPayload:
    intention: Optional[str] = None
    menu: Optional[str] = None
    goals: List[str] = field(default_factory=list)

@dataclass(slots=True)
class MenuPayload:
    traversal: Optional[str] = None
    interaction: Optional[str] = None

@dataclass(slots=True)
class DevicePayload:
    world: WorldPayload
    menu: MenuPayload