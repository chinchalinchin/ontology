"""
@test.fixtures

# Ontology: tests.unit.fixtures.properties.cursors

Mock Cursor Property fixtures aligned with src/assets/cursors/main.yaml.
"""
# External Libraries
import pytest

# Application Libraries
from app.models.properties import (
    CursorProperties,
    CursorPropertyInstances,
)

# Cython Libraries
from libs.core.models import Dimensions


@pytest.fixture
def mock_cursor_properties() -> CursorPropertyInstances:
    return CursorPropertyInstances(
        expressions={
            "bubbles": CursorProperties(
                dimensions=Dimensions(w=16, l=16),
                frames=[
                    "affection",
                    "agreement",
                    "anger",
                    "confusion",
                    "curiosity",
                    "disagreement",
                    "loquacity",
                    "surprise",
                    "tired",
                ],
            ),
        },
        projectiles={
            "arrow": CursorProperties(dimensions=Dimensions(w=30, l=21)),
            "bolt": CursorProperties(dimensions=Dimensions(w=32, l=10)),
        },
    )