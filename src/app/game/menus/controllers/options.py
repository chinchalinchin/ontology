"""
# Ontology: app.game.menus.controllers.options

Menu controller stub for the Options menu placeholder.
"""
from __future__ import annotations

# Standard Libraries
import collections
import logging
from typing import TYPE_CHECKING, Optional

# Application Libraries
from app.game.menus.controllers.base import MenuController
from app.game.menus.core import (
    Menu,
    Widget
)
from app.game.menus.events import UpdateEvent

if TYPE_CHECKING:
    from app.game.board import Board

logger = logging.getLogger(__name__)


class OptionsController(MenuController):
    """
    Controller handling options menu navigation and preview stamping.
    """
    _last_focus: Optional[str] = None
    _selector: Optional[str] = None

    DESCRIPTIONS = {
        "option-1": "Audio Configuration (Placeholder)",
        "option-2": "Display Settings (Placeholder)",
        "option-3": "Gameplay Settings (Placeholder).",
        "option-4": "Input Bindings (Placeholder)",
    }

    def open(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        self._last_focus = None
        self._selector = next((
            widget.binding.selector for widget 
            in menu.widgets.values() 
            if isinstance(widget, Widget)
        ), None)

    def select(self, name: str, menu: Menu, board: Board, bus: collections.deque) -> None:
        """Fires when pressing SELECT on the focused option."""
        widget = menu.widgets.get(name)
        if not widget or not widget.binding:
            return

        if self._selector is None:
            self._selector = widget.binding.selector

        parchment = menu.widgets.get(self._selector)
        
        selection = widget.binding.selection
        logger.info(f"Option selected: {selection}")

        if parchment:
            content = f"{name.upper()} ACTIVATED\n(Placeholder Action)"
            bus.append(UpdateEvent(widget=parchment, content=content))

    def update(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        """Fires per tick; updates parchment preview when focus traverses buttons."""
        if self._selector is None:
            self._selector = next((
                widget.binding.selector for widget 
                in menu.widgets.values() 
                if isinstance(widget, Widget)
            ), None)

        if menu.focus != self._last_focus:
            self._last_focus = menu.focus
            page_canvas = menu.widgets.get(self._selector)
            
            if page_canvas and menu.focus in self.DESCRIPTIONS:
                content = self.DESCRIPTIONS[menu.focus]
                bus.append(UpdateEvent(widget=page_canvas, content=content))

    def close(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        self._last_focus = None