"""
# Ontology: app.game.menus.controllers.base
"""
from __future__ import annotations

# Standard Libraries
from abc import ABC, abstractmethod
import collections
from typing import TYPE_CHECKING

# FIX: Defer the Board import
if TYPE_CHECKING:
    from app.game.board import Board
    
# Application Libraries
from app.game.menus.core import Menu

class MenuController(ABC):
    @abstractmethod
    def open(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass

    @abstractmethod
    def select(self, name: str, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass
        
    @abstractmethod
    def update(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass

    @abstractmethod
    def close(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass