# External Libraries
import pytest

# Application Libraries
from app.config.enums import ( 
    Directions,
    Seasons

)
from app.models.state import (
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

# --------------------------------------------------------------------------
# -------------------------------------------------------------- MOCK STATES
# --------------------------------------------------------------------------

@pytest.fixture
def mock_plot_state() -> PlotState:
    return PlotState(
        current="town-locked",
        previous=[]
    )


# ------------------------------------------------------------ TILE STATES

@pytest.fixture
def mock_multiplier_state() -> MultiplierState:
    return MultiplierState(
        id="temperate",
        name="the-steppe",
        layer="0",
        position=Position(x=0, y=0),
        multiple=Multiple(nx=10, ny=10)
    )


# -------------------------------------------------------- GEOGRAPHY STATES

@pytest.fixture
def mock_shoreline_state() -> ShorelineState:
    return ShorelineState(
        id="grassy-shore",
        name="shoreline-1",
        layer="0",
        position=Position(x=70, y=0),
        height=0,
        depth=0,
        orientation=Directions.LEFT.value,
        season=Seasons.SPRING.value,
        length=32,
        thickness=8,
        bidirectional=True,
        hitboxes=[
            Hitbox(Position(0, 0), Dimensions(32, 32))
        ]
    )

# ------------------------------------------------------- PROJECTILE STATES

@pytest.fixture
def mock_motor_state() -> MotorState:
    return MotorState(
        id="arrow-1",
        layer="0",
        position=Position(x=70, y=50),
        velocity=Velocity(vx=50.0, vy=0.0)
    )
