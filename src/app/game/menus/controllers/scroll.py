"""
# Ontology: app.gane.menus.controllers.scroll
"""
# Application Libraries
from app.config.enums import Selections
from app.game.menus.controllers.base import MenuController
from app.game.menus.core import Menu
from app.game.board import Board

class ScrollController(MenuController):
    """
    """

    def open(self, menu: Menu, board: Board) -> None:
        pass

    def select(self, widget_id: str, menu: Menu, board: Board) -> None:
        """Fires when the user presses SELECT on a focused widget."""
        widget = menu.widgets[widget_id]
        selection = widget.binding.selection
        
        # Find the targeted Page widget via the selector binding
        target = widget.binding.selector 
        page = menu.widgets[target]
        
        if selection == Selections.SCROLLDOWN and widget.state.more():
            widget.state.scrolldown()
        elif selection == Selections.SCROLLUP and widget.state.less():
            widget.state.scrollup()
            
    def update(self, menu: Menu, board: Board) -> None:
        """Fires every frame, used for dynamic HUDs or timers."""
        pass

    def close(self, menu: Menu, board: Board) -> None:
        pass