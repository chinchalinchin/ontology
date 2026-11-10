"""
@domain.user
@domain.concrete
@domain.system
@app.menu
@menu.handler

# Ontology: Source - app.game.menus.handlers.terminal

Terminal event handling implementations.
"""
# Standard Libraries
import logging

# Application Libraries
from app.static.semantics import Menus
from app.models.menus import (
    TerminalEvent,
    ViewContext
)
from app.game.menus.core import EventData
from app.game.menus.handlers.base import EventHandler
from app.models.state import PaneState

# Cython Libraries
import libs.graphics.render as render

# ---------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------

class TerminalEventHandler(EventHandler):
    def handle(self, event: TerminalEvent, data: EventData) -> None:
        if not data.board.menus:
            logger.warning("TerminalEvent received, but no Menus running on Board.")
            return 
        
        menu = data.board.menus.pop()
            
        if menu.id == Menus.LOAD.value:
            player = data.board.player()
            screen = data.screens.get(
                player.state.layer, 
                next(iter(data.screens.values()))
            )
            
            hud_menu = data.provider.unpack(
                Menus.VIEW.value, 
                data.board.configurations.menus.get(Menus.VIEW.value), 
                ViewContext(sprite=player.state), 
                screen.screensize
            )
            data.board.set_overlays([hud_menu])

        if menu.controller:
            menu.controller.close(menu, data.board, data.bus)

        if menu.widgets:
            for widget in menu.widgets.values():
                if isinstance(widget.state, PaneState) and widget.state.canvas is not None:
                    render.destroy(widget.state.canvas)
                    widget.state.canvas = None

        if not data.board.menus:
            data.board.paused = False


"""
@domain.user
@domain.concrete
@app.menu
@menu.handler
@workflow.traversal

# Ontology: Source - app.game.menus.handlers.terminal

Handler for closing active modal menus and releasing canvas textures.
"""
# Application Libraries
from app.game.menus.core import EventData
from app.game.menus.handlers.base import EventHandler
from app.models.menus import TerminalEvent
from app.models.state import PaneState

# Cython Libraries
import libs.graphics.render as render


class TerminalEventHandler(EventHandler):

    def handle(self, event: TerminalEvent, context: EventData) -> None:
        if not context.board.menus:
            return

        menu = context.board.menus.pop()
        if menu.controller:
            menu.controller.close(menu, context.board, context.bus)

        if menu.widgets:
            for widget in menu.widgets.values():
                if isinstance(widget.state, PaneState) and widget.state.canvas is not None:
                    render.destroy(widget.state.canvas)
                    widget.state.canvas = None

        if not context.board.menus:
            context.board.paused = False