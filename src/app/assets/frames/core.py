"""
# Ontology: app.assets.frames.core

Package for core Asset Frame implementations. 

**Overview**

Frames exist on the boundary of the Python-Cython interface.

-`index()`: This interface is a configuration-time method for generating the Asset Frame space from the Asset properties; this method is called inside of Cython from the Registry. Asset Properties are passed in as dicts.
- `keys()` interface is a runtime method for accessing the Frame key that corresponds to an Asset Frame state. It is called inside of Python from the Screen. Asset States are passed in as Python objects.
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
from app.config.enums import Orientations
from app.assets.base import Frame
from app.models.state import AssetState
from app.models.properties import AssetProperties

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------

class NoFrame(Frame):
    """
    ## NoFrame
    """
    
    def keys(self, id: str, state: AssetState) -> List[str]:
        """
        """
        return [(id, 0, 0)]

            
    def index(self, id: str, properties: AssetProperties) -> Dict[str, Tuple[int, int, int, int]]:
        """
        """
        return {id: (0, 0, 0, 0)}

# -------------------------------------------------------------------------------------

class SingleFrame(Frame):
    """
    ## SingleFrame
    """

    def keys(self, id: str, state: AssetState) -> List[str]:
        """
        """
        return [(id, 0, 0)]

        
    def index(self, id: str, properties: AssetProperties) -> Dict[str, Tuple[int, int, int, int]]:
        """
        """
        return {
            id: (0, 0, properties.dimensions.w, properties.dimensions.l)
        }

# -------------------------------------------------------------------------------------

        
class IterableFrame(Frame):
    """
    ## IterableFrame
    """
    
    def keys(self, id: str, state: AssetState) -> List[str]:
        """
        """
        return [(
            settings.SEPARATOR.join([
                id, 
                str(state.animation.frame)
            ]), 0, 0
        )]

        
    def index(self, id: str, properties: AssetProperties) -> Dict[str, Tuple[int, int, int, int]]:
        """
        """
        w = properties.dimensions.w 
        l = properties.dimensions.l

        return { 
            settings.SEPARATOR.join([
                id,
                str(i)
            ]): (i * w, 0, w, l)
            for i in range(properties.count) 
        }

# -------------------------------------------------------------------------------------

class OrientedFrame(Frame):
    """
    Indexes 2-axis horizontal atlas frames (Horizontal, Vertical) and emits
    the corresponding orientation frame key.
    """

    def index(self, id: str, properties: AssetProperties) -> Dict[str, Tuple[int, int, int, int]]:
        w = properties.dimensions.w
        l = properties.dimensions.l
        crops: Dict[str, Tuple[int, int, int, int]] = {}

        for i, orientation in enumerate(Orientations):
            key = settings.SEPARATOR.join([
                id, 
                orientation
            ])
            crops[key] = (i * w, 0, w, l)

        return crops

    def keys(self, id: str, state: AssetState) -> List[Tuple[str, int, int]]:
        key = settings.SEPARATOR.join([
            id, 
            state.orientation
        ])
        return [(key, 0, 0)]

# -------------------------------------------------------------------------------------

class IndexFrame(Frame):
    """
    ## IndexFrame

    Parses horizontal sheets where each frame corresponds to a specific string key.
    """
    
    def keys(self, id: str, state: AssetState) -> List[Tuple[str, int, int]]:
        icon_key = getattr(state, "icon", None)
        if not icon_key:
            return []
        return [(settings.SEPARATOR.join([
            id, 
            icon_key
        ]), 0, 0)]

    def index(self, id: str, properties: AssetProperties) -> Dict[str, Tuple[int, int, int, int]]:
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
