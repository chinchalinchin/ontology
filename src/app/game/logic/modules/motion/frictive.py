"""
# Ontology: app.game.logic.modules.motion.frictive
"""
from __future__ import annotations

# Standard Libraries
import logging
from typing import List, TYPE_CHECKING

# Application Libraries
from app.assets.base import Asset

if TYPE_CHECKING:
    from app.game.board import Board

# Cython Libraries
import libs.core.math.physics as physics
from libs.core.models import Position

logger = logging.getLogger(__name__)

def update(assets: List[Asset], board: Board, delta: float) -> None:
    """
    Determines linear velocity decay based on environmental properties for inert moving assets.
    Suspends friction calculations while assets are floating in environmental water bodies.
    """
    for asset in assets:
        if asset.state.velocity is None:
            continue

        cx = asset.state.position.x + (asset.dimensions.w / 2.0)
        cy = asset.state.position.y + (asset.dimensions.l / 2.0)
        
        center_pos = Position(int(cx), int(cy))

        # Suspend friction calculations while the asset is floating in water
        if board.fluid(asset.state.layer, center_pos):
            continue

        tile = board.tile(asset.state.layer, center_pos)

        if not tile:
            continue

        physics.friction(asset.state.velocity, tile.properties.friction, delta)