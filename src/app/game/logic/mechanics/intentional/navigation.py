"""
# Ontology: app.game.logic.mechanics.intentional.navigation

Package for managing the Sprite's pathfinding trajectory.
"""
from __future__ import annotations

# Standard Libraries
from typing import TYPE_CHECKING
import collections
import logging

if TYPE_CHECKING:
    from app.game.board import Board

# Application Libraries
from app.game.logic.mechanics.core import Mechanic
from app.game.logic.modules.paths.plan import Planner
from app.models.state import DevicePayload

# Cython Libraries
import libs.core.math.geometry as geometry
from libs.core.models import Position

logger = logging.getLogger(__name__)

class NavigationMechanics(Mechanic):
    """
    """

    def update(self, 
        board: Board, 
        delta: float, 
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
        pass
