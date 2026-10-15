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
from app.models.state.core import (
    PlotState,
    CalendarState
)
from app.models.state.assets import (
    MotorState,
    AttachmentState,
    MultiplierState,
    ContainerState,
    PositionalState,
    DoorState,
    SwitchState,
    PropertyState,
    DialogueState,
    EffectState,
    HazardState,
    ReactableState,
    CollectableState,
    FluidState,
    SpriteState,
    PlayerState,
    OrientedState,
    ResourceState,
    PlatformState,
    StairState
)

# --------------------------------------------------------------
# ------------------------------------------------- SCHEMA NODES
# --------------------------------------------------------------

@dataclass(slots=True)
class TileStateInstances:
    environ: List[MultiplierState] = field(default_factory=list)
    canopy: List[MultiplierState] = field(default_factory=list)
    grid: List[MultiplierState] = field(default_factory=list)

@dataclass(slots=True)
class ObjectStateInstances:
    chests: List[ContainerState] = field(default_factory=list)
    crates: List[PositionalState] = field(default_factory=list)
    doors: List[DoorState] = field(default_factory=list)
    gates: List[SwitchState] = field(default_factory=list)
    obstacles: List[PositionalState] = field(default_factory=list)
    plates: List[SwitchState] = field(default_factory=list)
    signs: List[DialogueState] = field(default_factory=list)
    rafts: List[PositionalState] = field(default_factory=list)
    
@dataclass(slots=True)
class CraftStateInstances:
    stairs: List[StairState] = field(default_factory=list)
    struts: List[PropertyState] = field(default_factory=list)
    bridges: List[OrientedState] = field(default_factory=list)
    platforms: List[PlatformState] = field(default_factory=list)
    railings: List[OrientedState] = field(default_factory=list)
    
@dataclass(slots=True)
class ResourceStateInstances:
    crops: List[ResourceState] = field(default_factory=list)
    ore: List[ResourceState] = field(default_factory=list)
    trees: List[ResourceState] = field(default_factory=list)
    
@dataclass(slots=True)
class CursorStateInstances:
    expressions: List[AttachmentState] = field(default_factory=list)
    projectiles: List[MotorState] = field(default_factory=list)

@dataclass(slots=True)
class EffectStateInstances:
    hazards: List[HazardState] = field(default_factory=list)
    passive: List[EffectState] = field(default_factory=list)
    collectables: List[CollectableState] = field(default_factory=list)
    reactables: List[ReactableState] = field(default_factory=list)
    fluids: List[FluidState] = field(default_factory=list)

@dataclass(slots=True)
class SheetStateInstances:
    sprites: List[SpriteState] = field(default_factory=list)
    players: List[PlayerState] = field(default_factory=list)


# --------------------------------------------------------------
# -------------------------------------------------- ROOT SCHEMA
# --------------------------------------------------------------

@dataclass(slots=True)
class StateSchema:
    # ASSET STATES
    tiles: TileStateInstances = field(default_factory=TileStateInstances)
    objects: ObjectStateInstances = field(default_factory=ObjectStateInstances)
    crafts: CraftStateInstances = field(default_factory=CraftStateInstances)
    cursors: CursorStateInstances = field(default_factory=CursorStateInstances)
    effects: EffectStateInstances = field(default_factory=EffectStateInstances)
    resources: ResourceStateInstances = field(default_factory=ResourceStateInstances)
    sheets: SheetStateInstances = field(default_factory=SheetStateInstances)
    ## VIRTUALIZED ASSETS
    compositions: List[PropertyState] = field(default_factory=list)
    # BOARD STATES
    plots: PlotState = field(default_factory=PlotState)
    calendar: CalendarState = field(default_factory=CalendarState)