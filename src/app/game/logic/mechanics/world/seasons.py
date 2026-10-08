"""
# Ontology: app.game.logic.mechanics.world.seasons

Mechanic implementation governing macro-temporal progression,
continuous soil moisture flux integration, and throttled biological stage transitions.
"""
from __future__ import annotations

# Standard Libraries
import collections
import logging
from typing import TYPE_CHECKING

# Application Libraries
import app.config.settings as settings
from app.config.enums import (
    AssetCategories,
    Seasons,
    Cycles,
)
from app.game.logic.mechanics.base import Mechanic
from app.game.menus.events import SeasonEvent
from app.models.state import DevicePayload, CalendarState

if TYPE_CHECKING:
    from app.game.board import Board

logger = logging.getLogger(__name__)


class SeasonMechanics(Mechanic):
    """
    World pipeline mechanic executing macro-temporal calendar tracking,
    continuous soil moisture diffusion via potential fields, and throttled
    declarative biological stage evaluations.
    """
    _transition_accumulator: float

    def __init__(self):
        super().__init__()
        # Initialized to threshold so the initial update tick evaluates immediately
        self._transition_accumulator = 1.0

    @property
    def period(self) -> float:
        return settings.SEASON_DURATION_SECONDS / 9.0

    def _advance_calendar(self, calendar: CalendarState) -> None:
        """
        Advances the calendar state across discrete temporal buckets:
        period (0..2) -> cycle (onset, peak, decline) -> season -> year.
        Emits log entries on period, cycle, season, and year transitions.
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
        else:
            logger.info(
                f"Calendar: Advanced period to {calendar.period} "
                f"(Season: '{calendar.season}', Cycle: '{calendar.cycle}')"
            )

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
        duration = self.period

        while board.calendar.elapsed >= duration:
            board.calendar.elapsed -= duration
            self._advance_calendar(board.calendar)
            period_changed = True

        if period_changed:
            logger.info(
                f"SeasonMechanics: Period boundary crossed. Emitting SeasonEvent for "
                f"season='{board.calendar.season}', cycle='{board.calendar.cycle}', period={board.calendar.period}."
            )
            bus.append(SeasonEvent())

        resources = board.categories(AssetCategories.RESOURCES.value)
        if not resources:
            return

        # 2. Continuous Environmental Moisture Integration (Zero Inner-Loop Allocations)
        evap_modifier = settings.SEASON_EVAPORATION_MODIFIERS.get(board.calendar.season, 1.0)
        evaporation_step = delta * settings.EVAPORATION_RATE * evap_modifier
        diffusion_step = settings.DIFFUSION_RATE * delta

        for resource in resources:
            flux = resource.state.moisture_flux
            if flux > 0.0:
                resource.state.retention = min(
                    settings.MAX_RETENTION,
                    resource.state.retention + (flux * diffusion_step)
                )
            else:
                resource.state.retention = max(
                    0.0,
                    resource.state.retention - evaporation_step
                )

        # 3. Throttled Declarative Stage Progression (1.0 Hz or Period Transition)
        self._transition_accumulator += delta
        should_evaluate = period_changed or (self._transition_accumulator >= 1.0)

        if should_evaluate:
            self._transition_accumulator = 0.0

            for resource in resources:
                lifespan_prop = resource.properties.lifespan
                lifespan_key = lifespan_prop.value if hasattr(lifespan_prop, "value") else str(lifespan_prop)
                executor = self.executors.get(lifespan_key)
                if not executor:
                    continue

                locals_map = {
                    "resource": resource.state,
                    "calendar": board.calendar,
                    "board": board,
                    "crop": resource.state,
                    "tree": resource.state,
                    resource.instance: resource.state
                }

                next_stage = executor.evaluate(resource.state.stage, locals_map)
                if next_stage:
                    logger.info(
                        f"Transition(resource={resource.name}): "
                        f"'{resource.state.stage}' -> '{next_stage}' "
                        f"(Retention={resource.state.retention:.1f}, Season='{board.calendar.season}')"
                    )
                    resource.state.stage = next_stage