"""
# Ontology: app.game.logic.mechanics.base

Package for defining the Mechanic interface.
"""
from __future__ import annotations

# Standard Libraries
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import collections
import logging

if TYPE_CHECKING:
    from app.game.board import Board

# Application Libraries

from app.models.state import (
    DevicePayload
)

logger = logging.getLogger(__name__)

class Mechanic(ABC):
    """
    """

    @abstractmethod 
    def update(self, 
        board: Board, 
        delta: float,
        bus: collections.deque, 
        payload: DevicePayload
    ) -> None:
        pass
