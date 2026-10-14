"""
# Ontology: tests.unit.fixtures.state.crafts

Mock Craft State Fixtures
"""
# External Libraries
import pytest

# Application Libraries

from app.config.enums import ( 
    Orientations,
    Directions
)
from app.models.state import (
    PlatformState,
    PropertyState,
    OrientedState,
    StairState
)

# Cython Libraries
from libs.core.models import (
    Position,
    Multiple,
)

# ------------------------------------------------------------ CRAFT STATES

@pytest.fixture
def mock_property_state() -> PropertyState:
    return PropertyState(
        id="strut-castle", 
        name="castle", 
        layer="0", 
        position=Position(x=250, y=250)
    )


@pytest.fixture
def mock_property_state_alt() -> PropertyState:
    return PropertyState(
        id="strut-wall",
        name="wall",
        layer="brick-house-compose-layer",
        position=Position(x=0, y=0)
    )


@pytest.fixture
def mock_property_state_alt2() -> PropertyState:
    return PropertyState(
        id="strut-floor",
        name="floor",
        layer="brick-house-compose-layer",
        position=Position(x=0, y=96)
    )


@pytest.fixture
def mock_bridge_state() -> OrientedState:
    """
    Bridge craft state initialized to an idle coordinate clear of fluid corridors.
    """
    return OrientedState(
        id="wood-bridge",
        name="bridge-main",
        layer="0",
        position=Position(x=200, y=250),
        orientation=Orientations.HORIZONTAL.value,
        multiple=Multiple(nx=1, ny=1),
        owner="player"
    )

@pytest.fixture
def mock_stair_state() -> StairState:
    return StairState(
        id="stairs-stone",
        name="stairs-main",
        layer="0",
        position=Position(x=100, y=100),
        direction=Directions.UP.value,
        delta=1,
        elevation=0
    )

@pytest.fixture
def mock_platform_state() -> PlatformState:
    return PlatformState(
        id="platform-marble",
        name="platform-main",
        layer="0",
        elevation=0,
        position=Position(x=350, y=50)
    )