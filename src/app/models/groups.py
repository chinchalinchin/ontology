"""
# Ontology: app.models.groups

Dataclasses for grouping asset properties for injection into generators and registries.
"""
from __future__ import annotations

# Standard Libraries
from typing import Dict
from dataclasses import dataclass, field

# Application Libraries
from app.models.properties import (
    CursorProperties,
    EffectProperties,
    CraftProperties,
    GeographyProperties,
    SheetProperties
)

@dataclass(slots=True)
class EquipmentGroup:
    armor: Dict[str, SheetProperties] = field(default_factory=dict)
    weapons: Dict[str, SheetProperties] = field(default_factory=dict)
    tools: Dict[str, SheetProperties] = field(default_factory=dict)
    utilities: Dict[str, SheetProperties] = field(default_factory=dict)
    shields: Dict[str, SheetProperties] = field(default_factory=dict)


@dataclass(slots=True)
class SpawnableGroup:
    projectiles: Dict[str, CursorProperties] = field(default_factory=dict)
    expressions: Dict[str, CursorProperties] = field(default_factory=dict)
    collectables: Dict[str, EffectProperties] = field(default_factory=dict)
    hazards: Dict[str, EffectProperties] = field(default_factory=dict)
    passive: Dict[str, EffectProperties] = field(default_factory=dict)
    struts: Dict[str, CraftProperties] = field(default_factory=dict)
    shorelines: Dict[str, GeographyProperties] = field(default_factory=dict)