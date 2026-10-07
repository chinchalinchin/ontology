"""
# Ontology: tests.unit.fixtures.properties.tiles

Mock Tile Property fixtures.
"""
# External Libraries
import pytest

# Application Libraries
from app.models.properties import (
    TileProperties,
    TilePropertyInstances,
)

# Cython Libraries
from libs.core.models import (
    Dimensions, 
)


@pytest.fixture
def mock_tile_properties() -> TilePropertyInstances:
    return TilePropertyInstances(
        back = {
            'temperate': TileProperties(
                dimensions=Dimensions(w=32, l=32),
                friction=100
            )       
        }
    )