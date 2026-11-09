"""
@domain.concrete
@app.asset
@asset.frame
@category.widgets

# Ontology: Source - app.assets.frames.widgets

Package for Widget Frame implementations.
"""
# Stamdard Libraries
from typing import (
    List,
)
import logging

# Application Libraries
import app.static.settings as settings
from app.assets.base import Frame
from app.static.semantics import (
    Statuses,
    Gauges
)
from app.models.state import (
    TraversalState,
    MeterState
)
from app.models.properties import WidgetProperties

# -------------------------------------------------------------

logger = logging.getLogger(__name__)

# -------------------------------------------------------------

class TraversalFrame(Frame):
    """
    ## TraversalFrame
    """
    
    def keys(self, id: str, state: TraversalState) -> List[str]:
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
            ]): (2*w, 0, w, l),
            settings.SEPARATOR.join([
                id, 
                Statuses.DISABLED.value
            ]): (3*w, 0, w, l)
        }

# -------------------------------------------------------------

class MeterFrame(Frame):
    """
    ## MeterFrame
    """
    
    def keys(self, id: str, state: MeterState) -> List[str]:
        """
        """
        return [
            (settings.SEPARATOR.join([
                id, 
                Gauges.EMPTY.value
            ]), 0, 0),
            (settings.SEPARATOR.join([
                id, 
                str(state.animation.frame)
            ]), 0, 0) 
        ]


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
        for res in range(1, Gauges.FULL.value):
            frame_index = settings.SEPARATOR.join([
                id, 
                str(res)
            ])
            crops[frame_index] = (w, 0, int(w * (res / Gauges.FULL.value)), l)
        return crops