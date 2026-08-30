"""
# Ontology: app.game.logic.mechanics.intentional.speech
"""
# Standard Libraries
from __future__ import annotations
from typing import TYPE_CHECKING
import collections

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board

from app.game.logic.mechanics import Mechanic
from app.models.state import DevicePayload

class SpeechMechanics(Mechanic):
    """
    """

    def update(self, 
        board: Board, 
        delta: float, 
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
        """
        """
        pass