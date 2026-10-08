"""
# Ontology: tests.unit.fixtures.structures

Application component fixtures
"""
# External Libraries
import pytest

from app.game.board.fields import MoistureField
from app.game.logic.relations import ShorelineIndex

# Cython Libraries
from libs.core.models import (
    Dimensions, 
    Position, 
    Boundary
)
from libs.core.math.space import Space

# ---------------------------------------------------------------------------
# ----------------------------------------------------------- MOCK STRUCTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_boundary() -> Boundary:
    """Boundary spatial constraint fixture."""
    return Boundary(Position(10, 20), Dimensions(30, 40))


@pytest.fixture
def mock_space_grid() -> Space:
    """
    Fixture providing an initialized Cython Space grid for testing 
    O(1) bucket lookups and broad-phase physics.
    """
    return Space(cell_size=64, max_entities=100)


@pytest.fixture
def mock_shoreline_index(mock_geography_properties):
    """ShorelineIndex fixture compiled from mock properties."""
    return ShorelineIndex.from_properties(mock_geography_properties.shorelines)


@pytest.fixture
def mock_moisture_field() -> MoistureField:
    """
    Continuous hydrological potential field fixture obeying superposition.
    """
    field = MoistureField(sigma=64.0, phi_0=1.0)
    field.add_stream(100.0, 100.0, 100.0, 132.0, flow=2)
    return field