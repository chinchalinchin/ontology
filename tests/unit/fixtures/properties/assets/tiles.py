"""
@domain.test
@tests.fixtures
@app.asset
@asset.property
@category.tiles

# Ontology: Tests - tests.unit.fixtures.properties.tiles

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
from libs.core.models import Dimensions


@pytest.fixture
def mock_tile_properties() -> TilePropertyInstances:
    return TilePropertyInstances(
        grid={
            "focus": TileProperties(dimensions=Dimensions(w=32, l=32)),
            "cell": TileProperties(dimensions=Dimensions(w=32, l=32)),
        },
        environ={
            "temperate": TileProperties(
                priority=-4,
                dimensions=Dimensions(w=32, l=32),
                friction=100,
            ),
            "highland": TileProperties(
                priority=-4,
                dimensions=Dimensions(w=32, l=32),
                friction=150,
            ),
        },
    )