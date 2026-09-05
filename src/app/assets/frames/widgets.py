"""
# Ontology: app.assets.frames

Package for Widget Frame implementations.
"""
# Stamdard Libraries
from typing import List
import logging

# Application Libraries
import app.config.settings as settings
from app.assets.base import Frame
from app.assets.frames.core import safe_dim
from app.config.enums import Statuses
from app.models.state import AssetState

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------


class TraversalFrame(Frame):
    """
    ## TraversalFrame
    """

    def keys(self, id: str, state: AssetState) -> List[str]:
        """
        """
        return [ 
            (settings.SEPARATOR.join([id, state.animation.action]), 0, 0) 
        ]


    def index(self, id: str, properties: dict) -> dict[str, tuple[int, int, int, int]]:
        """
        """
        w, l = safe_dim(properties)
        return {
            settings.SEPARATOR.join([id, Statuses.IDLE.value]): (0, 0, w, l),
            settings.SEPARATOR.join([id, Statuses.ACTIVE.value]): (w, 0, w, l),
            settings.SEPARATOR.join([id, Statuses.SELECTED.value]): (2*w, 0, w, l),
            settings.SEPARATOR.join([id, Statuses.DISABLED.value]): (3*w, 0, w, l)
        }

class MeterFrame(Frame):
    """
    ## MeterFrame
    """

    def keys(self, id: str, state: AssetState) -> List[str]:
        """
        """
        return [
            (settings.SEPARATOR.join([id, str(settings.EMPTY)]), 0, 0),
            (settings.SEPARATOR.join([id, str(state.animation.frame)]), 0, 0) 
        ]


    def index(self, id: str, properties: dict) -> dict[str, tuple[int, int, int, int]]:
        """
        """
        w, l = safe_dim(properties)
        crops = {
           settings.SEPARATOR.join([id, str(settings.EMPTY)]): (0, 0, w, l)
        }
        for res in range(1, 101):
            frame_index = settings.SEPARATOR.join([id, str(res)])
            crops[frame_index] = (w, 0, int(w * (res / 100.0)), l)
        return crops


class IndexFrame(Frame):
    """
    ## IndexedFrame
    Parses horizontal spritesheets where each frame corresponds to a specific string key.
    """
    def keys(self, id: str, state: AssetState) -> List[str]:
        # Retrieve the specific icon key from the state, defaulting to the asset ID
        return [(state.icon, 0, 0)]


    def index(self, id: str, properties: dict) -> dict[str, tuple[int, int, int, int]]:
        w, l = safe_dim(properties)
        crops = {}
        frames = properties.get("frames", [])
        
        # Failsafe: if no frames are defined, index the whole image
        if not frames:
            return {id: (0, 0, w, l)}
            
        for i, frame_name in enumerate(frames):
            crops[frame_name] = (i * w, 0, w, l)
            
        return crops