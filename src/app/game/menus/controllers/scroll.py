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

# FIX: Defer the Board import
if TYPE_CHECKING:
    from app.game.board import Board

class ScrollController(MenuController):
    """
    """

    def open(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass

    def select(self, id: str, menu: Menu, board: Board, bus: collections.deque) -> None:
        """Fires when the user presses SELECT on a focused widget."""
        widget = menu.widgets[id]
        selection = widget.binding.selection
        
        # Find the targeted Page widget via the selector binding
        target = widget.binding.selector 
        if not target or target not in menu.widgets:
            return
            
        page = menu.widgets[target]
        
        sel_val = selection.value if hasattr(selection, 'value') else selection
        sd_val = Selections.SCROLLDOWN.value if hasattr(Selections.SCROLLDOWN, 'value') else Selections.SCROLLDOWN
        su_val = Selections.SCROLLUP.value if hasattr(Selections.SCROLLUP, 'value') else Selections.SCROLLUP
        
        if sel_val == sd_val and page.state.more():
            page.state.scrolldown()
            from app.game.menus.events import UpdateEvent
            bus.append(UpdateEvent(widget=page, content=page.state.current()))
        elif sel_val == su_val and page.state.less():
            page.state.scrollup()
            from app.game.menus.events import UpdateEvent
            bus.append(UpdateEvent(widget=page, content=page.state.current()))
            
    def update(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        """Fires every frame, used for dynamic HUDs or timers."""
        pass

    def close(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass