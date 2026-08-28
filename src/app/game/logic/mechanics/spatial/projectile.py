"""
# Ontology: app.game.logic.mechanics.spatial.projectile

Package for ProjectileMechanics
"""
# Standard Libraries
from __future__ import annotations
from typing import TYPE_CHECKING
import collections

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board

from app.config.enums import (
    AssetCategories, 
    AssetInstances
)
from app.game.logic.mechanics.spatial.base import SpatialMechanic

class ProjectileMechanics(SpatialMechanic):
    """
    ## ProjectileMechanics

    Mechanic responsible for tracking projectile trajectories and impacts.
    """

    def __init__(self):
        super().__init__(max_entities=1000)


    def update(self, board: Board, delta_time: float, bus: collections.deque) -> None:
        """
        """
        for layer in board.layers():
            projectiles = board.instances(AssetInstances.PROJECTILES, layer)
            if not projectiles:
                continue
                
            sheets = board.categories(AssetCategories.SHEETS, layer)
            
            colliding_pairs = self.collisions(projectiles + sheets)

            for asset_a, asset_b in colliding_pairs:
                # Filter out sheet-sheet and proj-proj collisions 
                is_a_proj = asset_a.taxonomy.instance == AssetInstances.PROJECTILES
                is_b_proj = asset_b.taxonomy.instance == AssetInstances.PROJECTILES

                if is_a_proj and not is_b_proj:
                    proj, target = asset_a, asset_b
                elif is_b_proj and not is_a_proj:
                    proj, target = asset_b, asset_a
                else:
                    continue

                # TODO: Resolve projectile impact (e.g., mark proj for GC, apply damage to target)
                pass

