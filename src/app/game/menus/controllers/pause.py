"""
# Ontology: app.game.menus.controllers.pause

Menu controller handling pause state actions: saving, loading, options, and exiting.
"""
from __future__ import annotations

# Standard Libraries
import collections
import logging
from typing import TYPE_CHECKING

# Application Libraries
from app.config.enums import (
    Selections,
    Menus
)
from app.game.menus.controllers.base import MenuController
from app.game.menus.core import Menu
from app.game.menus.events import (
    MenuEvent,
    StateEvent,
    TerminalEvent,
)
from app.game.menus.contexts import MainContext

if TYPE_CHECKING:
    from app.game.board import Board

logger = logging.getLogger(__name__)


class PauseController(MenuController):
    """
    Handles pause menu selections: persisting world state, requesting state loads,
    pushing modal submenus, and quitting to the title screen.
    """

    def open(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        logger.debug("Pause menu opened.")

    def select(self, name: str, menu: Menu, board: Board, bus: collections.deque) -> None:
        """Fires when the user presses SELECT on an active button."""
        widget = menu.widgets.get(name)
        if not widget or not widget.binding:
            return

        selection = widget.binding.selection
        selector = widget.binding.selector

        if selection == Selections.SAVE.value:
            slot = selector or "save-01"
            logger.info(f"Executing save to slot '{slot}'...")
            board.serialize(slot)

        elif selection == Selections.LOAD.value:
            slot = selector or "save-01"
            logger.info(f"Requesting load for slot '{slot}'...")
            # Pop pause menu and signal the Migrator to load new state
            bus.append(TerminalEvent())
            bus.append(StateEvent(id=slot))

        elif selection == Selections.MENU.value:
            target_menu = selector or "options"
            logger.info(f"Opening submenu '{target_menu}'...")
            bus.append(MenuEvent(id=target_menu, context=menu.context))

        elif selection == Selections.QUIT.value:
            logger.info("Quitting session to main menu...")
            # Clear active world assets and caches
            board.clear()
            registry = getattr(board, "registry", None)
            bus.append(MenuEvent(id=Menus.MAIN.value, context=MainContext(registry=registry)))

    def update(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        """Per-tick execution while the pause menu remains top of stack."""
        pass

    def close(self, menu: Menu, board: Board, bus: collections.deque) -> None:
        logger.debug("Pause menu closed.")