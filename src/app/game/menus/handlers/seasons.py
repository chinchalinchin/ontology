"""
# Ontology: app.game.menus.handlers.update

Season event handling implementation.
"""
# Standard Libraries
import logging

# Application Libraries
from app.config.enums import (
    AssetCategories
)
from app.game.menus.events import (
    SeasonEvent,
    EventContext
)
from app.game.menus.handlers.base import EventHandler

logger = logging.getLogger(__name__)

class SeasonEventHandler(EventHandler):
    def handle(self, event: SeasonEvent, context: EventContext) -> None:
        calendar = context.board.calendar
        for layer, screen in context.screens.items():
            tiles = context.board.categories(AssetCategories.TILES.value, layer)
            screen.reconstruct(tiles, calendar)