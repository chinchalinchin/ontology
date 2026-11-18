"""
@domain.concrete
@app.asset
@app.core
@asset.frame
@category.cursors

# Ontology: Source - app.assets.frames.core

Cursor Frame implementations.
"""
# Stamdard Libraries
from typing import (
    List,
    Tuple,
    Dict
)
import logging

# Application Libraries
from app.static.semantics import (
    Directions
)
from app.assets.base import Frame
from app.models.state import AssetState
from app.models.properties import AssetProperties

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------

# TODO

class ProjectilFrame(Frame):
    """
    """
    
    def keys(self, id: str, state: AssetState) -> List[str]:
        """
        """
        pass

            
    def index(self, id: str, properties: AssetProperties) -> Dict[str, Tuple[int, int, int, int]]:
        """
        """
        pass