"""
# Ontology: app.game.logic.mechanics.motion.frictive
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
    """
    for asset in assets:
        if asset.state.velocity is None:
            continue

        cx = asset.state.position.x + (asset.dimensions.w / 2.0)
        cy = asset.state.position.y + (asset.dimensions.l / 2.0)
        
        center_pos = Position(int(cx), int(cy))
        tile = board.tile(asset.state.layer, center_pos)

        if not tile:
            continue

        physics.friction(asset.state.velocity, tile.properties.friction, delta)