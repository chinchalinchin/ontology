"""
# Ontology: app.game.menus.controllers.scroll
"""
from __future__ import annotations

# Standard Libraries
import collections
from typing import TYPE_CHECKING

# Application Libraries
from app.config.enums import Selections
from app.game.menus.controllers.base import MenuController
from app.game.menus.core import Menu
from app.game.menus.events import UpdateEvent

if TYPE_CHECKING:
    from app.game.board import Board

class ScrollController(MenuController):
    """
    Controller responsible for parsing text menu selections and updating display components.
    """

    def open(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass

    def select(self, name: str, menu: Menu, board: Board, bus: collections.deque) -> None:
        """Fires when the user presses SELECT on a focused widget."""
        widget = menu.widgets[name]
        
        selection = widget.binding.selection
        target_key = widget.binding.selector 
        
        if not target_key or target_key not in menu.widgets:
            return
            
        page = menu.widgets[target_key]
        
        if selection == Selections.SCROLLDOWN.value:
            page.state.scrolldown()
            bus.append(UpdateEvent(widget=page, content=page.state.current()))
        elif selection == Selections.SCROLLUP.value:
            page.state.scrollup()
            bus.append(UpdateEvent(widget=page, content=page.state.current()))
            
    def update(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        """Fires every frame."""
        pass

    def close(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass