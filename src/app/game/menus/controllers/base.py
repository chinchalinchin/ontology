"""
# Ontology: app.models.config

Models for typing the configuration attributes of Mechanics and other game components. See documentation for a more in-depth explanation of each field and its purpose. 
"""
# Standard Libraries
from abc import ABC, abstractmethod

# Application Libraries
from app.models.menus import MenuInstance
from app.game.board import Board

class MenuController(ABC):
    @abstractmethod
    def open(self, menu: MenuInstance, board: Board) -> None:
        pass

    @abstractmethod
    def select(self, widget_id: str, menu: MenuInstance, board: Board) -> None:
        """Fires when the user presses SELECT on a focused widget."""
        pass
        
    @abstractmethod
    def update(self, menu: MenuInstance, board: Board) -> None:
        """Fires every frame, used for dynamic HUDs or timers."""
        pass