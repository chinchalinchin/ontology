"""
@domain.concrete
@app.asset
@asset.frame
@category.widgets

# Ontology: Source - app.assets.frames.widgets

Package for Widget Frame implementations.
"""
# Standard Libraries
from typing import (
    List,
    Tuple
)
import logging

# Application Libraries
import app.static.settings as settings
from app.assets.base import Frame
from app.static.semantics import (
    Alignments,
    Statuses,
    Gauges
)
from app.models.state import (
    PaneState,
    TraversalState,
    MeterState,
    IconState
)
from app.models.properties import WidgetProperties

# -------------------------------------------------------------

logger = logging.getLogger(__name__)

# -------------------------------------------------------------

class PaneFrame(Frame):
    """
    ## PaneFrame

    Trisects a Pane texture in-place into a 3x3 9-slice atlas and projects
    (nx + 2) * (ny + 2) tile offsets from PaneState.multiple.
    """
    _PARTITIONS = (
        Alignments.START.value,
        Alignments.CENTER.value,
        Alignments.END.value,
    )

    def index(
        self,
        id: str,
        properties: WidgetProperties
    ) -> dict[str, tuple[int, int, int, int]]:
        wc = properties.dimensions.w // 3
        lc = properties.dimensions.l // 3
        crops = {}
        for r, v in enumerate(self._PARTITIONS):
            for c, h in enumerate(self._PARTITIONS):
                key = settings.SEPARATOR.join([id, v, h])
                crops[key] = (c * wc, r * lc, wc, lc)
        return crops

    def keys(
        self,
        id: str,
        state: PaneState
    ) -> List[Tuple[str, int, int]]:
        nx = state.multiple.nx
        ny = state.multiple.ny
        wc = state.span.w // (nx + 2)
        lc = state.span.l // (ny + 2)

        primitives: List[Tuple[str, int, int]] = []
        for iy in range(ny + 2):
            v = (
                Alignments.START.value if iy == 0
                else Alignments.END.value if iy == ny + 1
                else Alignments.CENTER.value
            )
            for ix in range(nx + 2):
                h = (
                    Alignments.START.value if ix == 0
                    else Alignments.END.value if ix == nx + 1
                    else Alignments.CENTER.value
                )
                key = settings.SEPARATOR.join([id, v, h])
                primitives.append((key, ix * wc, iy * lc))
        return primitives

# -------------------------------------------------------------

class TraversalFrame(Frame):
    """
    ## TraversalFrame
    """

    def keys(self, id: str, state: TraversalState) -> List[Tuple[str, int, int]]:
        """
        """
        return [
            (settings.SEPARATOR.join([
                id,
                state.status
            ]), 0, 0)
        ]

    def index(self, id: str, properties: WidgetProperties) -> dict[str, tuple[int, int, int, int]]:
        """
        """
        w = properties.dimensions.w
        l = properties.dimensions.l

        return {
            settings.SEPARATOR.join([
                id,
                Statuses.IDLE.value
            ]): (0, 0, w, l),
            settings.SEPARATOR.join([
                id,
                Statuses.ACTIVE.value
            ]): (w, 0, w, l),
            settings.SEPARATOR.join([
                id,
                Statuses.SELECTED.value
            ]): (2 * w, 0, w, l),
            settings.SEPARATOR.join([
                id,
                Statuses.DISABLED.value
            ]): (3 * w, 0, w, l)
        }

# -------------------------------------------------------------

class MeterFrame(Frame):
    """
    ## MeterFrame
    """

    def keys(self, id: str, state: MeterState) -> List[Tuple[str, int, int]]:
        """
        """
        unit = state.unit
        pct = (state.reading / unit) if unit > 0 else 0.0
        res = max(0, min(100, int(round(pct * 100))))

        frames = [
            (settings.SEPARATOR.join([
                id,
                str(Gauges.EMPTY.value)
            ]), 0, 0)
        ]
        if res > 0:
            frames.append(
                (settings.SEPARATOR.join([
                    id,
                    str(res)
                ]), 0, 0)
            )
        return frames

    def index(self, id: str, properties: WidgetProperties) -> dict[str, tuple[int, int, int, int]]:
        """
        """
        w = properties.dimensions.w
        l = properties.dimensions.l
        crops = {
            settings.SEPARATOR.join([
                id,
                str(Gauges.EMPTY.value)
            ]): (0, 0, w, l)
        }
        for res in range(1, Gauges.FULL.value + 1):
            frame_index = settings.SEPARATOR.join([
                id,
                str(res)
            ])
            crops[frame_index] = (w, 0, int(w * (res / Gauges.FULL.value)), l)
        return crops

# -------------------------------------------------------------

class IconFrame(Frame):
    """
    ## IndexFrame

    Parses horizontal sheets where each frame corresponds to a specific string key.
    """
    
    def keys(self, id: str, state: IconState) -> List[Tuple[str, int, int]]:
        if not state.icon:
            return []
        return [(settings.SEPARATOR.join([
            id, 
            state.icon
        ]), 0, 0)]

    def index(self, id: str, properties: WidgetProperties) -> Dict[str, Tuple[int, int, int, int]]:
        w = properties.dimensions.w
        l = properties.dimensions.l
        frames = properties.frames
        crops = {}
        
        # Failsafe: if no frames are defined, index the whole image
        if not frames:
            return {id: (0, 0, w, l)}
            
        for i, frame_name in enumerate(frames):
            frame_index = settings.SEPARATOR.join([
                id, 
                frame_name
            ])
            crops[frame_index] = (i * w, 0, w, l)
            
        return crops
