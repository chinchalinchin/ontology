"""
# Ontology: app.game.menus.handlers.update

Update event handling implementation.
"""
# Standard Libraries
import logging

# Application Libraries
from app.game.menus.events import (
    UpdateEvent,
    EventContext
)
from app.game.menus.handlers.base import EventHandler

logger = logging.getLogger(__name__)

class UpdateEventHandler(EventHandler):
    def handle(self, event: UpdateEvent, context: EventContext) -> None:
        player = context.board.player()
        screen = context.screens[player.state.layer] \
                    if player and context.board.loaded \
                        else next(iter(context.screens.values()))
        screen.stamp(event.widget, event.content)