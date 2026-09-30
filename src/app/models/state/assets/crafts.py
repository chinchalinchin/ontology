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
from app.models.adapters import (
    PydanticPosition as Position, 
)
from app.models.state.core import (
    AssetState,
)

# Cython Libraries

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------------- CRAFT STATES
# ---------------------------------------------------------------------------------------


@dataclass(slots=True)
class PropertyState(AssetState):
    owner: Optional[str] = None
    position: Optional[Position] = None # type: ignore
