"""
# Ontology: app.game.logic.mechanics.world.fluid
"""
from __future__ import annotations

# Standard Libraries
import collections
import logging
from typing import TYPE_CHECKING

# Application Libraries
from app.game.logic.mechanics import Mechanic
from app.models.state import DevicePayload

if TYPE_CHECKING:
    from app.game.board import Board
    
logger = logging.getLogger(__name__)

class FluidMechanics(Mechanic):
    """
    """
    
    def update(self, 
        board: Board, 
        delta: float, 
        bus: collections.deque, 
        payload: DevicePayload
    ) -> None:
        pass