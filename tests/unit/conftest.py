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
    # -------------------------------
    "tests.unit.fixtures.assets",
    "tests.unit.fixtures.components",
    "tests.unit.fixtures.menus",
    "tests.unit.fixtures.services",
    "tests.unit.fixtures.structures",
    # -------------------------------
    "tests.unit.fixtures.configuration.compositions",
    "tests.unit.fixtures.configuration.groups",
    "tests.unit.fixtures.configuration.recipes",
    "tests.unit.fixtures.configuration.transitions",
    "tests.unit.fixtures.configuration.schemas",
    # -------------------------------
    "tests.unit.fixtures.properties.assets.cursors",
    "tests.unit.fixtures.properties.assets.crafts",
    "tests.unit.fixtures.properties.assets.effects",
    "tests.unit.fixtures.properties.assets.fonts",
    "tests.unit.fixtures.properties.assets.geography",
    "tests.unit.fixtures.properties.assets.objects",
    "tests.unit.fixtures.properties.assets.tiles",
    "tests.unit.fixtures.properties.assets.widgets",
    "tests.unit.fixtures.properties.assets.sheets",
    "tests.unit.fixtures.properties.assets.resources",
    "tests.unit.fixtures.properties.schemas",
    # -------------------------------
    "tests.unit.fixtures.state.assets.crafts",
    "tests.unit.fixtures.state.assets.effects",
    "tests.unit.fixtures.state.assets.objects",
    "tests.unit.fixtures.state.assets.sheets",
    "tests.unit.fixtures.state.assets.resources",
    "tests.unit.fixtures.state.assets.world",
    "tests.unit.fixtures.state.schemas",
    # -------------------------------
]

@pytest.fixture(autouse=True)
def patch_app_settings(monkeypatch):
    monkeypatch.setattr("app.config.settings.FLUID_INVALIDATION_DEBOUNCE_TICKS", 0)
    monkeypatch.setattr("app.config.settings.BASE_FLOW_SPEED", 20)
    monkeypatch.setattr("app.config.settings.TILE_HASH_SIZE", 32)