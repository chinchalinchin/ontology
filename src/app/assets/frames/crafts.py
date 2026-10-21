"""
# Ontology: app.assets.frames.crafts

Package for Crafts Frame implementations.
"""
# Standard Libraries
from typing import (
    List,
    Tuple,
    Dict
)
import logging

# Application Libraries
import app.config.settings as settings
from app.assets.base import Frame
from app.game.logic.relations.materials import MaterialIndex
from app.models.state import CraftState
from app.models.properties import CraftProperties

logger = logging.getLogger(__name__)


class MaterialFrame(Frame):
    """
    Indexes 2D Craft Sheet atlases where rows correspond to Blueprint partitions
    and columns correspond to Material genus partitions.
    """

    def index(
        self,
        id: str,
        properties: CraftProperties
    ) -> Dict[str, Tuple[int, int, int, int]]:
        w = properties.dimensions.w
        l = properties.dimensions.l

        relations = MaterialIndex()
        rows = relations.blueprints(properties.blueprints)
        cols = relations.materials(properties.material.genus) if properties.material else ()

        atlas: Dict[str, Tuple[int, int, int, int]] = {}
        for r_idx, bp in enumerate(rows):
            for c_idx, mat in enumerate(cols):
                key = settings.SEPARATOR.join([id, bp, mat])
                atlas[key] = (c_idx * w, r_idx * l, w, l)
        return atlas

    def keys(self, id: str, state: CraftState) -> List[Tuple[str, int, int]]:
        return [(
            settings.SEPARATOR.join([
                id, 
                state.blueprint, 
                state.material
            ])
        , 0, 0)]