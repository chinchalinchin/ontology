"""
@domain.automata
@domain.concrete
@app.module
@modality.intention
@workflow.cognition

# Ontology: Source - app.game.logic.modules.cognition.outcomes

Abstract PortalLocator and OutcomeHandler interfaces, concrete lifecycle
implementations, and OutcomeResolver dispatcher.
"""
from __future__ import annotations

# Standard Libraries
import logging
from typing import (
    Optional,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from app.game.board import Board

# Application Libraries
from app.assets.base import Asset
from app.game.logic.modules.cognition.base import Locator
from app.static.semantics import AssetInstances

# Cython Libraries
import libs.core.math.geometry as geometry
from libs.core.models import Position

# -----------------------------------------------------

logger = logging.getLogger(__name__)

# -----------------------------------------------------

class DoorLocator(Locator):
    """
    Locates Doors (both LayerProjections.IN and
    LayerProjections.OUT) on the Sprite's current Layer. Prioritizes the
    nearest mapped door in memory.doors targeting goal.layer, falling back
    to the nearest unmapped door within vision.radius.
    """

    @staticmethod
    def _distance_sq(p1: Position, p2: Position) -> int:
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        return dx * dx + dy * dy

    def locate(self, sprite: Asset, board: Board) -> Optional[Asset]:
        goal = sprite.state.goal
        if not goal or sprite.state.layer is None:
            return None

        doors = board.instances(AssetInstances.DOORS, sprite.state.layer)
        if not doors:
            return None

        sprite_pos = sprite.state.position
        memory_doors = sprite.state.memory.doors

        # 1. Prioritize nearest mapped door known to reach goal.layer
        mapped_candidates = [
            portal for portal in doors
            if memory_doors.get(portal.name) == goal.layer
        ]
        if mapped_candidates:
            return min(
                mapped_candidates,
                key=lambda d: self._distance_sq(sprite_pos, d.state.position)
            )

        # 2. Fall back to nearest unmapped door within vision.radius
        vision_radius = sprite.state.mutators.parameters.vision.radius
        unmapped_candidates = [
            portal for portal in doors
            if (
                portal.name not in memory_doors
                or memory_doors[portal.name] == sprite.state.layer
            )
            and geometry.nearby(
                portal.state.position.x,
                portal.state.position.y,
                sprite_pos.x,
                sprite_pos.y,
                vision_radius
            )
        ]
        if unmapped_candidates:
            return min(
                unmapped_candidates,
                key=lambda d: self._distance_sq(sprite_pos, d.state.position)
            )

        return None


# -----------------------------------------------------