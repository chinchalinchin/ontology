from typing import (
    Dict,
    Tuple,
    Optional
)

class ShorelineIndex:
    """
    Relational lookup table mapping (tile_id, fluid_id) tuples to shoreline asset IDs.
    """
    def __init__(self, entries: Dict[Tuple[str, Optional[str]], str]):
        self._entries = entries

    def resolve(self, tile_id: str, fluid_id: Optional[str] = None) -> Optional[str]:
        # 1. Exact match: (tile, fluid)
        if fluid_id and (tile_id, fluid_id) in self._entries:
            return self._entries[(tile_id, fluid_id)]
        # 2. Substrate fallback: (tile, None)
        return self._entries.get((tile_id, None))