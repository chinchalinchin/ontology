"""
# Ontology: tests.unit.test_app_game_logic_relations_shorelines
"""
# External Libraries
import pytest

# Application Libraries
from app.game.logic.relations.shorelines import ShorelineIndex


@pytest.mark.fluids
def test_shoreline_index_exact_match(mock_geography_properties):
    index = ShorelineIndex.from_properties(mock_geography_properties.shorelines)
    assert index.resolve("grass", "waterflow-01") == "grassy-shore"


@pytest.mark.fluids
def test_shoreline_index_substrate_fallback(mock_geography_properties):
    # Temporarily bind an unconditioned shoreline to test substrate fallback
    mock_geography_properties.shorelines["grassy-shore"].fluid = None
    index = ShorelineIndex.from_properties(mock_geography_properties.shorelines)

    assert index.resolve("grass", "unknown-fluid") == "grassy-shore"
    assert index.resolve("grass", None) == "grassy-shore"


@pytest.mark.fluids
def test_shoreline_index_unmapped_returns_none(mock_shoreline_index):
    assert mock_shoreline_index.resolve("unregistered-tile", "waterflow-00") is None
    assert mock_shoreline_index.resolve("unregistered-tile", None) is None


@pytest.mark.fluids
def test_shoreline_index_from_properties(mock_geography_properties):
    index = ShorelineIndex.from_properties(mock_geography_properties.shorelines)
    assert index.resolve("grass", "waterflow-01") == "grassy-shore"
    assert index.resolve("unregistered-tile", "waterflow-01") is None