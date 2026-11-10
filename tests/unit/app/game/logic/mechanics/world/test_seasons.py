"""
@domain.test
@test.unit
@app.mechanic
@workflow.seasons

# Ontology: Tests - tests.unit.app.game.logic.mechanics.world.test_seasons

Unit tests verifying SeasonMechanics macro-temporal calendar integration,
hydrological moisture diffusion, MoistureField potential evaluation,
and declarative biological stage progression.
"""
# External Libraries
import pytest

# Application Libraries
import app.static.settings as settings
from app.static.semantics import (
    AssetInstances,
    Seasons,
    Cycles,
    AnnualStages,
    PerennialStages,
    Mechanics,
)
from app.models.menus import (
    SeasonEvent,
)
from app.game.menus.core import EventData
from app.game.menus.handlers.seasons import SeasonEventHandler

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_mechanic,
    pytest.mark.workflow_seasons,
    pytest.mark.workflow_ecology,
]

# -----------------------------------------------------
# -------------------------------- TEMPORAL INTEGRATION
# -----------------------------------------------------


def test_season_mechanics_temporal_period_cycle_advancement(
    mock_board,
    mock_mechanic,
    mock_bus,
):
    mock_board.calendar.year = 1
    mock_board.calendar.season = Seasons.SPRING.value
    mock_board.calendar.cycle = Cycles.ONSET.value
    mock_board.calendar.period = 0
    mock_board.calendar.elapsed = 0.0

    mechanics = mock_mechanic(Mechanics.SEASON.value)
    period_duration = mechanics.period

    mechanics.update(
        mock_board, delta=period_duration, bus=mock_bus, payload=None
    )

    assert mock_board.calendar.period == 1
    assert mock_board.calendar.cycle == Cycles.ONSET.value
    assert mock_board.calendar.season == Seasons.SPRING.value
    assert len(mock_bus) == 1
    assert isinstance(mock_bus.popleft(), SeasonEvent)

    mechanics.update(
        mock_board, delta=period_duration * 2, bus=mock_bus, payload=None
    )

    assert mock_board.calendar.period == 0
    assert mock_board.calendar.cycle == Cycles.PEAK.value
    assert mock_board.calendar.season == Seasons.SPRING.value


def test_season_mechanics_temporal_season_year_rollover(
    mock_board,
    mock_mechanic,
    mock_bus,
):
    """
    Verify complete progression through decline rolls season, and winter rolls year.
    """
    mechanics = mock_mechanic(Mechanics.SEASON.value)
    mock_board.calendar.year = 1
    mock_board.calendar.season = Seasons.WINTER.value
    mock_board.calendar.cycle = Cycles.DECLINE.value
    mock_board.calendar.period = 2
    mock_board.calendar.elapsed = 0.0

    mechanics.update(
        mock_board, delta=mechanics.period, bus=mock_bus, payload=None
    )

    assert mock_board.calendar.period == 0
    assert mock_board.calendar.cycle == Cycles.ONSET.value
    assert mock_board.calendar.season == Seasons.SPRING.value
    assert mock_board.calendar.year == 2
    assert len(mock_bus) == 1
    assert isinstance(mock_bus.popleft(), SeasonEvent)


# -----------------------------------------------------
# ----------------------------- HYDROLOGICAL DIFFUSION
# -----------------------------------------------------


def test_season_mechanics_hydrological_diffusion_near_water(
    mock_board,
    mock_mechanic,
    mock_bus,
):
    """
    Verify resources with positive moisture flux absorb moisture
    proportionally to DIFFUSION_RATE.
    """
    mechanics = mock_mechanic(Mechanics.SEASON.value)
    crop = mock_board.instances(AssetInstances.CROPS.value)[0]
    crop.state.retention = 5.0
    crop.state.moisture_flux = 1.0

    mechanics.update(mock_board, delta=1.0, bus=mock_bus, payload=None)

    # 5.0 initial + (1.0 flux * 10.0 diffusion_rate * 1.0 delta) = 15.0
    assert crop.state.retention == pytest.approx(15.0, rel=1e-3)


def test_season_mechanics_hydrological_evaporation_dry_soil(
    mock_board,
    mock_mechanic,
    mock_bus,
):
    """
    Verify resources with zero moisture flux lose moisture to evaporation modulated by season.
    """
    mechanics = mock_mechanic(Mechanics.SEASON.value)
    crop = mock_board.instances(AssetInstances.CROPS.value)[0]
    mock_board.calendar.season = Seasons.SUMMER.value
    mock_board.calendar.elapsed = 0.0

    crop.state.retention = 20.0
    crop.state.moisture_flux = 0.0

    # Summer evaporation modifier = 1.5, base rate = 1.0 -> 1.5/s decay
    mechanics.update(mock_board, delta=2.0, bus=mock_bus, payload=None)

    # 20.0 - (1.0 * 1.5 * 2.0) = 17.0
    assert crop.state.retention == pytest.approx(17.0, rel=1e-3)


def test_season_mechanics_hydrological_retention_clamping(
    mock_board,
    mock_mechanic,
    mock_bus,
):
    """
    Verify moisture retention clamps to [0.0, settings.MAX_RETENTION].
    """
    mechanics = mock_mechanic(Mechanics.SEASON.value)
    crop = mock_board.instances(AssetInstances.CROPS.value)[0]
    tree = mock_board.instances(AssetInstances.TREES.value)[0]

    crop.state.retention = 95.0
    crop.state.moisture_flux = 2.0

    tree.state.retention = 0.5
    tree.state.moisture_flux = 0.0

    mechanics.update(mock_board, delta=2.0, bus=mock_bus, payload=None)

    assert crop.state.retention == pytest.approx(float(settings.MAX_RETENTION))
    assert tree.state.retention == pytest.approx(0.0)


@pytest.mark.physics_fields
def test_moisture_field_superposition_and_cutoff(mock_moisture_field):
    """
    Verify MoistureField evaluates line streams, degenerate point streams,
    and annular pools within cutoff radii and zeroes out beyond R_max.
    """
    mock_moisture_field.add_stream(0.0, 0.0, 0.0, 100.0, flow=0)
    mock_moisture_field.add_pool(50.0, 50.0, radius=10.0, flow=0)
    assert mock_moisture_field.evaluate(0.0, 50.0) == 0.0

    mock_moisture_field.add_stream(0.0, 0.0, 0.0, 100.0, flow=1)
    # Directly on the stream axis (dist = 0): phi_0 * flow * exp(0) = 1.0
    assert mock_moisture_field.evaluate(0.0, 50.0) == pytest.approx(
        settings.BASE_MOISTURE_POTENTIAL
    )
    # Beyond cutoff (dist = 65.0 > sigma * 1 = 64.0)
    assert mock_moisture_field.evaluate(65.0, 50.0) == 0.0

    # Pool evaluation inside radius (dist = 0) and superposition
    mock_moisture_field.add_pool(0.0, 50.0, radius=16.0, flow=2)
    assert mock_moisture_field.evaluate(0.0, 50.0) == pytest.approx(
        settings.BASE_MOISTURE_POTENTIAL * 3.0
    )

    mock_moisture_field.clear()
    assert mock_moisture_field.evaluate(0.0, 50.0) == 0.0


# -----------------------------------------------------
# ----------------------------- ANNUAL CROP LIFECYCLE
# -----------------------------------------------------


def test_season_mechanics_annual_crop_stage_transition(
    mock_board,
    mock_mechanic,
    mock_bus,
):
    mechanics = mock_mechanic(Mechanics.SEASON.value)
    crop = mock_board.instances(AssetInstances.CROPS.value)[0]
    mock_board.calendar.season = Seasons.SPRING.value
    mock_board.calendar.cycle = Cycles.ONSET.value
    mock_board.calendar.period = 0

    crop.state.stage = AnnualStages.SPROUT.value
    crop.state.retention = 55.0
    crop.state.moisture_flux = 0.0

    mechanics.update(mock_board, delta=0.1, bus=mock_bus, payload=None)

    assert crop.state.stage == AnnualStages.GROWTH.value


def test_season_mechanics_annual_crop_full_lifecycle(
    mock_board,
    mock_mechanic,
    mock_bus,
):
    """
    Verify annual crop progresses through growth -> stalk -> bloom -> harvested stump -> spring sprout.
    """
    mechanics = mock_mechanic(Mechanics.SEASON.value)
    crop = mock_board.instances(AssetInstances.CROPS.value)[0]
    crop.state.moisture_flux = 0.0

    # 1. Summer: growth -> stalk (requires retention >= 75.0)
    mock_board.calendar.season = Seasons.SUMMER.value
    crop.state.stage = AnnualStages.GROWTH.value
    crop.state.retention = 80.0
    mechanics.update(mock_board, delta=1.0, bus=mock_bus, payload=None)
    assert crop.state.stage == AnnualStages.STALK.value

    # 2. Autumn: stalk -> bloom (requires retention >= 85.0)
    mock_board.calendar.season = Seasons.AUTUMN.value
    crop.state.retention = 90.0
    mechanics.update(mock_board, delta=1.0, bus=mock_bus, payload=None)
    assert crop.state.stage == AnnualStages.BLOOM.value

    # 3. Autumn unharvested: remains in bloom
    crop.state.harvested = False
    mechanics.update(mock_board, delta=1.0, bus=mock_bus, payload=None)
    assert crop.state.stage == AnnualStages.BLOOM.value

    # 4. Autumn harvested: bloom -> stump
    crop.state.harvested = True
    mechanics.update(mock_board, delta=1.0, bus=mock_bus, payload=None)
    assert crop.state.stage == AnnualStages.STUMP.value

    # 5. Spring Onset Period 0: stump -> sprout (requires retention >= 10.0)
    mock_board.calendar.season = Seasons.SPRING.value
    mock_board.calendar.cycle = Cycles.ONSET.value
    mock_board.calendar.period = 0
    crop.state.retention = 15.0
    mechanics.update(mock_board, delta=1.0, bus=mock_bus, payload=None)
    assert crop.state.stage == AnnualStages.SPROUT.value


def test_season_mechanics_annual_crop_winter_decay(
    mock_board,
    mock_mechanic,
    mock_bus,
):
    """
    Verify unharvested annual crops decay to stump when winter arrives.
    """
    mechanics = mock_mechanic(Mechanics.SEASON.value)
    crop = mock_board.instances(AssetInstances.CROPS.value)[0]

    mock_board.calendar.season = Seasons.WINTER.value
    mock_board.calendar.cycle = Cycles.ONSET.value
    mock_board.calendar.period = 0

    crop.state.stage = AnnualStages.GROWTH.value
    crop.state.retention = 10.0
    crop.state.moisture_flux = 0.0

    mechanics.update(mock_board, delta=0.1, bus=mock_bus, payload=None)

    assert crop.state.stage == AnnualStages.STUMP.value


# -----------------------------------------------------
# --------------------------- PERENNIAL TREE LIFECYCLE
# -----------------------------------------------------


def test_season_mechanics_perennial_tree_genesis_progression(
    mock_board,
    mock_mechanic,
    mock_bus,
):
    mechanics = mock_mechanic(Mechanics.SEASON.value)
    tree = mock_board.instances(AssetInstances.TREES.value)[0]
    mock_board.calendar.season = Seasons.SPRING.value
    mock_board.calendar.cycle = Cycles.PEAK.value
    mock_board.calendar.period = 0

    tree.state.stage = PerennialStages.SAPLING.value
    tree.state.retention = 20.0
    tree.state.moisture_flux = 0.0

    mechanics.update(mock_board, delta=0.1, bus=mock_bus, payload=None)

    assert tree.state.stage == PerennialStages.BUSH.value


def test_season_mechanics_perennial_tree_homeostasis_cycle(
    mock_board,
    mock_mechanic,
    mock_bus,
):
    """
    Verify mature tree cycles through healthy -> abscise -> snowcapt -> vibrant -> healthy.
    """
    mechanics = mock_mechanic(Mechanics.SEASON.value)
    tree = mock_board.instances(AssetInstances.TREES.value)[0]
    tree.state.moisture_flux = 0.0
    tree.state.stage = PerennialStages.HEALTHY.value

    # Autumn: healthy -> abscise (retention >= 15.0)
    mock_board.calendar.season = Seasons.AUTUMN.value
    tree.state.retention = 20.0
    mechanics.update(mock_board, delta=1.0, bus=mock_bus, payload=None)
    assert tree.state.stage == PerennialStages.ABSCISE.value

    # Winter: abscise -> snowcapt (retention >= 10.0)
    mock_board.calendar.season = Seasons.WINTER.value
    tree.state.retention = 15.0
    mechanics.update(mock_board, delta=1.0, bus=mock_bus, payload=None)
    assert tree.state.stage == PerennialStages.SNOWCAPT.value

    # Spring: snowcapt -> vibrant (retention >= 15.0)
    mock_board.calendar.season = Seasons.SPRING.value
    tree.state.retention = 20.0
    mechanics.update(mock_board, delta=1.0, bus=mock_bus, payload=None)
    assert tree.state.stage == PerennialStages.VIBRANT.value

    # Summer: vibrant -> healthy (retention >= 20.0)
    mock_board.calendar.season = Seasons.SUMMER.value
    tree.state.retention = 25.0
    mechanics.update(mock_board, delta=1.0, bus=mock_bus, payload=None)
    assert tree.state.stage == PerennialStages.HEALTHY.value


def test_season_mechanics_perennial_tree_homeostasis_apoptosis(
    mock_board,
    mock_mechanic,
    mock_bus,
):
    """
    Verify a mature tree in Homeostasis transitions to dying when severely dehydrated.
    """
    mechanics = mock_mechanic(Mechanics.SEASON.value)
    tree = mock_board.instances(AssetInstances.TREES.value)[0]

    mock_board.calendar.season = Seasons.SUMMER.value
    mock_board.calendar.cycle = Cycles.PEAK.value

    tree.state.stage = PerennialStages.HEALTHY.value
    tree.state.retention = 2.0
    tree.state.moisture_flux = 0.0

    mechanics.update(mock_board, delta=0.1, bus=mock_bus, payload=None)

    assert tree.state.stage == PerennialStages.DYING.value


def test_season_mechanics_perennial_tree_apoptosis_recovery(
    mock_board,
    mock_mechanic,
    mock_bus,
):
    """
    Verify a dying tree recovers directly into Homeostasis (vibrant) when rehydrated in Spring.
    """
    mechanics = mock_mechanic(Mechanics.SEASON.value)
    tree = mock_board.instances(AssetInstances.TREES.value)[0]

    mock_board.calendar.season = Seasons.SPRING.value
    mock_board.calendar.cycle = Cycles.PEAK.value

    tree.state.stage = PerennialStages.DYING.value
    tree.state.retention = 25.0
    tree.state.moisture_flux = 0.0

    mechanics.update(mock_board, delta=0.1, bus=mock_bus, payload=None)

    assert tree.state.stage == PerennialStages.VIBRANT.value


def test_season_mechanics_perennial_tree_apoptosis_death_and_rebirth(
    mock_board,
    mock_mechanic,
    mock_bus,
):
    """
    Verify an unrecovered dying tree progresses dying -> dead -> stump -> sapling.
    """
    mechanics = mock_mechanic(Mechanics.SEASON.value)
    tree = mock_board.instances(AssetInstances.TREES.value)[0]
    tree.state.moisture_flux = 0.0
    tree.state.stage = PerennialStages.DYING.value

    # Autumn dehydrated: dying -> dead (retention < 5.0)
    mock_board.calendar.season = Seasons.AUTUMN.value
    tree.state.retention = 2.0
    mechanics.update(mock_board, delta=1.0, bus=mock_bus, payload=None)
    assert tree.state.stage == PerennialStages.DEAD.value

    # Winter: dead -> stump
    mock_board.calendar.season = Seasons.WINTER.value
    mechanics.update(mock_board, delta=1.0, bus=mock_bus, payload=None)
    assert tree.state.stage == PerennialStages.STUMP.value

    # Spring Onset Period 0 rehydrated: stump -> sapling (retention >= 15.0)
    mock_board.calendar.season = Seasons.SPRING.value
    mock_board.calendar.cycle = Cycles.ONSET.value
    mock_board.calendar.period = 0
    tree.state.retention = 20.0
    mechanics.update(mock_board, delta=1.0, bus=mock_bus, payload=None)
    assert tree.state.stage == PerennialStages.SAPLING.value


# -----------------------------------------------------
# ----------------------- THROTTLING & EVENT HANDLERS
# -----------------------------------------------------

@pytest.mark.menu_handler
@pytest.mark.workflow_rendering
def test_season_event_handler_reconstructs_screens(
    mock_board,
    mock_screen,
    mock_provider,
    mock_bus,
    mock_render,
):
    handler = SeasonEventHandler()
    mock_board.calendar.season = Seasons.AUTUMN.value
    mock_board.calendar.cycle = Cycles.PEAK.value
    mock_board.calendar.period = 1

    data = EventData(
        board=mock_board,
        screens={"0": mock_screen},
        provider=mock_provider,
        bus=mock_bus,
    )
    mock_render.construct.reset_mock()

    handler.handle(SeasonEvent(), data)

    assert mock_render.construct.call_count == 2
    bg_canvas, back_tiles = mock_render.construct.call_args_list[0].args
    fg_canvas, fore_tiles = mock_render.construct.call_args_list[1].args

    assert bg_canvas is mock_screen.bg_canvas
    assert len(back_tiles) == 1
    # 'temperate-autumn-peak-1' -> row 2 (sy=64), col 4 (sx=128), 32x32, multiple 100x100
    _, sx, sy, sw, sl, dx, dy, dw, dl, nx, ny = back_tiles[0]
    assert (sx, sy, sw, sl) == (128, 64, 32, 32)
    assert (dx, dy, dw, dl, nx, ny) == (0, 0, 32, 32, 100, 100)
    assert fg_canvas is mock_screen.fg_canvas
    assert fore_tiles == []


def test_season_mechanics_stage_evaluation_throttling(
    mock_board,
    mock_mechanic,
    mock_bus,
):
    """
    Verify biological stage evaluation executes on frame 0, throttles on
    sub-second ticks, and re-evaluates once the accumulator reaches 1.0s.
    """
    mechanics = mock_mechanic(Mechanics.SEASON.value)
    crop = mock_board.instances(AssetInstances.CROPS.value)[0]

    mock_board.calendar.season = Seasons.SPRING.value
    mock_board.calendar.cycle = Cycles.ONSET.value
    mock_board.calendar.period = 0
    mock_board.calendar.elapsed = 0.0

    crop.state.stage = AnnualStages.SPROUT.value
    crop.state.retention = 60.0
    crop.state.moisture_flux = 0.0

    # Tick 1: Evaluates immediately on tick 0 (_transition_accumulator initialized to 1.0)
    mechanics.update(mock_board, delta=0.1, bus=mock_bus, payload=None)
    assert crop.state.stage == AnnualStages.GROWTH.value

    # Reset stage manually to verify throttling skips immediate re-evaluation
    crop.state.stage = AnnualStages.SPROUT.value

    # Tick 2: delta=0.1 -> accumulator=0.1 < 1.0 -> throttled, stage unchanged
    mechanics.update(mock_board, delta=0.1, bus=mock_bus, payload=None)
    assert crop.state.stage == AnnualStages.SPROUT.value

    # Tick 3: delta=0.9 -> accumulator=1.0 >= 1.0 -> evaluates again
    mechanics.update(mock_board, delta=0.9, bus=mock_bus, payload=None)
    assert crop.state.stage == AnnualStages.GROWTH.value