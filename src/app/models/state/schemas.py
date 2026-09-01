"""
# Ontology: app.models.state.schemas

Python data models for typing the entire Asset Hierarchy state attributes.
"""
# Standard Libraries
from typing import List
from dataclasses import (
    dataclass, 
    field
)

# Application Libraries
from app.models.state.objects import (
    MultiplierState,
    ContainerState,
    PositionalState,
    DoorState,
    SwitchState,
    PropertyState,
    MotorState,
    AnimatorState
)
from app.models.state.sprites import (
    SpriteState,
    PlayerState
)

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------------- ROOT SCHEMAS

@dataclass(slots=True)
class TileStateInstances:
    back: List[MultiplierState] = field(default_factory=list)
    fore: List[MultiplierState] = field(default_factory=list)

@dataclass(slots=True)
class ObjectStateInstances:
    chests: List[ContainerState] = field(default_factory=list)
    crates: List[PositionalState] = field(default_factory=list)
    doors: List[DoorState] = field(default_factory=list)
    gates: List[SwitchState] = field(default_factory=list)
    plates: List[SwitchState] = field(default_factory=list)

@dataclass(slots=True)
class CraftStateInstances:
    struts: List[PropertyState] = field(default_factory=list)

@dataclass(slots=True)
class CursorStateInstances:
    expressions: List[PositionalState] = field(default_factory=list)
    projectiles: List[MotorState] = field(default_factory=list)

@dataclass(slots=True)
class EffectStateInstances:
    temporary: List[PositionalState] = field(default_factory=list)
    persistent: List[AnimatorState] = field(default_factory=list)

@dataclass(slots=True)
class SheetStateInstances:
    pixies: List[AnimatorState] = field(default_factory=list)
    sprites: List[SpriteState] = field(default_factory=list)
    players: List[PlayerState] = field(default_factory=list)

@dataclass(slots=True)
class StateSchema:
    tiles: TileStateInstances = field(default_factory=TileStateInstances)
    objects: ObjectStateInstances = field(default_factory=ObjectStateInstances)
    crafts: CraftStateInstances = field(default_factory=CraftStateInstances)
    cursors: CursorStateInstances = field(default_factory=CursorStateInstances)
    effects: EffectStateInstances = field(default_factory=EffectStateInstances)
    sheets: SheetStateInstances = field(default_factory=SheetStateInstances)
    compositions: List[PropertyState] = field(default_factory=list)