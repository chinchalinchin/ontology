"""
# Ontology: app.assets.frames

Package for Geography Frame implementations. 

"""
# Stamdard Libraries
from typing import (
    List,
    Tuple,
    Dict
)
import logging

# Application Libraries
import app.config.settings as settings
from app.config.enums import (
    Directions,
)
from app.assets.base import Frame
from app.models.state import (
    AssetState, 
    ShorelineState
)
from app.models.properties import (
    AssetProperties,
    GeographyProperties
)

logger = logging.getLogger(__name__)

class ShorelineFrame(Frame):
    """
    ## ShorelineFrame

    Indexes 4 cardinal orientation rows (North, West, South, East) and distal
    fractional slices, emitting repeating tile offsets along the margin length.
    """

    CARDINAL_ROWS = {
        Directions.UP.value: 0,     # NORTH (Land North, Water South)
        Directions.LEFT.value: 1,   # WEST  (Land West, Water East)
        Directions.DOWN.value: 2,   # SOUTH (Land South, Water North)
        Directions.RIGHT.value: 3    # EAST  (Land East, Water West)
    }

    def __init__(self, tile_w: int = 32, tile_l: int = 32):
        self.tile_w = tile_w
        self.tile_l = tile_l

    def channels(self, 
        id: str, 
        state: AssetState,
        properties: AssetProperties
    ) -> List[Tuple]:
        return []

    def index(self, id: str, properties: GeographyProperties) -> Dict[str, Tuple[int, int, int, int]]:
        """
        Indexes 4 cardinal rows (UP, LEFT, DOWN, RIGHT) alongside forward
        fractional remainder slices into the Registry crop map.
        """
        w = properties.dimensions.w
        l = properties.dimensions.l
        self.tile_w = w
        self.tile_l = l
        crops: Dict[str, Tuple[int, int, int, int]] = {}

        for direction, row in self.CARDINAL_ROWS.items():
            base_y = row * l

            # 1. Base full tile key: {id}-{direction}
            full_key = settings.SEPARATOR.join([id, direction])
            crops[full_key] = (0, base_y, w, l)

            # 2. Fractional slices along the active propagation axis
            if direction in (Directions.UP.value, Directions.DOWN.value):
                # Horizontal bank: sliced along width W
                for s in range(1, w):
                    slice_key = settings.SEPARATOR.join([id, direction, str(s)])
                    crops[slice_key] = (0, base_y, s, l)
            else:
                # Vertical bank: sliced along length L
                for s in range(1, l):
                    slice_key = settings.SEPARATOR.join([id, direction, str(s)])
                    crops[slice_key] = (0, base_y, w, s)

        return crops

    def keys(self, id: str, state: ShorelineState) -> List[Tuple[str, int, int]]:
        """
        Emits repeated full-tile keys along state.length and a terminal fractional
        slice remainder.
        """
        length = state.length
        if length <= 0:
            return []

        direction = state.orientation
        full_key = settings.SEPARATOR.join([id, direction])
        w = self.tile_w
        l = self.tile_l
        frame_keys: List[Tuple[str, int, int]] = []

        if direction in (Directions.UP.value, Directions.DOWN.value):
            full_tiles = length // w
            rem = length % w

            for i in range(full_tiles):
                frame_keys.append((full_key, i * w, 0))

            if rem > 0:
                slice_key = settings.SEPARATOR.join([id, direction, str(rem)])
                frame_keys.append((slice_key, full_tiles * w, 0))

        elif direction in (Directions.LEFT.value, Directions.RIGHT.value):
            full_tiles = length // l
            rem = length % l

            for i in range(full_tiles):
                frame_keys.append((full_key, 0, i * l))

            if rem > 0:
                slice_key = settings.SEPARATOR.join([id, direction, str(rem)])
                frame_keys.append((slice_key, 0, full_tiles * l))

        return frame_keys