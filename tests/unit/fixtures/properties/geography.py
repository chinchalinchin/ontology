"""
# Ontology: tests.unit.fixtures.properties.geography

Mock Geography Property fixtures.
"""
# External Libraries
import pytest

# Application Libraries
from app.models.properties import (
    GeographyProperties,
    GeographyPropertyInstances,
)

# Cython Libraries
from libs.core.models import (
    Dimensions, 
)

@pytest.fixture
def mock_geography_properties() -> GeographyPropertyInstances:
    """GeographyProperties dataclass fixture."""
    return GeographyPropertyInstances(
        shorelines = {
            "grassy-shore": GeographyProperties(
                dimensions=Dimensions(w=32, l=32),
                tile="tile-1",
                fluid="waterflow-01",
                thickness=8,
                mass=-1
            )
        }
    )

