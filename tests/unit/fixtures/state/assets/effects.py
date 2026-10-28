"""
# Ontology: tests.unit.fixtures.state.effects

Mock Effect State Fixtures aligned with src/data/state/world-01/effects/.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    Intentions,
    Directions,
)
from app.models.state import (
    EffectStateInstances,
    ReactableState,
    FluidState,
)

# Cython Libraries
from libs.core.models import Position


@pytest.fixture
def mock_fluid_state() -> FluidState:
    return FluidState(
        id="waterflow",
        name="jasilynns-tears-00",
        layer="0",
        position=Position(x=60, y=0),
        flow=2,
        source=Directions.DOWN.value,
    )


@pytest.fixture
def mock_fluid_state_alt() -> FluidState:
    return FluidState(
        id="waterflow",
        name="jasilynns-tears-03",
        layer="0",
        flow=4,
        position=Position(x=595, y=0),
        source=Directions.DOWN.value,
    )


@pytest.fixture
def mock_reactable_state() -> ReactableState:
    return ReactableState(
        id="spinning-dummy",
        name="test-dummy",
        layer="0",
        position=Position(x=999, y=885),
        intention=Intentions.ATTACK.value,
        cooldown=30,
    )


@pytest.fixture
def mock_effect_states(
    mock_fluid_state,
    mock_fluid_state_alt,
    mock_reactable_state,
) -> EffectStateInstances:
    return EffectStateInstances(
        fluids=[
            mock_fluid_state,
            mock_fluid_state_alt,
        ],
        reactables=[
            mock_reactable_state,
        ],
    )