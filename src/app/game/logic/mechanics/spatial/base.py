"""
# Ontology: app.game.logic.mechanics.spatial.base

Package for SpatialMechanic parent class.
"""
# Standard Libraries
from typing import List, Tuple

from app.assets.base import Asset
from app.game.logic.mechanics import Mechanic

# Cython Libraries
from libs.core.math import (
    Geometry, 
    Physics, 
    Space
)
from libs.core.models import Position, Dimensions

# ----------------------------------------------------------------------------------------

class SpatialMechanic(Mechanic):
    """
    ## SpatialMechanic

    Base mechanic for systems requiring broad-phase spatial hashing and geometry resolution.
    """
    grid: Space

    def __init__(self, cell_size: int = 64, max_entities: int = 2000):
        # Allocated exactly once in memory during orchestration
        self.grid = Space(cell_size=cell_size, max_entities=max_entities)


    def center(self, position: Position, dimensions: Dimensions):
        return (position.x + dimensions.w / 2, position.y + dimensions.l / 2)

    
    def collisions(self, assets: List[Asset]) -> List[Tuple]:
        """
        Extracts primitives, queries the C-grid, and returns colliding Asset pairs.
        """
        self.grid.clear()
        
        if not assets:
            return []

        asset_map = dict(enumerate(assets))
        primitive_data = [asset.primitive(i) for i, asset in enumerate(assets)]
        
        colliding_indices = Physics.collisions(primitive_data, self.grid)
        return [(asset_map[id_a], asset_map[id_b]) for id_a, id_b in colliding_indices]
    