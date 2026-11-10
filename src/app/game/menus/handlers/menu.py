"""
@domain.user
@domain.concrete
@domain.system
@app.menu
@menu.handler
@workflow.rendering

# Ontology: Source - app.game.menus.handlers.menu

Menu event handling implemention.
"""
# Standard Libraries
import logging

# Application Libraries
from app.game.menus.handlers.base import EventHandler
from app.models.menus import MenuEvent
from app.models.state import PaneState
from app.game.menus.core import EventData

# ----------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------

class MenuEventHandler(EventHandler):
    def handle(self, event: MenuEvent, data: EventData) -> None:
        if not data.board.configurations.menus.get(event.id):
            logger.warning(f"MenuEvent Received, but no {event.id} Menu Defined")
            return
        
        data.board.paused = True
        player = data.board.player()
        screen = data.screens[player.state.layer] \
                    if player and data.board.loaded \
                        else next(iter(data.screens.values()))
        
        menu = data.provider.unpack(
            event.id, 
            data.board.configurations.menus.get(event.id), 
            event.context, 
            screen.screensize
        )
        data.board.menus.append(menu)

        if menu.controller:
            menu.controller.open(menu, data.board, data.bus)
            
        # Stamp any initial canvas content
        for widget in menu.widgets.values():
            if isinstance(widget.state, PaneState) and widget.state.canvas is not None:
                screen.stamp(widget, widget.state.current())

        