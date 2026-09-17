"""
# Ontology: app.game.menus.controllers.main
"""
from __future__ import annotations

# Standard Libraries
import collections
from typing import TYPE_CHECKING
import logging

# Application Libraries
import app.config.settings as settings
from app.config.enums import Selections
from app.game.menus.controllers.base import MenuController
from app.game.menus.core import Menu
from app.game.menus.events import (
    StateEvent, 
    TerminalEvent,
    MenuEvent
)

if TYPE_CHECKING:
    from app.game.board import Board

logger = logging.getLogger(__name__)

class MainController(MenuController):
    def open(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass
        
    def close(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        pass
        
    def update(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        # Prewarm rendering textures while the user is idle on the Main Menu
        registry = menu.context.registry
        if registry:
            registry.prewarm(budget_ms=settings.MIGRATOR_DELAY)

    def select(self, name: str, menu: Menu, board: Board, bus: collections.deque) -> None:
        widget = menu.widgets[name]
        selection = widget.binding.selection
        selector = widget.binding.selector

        # Target the requested board state mapping
        if selection == Selections.NEW.value:
            # Terminate the Main Menu before triggering the State transition
            bus.append(TerminalEvent())
            bus.append(StateEvent(id=settings.NEW_BOARD))
            
        elif selection == Selections.LOAD.value:
            # TODO: resolve through binding somehow
            bus.append(TerminalEvent())
            bus.append(StateEvent(id=settings.NEW_BOARD))

        elif selection == Selections.MENU.value:
            logger.info(selector)
            bus.append(MenuEvent(id=selector, context=menu.context))
