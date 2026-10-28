"""
# Ontology: tests.unit.fixtures.state.schemas

Root StateSchema fixture aligned with world-01.
"""
# External Libraries
import pytest

# Application Libraries
from app.models.state import StateSchema


@pytest.fixture
def mock_state(
    mock_sheet_states,
    mock_tile_states,
    mock_craft_states,
    mock_object_states,
    mock_effect_states,
    mock_resource_states,
    mock_plot_state,
) -> StateSchema:
    return StateSchema(
        effects=mock_effect_states,
        sheets=mock_sheet_states,
        tiles=mock_tile_states,
        crafts=mock_craft_states,
        objects=mock_object_states,
        resources=mock_resource_states,
        plots=mock_plot_state,
    )