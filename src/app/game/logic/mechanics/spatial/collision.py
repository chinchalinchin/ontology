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
from app.game.logic.mechanics.spatial.base import SpatialMechanic


class CollisionMechanics(SpatialMechanic):
    """
    ## CollisionMechanics

    Mechanic responsible for resolving Asset collisions natively.
    """

    def __init__(self):
        super().__init__(max_entities=2000)

    def _resolve(self, asset_a: Asset, asset_b: Asset):
        """
        """
        # Calculate centers
        cx_a, cy_a = self.center(asset_a.state.position, asset_a.dimensions)
        cx_b, cy_b = self.center(asset_b.state.position, asset_b.dimensions)

        dx, dy = cx_b - cx_a, cy_b - cy_a

        if dx == 0 and dy == 0:
            dx = 1

        # Resolve spatial overlap
        overlap_x = (asset_a.dimensions.w / 2 + asset_b.dimensions.w / 2) - abs(dx)
        overlap_y = (asset_a.dimensions.l / 2 + asset_b.dimensions.l / 2) - abs(dy)

        if overlap_x > 0 and overlap_y > 0:
            m1 = getattr(asset_a.properties, 'mass', 0)
            m2 = getattr(asset_b.properties, 'mass', 0)

            # ----------------------------------------------------
            # 1. Spatial Resolution
            
            inv_m1 = 1.0 / m1 if m1 > 0 else 0.0
            inv_m2 = 1.0 / m2 if m2 > 0 else 0.0
            inv_total = inv_m1 + inv_m2

            if inv_total > 0:
                p1 = inv_m1 / inv_total
                p2 = inv_m2 / inv_total

                # Push along the shallowest axis of penetration
                if overlap_x < overlap_y:
                    shift_x1 = overlap_x * p1
                    shift_x2 = overlap_x * p2
                    if dx > 0:
                        asset_a.state.position.x -= int(shift_x1)
                        asset_b.state.position.x += int(shift_x2)
                    else:
                        asset_a.state.position.x += int(shift_x1)
                        asset_b.state.position.x -= int(shift_x2)
                else:
                    shift_y1 = overlap_y * p1
                    shift_y2 = overlap_y * p2
                    if dy > 0:
                        asset_a.state.position.y -= int(shift_y1)
                        asset_b.state.position.y += int(shift_y2)
                    else:
                        asset_a.state.position.y += int(shift_y1)
                        asset_b.state.position.y -= int(shift_y2)

            # ----------------------------------------------------
            # 2. Momentum Transfer
            
            has_v1 = hasattr(asset_a.state, 'velocity') and asset_a.state.velocity is not None
            has_v2 = hasattr(asset_b.state, 'velocity') and asset_b.state.velocity is not None

            v1x = asset_a.state.velocity.vx if has_v1 else 0.0
            v1y = asset_a.state.velocity.vy if has_v1 else 0.0
            v2x = asset_b.state.velocity.vx if has_v2 else 0.0
            v2y = asset_b.state.velocity.vy if has_v2 else 0.0

            if m1 == 0 and m2 == 0:
                pass
            elif m1 == 0:
                # M1 is static, M2 rebounds fully
                if has_v2:
                    asset_b.state.velocity.vx = -v2x
                    asset_b.state.velocity.vy = -v2y
            elif m2 == 0:
                # M2 is static, M1 rebounds fully
                if has_v1:
                    asset_a.state.velocity.vx = -v1x
                    asset_a.state.velocity.vy = -v1y
            else:
                # Both dynamic, calculate 1D elastic collisions independently for X and Y
                v1f_x = (v1x * (m1 - m2) + 2 * m2 * v2x) / (m1 + m2)
                v1f_y = (v1y * (m1 - m2) + 2 * m2 * v2y) / (m1 + m2)
                
                v2f_x = (v2x * (m2 - m1) + 2 * m1 * v1x) / (m1 + m2)
                v2f_y = (v2y * (m2 - m1) + 2 * m1 * v1y) / (m1 + m2)

                if has_v1:
                    asset_a.state.velocity.vx = v1f_x
                    asset_a.state.velocity.vy = v1f_y
                if has_v2:
                    asset_b.state.velocity.vx = v2f_x
                    asset_b.state.velocity.vy = v2f_y


    def update(self, board: Board, delta: float) -> None:
        """
        ### update(board, delta)

        Resolves kinematic overlap constraints using the broad-phase physics pipeline.
        """
        for layer in board.layers():
            # Query Board.weights(layer) to evaluate dynamic overlaps exclusively
            weights = board.weights(layer)
            
            colliding_pairs = self.collisions(weights)
            
            for asset_a, asset_b in colliding_pairs:
                # Setup trigger interactions
                if hasattr(asset_a.state, 'mutators') and \
                    hasattr(asset_a.state.mutators, 'triggers'):
                    asset_a.state.mutators.triggers.struck = True
                if hasattr(asset_b.state, 'mutators') and \
                    hasattr(asset_b.state.mutators, 'triggers'):
                    asset_b.state.mutators.triggers.struck = True

                self._resolve(asset_a, asset_b)