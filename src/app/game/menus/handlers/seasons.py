"""
# Ontology: app.game.menus.handlers.update

Season event handling implementation.
"""
# Standard Libraries
import logging

# Application Libraries
from app.config.enums import (
    AssetCategories,
    AssetInstances
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
        cycle = context.board.calendar.cycle
        period = context.board.calendar.period

        logger.info(
            f"SeasonEventHandler: Received SeasonEvent for season='{active_season}' "
            f"(Cycle='{cycle}', Period={period})"
        )

        # 1. Screen Reconstruction: Re-bake seasonal tile canvases
        if context.screens:
            for layer, screen in context.screens.items():
                tiles = context.board.categories(AssetCategories.TILES.value, layer)
                logger.info(
                    f"SeasonEventHandler: Triggering canvas reconstruction for layer='{layer}' "
                    f"({len(tiles)} tiles) to season='{active_season}'."
                )
                screen.reconstruct(tiles, context.board.calendar)

        # 2. Shoreline Frame Invalidation (Zero Geometry Regeneration)
        shorelines = context.board.shorelines()
        if not shorelines:
            shorelines = context.board.instances(AssetInstances.SHORELINES.value)

        updated_count = 0
        for shore in shorelines:
            prev_season = shore.state.season
            shore.state.season = active_season
            shore.state._keys = None
            updated_count += 1
            logger.debug(
                f"SeasonEventHandler: Updated shoreline '{shore.name}' "
                f"season '{prev_season}' -> '{active_season}' (_keys invalidated)."
            )

        logger.info(
            f"SeasonEventHandler: Synchronized {updated_count} shorelines to season='{active_season}'."
        )