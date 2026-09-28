"""
# Ontology: app.models.state.core

Python data models for typing Asset state attributes.
"""
# Standard Libraries
from typing import (
    Optional, 
    Union, 
    List
)
from dataclasses import (
    dataclass,
    field
)

# Application Libraries
from app.config.enums import (
    Actions, 
    Directions,
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

@dataclass(slots=True)
class MutatorParameters:
    fear: Optional[FearParameters] = field(default_factory=FearParameters)
    vision: Optional[RadialParameters] = field(default_factory=RadialParameters)
    action: Optional[RadialParameters] = field(default_factory=RadialParameters)
    squeeze: Optional[RadialParameters] = field(default_factory=RadialParameters)
    
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
    depth: int = 0
    height: Optional[Union[int, str]] = None
    mutators: Mutators = field(default_factory=Mutators)

@dataclass(slots=True)
class AnimationState:
    action: str = Actions.WALK.value
    direction: str = Directions.DOWN.value
    frame: int = 0
    tick: int = 1

@dataclass(slots=True)
class PlotState:
    current: Optional[str] = None
    previous: List[str] = field(default_factory=list)