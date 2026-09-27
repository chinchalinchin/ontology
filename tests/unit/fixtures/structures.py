"""
# Ontology: tests.unit.fixtures.components

Application component fixtures
"""
# External Libraries
import pytest

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

