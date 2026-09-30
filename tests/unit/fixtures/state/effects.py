"""
# Ontology: tests.unit.fixtures.state

Mock Asset State Fixtures
"""
# External Libraries
import pytest

# Application Libraries

from app.config.enums import ( 
    # -------- SPRITE FIELDS
    Intentions,
    Directions,
)
from app.models.state import (
    ReactableState,
    FluidState,
    AnimationState,
)

# Cython Libraries
from libs.core.models import (
    Dimensions, 
    Position,
    Hitbox,
)

# ---------------------------------------------------------- EFFECT STATES

@pytest.fixture
def mock_fluid_state() -> FluidState:
    return FluidState(
        id="waterflow-01",
        name="jasilynns-tears",
        layer="0",
        position=Position(x=70, y=0),
        source=Directions.DOWN.value,
        flow=2,
        length=0,
        dirty=True
    )


@pytest.fixture
def mock_fluid_state_alt() -> FluidState:
    return FluidState(
        id="waterflow-01",
        name="jasilynns-tears-alt",
        layer="0",
        position=Position(x=200, y=100),
        source=Directions.LEFT.value,
        flow=1,
        length=100,
        hitboxes=[Hitbox(Position(-100, 0), Dimensions(100, 32))]
    )


@pytest.fixture
def mock_fluid_state_alt2() -> FluidState:
    """
    Secondary fluid emitter state adjacent to fluid-1's East flank.
    """
    return FluidState(
        id="waterflow-01",
        name="fluid-adjacent",
        layer="0",
        position=Position(x=102, y=0),
        source=Directions.DOWN.value,
        flow=1,
        length=320,
        dirty=True
    )

@pytest.fixture
def mock_reactable_state() -> ReactableState:
    return ReactableState(
        id="reactable-1",
        layer="0",
        depth=0,
        height=None,
        position=Position(x=200, y=200),
        animation=AnimationState(),
        intention=Intentions.ATTACK.value,
        active=True
    )
