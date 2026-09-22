"""
# Ontology: app.game.logic.relations.shorelines

Relational lookup table mapping terrain tiles and fluids to shoreline asset IDs.
"""
from __future__ import annotations

# Standard Libraries
from typing import (
    Dict,
    Tuple,
    Optional,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from app.models.properties import GeographyProperties

class ShorelineIndex:
    """
    Relational lookup table mapping (tile_id, fluid_id) tuples to shoreline asset IDs.
    """
    _entries: Dict[Tuple[str, Optional[str]], str]

    def __init__(self, entries: Dict[Tuple[str, Optional[str]], str]):
        self._entries = entries

    @classmethod
    def from_properties(cls, shorelines: Dict[str, GeographyProperties]) -> ShorelineIndex:
        """
        Compiles a ShorelineIndex from the dictionary of shoreline geography properties.
        """
        entries: Dict[Tuple[str, Optional[str]], str] = {
            (prop.tile, prop.fluid): asset_id
            for asset_id, prop in shorelines.items()
        }
        return cls(entries)

    def resolve(self, tile_id: str, fluid_id: Optional[str] = None) -> Optional[str]:
        # 1. Exact match: (tile, fluid)
        if fluid_id and (tile_id, fluid_id) in self._entries:
            return self._entries[(tile_id, fluid_id)]
        # 2. Substrate fallback: (tile, None)
        return self._entries.get((tile_id, None))