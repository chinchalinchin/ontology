"""
# Ontology: tests.unit.fixtures.state.objects

Mock Object State Fixtures aligned with src/data/state/world-01/objects/.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    Chromatics,
    Geologics,
    Metallics,
    Organics,
)
from app.models.state import (
    ObjectStateInstances,
    ContainerState,
    DialogueState,
    DoorState,
    MotiveState,
    SwitchState,
)

# Cython Libraries
from libs.core.models import (
    Position,
    Velocity,
)


@pytest.fixture
def mock_positional_state() -> MotiveState:
    return MotiveState(
        id="box",
        name="castle-dawn-barrel-00",
        material=Organics.WOOD.value,
        layer="0",
        position=Position(x=200, y=390),
        velocity=Velocity(vx=0.0, vy=0.0),
    )


@pytest.fixture
def mock_obstacle_state() -> MotiveState:
    return MotiveState(
        id="gray-rock-00",
        name="jasilynns-rock",
        layer="0",
        position=Position(x=68, y=600),
    )


@pytest.fixture
def mock_obstacle_state_alt() -> MotiveState:
    return MotiveState(
        id="gray-rock-00",
        name="jasilynns-other-rock",
        layer="0",
        position=Position(x=632, y=600),
    )


@pytest.fixture
def mock_sign_state() -> DialogueState:
    return DialogueState(
        id="plaque",
        name="castle-dawn-sign-00",
        layer="0",
        persona="castle-dawn-sign",
        lexicon="spring",
        material=Geologics.LIMESTONE.value,
        position=Position(x=430, y=330),
    )


@pytest.fixture
def mock_door_state() -> DoorState:
    return DoorState(
        id="panel",
        name="wood-door",
        material=Chromatics.NEUTRAL.value,
        layer="0",
        outlayer="brick-house-compose-layer-1",
        position=Position(x=100, y=100),
        out=Position(x=20, y=20),
    )


@pytest.fixture
def mock_switch_state() -> SwitchState:
    return SwitchState(
        id="postern",
        name="cool-gate",
        material=Geologics.GRANITE.value,
        layer="0",
        position=Position(x=170, y=180),
        switch=True,
    )


@pytest.fixture
def mock_switch_state_alt() -> SwitchState:
    return SwitchState(
        id="stone-switch",
        name="plate-1",
        layer="0",
        position=Position(x=30, y=30),
        switch=False,
        link="postern",
    )


@pytest.fixture
def mock_container_state() -> ContainerState:
    return ContainerState(
        id="trunk",
        name="chest-1",
        material=Metallics.IRON.value,
        layer="brick-house-compose-layer-1",
        position=Position(x=100, y=100),
        switch=False,
        content=["gold-coin"],
    )


@pytest.fixture
def mock_object_states(
    mock_positional_state,
    mock_obstacle_state,
    mock_obstacle_state_alt,
    mock_sign_state,
) -> ObjectStateInstances:
    return ObjectStateInstances(
        crates=[mock_positional_state],
        obstacles=[
            mock_obstacle_state,
            mock_obstacle_state_alt,
        ],
        signs=[mock_sign_state],
    )