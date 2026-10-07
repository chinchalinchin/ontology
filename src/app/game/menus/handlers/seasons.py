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
    """
    Handles macro-temporal SeasonEvents by synchronizing dynamic shoreline states,
    invalidating frame key caches, and triggering static canvas reconstruction.
    """

    def handle(self, event: SeasonEvent, context: EventContext) -> None:
        if not context.board:
            return

        active_season = context.board.calendar.season

        # 1. Screen Reconstruction: Re-bake seasonal tile canvases
        if context.screens:
            for layer, screen in context.screens.items():
                tiles = context.board.categories(AssetCategories.TILES.value, layer)
                screen.reconstruct(tiles, context.board.calendar)

        # 2. Shoreline Frame Invalidation (Zero Geometry Regeneration)
        for shore in context.board.shorelines():
            shore.state.season = active_season
            shore.state._keys = None