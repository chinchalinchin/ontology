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

logger = logging.getLogger(__name__)

class TerminalEventHandler(EventHandler):
    def handle(self, event: TerminalEvent, data: EventData) -> None:
        if not data.board.menus:
            logger.warning("TerminalEvent received, but no Menus running on Board.")
            return 
        
        popped_menu = data.board.menus.pop()
            
        if popped_menu.id == Menus.LOAD.value:
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

        if not data.board.menus:
            data.board.paused = False