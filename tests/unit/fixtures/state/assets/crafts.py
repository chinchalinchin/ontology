"""
# Ontology: tests.unit.fixtures.state.crafts

Mock Craft State Fixtures.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    Directions,
    Geologics,
    Organics,
    Orientations,
)
from app.models.state import (
    CraftStateInstances,
    PropertyState,
    StairState,
)

# Cython Libraries
from libs.core.models import (
    Position,
    Multiple,
)


@pytest.fixture
def mock_bridge_state() -> PropertyState:
    return PropertyState(
        id="arch",
        name="the-bridge-of-tears-left",
        layer="0",
        material=Geologics.GRANITE.value,
        blueprint=Orientations.HORIZONTAL.value,
        position=Position(x=30, y=290),
        multiple=Multiple(nx=2, ny=0),
        owner="evil-empress-jasilynn",
    )


@pytest.fixture
def mock_stair_state() -> StairState:
    return StairState(
        id="steps",
        name="stairs-main",
        layer="0",
        material=Geologics.GRANITE.value,
        blueprint=Directions.UP.value,
        position=Position(x=100, y=100),
        delta=1,
        elevation=0,
    )


@pytest.fixture
def mock_property_state() -> PropertyState:
    return PropertyState(
        id="home",
        name="castle",
        layer="0",
        material=Geologics.GRANITE.value,
        position=Position(x=250, y=250),
    )


@pytest.fixture
def mock_craft_states() -> CraftStateInstances:
    return CraftStateInstances(
        bridges=[
            PropertyState(
                id="arch",
                name="the-bridge-of-tears-left",
                layer="0",
                material=Geologics.GRANITE.value,
                blueprint=Orientations.HORIZONTAL.value,
                position=Position(x=30, y=290),
                multiple=Multiple(nx=2, ny=0),
                owner="evil-empress-jasilynn",
            ),
            PropertyState(
                id="arch",
                name="the-bridge-of-tears-right",
                layer="0",
                material=Geologics.GRANITE.value,
                blueprint=Orientations.HORIZONTAL.value,
                position=Position(x=570, y=290),
                multiple=Multiple(nx=2, ny=0),
                owner="evil-empress-jasilynn",
            ),
            PropertyState(
                id="suspension",
                name="the-downtown-bridge",
                layer="0",
                material=Organics.WOOD.value,
                blueprint=Orientations.VERTICAL.value,
                position=Position(x=850, y=425),
                multiple=Multiple(nx=0, ny=4),
                owner="evil-empress-jasilynn",
            ),
            PropertyState(
                id="suspension",
                name="the-harvest-bridge",
                layer="0",
                material=Organics.COTTON.value,
                blueprint=Orientations.HORIZONTAL.value,
                position=Position(x=140, y=1200),
                multiple=Multiple(nx=3, ny=0),
                owner="evil-empress-jasilynn",
            ),
        ],
    )