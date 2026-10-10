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
from app.config.enums import (
    AssetInstances, 
    Directions
)
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
    def __init__(self, cell_size : int = 64, max_entities : int = 200):
        super().__init__(cell_size=cell_size, max_entities=max_entities)

    def _traverse_stairs(self, sprite: Asset, stairs: Asset) -> None:
        """
        Evaluates dynamic body progression across stair tread bounds and shifts elevation.
        Restricted to entities currently at either base or summit tier to prevent cross-tier jumping.
        """
        e_base = stairs.state.elevation
        e_top = e_base + stairs.state.delta
        curr_e = sprite.state.elevation

        # Entity must be on either the bottom or top tier of the stair incline
        if curr_e != e_base and curr_e != e_top:
            return

        direction = stairs.state.direction
        direction_val = direction.value if hasattr(direction, "value") else str(direction)

        if direction_val in (Directions.UP.value, Directions.DOWN.value):
            stair_top = stairs.state.position.y
            stair_len = stairs.dimensions.l
            sprite_bottom = sprite.state.position.y + (sprite.dimensions.l if sprite.dimensions else 0)
            tread_progress = (sprite_bottom - stair_top) / stair_len

            if direction_val == Directions.UP.value:
                if tread_progress <= 0.2:
                    sprite.state.elevation = e_top
                elif tread_progress >= 0.8:
                    sprite.state.elevation = e_base
            else:
                if tread_progress <= 0.2:
                    sprite.state.elevation = e_base
                elif tread_progress >= 0.8:
                    sprite.state.elevation = e_top

        elif direction_val in (Directions.LEFT.value, Directions.RIGHT.value):
            stair_left = stairs.state.position.x
            stair_w = stairs.dimensions.w
            sprite_right = sprite.state.position.x + (sprite.dimensions.w if sprite.dimensions else 0)
            tread_progress = (sprite_right - stair_left) / stair_w

            if direction_val == Directions.RIGHT.value:
                if tread_progress >= 0.8:
                    sprite.state.elevation = e_top
                elif tread_progress <= 0.2:
                    sprite.state.elevation = e_base
            else:
                if tread_progress <= 0.2:
                    sprite.state.elevation = e_top
                elif tread_progress >= 0.8:
                    sprite.state.elevation = e_base

    def _boundary(self, asset: Asset, boundary: Boundary):
        """
        Delegates Asset vs Boundary interaction to the specialized Cython constraint solver.
        """
        is_kinematic = asset.taxonomy.instance == AssetInstances.PLAYERS.value
        mass = getattr(asset.properties, 'mass', 0)

        # Static environment architecture (m == 0) cannot be shifted by boundary hulls
        if mass == 0 and not is_kinematic:
            return

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

        Executes the physics loop partitioned by discrete elevation tiers to guarantee
        that entities on different Z-planes cannot resolve collisions or boundary shifts against one another.
        """
        for layer in board.layers():
            # -------------------------------------------------------------
            # PHASE 0: Incline Traversal & Elevation State Mutation
            # -------------------------------------------------------------
            stairs = board.instances(AssetInstances.STAIRS, layer)
            if stairs:
                movers = [
                    w for w in board.weights(layer)
                    if getattr(w.properties, 'mass', 0) > 0 
                    or w.taxonomy.instance == AssetInstances.PLAYERS.value
                ]
                for stair in stairs:
                    # Spatial intersection check between dynamic characters and stair sensors
                    for mover in movers:
                        if geometry.intersects(
                            mover.state.position,
                            mover.dimensions,
                            mover.hitboxes,
                            stair.state.position,
                            stair.dimensions,
                            stair.hitboxes
                        ): self._traverse_stairs(mover, stair)

            # -------------------------------------------------------------
            # TIER PARTITIONING
            # -------------------------------------------------------------
            weights = board.weights(layer)
            weights_by_elevation = collections.defaultdict(list)
            for w in weights:
                weights_by_elevation[w.state.elevation].append(w)

            for elevation, tier_weights in weights_by_elevation.items():
                # ---------------------------------------------------------
                # PHASE 1: Environmental Constraints
                # ---------------------------------------------------------
                perimeters = board.perimeters.get(layer, {}).get(elevation, [])
                if perimeters:
                    dynamics = [
                        w for w in tier_weights 
                        if getattr(w.properties, 'mass', 0) > 0 
                        or w.taxonomy.instance == AssetInstances.PLAYERS.value
                    ]
                    boundary_collisions = self.constrain(dynamics, perimeters)
                    for asset, boundary in boundary_collisions:
                        self._boundary(asset, boundary)
                        
                # ---------------------------------------------------------
                # PHASE 2: Dynamic Collisions
                # ---------------------------------------------------------
                colliding_pairs = self.collisions(tier_weights)
                for asset_a, asset_b in colliding_pairs:
                    self._resolve(asset_a, asset_b)