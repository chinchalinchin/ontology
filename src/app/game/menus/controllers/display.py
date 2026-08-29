"""
# Ontology: app.gane.menus.controllers.display
"""
from __future__ import annotations

# Standard Libraries
import collections
from typing import TYPE_CHECKING

# Application Libraries
from app.game.menus.controllers.base import MenuController
from app.game.menus.core import Menu

# FIX: Defer the Board import
if TYPE_CHECKING:
    from app.game.board import Board

class DisplayController(MenuController):
    def open(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass

    def select(self, id: str, menu: Menu, board: Board, bus: collections.deque) -> None:
        """Fires when the user presses SELECT on a focused widget."""
        pass
        
    def update(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        """Fires every frame, used for dynamic HUDs or timers."""
        pass

    def close(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass