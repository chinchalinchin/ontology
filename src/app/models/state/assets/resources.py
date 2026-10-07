"""
# Ontology: app.models.state.resources

Python data models for typing Resource state attributes.
"""
# Standard Libraries
from typing import Optional
from dataclasses import dataclass

# Application Libraries
from app.config.enums.assets import (
    AnnualStages
)
from app.models.adapters import (
    PydanticPosition as Position, 
    PydanticMultiple as Multiple, 
)
from app.models.state.core import (
    AssetState
)

# ---------------------------------------------------------------------------------------
# ----------------------------------------------------------------------- RESOURCE STATES
# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class ResourceState(AssetState):
    """
    Unified state representation for Resource entities across all lifespans.
    """
    stage: str = AnnualStages.STUMP.value
    position: Optional[Position] = None  # type: ignore
    retention: float = 0.0
    moisture_flux: float = 0.0
    harvested: bool = False              # For harvestable bloom states