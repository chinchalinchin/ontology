"""
# Ontology: app.game.logic.mechanics.motion.frictive
"""
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

def update(crates: List[Asset], board: Board, delta: float) -> None:
    """
    Determines linear velocity decay based on environmental properties for inert moving assets.
    """
    for crate in crates:
        if crate.state.velocity is None:
            continue

        cx = crate.state.position.x + (crate.dimensions.w / 2.0)
        cy = crate.state.position.y + (crate.dimensions.l / 2.0)
        
        center_pos = Position(int(cx), int(cy))
        tile = board.tile(crate.state.layer, center_pos)

        if not tile:
            continue

        physics.friction(crate.state.velocity, tile.properties.friction, delta)