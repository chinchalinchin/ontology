"""
# Ontology: app.game.menus.handlers.menu

Menu event handling implemention.
"""
# Standard Libraries
import logging

# Application Libraries
from app.game.menus.handlers.base import EventHandler
from app.game.menus.events import (
    MenuEvent, 
    EventContext
)

logger = logging.getLogger(__name__)

class MenuEventHandler(EventHandler):
    def handle(self, event: MenuEvent, context: EventContext) -> None:
        if not context.board.configurations.menus.get(event.id):
            logger.warning(f"MenuEvent Received, but no {event.id} Menu Defined")
            return
        
        context.board.paused = True
        player = context.board.player()
        screen = context.screens[player.state.layer] \
                    if player and context.board.loaded \
                        else next(iter(context.screens.values()))
        
        menu = context.provider.unpack(
            event.id, 
            context.board.configurations.menus.get(event.id), 
            event.context, 
            screen.screensize
        )
        context.board.menus.append(menu)

        # Stamp any initial canvas content
        for widget in menu.widgets.values():
            if hasattr(widget.state, 'canvas') and widget.state.canvas is not None:
                if hasattr(widget.state, 'current'):
                    screen.stamp(widget, widget.state.current())
