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

# Application Libraries
from app.assets.base import (
    Frame,
    Animation
)


pytest_plugins = [
    "tests.unit.fixtures.assets",
    "tests.unit.fixtures.components",
    "tests.unit.fixtures.configuration",
    "tests.unit.fixtures.menus",
    "tests.unit.fixtures.properties",
    "tests.unit.fixtures.state"
]


# ---------------------------------------------------------------------------
# -------------------------------------------------------------- MOCK CLASSES
# ---------------------------------------------------------------------------


class DummyFrame(Frame):
    def channels(self, id, state, properties): return []
    def keys(self, id, state): return [id]
    def index(self, id, properties): return {}


class DummyAnimation(Animation):
    def animate(self, state, properties): return state
