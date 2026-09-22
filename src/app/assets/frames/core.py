"""
# Ontology: app.assets.frames

Package for Asset Frame implementations. 

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
from app.assets.base import Frame
from app.models.state import AssetState
from app.models.properties import AssetProperties

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------

class NoFrame(Frame):
    """
    ## NoFrame
    """

    def channels(self, 
        id: str, 
        state: AssetState,
        properties: AssetProperties
    ) -> List[Tuple]:
        return []
    
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

    def channels(self, 
        id: str, 
        state: AssetState,
        properties: AssetProperties
    ) -> List[Tuple]:
        return []
    
    def keys(self, id: str, state: AssetState) -> List[str]:
        """
        """
        return [(id, 0, 0)]

        
    def index(self, id: str, properties: AssetProperties) -> Dict[str, Tuple[int, int, int, int]]:
        """
        """
        return {id: (0, 0, properties.dimensions.w, properties.dimensions.l)}

# -------------------------------------------------------------------------------------

        
class IterableFrame(Frame):
    """
    ## IterableFrame
    """
    
    def channels(self, 
        id: str, 
        state: AssetState,
        properties: AssetProperties
    ) -> List[Tuple]:
        return []

    def keys(self, id: str, state: AssetState) -> List[str]:
        """
        """
        return [
            (settings.SEPARATOR.join([id, str(state.animation.frame)]), 0, 0)
        ]

        
    def index(self, id: str, properties: AssetProperties) -> Dict[str, Tuple[int, int, int, int]]:
        """
        """
        w = properties.dimensions.w 
        l = properties.dimensions.l

        return { 
            settings.SEPARATOR.join([id,str(i)]): (i * w, 0, w, l)
            for i in range(properties.count) 
        }