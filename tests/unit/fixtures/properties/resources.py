"""
# Ontology: tests.unit.fixtures.properties.resources
Mock Geography Property fixtures.
"""
# External Libraries
import pytest

# Application Libraries
from app.config.enums import (
    Lifespans
)
from app.models.properties import (
    ResourceProperties,
    ResourcePropertyInstances,
)

# Cython Libraries
from libs.core.models import (
    Dimensions, 
)

@pytest.fixture
def mock_resource_properties() -> ResourcePropertyInstances:
    """ResourceProperties dataclass fixture."""
    return ResourcePropertyInstances(
        trees = {
            "deciduous": ResourceProperties(
                dimensions=Dimensions(w=94, l=137),
                lifespan=Lifespans.PERENNIAL.value,
                loot="wood",
                mass=0,
                hitboxes=[]
            )
        }
    )

