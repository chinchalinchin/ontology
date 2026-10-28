"""
@domain.test
@test.config

# Ontology: tests.unit.conftest
"""
# Standard Libraries
import sys
from pathlib import Path

# External Libraries
import pytest

UNIT_DIR = Path(__file__).resolve().parent
ROOT_DIR = UNIT_DIR.parent.parent

# Inject src/ into Python path prior to local imports
sys.path.insert(0, str(ROOT_DIR / "src"))

pytest_plugins = [
    "tests.unit.fixtures.schemas",
    "tests.unit.fixtures.assets",
    "tests.unit.fixtures.components",
    "tests.unit.fixtures.menus",
    "tests.unit.fixtures.services",
    "tests.unit.fixtures.structures",
]

@pytest.fixture
def testbed():
    return "world-testbed"

@pytest.fixture(autouse=True)
def patch_app_settings(monkeypatch, tmp_path: Path):
    """
    Overrides settings and isolates save-state output to an ephemeral tmp_path.
    """
    monkeypatch.setattr("app.static.settings.SAVE_DIR", tmp_path / "saves")

    monkeypatch.setattr("app.static.settings.FLUID_INVALIDATION_DEBOUNCE_TICKS", 0)
    monkeypatch.setattr("app.static.settings.BASE_FLOW_SPEED", 20)
    monkeypatch.setattr("app.static.settings.TILE_HASH_SIZE", 32)