"""
# Ontology: app.game.logic.relations.shorelines

Relational index mapping terrain tiles, fluids, and seasons to shoreline asset IDs.
"""
from __future__ import annotations

# Standard Libraries
from typing import (
    Dict,
    Tuple,
    Optional,
    Any,
    TYPE_CHECKING
)
import logging

if TYPE_CHECKING:
    from app.models.properties import GeographyProperties

logger = logging.getLogger(__name__)


class ShorelineIndex:
    """
    Relational secondary index mapping (tile_id, fluid_id, [season]) to shoreline Asset ID.
    Supports multi-level fallback:
    1. (tile_id, fluid_id, season)
    2. (tile_id, fluid_id)
    3. (tile_id, None, season)
    4. (tile_id, None)
    """
    _map: Dict[Tuple[str, Optional[str], Optional[str]], str]
    _fallback_map: Dict[Tuple[str, Optional[str]], str]

    def __init__(self, relations: Optional[Dict[Any, str]] = None):
        self._map = {}
        self._fallback_map = {}
        if relations:
            for key, shoreline_id in relations.items():
                self.register(key, shoreline_id)

    @classmethod
    def from_properties(cls, shorelines: Dict[str, GeographyProperties]) -> ShorelineIndex:
        """
        Factory constructor compiling relational definitions from geography property schemas.
        """
        index = cls()
        for shoreline_id, props in shorelines.items():
            season = getattr(props, "season", None)
            if season:
                index.register((props.tile, props.fluid, season), shoreline_id)
            index.register((props.tile, props.fluid), shoreline_id)
        return index

    def register(self, key: Tuple, shoreline_id: str) -> None:
        """
        Registers a composite relation tuple to target shoreline asset ID.
        """
        if len(key) == 3:
            tile_id, fluid_id, season = key
            self._map[(tile_id, fluid_id, season)] = shoreline_id
        elif len(key) == 2:
            tile_id, fluid_id = key
            self._fallback_map[(tile_id, fluid_id)] = shoreline_id

    def resolve(
        self,
        tile_id: str,
        fluid_id: Optional[str] = None,
        season: Optional[str] = None
    ) -> Optional[str]:
        """
        Resolves the appropriate shoreline asset ID across compound keys with seasonal fallback.
        """
        # 1. Primary seasonal resolution: (tile, fluid, season)
        if season is not None:
            seasonal_key = (tile_id, fluid_id, season)
            if seasonal_key in self._map:
                return self._map[seasonal_key]

            # Seasonal fallback without fluid constraint
            if fluid_id is not None:
                dry_seasonal_key = (tile_id, None, season)
                if dry_seasonal_key in self._map:
                    return self._map[dry_seasonal_key]

        # 2. Base relational fallback: (tile, fluid)
        base_key = (tile_id, fluid_id)
        if base_key in self._fallback_map:
            return self._fallback_map[base_key]

        # 3. Base fallback without fluid constraint: (tile, None)
        if fluid_id is not None:
            dry_base_key = (tile_id, None)
            if dry_base_key in self._fallback_map:
                return self._fallback_map[dry_base_key]

        return None