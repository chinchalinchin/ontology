"""
# Ontology: tests.unit.fixtures.state.objects

Mock Object State Fixtures
"""
# External Libraries
import pytest

# Application Libraries
from app.models.state import (
    ContainerState,
    DoorState,
    PositionalState,
    SwitchState,
)

# Cython Libraries
from libs.core.models import (
    Position,
    Velocity,
)

# ------------------------------------------------------------ OBJECT STATES

@pytest.fixture
def mock_positional_state() -> PositionalState:
    return PositionalState(
        id="wood-crate", 
        layer="0", 
        position=Position(x=10, y=10), 
        velocity=Velocity(vx=0.0, vy=0.0)
    )


@pytest.fixture
def mock_positional_state_alt() -> PositionalState:
    """
    Raft positional state initialized to an idle coordinate clear of fluid corridors.
    """
    return PositionalState(
        id="wood-raft",
        layer="0",
        position=Position(x=10, y=200),
        velocity=Velocity(vx=0.0, vy=0.0)
    )


@pytest.fixture
def mock_positional_state_alt2() -> PositionalState:
    """
    Upstream crate positional state positioned along the fluid x=70 axis.
    """
    return PositionalState(
        id="wood-crate",
        layer="0",
        position=Position(x=70, y=10),
        velocity=Velocity(vx=0.0, vy=0.0)
    )


@pytest.fixture
def mock_door_state() -> DoorState:
    return DoorState(
        id="door-front",
        layer="0",
        outlayer="brick-house-compose-layer",
        position=Position(x=100, y=100),
        out=Position(x=20, y=20)
    )


@pytest.fixture
def mock_switch_state() -> SwitchState:
    return SwitchState(
        id="castle-gate", 
        layer="0", 
        position=Position(x=170, y=180), 
        switch=True
    )


@pytest.fixture
def mock_switch_state_alt() -> SwitchState:
    return SwitchState(
        id="pressure-plate",
        layer="0",
        depth=0,
        height=None,
        position=Position(x=30, y=30),
        switch=False,
        link="castle-gate"
    )

@pytest.fixture
def mock_container_state() -> ContainerState:
    return ContainerState(
        id="wood-chest",
        layer="brick-house-compose-layer",
        depth=0,
        height=None,
        position=Position(x=100, y=100),
        switch=False,
        content=["gold-coin"]
    )

