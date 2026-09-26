"""
# Ontology: tests.unit.test_app_game_logic_relations_shorelines
"""
# External Libraries
import pytest

# Application Libraries
from app.game.logic.relations.shorelines import ShorelineIndex
from app.models.properties import GeographyProperties

# Cython Libraries
from libs.core.models import Dimensions

@pytest.mark.fluids
def test_shoreline_index_exact_match():
    entries = {
        ("grass", "water-clean"): "shore-grass-clean",
        ("grass", "water-murky"): "shore-grass-murky",
        ("sand", None): "shore-sand"
    }
    index = ShorelineIndex(entries)

    assert index.resolve("grass", "water-clean") == "shore-grass-clean"
    assert index.resolve("grass", "water-murky") == "shore-grass-murky"


@pytest.mark.fluids
def test_shoreline_index_substrate_fallback():
    entries = {
        ("sand", None): "shore-sand-default",
        ("grass", "water-clean"): "shore-grass-clean",
        ("grass", None): "shore-grass-default"
    }
    index = ShorelineIndex(entries)

    # Substrate fallback when fluid has no exact override
    assert index.resolve("sand", "lava") == "shore-sand-default"
    assert index.resolve("sand", None) == "shore-sand-default"
    assert index.resolve("grass", "unknown-fluid") == "shore-grass-default"


@pytest.mark.fluids
def test_shoreline_index_unmapped_returns_none():
    entries = {("dirt", "water"): "shore-dirt"}
    index = ShorelineIndex(entries)

    assert index.resolve("stone", "water") is None
    assert index.resolve("stone", None) is None


@pytest.mark.fluids
def test_shoreline_index_from_properties():
    props = {
        "grassy-river": GeographyProperties(
            dimensions=Dimensions(w=32, l=32),
            tile="grass-meadow",
            fluid="water-clean",
            thickness=8
        ),
        "rocky-shore": GeographyProperties(
            dimensions=Dimensions(w=32, l=32),
            tile="stone-cavern",
            fluid=None,
            thickness=10
        )
    }

    index = ShorelineIndex.from_properties(props)

    assert index.resolve("grass-meadow", "water-clean") == "grassy-river"
    assert index.resolve("stone-cavern", "any-fluid") == "rocky-shore"
    assert index.resolve("unregistered-tile", "water-clean") is None