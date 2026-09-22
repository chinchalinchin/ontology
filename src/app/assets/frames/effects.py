"""
# Ontology: app.assets.frames.effects

Package for Effect Frame implementations. 

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
    Directions
)
from app.assets.base import Frame
from app.models.state import (
    AssetState, 
    FluidState
)
from app.models.properties import (
    AssetProperties,
    EffectProperties
)

logger = logging.getLogger(__name__)


class FluidFrame(Frame):
    """
    ## FluidFrame

    Translates physical stream lengths and annular pooling bounds into full-tile
    keys and directional sub-pixel fractional slices across animation states.
    """

    def __init__(self, tile_w: int = 32, tile_l: int = 32):
        self.tile_w = tile_w
        self.tile_l = tile_l

    def channels(self, 
        id: str, 
        state: AssetState,
        properties: AssetProperties
    ) -> List[Tuple]:
        return []
    
    def index(self, id: str, properties: EffectProperties) -> Dict[str, Tuple[int, int, int, int]]:
        """
        Pre-indexes full animation frames alongside multi-axis forward and reverse
        truncated fractional slices into the Registry crop map.
        """
        w = properties.dimensions.w
        l = properties.dimensions.l
        count = max(1, properties.count)

        self.tile_w = w
        self.tile_l = l
        crops: Dict[str, Tuple[int, int, int, int]] = {}

        for f in range(count):
            base_x = f * w
            frame_str = str(f)

            # 1. Base full tile key
            full_key = settings.SEPARATOR.join([id, frame_str])
            crops[full_key] = (base_x, 0, w, l)

            # 2. Vertical forward slicing: Down (anchored at origin)
            for s in range(1, l):
                slice_key = settings.SEPARATOR.join([
                    id, 
                    frame_str, 
                    Directions.DOWN.value, 
                    str(s)
                ])
                crops[slice_key] = (base_x, 0, w, s)
                crops[settings.SEPARATOR.join([
                    id, 
                    frame_str,
                    Directions.DOWN.value, 
                    "slice", 
                    str(s)]
                )] = (base_x, 0, w, s)

            # 3. Vertical reverse slicing: Up (anchored at distal edge)
            for s in range(1, l):
                slice_key = settings.SEPARATOR.join([
                    id, 
                    frame_str, 
                    Directions.UP.value, 
                    str(s)]
                )
                crops[slice_key] = (base_x, l - s, w, s)
                crops[settings.SEPARATOR.join([
                    id, 
                    frame_str, 
                    Directions.UP.value, 
                    "slice", 
                    str(s)]
                )] = (base_x, l - s, w, s)

            # 4. Horizontal forward slicing: Right (anchored at origin)
            for s in range(1, w):
                slice_key = settings.SEPARATOR.join([
                    id, 
                    frame_str,
                    Directions.RIGHT.value, 
                    str(s)
                ])
                crops[slice_key] = (base_x, 0, s, l)
                crops[settings.SEPARATOR.join([
                    id, 
                    frame_str, 
                    Directions.RIGHT.value, 
                    "slice", 
                    str(s)]
                )] = (base_x, 0, s, l)

            # 5. Horizontal reverse slicing: Left (anchored at distal edge)
            for s in range(1, w):
                slice_key = settings.SEPARATOR.join([
                    id, 
                    frame_str, 
                    Directions.LEFT.value, 
                    str(s)
                ])
                crops[slice_key] = (base_x + w - s, 0, s, l)
                crops[settings.SEPARATOR.join([
                    id, 
                    frame_str, 
                    Directions.LEFT.value, 
                    "slice", 
                    str(s)]
                )] = (base_x + w - s, 0, s, l)

        return crops

    def keys(self, id: str, state: FluidState) -> List[Tuple[str, int, int]]:
        """
        Dynamically computes coordinate offsets and emits frame keys for the active
        stream corridor and surrounding annular pool without mutating state.
        """
        frame_keys: List[Tuple[str, int, int]] = []
        frame_str = str(state.animation.frame)
        full_key = settings.SEPARATOR.join([id, frame_str])

        w = self.tile_w
        l = self.tile_l
        direction = state.source
        length = state.length

        # ---------------------------------------------------------
        # 1. STREAM CORRIDOR DECOMPOSITION
        # ---------------------------------------------------------
        dim = l if direction in (
            Directions.DOWN.value, 
            Directions.UP.value
        ) else w
        full_tiles = length // dim
        rem = length % dim

        if direction == Directions.DOWN.value:
            for i in range(full_tiles):
                frame_keys.append((full_key, 0, i * l))
            if rem > 0:
                slice_key = settings.SEPARATOR.join([
                    id, 
                    frame_str, 
                    Directions.DOWN.value, 
                    str(rem)
                ])
                frame_keys.append((slice_key, 0, full_tiles * l))

        elif direction == Directions.UP.value:
            for i in range(1, full_tiles + 1):
                frame_keys.append((full_key, 0, -i * l))
            if rem > 0:
                slice_key = settings.SEPARATOR.join([
                    id, 
                    frame_str, 
                    Directions.UP.value, 
                    str(rem)
                ])
                frame_keys.append((slice_key, 0, -length))

        elif direction == Directions.RIGHT.value:
            for i in range(full_tiles):
                frame_keys.append((full_key, i * w, 0))
            if rem > 0:
                slice_key = settings.SEPARATOR.join([
                    id, 
                    frame_str, 
                    Directions.RIGHT.value, 
                    str(rem)
                ])
                frame_keys.append((slice_key, full_tiles * w, 0))

        elif direction == Directions.LEFT.value:
            for i in range(1, full_tiles + 1):
                frame_keys.append((full_key, -i * w, 0))
            if rem > 0:
                slice_key = settings.SEPARATOR.join([
                    id, 
                    frame_str,
                    Directions.LEFT.value,
                    str(rem)
                ])
                frame_keys.append((slice_key, -length, 0))

        # ---------------------------------------------------------
        # 2. ANNULAR POOLING DECOMPOSITION
        # ---------------------------------------------------------
        if state.pool:
            if len(state.hitboxes) > 1:
                # Flanks 1 through 4 represent non-overlapping rectangular pool flanks
                for flank_hb in state.hitboxes[1:]:
                    for px in range(0, flank_hb.dimensions.w, w):
                        for py in range(0, flank_hb.dimensions.l, l):
                            frame_keys.append((full_key, flank_hb.position.x + px, flank_hb.position.y + py))
            else:
                pos_x = state.position.x if state.position else 0
                pos_y = state.position.y if state.position else 0
                for px in range(state.pool.x, state.pool.x + state.pool.w, w):
                    for py in range(state.pool.y, state.pool.y + state.pool.l, l):
                        frame_keys.append((full_key, px - pos_x, py - pos_y))

        return frame_keys