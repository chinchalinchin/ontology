"""
# Ontology: app.gane.menus.controllers.display
"""
from __future__ import annotations

# Standard Libraries
import collections
from typing import TYPE_CHECKING

# Application Libraries
from app.config.enums import (
    Menus,
    Selections
)
from app.game.menus.controllers.base import MenuController
from app.game.menus.core import Menu
from app.game.menus.events import MenuEvent

if TYPE_CHECKING:
    from app.game.board import Board

class MainController(MenuController):
    def select(self, 
        name: str, 
        menu: Menu, 
        board: Board, 
        bus: collections.deque
    ) -> None:
        widget = menu.widgets[name]
                
        # 1. Get the action and the target key
        selection = widget.binding.selection

        if selection == Selections.NEW.value:
            # Pass the registry into the Event context
            bus.append(MenuEvent(
                id=Menus.LOAD.value, 
                context={'registry': board.screens[0].registry} 
            ))