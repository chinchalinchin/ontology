"""
# Ontology: tests.unit.fixtures.state.crafts

Mock Craft State Fixtures
"""
# External Libraries
import pytest

# Application Libraries

from app.config.enums import ( 
    Orientations
)
from app.models.state import (
    PropertyState,
    BridgeState,
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
        name="castle", layer="0", 
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
def mock_bridge_state() -> BridgeState:
    """
    Bridge craft state initialized to an idle coordinate clear of fluid corridors.
    """
    return BridgeState(
        id="wood-bridge",
        name="bridge-main",
        layer="0",
        position=Position(x=200, y=250),
        orientation=Orientations.HORIZONTAL.value,
        multiple=Multiple(nx=1, ny=1),
        owner="player",
        depth=1,
        height=0
    )