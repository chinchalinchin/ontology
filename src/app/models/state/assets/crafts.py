"""
@domain.model
@app.asset
@asset.state
@category.crafts
@modality.material
@workflow.compositions

# Ontology: Source - app.models.state.crafts

Craft State models.
"""
# Standard Libraries
from typing import ( 
    Optional,
    Union
)
from dataclasses import dataclass

# Application Libraries
from app.static.semantics import (
    # ---- BLUEPRINT SCHEMAS
    Buildings,
    Corridors,
    Columns,
    Enclosures,
    Inclines,
    Decor,
    Directions,
    Orientations,
    # --- MATERIAL GENERA
    Ceramics,
    Geologics,
    Organics,
    Metallics,
    Chromatics
)
from app.models.adapters import (
    PydanticPosition as Position, 
    PydanticMultiple as Multiple
)
from app.models.state.core import AssetState

# ------------------------------------------------------------

@dataclass(slots=True)
class CraftState(AssetState):
    position: Optional[Position] = None # type: ignore
    multiple: Optional[Multiple] = None # type: ignore
    material: Optional[Union[
        Ceramics,
        Chromatics,
        Geologics,
        Organics,
        Metallics
    ]] = None
    blueprint: Optional[Union[
        Buildings,
        Corridors,
        Columns,
        Decor,
        Directions,
        Enclosures,
        Inclines,
        Orientations,
    
    ]] = None


@dataclass(slots=True)
class PropertyState(CraftState):
    owner: Optional[str] = None


@dataclass(slots=True)
class StairState(CraftState):
    """
    State representation for walkable incline transitions.
    """
    delta: int = 1

    @property
    def direction(self) -> Optional[str]:
        return self.blueprint