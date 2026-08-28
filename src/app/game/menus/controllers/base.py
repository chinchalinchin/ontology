"""
# Ontology: app.game.menus.controllers.base
"""
# Standard Libraries
from abc import ABC, abstractmethod
import collections

# Application Libraries
from app.game.menus.core import Menu
from app.game.board import Board

class MenuController(ABC):
    @abstractmethod
    def open(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass

    @abstractmethod
    def select(self, widget_id: str, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass
        
    @abstractmethod
    def update(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass

    @abstractmethod
    def close(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass