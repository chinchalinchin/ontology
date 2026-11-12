"""
@domain.model
@app.asset
@app.core
@asset.state
@workflow.plot
@workflow.seasons

# Ontology: Source - app.models.state.core

Core State Models.
"""
# Standard Libraries
from typing import (
    Optional, 
    List
)
from dataclasses import (
    dataclass,
    field
)

# Application Libraries
from app.models.adapters import Enumerated
from app.static.semantics import (
    Actions, 
    Directions,
    Cycles,
    Seasons,
    Hands
)

# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class RadialParameters:
    radius: int = 30

@dataclass(slots=True)
class FearParameters(RadialParameters):
    limit: float = 0.50
    enemy: int = 5

@dataclass(slots=True)
class MutatorTriggers:
    animated: bool = False
    frightened: bool = False
    dead: bool = False
    vision: bool = False
    submerged: bool = False
    falling: bool = False

@dataclass(slots=True)
class MutatorParameters:
    fear: Optional[FearParameters] = field(default_factory=FearParameters)
    vision: Optional[RadialParameters] = field(default_factory=RadialParameters)
    action: Optional[RadialParameters] = field(default_factory=RadialParameters)
    squeeze: Optional[RadialParameters] = field(default_factory=RadialParameters)
    descension: Optional[float] = 0.0
    hand: Optional[Enumerated[Hands]] = None

@dataclass(slots=True)
class Mutators:
    triggers: MutatorTriggers = field(default_factory=MutatorTriggers)
    parameters: Optional[MutatorParameters] = None

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------- CORE ASSET STATES
# ---------------------------------------------------------------------------------------

class NoState:
    pass

@dataclass(slots=True)
class AssetState:
    id: str
    name: Optional[str] = None
    layer: Optional[str] = None
    elevation: Optional[int] = 0
    anchor: Optional[int] = 0
    mutators: Mutators = field(default_factory=Mutators)

@dataclass(slots=True)
class AnimationState:
    action: Enumerated[Actions] = Actions.WALK.value
    direction: Enumerated[Directions] = Directions.DOWN.value
    frame: int = 0
    tick: int = 1

@dataclass(slots=True)
class PlotState:
    current: Optional[str] = None
    previous: List[str] = field(default_factory=list)

@dataclass(slots=True)
class CalendarState:
    year: int = 1
    season: Enumerated[Seasons] = Seasons.SPRING.value
    cycle: Enumerated[Cycles]= Cycles.ONSET.value
    period: int = 0
    elapsed: float = 0.0