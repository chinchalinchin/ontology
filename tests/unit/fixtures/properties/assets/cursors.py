"""
@domain.test
@test.fixtures
@app.asset
@asset.property
@category.cursors

# Ontology: Tests - tests.unit.fixtures.properties.cursors

Mock Cursor Property fixtures aligned.
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