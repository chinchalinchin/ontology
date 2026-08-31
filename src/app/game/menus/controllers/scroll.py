"""
# Ontology: app.gane.menus.controllers.scroll
"""
from __future__ import annotations

# Standard Libraries
import collections
from typing import TYPE_CHECKING

# Application Libraries
from app.config.enums import Selections
from app.game.menus.controllers.base import MenuController
from app.game.menus.core import Menu

if TYPE_CHECKING:
    from app.game.board import Board

class ScrollController(MenuController):
    """
    """

    def open(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass

    def select(self, name: str, menu: Menu, board: Board, bus: collections.deque) -> None:
        """Fires when the user presses SELECT on a focused widget."""
        widget = menu.widgets[name]
        
        # 1. Get the action and the target key
        selection = widget.binding.selection
        target_key = widget.binding.selector 
        
        # 2. O(1) Dictionary Lookup
        if not target_key or target_key not in menu.widgets:
            return
            
        page = menu.widgets[target_key]
        
        # 3. Execute logic
        if selection == Selections.SCROLLDOWN:
            page.state.scrolldown()
            from app.game.menus.events import UpdateEvent
            bus.append(UpdateEvent(widget=page, content=page.state.current()))
        elif selection == Selections.SCROLLUP:
            page.state.scrollup()
            from app.game.menus.events import UpdateEvent
            bus.append(UpdateEvent(widget=page, content=page.state.current()))
            
    def update(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        """Fires every frame."""
        pass

    def close(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass