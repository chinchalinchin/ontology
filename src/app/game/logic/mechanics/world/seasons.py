"""
# Ontology: app.game.logic.mechanics.world.seasons

Mechanic implementation governing macro-temporal progression,
hydrological moisture diffusion, and biological stage transitions.
"""
from __future__ import annotations

# Standard Libraries
import collections
import logging
from typing import (
    List,
    TYPE_CHECKING
)

# Application Libraries
import app.config.settings as settings
from app.config.enums import (
    AssetCategories,
    Seasons,
    Cycles
)
from app.game.logic.mechanics.base import Mechanic
from app.game.menus.events import SeasonEvent
from app.models.state import DevicePayload, CalendarState

# Cython Libraries
from libs.core.models import Position

if TYPE_CHECKING:
    from app.assets.base import Asset
    from app.game.board import Board

logger = logging.getLogger(__name__)


class SeasonMechanics(Mechanic):
    """
    World pipeline mechanic executing macro-temporal calendar tracking,
    hydrological moisture diffusion from fluid networks, and declarative
    biological stage transitions.
    """

    @property
    def period_duration(self) -> float:
        return getattr(
            settings,
            "PERIOD_DURATION_SECONDS",
            getattr(settings, "SEASON_DURATION_SECONDS", 3600.0) / 9.0
        )

    def _advance_calendar(self, calendar: CalendarState) -> None:
        """
        Advances the calendar state across discrete temporal buckets:
        period (0..2) -> cycle (onset, peak, decline) -> season -> year.
        Emits log entries on cycle, season, and year transitions.
        """
        seasons = [s.value for s in Seasons]
        cycles = [c.value for c in Cycles]

        calendar.period += 1
        if calendar.period >= 3:
            calendar.period = 0
            cycle_idx = cycles.index(calendar.cycle) if calendar.cycle in cycles else 0
            cycle_idx += 1

            if cycle_idx >= len(cycles):
                cycle_idx = 0
                season_idx = seasons.index(calendar.season) if calendar.season in seasons else 0
                season_idx += 1

                if season_idx >= len(seasons):
                    season_idx = 0
                    calendar.year += 1
                    logger.info(f"Calendar: Advanced year to Year {calendar.year}")

                calendar.season = seasons[season_idx]
                logger.info(
                    f"Calendar: Advanced season to '{calendar.season}' "
                    f"(Year: {calendar.year})"
                )

            calendar.cycle = cycles[cycle_idx]
            logger.info(
                f"Calendar: Advanced cycle to '{calendar.cycle}' "
                f"(Season: '{calendar.season}', Period: {calendar.period})"
            )

    @staticmethod
    def _probes(resource: Asset) -> List[Position]:
        """
        Generates center and cardinal boundary probe coordinates for hydrological lookup.
        """
        pos = resource.state.position
        if not pos:
            return []
        w = resource.dimensions.w if resource.dimensions else 32
        l = resource.dimensions.l if resource.dimensions else 32
        mid_x = pos.x + (w // 2)
        mid_y = pos.y + (l // 2)
        return [
            Position(mid_x, mid_y),
            Position(mid_x, pos.y - 1),
            Position(mid_x, pos.y + l),
            Position(pos.x - 1, mid_y),
            Position(pos.x + w, mid_y)
        ]

    def update(
        self,
        board: Board,
        delta: float,
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
        # 1. Temporal Integration
        board.calendar.elapsed += delta
        period_changed = False
        duration = self.period_duration

        while board.calendar.elapsed >= duration:
            board.calendar.elapsed -= duration
            self._advance_calendar(board.calendar)
            period_changed = True

        if period_changed:
            bus.append(SeasonEvent())

        resources = board.categories(AssetCategories.RESOURCES.value)
        if not resources:
            return

        # 2. Hydrological Parameters
        max_ret = getattr(settings, "MAX_RETENTION", 100.0)
        diff_rate = getattr(settings, "DIFFUSION_RATE", 10.0)
        evap_rate = getattr(settings, "EVAPORATION_RATE", 1.0)
        evap_mods = getattr(
            settings,
            "SEASON_EVAPORATION_MODIFIERS",
            {
                Seasons.SPRING.value: 1.0,
                Seasons.SUMMER.value: 1.5,
                Seasons.AUTUMN.value: 1.0,
                Seasons.WINTER.value: 0.5
            }
        )
        season_mod = evap_mods.get(board.calendar.season, 1.0)

        # 3. Environmental Diffusion & Stage Progression
        for resource in resources:
            is_near_water = any(
                board.fluid(resource.state.layer, probe_pos)
                for probe_pos in self._probes(resource)
            )
            if is_near_water:
                resource.state.retention = min(
                    max_ret,
                    resource.state.retention + (diff_rate * delta)
                )
            else:
                resource.state.retention = max(
                    0.0,
                    resource.state.retention - (evap_rate * season_mod * delta)
                )

            lifespan = resource.properties.lifespan
            lifespan_key = lifespan.value if hasattr(lifespan, "value") else str(lifespan)
            executor = self.executors.get(lifespan_key)
            if not executor:
                continue

            locals_env = {
                "resource": resource.state,
                "calendar": board.calendar,
                "properties": resource.properties
            }

            next_stage = executor.evaluate(resource.state.stage, locals_env)
            if next_stage:
                logger.info(
                    f"Transition(resource={resource.name}): "
                    f"'{resource.state.stage}' -> '{next_stage}'"
                )
                resource.state.stage = next_stage