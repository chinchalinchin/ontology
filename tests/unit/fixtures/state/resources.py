"""
# Ontology: tests.unit.fixtures.state.resources

Mock Object State Fixtures
"""
# External Libraries
import pytest

# Application Libraries
from app.config.enums import (
    PerennialStages,
    AnnualStages
)
from app.models.state import (
    ResourceState
)

# Cython Libraries
from libs.core.models import (
    Position,
    Velocity,
)

# ------------------------------------------------------------ OBJECT STATES

@pytest.fixture
def mock_tree_state() -> ResourceState:
    return ResourceState(
        id="deciduous", 
        name="the-mighty-oak",
        layer="0", 
        position=Position(x=670, y=206),
        stage=PerennialStages.SAPLING.value,
        retention=0.0,
        moisture_flux=0.0
    )

@pytest.fixture
def mock_crop_state() -> ResourceState:
    return ResourceState(
        id="lettuce",
        name="some-lettuce",
        layer="0",
        position=Position(x=415, y=390),
        stage=AnnualStages.SPROUT.value,
        retention=0.0,
        moisture_flux=0.0
    )