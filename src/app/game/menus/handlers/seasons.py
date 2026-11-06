"""
@domain.user
@domain.concrete
@domain.logic
@app.menu
@menu.handler
@workflow.seasons

# Ontology: Source - app.game.menus.handlers.seasons

Season event handling implementation.
"""
# Standard Libraries
import logging

# Application Libraries
from app.static.semantics import (
    AssetCategories,
    AssetInstances
)
from app.models.menus import SeasonEvent
from app.game.menus.core import EventData
from app.game.menus.handlers.base import EventHandler

logger = logging.getLogger(__name__)

class SeasonEventHandler(EventHandler):
    """
    Handles macro-temporal SeasonEvents by synchronizing dynamic shoreline states,
    invalidating frame key caches, and triggering static canvas reconstruction.
    """

    def handle(self, event: SeasonEvent, data: EventData) -> None:
        if not data.board:
            return

        active_season = data.board.calendar.season
        cycle = data.board.calendar.cycle
        period = data.board.calendar.period

        logger.info(
            f"SeasonEventHandler: Received SeasonEvent for season='{active_season}' "
            f"(Cycle='{cycle}', Period={period})"
        )

        # 1. Screen Reconstruction: Re-bake seasonal tile canvases
        if data.screens:
            for layer, screen in data.screens.items():
                tiles = data.board.categories(AssetCategories.TILES.value, layer)
                logger.info(
                    f"SeasonEventHandler: Triggering canvas reconstruction for layer='{layer}' "
                    f"({len(tiles)} tiles) to season='{active_season}'."
                )
                screen.reconstruct(tiles, data.board.calendar)

        # 2. Shoreline Frame Invalidation (Zero Geometry Regeneration)
        shorelines = data.board.shorelines()
        if not shorelines:
            shorelines = data.board.instances(AssetInstances.SHORELINES.value)

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