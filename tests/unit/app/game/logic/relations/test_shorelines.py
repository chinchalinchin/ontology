"""
@domain.test
@test.unit
@workflow.fluids

# Ontology: Tests - tests.unit.app.game.logic.relations.test_shorelines

Unit tests for ShorelineIndex.
"""
# Standard Libraries
from dataclasses import replace

# External Libraries
import pytest

# Application Libraries
from app.game.logic.relations.shorelines import ShorelineIndex
from app.models.properties import PropertiesSchema

# -----------------------------------------------------

pytestmark = [
    pytest.mark.workflow_fluids
]

# -----------------------------------------------------

def test_shoreline_index_exact_match(mock_shoreline_index: ShorelineIndex):
    assert mock_shoreline_index.resolve("temperate", "waterflow") == "temperate-banks"


def test_shoreline_index_substrate_fallback(
    mock_properties_schema: PropertiesSchema,
):
    shorelines = {
        k: replace(v, fluid=None)
        for k, v in mock_properties_schema.geography.shorelines.items()
    }
    index = ShorelineIndex.from_properties(shorelines)

    assert index.resolve("temperate", "unknown-fluid") == "temperate-banks"
    assert index.resolve("temperate", None) == "temperate-banks"


def test_shoreline_index_unmapped_returns_none(
    mock_shoreline_index: ShorelineIndex,
):
    assert mock_shoreline_index.resolve("unregistered-tile", "waterflow") is None
    assert mock_shoreline_index.resolve("unregistered-tile", None) is None


def test_shoreline_index_from_properties(
    mock_properties_schema: PropertiesSchema,
):
    index = ShorelineIndex.from_properties(
        mock_properties_schema.geography.shorelines
    )
    assert index.resolve("temperate", "waterflow") == "temperate-banks"
    assert index.resolve("unregistered-tile", "waterflow") is None