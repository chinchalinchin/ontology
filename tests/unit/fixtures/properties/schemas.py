"""
# Ontology: tests.unit.fixtures.properties.schemas

Mock Property Schema fixtures.
"""
# External Libraries
import pytest

# Application Libraries
from app.models.properties import (
    # -------- FIELDS
    RGBA,
    Outline,
    FontProperties,
    PropertiesSchema,
)

@pytest.fixture
def mock_properties(
    mock_cursor_properties,
    mock_effect_properties,
    mock_geography_properties,
    mock_object_properties,
    mock_sheet_properties,
    mock_widget_properties,
    mock_craft_properties,
    mock_tile_properties
) -> PropertiesSchema:
    return PropertiesSchema(
        cursors = mock_cursor_properties,
        crafts = mock_craft_properties,
        effects = mock_effect_properties,
        geography = mock_geography_properties,
        objects = mock_object_properties,
        sheets = mock_sheet_properties,
        widgets = mock_widget_properties,
        tiles = mock_tile_properties
    )

