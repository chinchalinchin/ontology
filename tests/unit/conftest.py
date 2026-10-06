"""
# Ontology: tests.unit.conftest
"""
# Standard Libraries
import sys
from pathlib import Path

# External Libraries 
import pytest

# NOTE: Inject the src/ directory into the Python path prior to any local imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

pytest_plugins = [
    "tests.unit.fixtures.assets",
    "tests.unit.fixtures.components",
    # -------------------------------
    "tests.unit.fixtures.configuration.compositions",
    "tests.unit.fixtures.configuration.groups",
    "tests.unit.fixtures.configuration.recipes",
    "tests.unit.fixtures.configuration.transitions",
    "tests.unit.fixtures.configuration.schemas",
    # -------------------------------
    "tests.unit.fixtures.menus",
    # -------------------------------
    "tests.unit.fixtures.properties.cursors",
    "tests.unit.fixtures.properties.crafts",
    "tests.unit.fixtures.properties.effects",
    "tests.unit.fixtures.properties.fonts",
    "tests.unit.fixtures.properties.geography",
    "tests.unit.fixtures.properties.objects",
    "tests.unit.fixtures.properties.tiles",
    "tests.unit.fixtures.properties.widgets",
    "tests.unit.fixtures.properties.sheets",
    "tests.unit.fixtures.properties.resources",
    "tests.unit.fixtures.properties.schemas",
    # -------------------------------
    "tests.unit.fixtures.services",
    # -------------------------------
    "tests.unit.fixtures.state.crafts",
    "tests.unit.fixtures.state.effects",
    "tests.unit.fixtures.state.objects",
    "tests.unit.fixtures.state.sheets",
    "tests.unit.fixtures.state.resources",
    "tests.unit.fixtures.state.world",
    "tests.unit.fixtures.state.schemas",
    # -------------------------------
    "tests.unit.fixtures.structures"
]

@pytest.fixture(autouse=True)
def patch_app_settings(monkeypatch):
    monkeypatch.setattr("app.config.settings.FLUID_INVALIDATION_DEBOUNCE_TICKS", 0)
    monkeypatch.setattr("app.config.settings.BASE_FLOW_SPEED", 20)
    monkeypatch.setattr("app.config.settings.TILE_HASH_SIZE", 32)