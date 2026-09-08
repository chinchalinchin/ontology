"""
# Ontology: app.game.menus.handlers.terminal

Terminal event handling implementations.
"""
# Standard Libraries
import logging

# Application Libraries
from app.config.enums import Menus
from app.game.menus.events import (
    TerminalEvent, 
    EventContext
)
from app.game.menus.contexts import ViewContext
from app.game.menus.handlers.base import EventHandler

logger = logging.getLogger(__name__)

class TerminalEventHandler(EventHandler):
    def handle(self, event: TerminalEvent, context: EventContext) -> None:
        if not context.board.menus:
            logger.warning("TerminalEvent received, but no Menus running on Board.")
            return 
        
        popped_menu = context.board.menus.pop()
            
        if popped_menu.id == Menus.LOAD.value:
            player = context.board.player()
            screen = context.screens.get(
                player.state.layer, 
                next(iter(context.screens.values()))
            )
            
            hud_menu = context.provider.unpack(
                Menus.VIEW.value, 
                context.board.configurations.menus.get(Menus.VIEW.value), 
                ViewContext(sprite=player.state), 
                screen.screensize
            )
            context.board.set_overlays([hud_menu])

        if not context.board.menus:
            context.board.paused = False