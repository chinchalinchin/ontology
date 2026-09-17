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
from app.game.menus.core import Menu
from app.game.menus.events import UpdateEvent

if TYPE_CHECKING:
    from app.game.board import Board

logger = logging.getLogger(__name__)


class OptionsController(MenuController):
    """
    Controller handling options menu navigation and preview stamping.
    """
    _last_focus: Optional[str] = None

    DESCRIPTIONS = {
        "option-1": "Audio Configuration (Placeholder)",
        "option-2": "Display Settings (Placeholder)",
        "option-3": "Gameplay Settings (Placeholder).",
        "option-4": "Input Bindings (Placeholder)",
    }

    def open(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        self._last_focus = None
        parchment = menu.widgets.get("options-parchment")
        if parchment:
            bus.append(UpdateEvent(widget=parchment, content="SELECT AN OPTION"))

    def select(self, name: str, menu: Menu, board: Board, bus: collections.deque) -> None:
        """Fires when pressing SELECT on the focused option."""
        widget = menu.widgets.get(name)
        if not widget or not widget.binding:
            return

        target_key = widget.binding.selector or "options-parchment"
        parchment = menu.widgets.get(target_key)
        
        selection = widget.binding.selection or name
        logger.info(f"Option selected: {selection}")

        if parchment:
            content = f"{name.upper()} ACTIVATED\n(Placeholder Action)"
            bus.append(UpdateEvent(widget=parchment, content=content))

    def update(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        """Fires per tick; updates parchment preview when focus traverses buttons."""
        if menu.focus != self._last_focus:
            self._last_focus = menu.focus
            parchment = menu.widgets.get("options-parchment")
            
            if parchment and menu.focus in self.DESCRIPTIONS:
                content = self.DESCRIPTIONS[menu.focus]
                bus.append(UpdateEvent(widget=parchment, content=content))

    def close(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        self._last_focus = None