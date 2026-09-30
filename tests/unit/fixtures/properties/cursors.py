"""
# Ontology: tests.unit.fixtures.properties.cursors

Mock Asset Property fixtures.
"""
# External Libraries
import pytest

# Application Libraries
from app.models.properties import (
    CursorProperties,
    CursorPropertyInstances,
)

# Cython Libraries
from libs.core.models import (
    Dimensions, 
)


@pytest.fixture
def mock_cursor_properties() -> CursorPropertyInstances:
    return CursorPropertyInstances(
        projectiles = {
            'arrow-1': CursorProperties(dimensions=Dimensions(w=16, l=16))
        }
    )
