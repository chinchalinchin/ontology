"""
# Ontology: app.game.logic.mechanics.spatial.collision

Package for CollisionMechanics
"""
# Standard Libraries
from __future__ import annotations
from typing import TYPE_CHECKING
import collections

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board

from app.assets.base import Asset
from app.config.enums import AssetInstances
from app.game.logic.mechanics.spatial import SpatialMechanic
from app.models.state import DevicePayload

# Cython Libraries
import libs.core.math.physics as physics
import libs.core.math.geometry as geometry
from libs.core.models import Boundary

class CollisionMechanics(SpatialMechanic):
    """
    ## CollisionMechanics

    Mechanic responsible for resolving Asset collisions natively.
    """
    def __init__(self):
        super().__init__(max_entities=2000)


    def _boundary(self, asset: Asset, boundary: Boundary):
        """
        Delegates Asset vs Boundary interaction to the specialized Cython constraint solver.
        """
        is_kinematic = asset.taxonomy.instance == AssetInstances.PLAYERS.value
        vel = getattr(asset.state, 'velocity', None)
        
        intersection = geometry.bounded(
            int(asset.state.position.x), 
            int(asset.state.position.y), 
            asset.hitboxes,
            boundary.position.x,
            boundary.position.y,
            boundary.dimensions.w,
            boundary.dimensions.l
        )
        
        if not intersection:
            return
            
        hb = intersection[0]
        physics.constrain(
            asset.state.position, 
            hb, 
            vel, 
            is_kinematic,
            boundary.position.x, 
            boundary.position.y, 
            boundary.dimensions.w, 
            boundary.dimensions.l
        )


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

        intersection = geometry.intersects(
            asset_a.state.position, 
            asset_a.dimensions, 
            asset_a.hitboxes,
            asset_b.state.position, 
            asset_b.dimensions, 
            asset_b.hitboxes
        )

        if not intersection:
            return

        hb_a, hb_b = intersection

        physics.collide(
            asset_a.state.position, 
            hb_a, 
            vel1, 
            m1, 
            is_kinematic1,
            asset_b.state.position, 
            hb_b, 
            vel2, 
            m2, 
            is_kinematic2
        )

    def update(self, 
        board: Board, 
        delta: float, 
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
        """
        ### update(board, delta)

        Executes the physics loop strictly in two phases to guarantee environmental 
        stability before dynamic entity resolution.
        """
        for layer in board.layers():
            weights = board.weights(layer)
            
            # -------------------------------------------------------------
            # PHASE 1: Environmental Constraints
            # -------------------------------------------------------------
            perimeters = board.perimeters.get(layer, [])
            if perimeters:
                boundary_collisions = self.constrain(weights, perimeters)
                for asset, boundary in boundary_collisions:
                    self._boundary(asset, boundary)
                    
            # -------------------------------------------------------------
            # PHASE 2: Dynamic Collisions
            # -------------------------------------------------------------
            colliding_pairs = self.collisions(weights)
            for asset_a, asset_b in colliding_pairs:
                self._resolve(asset_a, asset_b)