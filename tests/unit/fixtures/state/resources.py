"""
# Ontology: tests.unit.fixtures.state.resources

Mock Object State Fixtures
"""
# External Libraries
import pytest

# Application Libraries
from app.config.enums import (
    PerennialStages
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
def mock_resource_state() -> ResourceState:
    return ResourceState(
        id="deciduous", 
        name="the-mighty-oak",
        layer="0", 
        position=Position(x=670, y=206),
        stage=PerennialStages.SAPLING 
    )

