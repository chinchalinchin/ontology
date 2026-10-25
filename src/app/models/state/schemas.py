"""
@domain.model
@app.core
@app.schema
@asset.state

# Ontology: Source - app.models.state.schemas

State Schema Models.
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
    MotiveState,
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
    SheetState,
    CraftState,
    ResourceState,
    PlatformState,
    StairState
)

# --------------------------------------------------------------
# ------------------------------------------------- SCHEMA NODES
# --------------------------------------------------------------

@dataclass(slots=True)
class CraftStateInstances:
    stairs: List[StairState] = field(default_factory=list)
    struts: List[CraftState] = field(default_factory=list)
    bridges: List[CraftState] = field(default_factory=list)
    platforms: List[PlatformState] = field(default_factory=list)

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
class ObjectStateInstances:
    chests: List[ContainerState] = field(default_factory=list)
    crates: List[MotiveState] = field(default_factory=list)
    doors: List[DoorState] = field(default_factory=list)
    gates: List[SwitchState] = field(default_factory=list)
    obstacles: List[MotiveState] = field(default_factory=list)
    plates: List[SwitchState] = field(default_factory=list)
    signs: List[DialogueState] = field(default_factory=list)
    rafts: List[MotiveState] = field(default_factory=list)
    
@dataclass(slots=True)
class ResourceStateInstances:
    crops: List[ResourceState] = field(default_factory=list)
    ore: List[ResourceState] = field(default_factory=list)
    trees: List[ResourceState] = field(default_factory=list)
    
@dataclass(slots=True)
class SheetStateInstances:
    sprites: List[SpriteState] = field(default_factory=list)
    players: List[SheetState] = field(default_factory=list)

@dataclass(slots=True)
class TileStateInstances:
    environ: List[MultiplierState] = field(default_factory=list)
    canopy: List[MultiplierState] = field(default_factory=list)
    grid: List[MultiplierState] = field(default_factory=list)


# --------------------------------------------------------------
# -------------------------------------------------- ROOT SCHEMA
# --------------------------------------------------------------

@dataclass(slots=True)
class StateSchema:
    # NOTE: ASSET STATES
    crafts: CraftStateInstances = field(default_factory=CraftStateInstances)
    cursors: CursorStateInstances = field(default_factory=CursorStateInstances)
    effects: EffectStateInstances = field(default_factory=EffectStateInstances)
    objects: ObjectStateInstances = field(default_factory=ObjectStateInstances)
    resources: ResourceStateInstances = field(default_factory=ResourceStateInstances)
    sheets: SheetStateInstances = field(default_factory=SheetStateInstances)
    tiles: TileStateInstances = field(default_factory=TileStateInstances)
    ## NOTE: VIRTUALIZED ASSETS
    compositions: List[PropertyState] = field(default_factory=list)
    # NOTE: BOARD STATES
    plots: PlotState = field(default_factory=PlotState)
    calendar: CalendarState = field(default_factory=CalendarState)