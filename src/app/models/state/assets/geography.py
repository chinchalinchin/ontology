"""
@asset.state
@category.geography
@workflow.generation

# Ontology: app.models.state.geography

Geography State Models.
"""
# Standard Libraries
from typing import ( 
    List,
    Optional,
    Tuple
)
from dataclasses import dataclass, field

# Application Libraries
from app.static.semantics import (
    Directions,
    Seasons
)
from app.models.adapters import (
    PydanticPosition as Position, 
    PydanticHitbox as Hitbox
)
from app.models.state.core import (
    AssetState
)

# ------------------------------------------------------------

@dataclass(slots=True)
class ShorelineState(AssetState):
    # Shoreline fields
    position: Optional[Position] = None  # type: ignore
    orientation: Directions = Directions.DOWN.value
    season: Seasons = Seasons.SPRING.value
    length: int = 0
    thickness: int = 8
    bidirectional: bool = True
    hitboxes: List[Hitbox] = field(default_factory=list)  # type: ignore
    _keys: Optional[List[Tuple[str, int, int]]] = None