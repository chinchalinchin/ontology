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
# -------------------------------------------------------------------- CORE ASSET STATES

class NoState:
    pass

@dataclass(slots=True)
class AssetState:
    id: str
    name: Optional[str] = None
    layer: Optional[str] = None
    depth: int = 0
    height: Optional[Union[int, str]] = None

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