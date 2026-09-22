"""
# Ontology: app.game.logic.mechanics.base

Package for defining the Mechanic interface.
"""
from __future__ import annotations

# Standard Libraries
from abc import ABC, abstractmethod
from typing import (
    Dict,
    Any,
    TYPE_CHECKING
)
import collections
import logging

# Application Libraries
from app.models.state import  DevicePayload

if TYPE_CHECKING:
    from app.game.board import Board

logger = logging.getLogger(__name__)

class Mechanic(ABC):
    """
    """
    executors: Dict[str, Any]

    def __init__(self):
        self.executors = {}

    def set_executor(self, key: str, executor: Any) -> None:
        self.executors[key] = executor

    @property
    def executor(self) -> Any:
        """Convenience accessor for mechanics that rely on a single primary executor."""
        if not self.executors:
            return None
        return next(iter(self.executors.values()))

    @abstractmethod 
    def update(self, 
        board: Board, 
        delta: float,
        bus: collections.deque, 
        payload: DevicePayload
    ) -> None:
        pass
