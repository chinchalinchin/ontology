"""
@domain.logic
@domain.concrete
@app.menu
@menu.controller
@workflow.traversal

# Ontology: Source - app.game.menus.controllers.scroll
"""
from __future__ import annotations

# Standard Libraries
import collections
from typing import TYPE_CHECKING

# Application Libraries
from app.static.semantics import Selections
from app.game.menus.controllers.base import MenuController
from app.game.menus.core import Menu
from app.models.menus import UpdateEvent
from app.models.state import (
    PaneState,
    TraversalState
)

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

        if not widget or not widget.binding:
            return
        
        selection = widget.binding.selection
        selector = widget.binding.selector 
        
        if not selector or selector not in menu.widgets:
            return
            
        pane = menu.widgets[selector]

        if not isinstance(pane.state, PaneState):
            return
        
        if selection == Selections.SCROLLDOWN.value:
            pane.state.scrolldown()
            bus.append(UpdateEvent(
                widget=pane, 
                content=pane.state.current()
            ))

        elif selection == Selections.SCROLLUP.value:
            pane.state.scrollup()
            bus.append(UpdateEvent(
                widget=pane, 
                content=pane.state.current()
            ))
            
    def update(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        """Fires every frame."""
        pass

    def close(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass