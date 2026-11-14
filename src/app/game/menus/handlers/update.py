"""
@domain.concrete
@app.menu
@menu.handler
@workflow.rendering

# Ontology: Source - app.game.menus.handlers.update

Update event handling implementation.
"""
# Standard Libraries
import logging

# Application Libraries
from app.models.menus import UpdateEvent
from app.game.menus.core import EventData
from app.game.menus.handlers.base import EventHandler

logger = logging.getLogger(__name__)

class UpdateEventHandler(EventHandler):
    def handle(self, event: UpdateEvent, data: EventData) -> None:
        player = data.board.player()
        screen = data.screens[player.state.layer] \
                    if player and data.board.loaded \
                        else next(iter(data.screens.values()))
        screen.stamp(event.widget, event.content)