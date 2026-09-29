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
    executors: Dict[str, Any]
    relations: Dict[str, Any]

    def __init__(self):
        self.executors = {}
        self.relations = {}


    def set_executor(self, key: str, executor: Any) -> None:
        self.executors[key] = executor


    def set_relation(self, key: str, relation: Any) -> None:
        self.relations[key] = relation


    @property
    def executor(self) -> Any:
        if not self.executors:
            return None
        return next(iter(self.executors.values()))


    @executor.setter
    def executor(self, executor: Any) -> None:
        if executor is None:
            self.executors.clear()
        else:
            if self.executors:
                first_key = next(iter(self.executors.keys()))
                self.executors[first_key] = executor
            else:
                self.executors["default"] = executor


    @property
    def relation(self) -> Any:
        if not self.relations:
            return None
        return next(iter(self.relations.values()))


    @relation.setter
    def relation(self, relation: Any) -> None:
        if relation is None:
            self.relations.clear()
        else:
            if self.relations:
                first_key = next(iter(self.relations.keys()))
                self.relations[first_key] = relation
            else:
                self.relations["default"] = relation


    @abstractmethod 
    def update(self, 
        board: Board, 
        delta: float,
        bus: collections.deque, 
        payload: DevicePayload
    ) -> None:
        pass
