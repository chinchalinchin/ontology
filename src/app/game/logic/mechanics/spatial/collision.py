"""
# Ontology: app.game.logic.mechanics.spatial.collision

Package for CollisionMechanics
"""
# Standard Libraries
from __future__ import annotations
from typing import TYPE_CHECKING

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board

from app.assets.base import Asset
from app.config.enums import AssetInstances
from app.game.logic.mechanics.spatial.base import SpatialMechanic

# Cython Libraries
from libs.core.math import Physics

class CollisionMechanics(SpatialMechanic):
    """
    ## CollisionMechanics

    Mechanic responsible for resolving Asset collisions natively.
    """
    def __init__(self):
        super().__init__(max_entities=2000)

    def _resolve(self, asset_a: Asset, asset_b: Asset):
        """
        Extract variables logically and defer matrix shifts to Cython.
        """
        m1 = getattr(asset_a.properties, 'mass', 0)
        m2 = getattr(asset_b.properties, 'mass', 0)

        is_kinematic1 = asset_a.taxonomy.instance == AssetInstances.PLAYERS
        is_kinematic2 = asset_b.taxonomy.instance == AssetInstances.PLAYERS

        vel1 = getattr(asset_a.state, 'velocity', None)
        vel2 = getattr(asset_b.state, 'velocity', None)

        Physics.resolve_collision(
            asset_a.state.position, asset_a.dimensions, vel1, m1, is_kinematic1,
            asset_b.state.position, asset_b.dimensions, vel2, m2, is_kinematic2
        )

    def update(self, board: Board, delta: float) -> None:
        """
        ### update(board, delta)

        Resolves kinematic overlap constraints using the broad-phase physics pipeline.
        """
        for layer in board.layers():
            weights = board.weights(layer)
            
            colliding_pairs = self.collisions(weights)
            
            for asset_a, asset_b in colliding_pairs:
                if hasattr(asset_a.state, 'mutators') and \
                    hasattr(asset_a.state.mutators, 'triggers'):
                    asset_a.state.mutators.triggers.struck = True
                if hasattr(asset_b.state, 'mutators') and \
                    hasattr(asset_b.state.mutators, 'triggers'):
                    asset_b.state.mutators.triggers.struck = True

                self._resolve(asset_a, asset_b)