"""
# Ontology: app.models.groups

"""
# Standard Libraries
from typing import Dict
from dataclasses import dataclass, field

# Application Libraries
from app.models.properties import (
    AssetProperties,
    SheetProperties,
    CursorProperties,
    CraftProperties,
    EffectProperties
)

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------------- GROUP MODELS
# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class EquipmentGroup(AssetProperties):
    """
    """
    armor: Dict[str, SheetProperties]
    tools: Dict[str, SheetProperties]
    utilities: Dict[str, SheetProperties]
    weapons: Dict[str, SheetProperties]
    shields: Dict[str, SheetProperties] = field(default_factory=dict)

@dataclass(slots=True)
class SpawnableGroup:
    """
    """
    projectiles: Dict[str, CursorProperties]
    expressions: Dict[str, CursorProperties]
    temporary: Dict[str, EffectProperties]
    struts: Dict[str, CraftProperties]