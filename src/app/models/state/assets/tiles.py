"""
@asset.state
@category.tiles

# Ontology: app.models.state.tiles

Tile State Models.
"""
# Standard Libraries
from typing import Optional
from dataclasses import dataclass

# Application Libraries
from app.models.adapters import (
    PydanticPosition as Position, 
    PydanticMultiple as Multiple, 
)
from app.models.state.core import AssetState

# ------------------------------------------------------------

@dataclass(slots=True)
class MultiplierState(AssetState):
    position: Optional[Position] = None # type: ignore
    multiple: Optional[Multiple] = None # type: ignore