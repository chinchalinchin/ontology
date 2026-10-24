"""
# Ontology: Source - app.game.logic.mechanics.spatial.collision

Package for CollisionMechanics
"""
from __future__ import annotations

# Standard Libraries
from typing import TYPE_CHECKING
import collections
import logging

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board

from app.assets.base import Asset
from app.static.semantics import (
    AssetInstances, 
    Directions
)
from app.game.logic.mechanics.spatial import SpatialMechanic
from app.models.state import DevicePayload

# Cython Libraries
import libs.core.math.physics as physics
import libs.core.math.geometry as geometry
from libs.core.models import Boundary

logger = logging.getLogger(__name__)

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
        Combines normalized sensory foot-anchor positioning with directional velocity
        gating to prevent premature tier transitions and boundary snapping.
        """
        e_base = stairs.elevation
        e_top = e_base + stairs.state.delta
        curr_e = sprite.elevation
        prev_e = sprite.elevation

        # Entity must be on either the base or summit tier of the stair incline
        if curr_e != e_base and curr_e != e_top:
            return

        direction = stairs.state.direction
        direction_val = direction.value if hasattr(direction, "value") else str(direction)

        vel = getattr(sprite.state, "velocity", None)
        vx = vel.vx if vel is not None else 0.0
        vy = vel.vy if vel is not None else 0.0

        dim_w = sprite.dimensions.w if sprite.dimensions else 0
        dim_l = sprite.dimensions.l if sprite.dimensions else 0

        # Calculate sensory ground contact point (center-x, bottom-y)
        foot_x = sprite.state.position.x + (dim_w // 2)
        foot_y = sprite.state.position.y + dim_l

        # -----------------------------------------------------------------
        # VERTICAL STAIRS (UP)
        # -----------------------------------------------------------------
        # NOTE: DOWN is impossible due to LPC perspective specification.
        if direction_val == Directions.UP.value:
            stair_l = stairs.dimensions.l
            if stair_l == 0:
                return

            tread_progress = (foot_y - stairs.state.position.y) / stair_l

            if direction_val == Directions.UP.value:
                # Ascent moves North (vy < 0); Descent moves South (vy > 0)
                if tread_progress <= 0.85 and vy < 0:
                    sprite.elevation = e_top
                elif tread_progress >= 0.85 and vy > 0:
                    sprite.elevation = e_base

        # -----------------------------------------------------------------
        # HORIZONTAL STAIRS (LEFT / RIGHT)
        # -----------------------------------------------------------------
        elif direction_val in (Directions.LEFT.value, Directions.RIGHT.value):
            stair_w = stairs.dimensions.w
            if stair_w == 0:
                return

            tread_progress = (foot_x - stairs.state.position.x) / stair_w

            if direction_val == Directions.RIGHT.value:
                # Ascent moves East (vx > 0); Descent moves West (vx < 0)
                if tread_progress >= 0.15 and vx > 0:
                    sprite.elevation = e_top
                elif tread_progress <= 0.15 and vx < 0:
                    sprite.elevation = e_base

            elif direction_val == Directions.LEFT.value:
                # Ascent moves West (vx < 0); Descent moves East (vx > 0)
                if tread_progress <= 0.85 and vx < 0:
                    sprite.elevation = e_top
                elif tread_progress >= 0.85 and vx > 0:
                    sprite.elevation = e_base

        if sprite.elevation != prev_e:
            logger.info(
                f"Telemetry:Stairs:{sprite.name} traversed {stairs.name} "
                f"dir={direction_val} progress={tread_progress:.2f} "
                f"foot=({foot_x},{foot_y}) vel=({vx:.1f},{vy:.1f}) "
                f"elevation: {prev_e} -> {sprite.elevation}"
            )


    def _boundary(self, asset: Asset, boundary: Boundary, elevation: int) -> None:
        """
        Delegates Asset vs Boundary interaction to the specialized Cython constraint solver,
        evaluating hitboxes specific to the active elevation tier.
        """
        is_kinematic = asset.taxonomy.instance == AssetInstances.PLAYERS.value
        mass = getattr(asset.properties, 'mass', 0)

        # Static environment architecture (m == 0) cannot be shifted by boundary hulls
        if mass == 0 and not is_kinematic:
            return

        vel = getattr(asset.state, 'velocity', None)
        hitboxes = asset.hitbox.get(asset.properties, asset.state, elevation, asset.frame)

        intersection = geometry.bounded(
            int(asset.state.position.x), 
            int(asset.state.position.y), 
            hitboxes,
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

    def _resolve(self, asset_a: Asset, asset_b: Asset, elevation: int) -> None:
        """
        Extract variables logically and defer matrix shifts to Cython,
        resolving hitboxes matching the active collision elevation tier.
        """
        # TODO: mass and velocity should probably be core Asset properties.
        m1 = getattr(asset_a.properties, 'mass', 0)
        m2 = getattr(asset_b.properties, 'mass', 0)

        is_kinematic1 = asset_a.taxonomy.instance == AssetInstances.PLAYERS.value
        is_kinematic2 = asset_b.taxonomy.instance == AssetInstances.PLAYERS.value

        vel1 = getattr(asset_a.state, 'velocity', None)
        vel2 = getattr(asset_b.state, 'velocity', None)

        hitboxes_a = asset_a.hitbox.get(asset_a.properties, asset_a.state, elevation, asset_a.frame)
        hitboxes_b = asset_b.hitbox.get(asset_b.properties, asset_b.state, elevation, asset_b.frame)

        intersection = geometry.intersects(
            asset_a.state.position, 
            asset_a.dimensions, 
            hitboxes_a,
            asset_b.state.position, 
            asset_b.dimensions, 
            hitboxes_b
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
        Executes the physics loop partitioned by discrete elevation tiers.
        """
        for layer in board.layers():
            # -------------------------------------------------------------
            # PHASE 0: Incline Traversal & Elevation State Mutation
            # -------------------------------------------------------------
            stairs = board.instances(AssetInstances.STAIRS.value, layer)
            if stairs:
                movers = [
                    w for w in board.weights(layer)
                    if getattr(w.properties, 'mass', 0) > 0
                ]
                for stair in stairs:
                    for mover in movers:
                        if geometry.intersects(
                            mover.state.position,
                            mover.dimensions,
                            mover.hitboxes,
                            stair.state.position,
                            stair.dimensions,
                            stair.hitboxes
                        ): 
                            self._traverse_stairs(mover, stair)

            # -------------------------------------------------------------
            # TIER PARTITIONING
            # -------------------------------------------------------------
            weights = board.weights(layer)
            weights_by_elevation = collections.defaultdict(list)
            for w in weights:
                # Deduplicate tiers that collapse to <= 0
                for tier in {max(0, t) for t in w.hitbox.elevations(w.properties, w.state)}:
                    weights_by_elevation[tier].append(w)

            for elevation, tier_weights in weights_by_elevation.items():
                # Phase 1: Boundary Constraints
                perimeters = board.perimeters.get(layer, {}).get(elevation, [])
                if perimeters:
                    dynamics = [
                        w for w in tier_weights
                        if getattr(w.properties, 'mass', 0) > 0
                    ]
                    for asset, boundary in self.constrain(dynamics, perimeters, elevation=elevation):
                        self._boundary(asset, boundary, elevation=elevation)

                # Phase 2: Dynamic Collisions
                for asset_a, asset_b in self.collisions(tier_weights, elevation=elevation):
                    self._resolve(asset_a, asset_b, elevation=elevation)