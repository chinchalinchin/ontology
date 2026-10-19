"""
# Ontology: app.assets.frames.resources

Package for Resource Frame implementations. 

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
from app.assets.base import (
    Frame
)
from app.models.state import (
    StrutState
)
from app.models.properties import (
    CraftProperties
)

logger = logging.getLogger(__name__)


class MaterialFrame(Frame):
    """
    Indexes 2D Strut Sheet atlases where rows correspond to Blueprint partitions
    and columns correspond to Material genus partitions.
    """

    def index(self, id: str, properties: CraftProperties) -> Dict[str, Tuple[int, int, int, int]]:
        w = properties.dimensions.w
        l = properties.dimensions.l

        rows = settings.BLUEPRINT_PARTITIONS.get(properties.blueprints, ())
        cols = settings.MATERIAL_PARTITIONS.get(properties.material.genus, ())

        atlas: Dict[str, Tuple[int, int, int, int]] = {}
        for r_idx, bp in enumerate(rows):
            for c_idx, mat in enumerate(cols):
                key = settings.SEPARATOR.join([id, bp, mat])
                atlas[key] = (c_idx * w, r_idx * l, w, l)
        return atlas

    def keys(self, id: str, state: StrutState) -> List[Tuple[str, int, int]]:
        return settings.SEPARATOR.join([id, state.blueprint, state.material])
