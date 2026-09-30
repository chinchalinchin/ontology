"""
# Ontology: app.models.state.crafts

Python data models for typing Craft state attributes.
"""
# Standard Libraries
from typing import ( 
    Optional,
)
from dataclasses import (
    dataclass,
)

# Application Libraries
from app.config.enums import (
    Orientations
)
from app.models.adapters import (
    PydanticPosition as Position, 
    PydanticMultiple as Multiple
)
from app.models.state.core import (
    AssetState,
)

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------------- CRAFT STATES
# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class PropertyState(AssetState):
    owner: Optional[str] = None
    position: Optional[Position] = None # type: ignore

@dataclass(slots=True)
class BridgeState(AssetState):
    # Overrides to enforce Z-ordering: 
    #       Fluid (-1) < Shoreline (0) < Bridge (1) < Entities (>1)
    height: Optional[int] = 0
    depth: int = 1
    # Bridge Fields
    position: Optional[Position] = None # type: ignore
    orientation: str = Orientations.HORIZONTAL.value
    multiple: Optional[Multiple] = None # type: ignore
    owner: Optional[str] = None