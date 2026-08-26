"""
# Ontology: app.gane.menus.controllers.display
"""
# Application Libraries
from app.game.menus.controllers.base import MenuController
from app.game.menus.core import Menu
from app.game.board import Board

class DisplayController(MenuController):
    def open(self, menu: Menu, board: Board) -> None:
        pass

    def select(self, widget_id: str, menu: Menu, board: Board) -> None:
        """Fires when the user presses SELECT on a focused widget."""
        pass
        
    def update(self, menu: Menu, board: Board) -> None:
        """Fires every frame, used for dynamic HUDs or timers."""
        pass

    def close(self, menu: Menu, board: Board) -> None:
        pass