"""
# Ontology: tests.unit.app.game.logic.mechanics.world.test_seasons

Unit tests verifying SeasonMechanics macro-temporal calendar integration,
hydrological moisture diffusion, and declarative biological stage progression.
"""
# External Libraries
import pytest

# Application Libraries
from app.config.enums import (
    Seasons,
    Cycles,
    AnnualStages,
    PerennialStages
)
from app.game.logic.mechanics.world.seasons import SeasonMechanics
from app.game.menus.events import SeasonEvent
from app.game.menus.handlers.seasons import SeasonEventHandler
from app.game.menus.events import EventContext
from app.models.state import CalendarState

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Position,
    Hitbox
)

@pytest.mark.seasons
@pytest.mark.ecology
def test_season_mechanics_temporal_period_cycle_advancement(
    mock_board, mock_season_mechanics, mock_bus
):
  mock_board.calendar = CalendarState(
      year=1,
      season=Seasons.SPRING.value,
      cycle=Cycles.ONSET.value,
      period=0,
      elapsed=0.0,
  )
  period_duration = mock_season_mechanics.period

  mock_season_mechanics.update(
      mock_board, delta=period_duration, bus=mock_bus, payload=None
  )

  assert mock_board.calendar.period == 1
  assert mock_board.calendar.cycle == Cycles.ONSET.value
  assert mock_board.calendar.season == Seasons.SPRING.value
  assert len(mock_bus) == 1
  assert isinstance(mock_bus.popleft(), SeasonEvent)

  mock_season_mechanics.update(
      mock_board, delta=period_duration * 2, bus=mock_bus, payload=None
  )

  assert mock_board.calendar.period == 0
  assert mock_board.calendar.cycle == Cycles.PEAK.value
  assert mock_board.calendar.season == Seasons.SPRING.value

@pytest.mark.seasons
@pytest.mark.ecology
def test_season_mechanics_temporal_season_year_rollover(
    mock_board,
    mock_bus
):
    """
    Verify complete progression through decline rolls season, and winter rolls year.
    """
    mechanic = SeasonMechanics()
    mock_board.calendar = CalendarState(
        year=1,
        season=Seasons.WINTER.value,
        cycle=Cycles.DECLINE.value,
        period=2,
        elapsed=0.0
    )
    period_duration = mechanic.period

    mechanic.update(mock_board, delta=period_duration, bus=mock_bus, payload=None)

    assert mock_board.calendar.period == 0
    assert mock_board.calendar.cycle == Cycles.ONSET.value
    assert mock_board.calendar.season == Seasons.SPRING.value
    assert mock_board.calendar.year == 2
    assert len(mock_bus) == 1
    assert isinstance(mock_bus.popleft(), SeasonEvent)


@pytest.mark.seasons
@pytest.mark.ecology
def test_season_mechanics_hydrological_diffusion_near_water(
    mock_board,
    mock_crop_resource,
    mock_bus
):
    """
    Verify resources with positive moisture flux absorb moisture
    up to the configured saturation ceiling.
    """
    mechanic = SeasonMechanics()

    mock_crop_resource.state.position = Position(100, 132)
    mock_crop_resource.state.layer = "0"
    mock_crop_resource.state.retention = 5.0
    mock_crop_resource.state.moisture_flux = 1.0

    mock_board.clear()
    mock_board.add([mock_crop_resource])

    mechanic.update(mock_board, delta=1.0, bus=mock_bus, payload=None)

    # 5.0 initial + (1.0 flux * 10.0 diffusion_rate * 1.0 delta) = 15.0
    assert mock_crop_resource.state.retention == pytest.approx(15.0, rel=1e-3)


@pytest.mark.seasons
@pytest.mark.ecology
def test_season_mechanics_hydrological_evaporation_dry_soil(
    mock_board,
    mock_crop_resource,
    mock_bus
):
    """
    Verify resources away from water lose moisture to evaporation modulated by season.
    """
    mechanic = SeasonMechanics()
    mock_board.calendar = CalendarState(season=Seasons.SUMMER.value)

    mock_crop_resource.state.position = Position(500, 500)
    mock_crop_resource.state.layer = "0"
    mock_crop_resource.state.retention = 20.0

    mock_board.clear()
    mock_board.add([mock_crop_resource])

    # Summer evaporation modifier = 1.5, base rate = 1.0 -> 1.5/s decay
    mechanic.update(mock_board, delta=2.0, bus=mock_bus, payload=None)

    # 20.0 - (1.0 * 1.5 * 2.0) = 17.0
    assert mock_crop_resource.state.retention == pytest.approx(17.0, rel=1e-3)


@pytest.mark.seasons
@pytest.mark.ecology
def test_season_mechanics_annual_crop_stage_transition(
    mock_board, mock_season_mechanics, mock_bus
):
  crop = mock_board.asset("some-lettuce")
  mock_board.calendar = CalendarState(
      season=Seasons.SPRING.value, cycle=Cycles.ONSET.value, period=0
  )
  crop.state.stage = AnnualStages.SPROUT.value
  crop.state.retention = 25.0

  mock_season_mechanics.update(mock_board, delta=0.1, bus=mock_bus, payload=None)

  assert crop.state.stage == AnnualStages.GROWTH.value


@pytest.mark.seasons
@pytest.mark.ecology
def test_season_mechanics_annual_crop_winter_decay(
    mock_board,
    mock_crop_resource,
    mock_lambda_executors,
    mock_bus
):
    """
    Verify unharvested annual crops decay to stump when winter arrives.
    """
    mechanic = SeasonMechanics()
    mechanic.executors = mock_lambda_executors

    mock_board.calendar = CalendarState(
        season=Seasons.WINTER.value,
        cycle=Cycles.ONSET.value,
        period=0
    )

    mock_crop_resource.state.stage = AnnualStages.GROWTH.value
    mock_crop_resource.state.retention = 10.0

    mock_board.clear()
    mock_board.add([mock_crop_resource])

    mechanic.update(mock_board, delta=0.1, bus=mock_bus, payload=None)

    assert mock_crop_resource.state.stage == AnnualStages.STUMP.value


@pytest.mark.seasons
@pytest.mark.ecology
def test_season_mechanics_perennial_tree_genesis_progression(
    mock_board, mock_season_mechanics, mock_bus
):
  tree = mock_board.asset("the-mighty-oak")
  mock_board.calendar = CalendarState(
      season=Seasons.SPRING.value, cycle=Cycles.PEAK.value, period=0
  )
  tree.state.stage = PerennialStages.SAPLING.value
  tree.state.retention = 20.0

  mock_season_mechanics.update(mock_board, delta=0.1, bus=mock_bus, payload=None)

  assert tree.state.stage == PerennialStages.BUSH.value


@pytest.mark.seasons
@pytest.mark.ecology
def test_season_mechanics_perennial_tree_homeostasis_apoptosis(
    mock_board,
    mock_tree_resource,
    mock_lambda_executors,
    mock_bus
):
    """
    Verify a mature tree in Homeostasis transitions to dying when severely dehydrated.
    """
    mechanic = SeasonMechanics()
    mechanic.executors = mock_lambda_executors

    mock_board.calendar = CalendarState(
        season=Seasons.SUMMER.value,
        cycle=Cycles.PEAK.value
    )

    mock_tree_resource.state.stage = PerennialStages.HEALTHY.value
    mock_tree_resource.state.retention = 2.0

    mock_board.clear()
    mock_board.add([mock_tree_resource])

    mechanic.update(mock_board, delta=0.1, bus=mock_bus, payload=None)

    assert mock_tree_resource.state.stage == PerennialStages.DYING.value


@pytest.mark.seasons
@pytest.mark.ecology
def test_season_mechanics_perennial_tree_apoptosis_recovery(
    mock_board,
    mock_tree_resource,
    mock_lambda_executors,
    mock_bus
):
    """
    Verify a dying tree recovers directly into Homeostasis (vibrant) when rehydrated in Spring.
    """
    mechanic = SeasonMechanics()
    mechanic.executors = mock_lambda_executors

    mock_board.calendar = CalendarState(
        season=Seasons.SPRING.value,
        cycle=Cycles.PEAK.value
    )

    mock_tree_resource.state.stage = PerennialStages.DYING.value
    mock_tree_resource.state.retention = 25.0

    mock_board.clear()
    mock_board.add([mock_tree_resource])

    mechanic.update(mock_board, delta=0.1, bus=mock_bus, payload=None)

    assert mock_tree_resource.state.stage == PerennialStages.VIBRANT.value


@pytest.mark.seasons
def test_season_event_handler_reconstructs_screens(
    mock_board, mock_screen, mock_provider, mock_bus
):
  handler = SeasonEventHandler()
  mock_board.calendar = CalendarState(
      season=Seasons.AUTUMN.value, cycle=Cycles.PEAK.value, period=1
  )

  context = EventContext(
      board=mock_board,
      screens={"0": mock_screen},
      provider=mock_provider,
      bus=mock_bus,
  )

  handler.handle(SeasonEvent(), context)

  assert len(mock_screen.reconstructed_tiles) == 1
  assert mock_screen.reconstructed_calendar.season == Seasons.AUTUMN.value
  assert mock_screen.reconstructed_calendar.cycle == Cycles.PEAK.value
  assert mock_screen.reconstructed_calendar.period == 1
  

@pytest.mark.seasons
@pytest.mark.ecology
def test_season_mechanics_stage_evaluation_throttling(
    mock_board,
    mock_crop_resource,
    mock_lambda_executors,
    mock_bus
):
    """
    Verify biological stage evaluation executes on frame 0, throttles on
    sub-second ticks, and re-evaluates once the accumulator reaches 1.0s.
    """
    mechanic = SeasonMechanics()
    mechanic.executors = mock_lambda_executors

    mock_board.calendar = CalendarState(
        season=Seasons.SPRING.value,
        cycle=Cycles.ONSET.value,
        period=0
    )

    mock_crop_resource.state.stage = AnnualStages.SPROUT.value
    mock_crop_resource.state.retention = 25.0

    mock_board.clear()
    mock_board.add([mock_crop_resource])

    # Tick 1: Evaluates immediately on tick 0
    mechanic.update(mock_board, delta=0.1, bus=mock_bus, payload=None)
    assert mock_crop_resource.state.stage == AnnualStages.GROWTH.value

    # Reset stage manually to verify throttling skips immediate re-evaluation
    mock_crop_resource.state.stage = AnnualStages.SPROUT.value

    # Tick 2: delta=0.1 -> accumulator=0.1 < 1.0 -> throttled, stage unchanged
    mechanic.update(mock_board, delta=0.1, bus=mock_bus, payload=None)
    assert mock_crop_resource.state.stage == AnnualStages.SPROUT.value

    # Tick 3: delta=0.9 -> accumulator=1.0 >= 1.0 -> evaluates again
    mechanic.update(mock_board, delta=0.9, bus=mock_bus, payload=None)
    assert mock_crop_resource.state.stage == AnnualStages.GROWTH.value