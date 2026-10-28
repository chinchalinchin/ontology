"""
# Ontology: tests.unit.fixtures.state.world

Mock World, Tile, Geography, and Cursor State Fixtures aligned with world-01.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    Directions,
    Seasons,
)
from app.models.state import (
    TileStateInstances,
    PlotState,
    MultiplierState,
    ShorelineState,
    MotorState,
)

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Position,
    Multiple,
    Velocity,
    Hitbox,
)


@pytest.fixture
def mock_plot_state() -> PlotState:
    return PlotState(
        current="castle-dawn-locked",
        previous=[],
    )


@pytest.fixture
def mock_multiplier_state() -> MultiplierState:
    return MultiplierState(
        id="temperate",
        name="the-steppe",
        layer="0",
        position=Position(x=0, y=0),
        multiple=Multiple(nx=100, ny=100),
    )


@pytest.fixture
def mock_tile_states(mock_multiplier_state) -> TileStateInstances:
    return TileStateInstances(
        environ=[mock_multiplier_state],
    )


@pytest.fixture
def mock_shoreline_state() -> ShorelineState:
    return ShorelineState(
        id="temperate-banks",
        name="shoreline-1",
        layer="0",
        position=Position(x=70, y=0),
        orientation=Directions.LEFT.value,
        season=Seasons.SPRING.value,
        length=41,
        thickness=22,
        bidirectional=True,
        hitboxes=[
            Hitbox(Position(0, 0), Dimensions(41, 41)),
        ],
    )


@pytest.fixture
def mock_motor_state() -> MotorState:
    return MotorState(
        id="arrow",
        name="feathered-arrow",
        layer="0",
        position=Position(x=70, y=50),
        velocity=Velocity(vx=50.0, vy=0.0),
    )