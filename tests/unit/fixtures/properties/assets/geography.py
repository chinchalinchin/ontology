"""
@domain.test
@tests.fixtures
@app.asset
@asset.property
@category.geography

# Ontology: Tests - tests.unit.fixtures.properties.geography

Mock Geography Property fixtures
"""
# External Libraries
import pytest

# Application Libraries
from app.models.properties import (
    GeographyProperties,
    GeographyPropertyInstances,
)

# Cython Libraries
from libs.core.models import Dimensions


@pytest.fixture
def mock_geography_properties() -> GeographyPropertyInstances:
    return GeographyPropertyInstances(
        shorelines={
            "temperate-banks": GeographyProperties(
                tile="temperate",
                fluid="waterflow",
                dimensions=Dimensions(w=41, l=41),
                thickness=22,
                mass=-1,
                priority=-2,
                hitboxes=None,
            ),
        },
    )